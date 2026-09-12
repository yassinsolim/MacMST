import collections
import hashlib

from dyld_cache import direct_branch_target


def function_edges(function):
    start = int(function["address_hex"], 16)
    instructions = function["instructions"]
    size = function["size"]
    if start < 0 or start % 4 or not 0 < size <= 32768 or size % 4 or start + size > 1 << 64:
        raise ValueError("Invalid call-graph function range")
    if len(instructions) * 4 != size:
        raise ValueError("Incomplete call-graph instruction coverage")
    raw = b"".join(bytes.fromhex(instruction["bytes_hex"]) for instruction in instructions)
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != function["bytes_sha256"]:
        raise ValueError("Call-graph function bytes do not match their hash")
    for index, instruction in enumerate(instructions):
        if int(instruction["address_hex"], 16) != start + index * 4 or len(bytes.fromhex(instruction["bytes_hex"])) != 4:
            raise ValueError("Call-graph instruction addresses are not contiguous")
    end = start + size
    pending = [start]
    visited = set()
    edges = []
    unresolved = []
    while pending:
        address = pending.pop()
        if address in visited:
            continue
        if not start <= address < end or address % 4:
            unresolved.append({"address_hex": hex(address), "reason": "FALLTHROUGH_OUTSIDE_FUNCTION"})
            continue
        visited.add(address)
        index = (address - start) // 4
        instruction = instructions[index]
        word = int.from_bytes(raw[index * 4:index * 4 + 4], "little")
        evidence = {"callsite_hex": hex(address), "bytes_hex": instruction["bytes_hex"],
                    "instruction": instruction["instruction"]}
        if instruction["instruction"] == "UNDECODED":
            unresolved.append({**evidence, "reason": "UNDECODED_INSTRUCTION"})
            continue
        target = direct_branch_target(raw[index * 4:index * 4 + 4], address)
        if target is not None:
            call = bool(word & 0x80000000)
            if call or not start <= target < end:
                edges.append({**evidence, "kind": "DIRECT_CALL" if call else "TAIL_BRANCH", "target_hex": hex(target)})
            else:
                pending.append(target)
            if call:
                pending.append(address + 4)
            continue
        conditional = None
        if word & 0xff000010 == 0x54000000 or word & 0x7e000000 == 0x34000000:
            immediate = (word >> 5) & 0x7ffff
            conditional = address + (immediate - 0x80000 if immediate & 0x40000 else immediate) * 4
        elif word & 0x7e000000 == 0x36000000:
            immediate = (word >> 5) & 0x3fff
            conditional = address + (immediate - 0x4000 if immediate & 0x2000 else immediate) * 4
        if conditional is not None:
            if start <= conditional < end:
                pending.append(conditional)
            else:
                edges.append({**evidence, "kind": "CONDITIONAL_TAIL", "target_hex": hex(conditional)})
            pending.append(address + 4)
            continue
        if word & 0xfffffc1f == 0xd65f0000 or word in (0xd65f0bff, 0xd65f0fff):
            continue
        if word & 0xfe000000 == 0xd6000000:
            unresolved.append({**evidence, "reason": "UNRESOLVED_INDIRECT_CONTROL_FLOW",
                               "preceding_instructions": instructions[max(0, index - 10):index]})
            if instruction["instruction"].split()[0].startswith("blr"):
                pending.append(address + 4)
            continue
        if word & 0xff000000 == 0xd4000000:
            if word & 0xffe0001f != 0xd4200000:
                unresolved.append({**evidence, "reason": "UNRESOLVED_EXCEPTION_TRANSFER"})
            continue
        pending.append(address + 4)
    return {"edges": sorted(edges, key=lambda edge: int(edge["callsite_hex"], 16)),
            "unresolved": unresolved, "reachable_instruction_count": len(visited)}


def resolve_vtable_slot(vtables, symbol, offset):
    tables = [table for table in vtables if table["symbol"] == symbol]
    if len(tables) != 1 or type(offset) is not int or offset < 0 or offset % 8:
        raise ValueError("Missing or ambiguous vtable, or invalid slot offset")
    table = tables[0]
    bindings = [binding for binding in table["bindings"] if binding["offset_from_primary_address_point"] == offset]
    if len(bindings) != 1:
        raise ValueError("Vtable slot lacks a unique declared binding")
    pointer = bindings[0]["pointer"]
    raw = bytes.fromhex(table["raw_bytes_hex"])
    position = 16 + offset
    if pointer["pointer_format"] != 8 or int(pointer["slot_address_hex"], 16) != int(table["address_hex"], 16) + position:
        raise ValueError("Vtable slot format or address mismatch")
    if position + 8 > len(raw) or raw[position:position + 8] != bytes.fromhex(pointer["raw_bytes_hex"]):
        raise ValueError("Vtable pointer bytes do not match table capture")
    return {"vtable_symbol": symbol, "offset": offset, "pointer": pointer,
            "table_sha256": hashlib.sha256(raw).hexdigest(),
            "target_hex": pointer["target_address_hex"],
            "exact_symbol_matches": bindings[0]["exact_symbol_matches"],
            "receiver_scope": "Analyst-selected receiver context; pointer binding alone does not prove this receiver reaches this callsite."}


def bounded_call_graph(load_function, roots, sinks, node_limit=64, depth_limit=8, virtual_edges=None):
    if not roots or len(roots) > 32 or not 1 <= node_limit <= 512 or not 0 <= depth_limit <= 32:
        raise ValueError("Invalid call-graph traversal bounds")
    if any(type(address) is not int or address < 0 or address >= 1 << 64 or address % 4 for address in (*roots, *sinks)):
        raise ValueError("Invalid graph root or sink address")
    virtual_edges = virtual_edges or {}
    if len(virtual_edges) > 128:
        raise ValueError("Excessive contextual virtual edges")
    results = []
    for root in sorted(set(roots)):
        pending = collections.deque([(root, [], 0)])
        visited = set()
        nodes = []
        gaps = []
        sink_paths = []
        while pending:
            address, path, depth = pending.popleft()
            if address in visited:
                continue
            visited.add(address)
            if depth > depth_limit or len(nodes) >= node_limit:
                gaps.append({"address_hex": hex(address), "path": path, "reason": "TRAVERSAL_LIMIT"})
                continue
            try:
                function = load_function(address)
                if int(function["address_hex"], 16) != address:
                    raise ValueError("Target is not an exact function start")
                analysis = function_edges(function)
            except (ValueError, KeyError) as error:
                gaps.append({"address_hex": hex(address), "path": path,
                             "reason": "MISSING_OR_INVALID_FUNCTION", "detail": str(error)})
                continue
            if address in sinks:
                sink_paths.append({"sink_hex": hex(address), "path": path,
                                   "bytes_sha256": function["bytes_sha256"]})
                continue
            nodes.append({"address_hex": hex(address), "size": function["size"],
                          "bytes_sha256": function["bytes_sha256"],
                          "symbols": function.get("symbols", []), **analysis})
            for unresolved in analysis["unresolved"]:
                receipt = virtual_edges.get(int(unresolved.get("callsite_hex", "0"), 16))
                if receipt is not None and unresolved["reason"] == "UNRESOLVED_INDIRECT_CONTROL_FLOW":
                    edge = {"from_hex": hex(address), "callsite_hex": unresolved["callsite_hex"],
                            "bytes_hex": unresolved["bytes_hex"], "kind": "CONTEXTUAL_VTABLE", **receipt}
                    analysis["edges"].append(edge)
                    gaps.append({"address_hex": hex(address), "path": path, **unresolved,
                                 "reason": "RECEIVER_CONTEXT_REQUIRES_PROOF", "candidate_binding": receipt})
                else:
                    gaps.append({"address_hex": hex(address), "path": path, **unresolved})
            for edge in analysis["edges"]:
                pending.append((int(edge["target_hex"], 16), [*path, {"from_hex": hex(address), **edge}], depth + 1))
        results.append({"root_hex": hex(root), "nodes": nodes, "gaps": gaps, "sink_paths": sink_paths,
                        "complete": not gaps,
                        "status": "CALL_GRAPH_INCOMPLETE" if gaps else "SINK_PATH_PRESENT" if sink_paths else "COMPLETE_NO_SELECTED_SINK"})
    return {"roots": results, "node_limit_per_root": node_limit, "depth_limit": depth_limit,
            "sink_addresses_hex": [hex(address) for address in sorted(set(sinks))],
            "scope": "Syntactic reachability from exact function starts; both conditional outcomes retained. No value/receiver analysis or hardware execution. Indirect calls, missing boundaries and traversal limits prevent a complete absence proof."}