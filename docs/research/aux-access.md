# Native AUX Investigation

## Current Result

RPC-03 update: the owner-controlled ZMUIPNG connected/disconnected/reconnected
cycle associates an External DCPEXT0 path with the hub. CF lifecycle, exact caller
bindings and host selector-0 dispatch are now resolved. The host sends a DCP
register RPC. Its host buffer is zero-filled, but its wait has no local deadline,
the selected abort hook is a no-op, and complete firmware/read-only/authorization
guarantees remain unestablished: **NOT_READY_FOR_DPCD_TEST**.
See [the lower RPC contract](dcp-dpcd-rpc-03.md),
[authorization analysis](dpdv-authorization.md) and
[external differential](external-dock-diff.md). The B03 observations below remain
historical evidence, not a claim that the current topology is internal-only.

`VERIFIED_ON_M5` (E014): **IODPDeviceReadDPCD resolves in the running probe**,
along with IODPDeviceCreateWithService, IODPDeviceWriteDPCD, and
IODPServiceGetDevice. One Embedded DCPDPDeviceProxy and one Embedded
DCPDPServiceProxy are present. No private function was invoked.

`PRIMARY_SOURCE` (S10): the installed IOKit linker stub exports those names.
It also exports IOAVService I2C/EDID/property/link functions and IODP controller
configuration functions. Export names do not disclose a verified private ABI.

`HYPOTHESIS`: the IODP device family may provide the needed userspace DPCD path.
It is a stronger investigation lead than guessing IOAVServiceReadAUX names, but
is not a demonstrated native AUX transport. **Do not call a guessed prototype.**

## Separate The Interfaces

| Interface | Evidence | What Remains Unknown |
| --- | --- | --- |
| Public CoreGraphics/registry APIs | VERIFIED_ON_M5: the probe enumerates logical displays and selected registry properties without IOServiceOpen/IOConnect calls. | These APIs do not expose live AUX in this implementation. |
| Public IOI2C API | PRIMARY_SOURCE S03: native transaction type 4; framebuffer/bus interface required; IOI2CSendRequest return and request.result are distinct. | No IOFramebuffer/IOI2CInterface match in B03; applicability to another attached M5 path unknown. |
| Private IOAVService I2C | PRIMARY_SOURCE S06/S07: chip-address/register calls used for DDC; VERIFIED_ON_M5 E013: functions resolve. | Actual I2C-over-AUX operation on this M5/dock; routing and permission requirements. |
| Private IODPDevice DPCD | VERIFIED_ON_M5 E014/E040: symbol and External client class; PRIMARY_SOURCE E041-E049: CF lifecycle, bound caller, machine ABI and selector-0 host routing. | Complete reply, bounded wait, caching, actual permissions and native read-only DCP/AUX behavior. |
| DCP/EPIC services | PRIMARY_SOURCE S04/S05: EDID-copy and PHY/link-control protocols in Asahi/m1n1. | Exact M5 firmware ABI and whether a native read method is exposed via macOS. |

DDC/CI Get operations can involve an I2C write of a request followed by an I2C
read. This phase did not even perform those operations. Do not treat a utility's
read command as proof it only sends bus reads, and do not run m1ddc experimentally
without inspecting the particular command's behavior first.

Native AUX reads use a DPCD address and an AUX-native opcode; I2C-over-AUX uses a
different transaction type and address interpretation (S01). An I2C register
offset of `0x21` is not access to `DP_MSTM_CAP` at native address `0x00021`.

## Competing Explanations

| Candidate | Current Classification | Discriminating Evidence Needed |
| --- | --- | --- |
| A: only DDC/I2C is exposed to userspace on the relevant external path | HYPOTHESIS | A verified IODP/native read on that path would disprove the word only. Symbol presence alone does not. |
| B: a private userspace native-AUX method exists and works | HYPOTHESIS | Recover and verify IODPDeviceReadDPCD's ABI and external binding; an approved, bounded read must return meaningful bytes. |
| C: a kernel/DCP native-AUX path exists but is not directly exposed | HYPOTHESIS | Trace a source-backed user-client/EPIC path, including unsupported branches and entitlement checks; absence of one export is insufficient. |
| D: the usable path needs a new kernel/system component | UNKNOWN | Exhaust supported/private user paths with evidence first; no custom component or security change is authorized. |
| E: DCP abstraction prevents access to native AUX | HYPOTHESIS | Show the precise abstraction boundary/limitations; firmware ownership alone does not imply inaccessibility or absent physical AUX. |

These are scoped alternatives, not exhaustive silicon explanations. None has
been selected as the conclusion. Separately, **MST source hardware remains UNKNOWN**
even if B is eventually demonstrated.

## Smallest Safe Discriminating Experiment

The [M2-01 correlation](external-dock-diff.md#correlation-status) has now been
completed for the owner-identified ZMUIPNG hub. Embedded services are still never
substitutes for the correlated External target. ABI-02 resolves object lifecycle
and host user-client dispatch. The remaining gates are the lower RPC/firmware
completion and read-only contracts, as described in
[the current readiness gates](dcp-dpcd-rpc-03.md#readiness-gates).

After M2-01, the smallest native-AUX experiment has these gates:

1. **Complete the remaining static contract first:** preserve ABI-02's exact
   current-image lifecycle, argument and dispatch evidence; resolve lower reply
   validation, firmware-native read semantics and bounded waiting. A debugger
   attachment failed earlier and must not be retried with weakened security.
   Symbol names alone remain insufficient. No kernel attachment, firmware
   modification or security-setting change is permitted.
2. **Bind deliberately:** match the observed External device by path/Unit and
   topology; never use an unqualified default service that could address the
   internal panel. Establish whether object creation opens a client or changes
   state, and whether the function reads live hardware or returns cached data.
3. **Request explicit approval for the private-interface experiment.** Then, and
   only with verified lifecycle/read semantics and the correlated External target,
   the first operation is exactly **one byte at `0x000` (DPCD_REV)**. Do not read
   `0x021` or additional capabilities as the first transport test. Retain raw bytes,
   requested length and any independently established completion information,
   raw return codes, timing, service path, OS/SDK,
   topology, and decoder output. No register writes, retries without bounds,
   unknown selectors, IOConnect fuzzing, or fallback to the internal display.
   This wrapper discards actual output size; never fabricate a returned count.
4. An independently attributable native AUX read would disprove A/E for the
   tested path; a plausible byte alone cannot exclude cached data. A failure
   must distinguish no device, permission, unsupported operation, timeout,
   malformed ABI, and stale/disconnected service. No single failure establishes
   D or proves absent hardware. If provenance/semantics remain ambiguous, stop.

This experiment was **not executed**. No private prototypes or selector guesses
were added to the code. There is no AuxTransport implementation to accidentally
report as available.

## Sideband And Firmware

`PRIMARY_SOURCE` (S01): MST sideband buffers and MST enable controls occupy
separate DPCD ranges. Sending even a topology-discovery request writes messages
and may require state-changing setup. It is outside this phase. The existence
of IODPDeviceWriteDPCD is not permission to invoke it.

`UNKNOWN`: source MST packetizer, payload allocation/ACT handling, multi-stream
scanout routing, or dormant firmware support. DPCD-readable receivers do not
settle those questions. A complete negative conclusion would require much more
than a missing userspace selector or the limitations of one firmware ABI.

Sources and revisions: [S01, S03-S11 in the ledger](evidence-ledger.md#primary-and-reproducible-source-catalog).