# MacMST

Experimental, read-only investigation of native DisplayPort MST on Apple Silicon,
currently targeting Apple M5. **Whether native MST can be enabled is unknown.**
MacMST is at the research/probe stage: it does not enable MST or make private
DPCD calls, and it is not an MST driver or DisplayLink replacement.

## Build And Probe

Prerequisites: Xcode/Command Line Tools with a C++20 compiler, CMake, and Ninja
(or another CMake generator). Tests and the independent capture tool also use
Python 3.9 or newer. No third-party libraries are downloaded.

```sh
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug -DMACMST_ENABLE_HARDWARE_TESTS=OFF
cmake --build build
ctest --test-dir build -L unit --output-on-failure
build/macmst probe
build/macmst probe --json
```

The probe uses public sysctl, CoreGraphics and IORegistry reads. It inspects
selected library symbols with `dlsym` but never invokes private AV/DP functions,
opens a user client, or sends DDC/AUX/MST transactions. It does not change display
or system settings. No sudo or security-setting changes are needed.

Output includes host, logical displays, DCP/DCPEXT-related registry paths and
immediate parent/child identities, published port/link fields, USB candidates,
symbol visibility, and conservative External device/service candidates. Pairings
and single-active-context associations are labeled `INFERRED`, not proven physical
routes. DPCD read capability remains `UNVERIFIED`; no private object is acquired.
Public DisplayPort diagnostics select only one active external display, inspect
the public CG service mapping, and conditionally enumerate framebuffer I2C buses
and transaction masks. No I2C interface is opened and no request is sent. Missing
targets, zero counts, API errors and unknown masks are reported separately.
A USB candidate is not automatically the dock.
Exit codes: 0 for a collected report, 1 for observation/report failure, 2 for
invalid arguments. Exit 0 does not establish any bus or MST functionality.

## Reproducible Captures

```sh
python3 tools/capture_baseline.py --probe build/macmst
```

Creates a new ignored `artifacts/probes/<UTC timestamp>/` directory with selected
raw profiler/registry values, CLI JSON, environment and SDK metadata, commands,
errors, and SHA-256 hashes. Serials, UUIDs, raw EDID and opaque/private properties
are omitted before saving. Artifacts are not complete raw machine dumps; review
product descriptors before sharing. Never commit credentials or unrelated data.

## Separate Hardware Validation

The normal unit suite does not enumerate hardware. Opt in explicitly:

```sh
cmake -S . -B build -DMACMST_ENABLE_HARDWARE_TESTS=ON
cmake --build build
ctest --test-dir build -L hardware --output-on-failure
```

For deterministic sanitizer tests:

```sh
cmake -S . -B build-sanitized -G Ninja -DCMAKE_BUILD_TYPE=Debug -DMACMST_ENABLE_SANITIZERS=ON
cmake --build build-sanitized
ctest --test-dir build-sanitized -L unit --output-on-failure
```

The [DPCD decoder](src/displayport/dpcd/capabilities.hpp) has no macOS dependency.
It decodes synthetic or future acquired receiver bytes, not a fabricated AUX
transport. On non-Apple hosts CMake builds the generic library/tests, not the
macOS CLI; that cross-platform build has not yet been executed here.

## Research Status

| Area | Current Status |
| --- | --- |
| External DCPDP path | Identified for the recorded M5/hub topology. |
| IODP read ABI | Substantially reconstructed through static analysis. |
| DPDV selector-0 path | Reconstructed through the host-side read RPC. |
| DCP RPC safety | Under investigation; critical gates remain unresolved. |
| Public framebuffer/I2C route | Unavailable on the recorded active M5 external path; no type-4 advertisement observed. |
| Native DPCD access | Not yet exercised. |
| MST source capability | Unknown. |

The owner-controlled connected/disconnected/reconnected test now associates the
External **DCPEXT0 / Unit 0** DP/AV path with a **ZMUIPNG 14-in-1 hub** on the
right-side USB-C socket. Both physical VG248 panels show the same image according
to the owner, while macOS enumerates one external logical display. Published
transport state reports USB-C port 4, two lanes, HBR3, and no tunneling. This
experiment was not performed with the earlier HP dock.

All 97 inventoried IODP names resolve. ABI-02 resolves the CF lifecycle,
authenticated PS190 caller bindings, DPDV client routing and selector-0 host
read path. RPC-03 traces the lower AFK path: the host buffer is zero-filled,
but the DCP wait has no local deadline and its selected abort hook is a no-op.
Complete-reply/firmware semantics and actual process authorization remain unresolved.
**NOT_READY_FOR_DPCD_TEST**. No native AUX or DPCD transaction has been executed;
MST source support remains unknown.

The `research/dcp-rpc-safety` follow-up revalidates the External path and adds
deadline-free admission waits, conditional recovery triggers, concrete endpoint
cleanup and fresh signing/policy evidence. Its [explicit readiness matrix](docs/research/dcp-dpcd-rpc-03.md#readiness-gates)
keeps reply completeness, bounded waiting and cancellation blocked. It was
integrated into main by merge `2ffc77d9d532502495fca5d88291d42eed61e45b`; the
`research-baseline-v0.1` tag and the completed research branch are retained.

The separate `research/public-dp-native` investigation reports
**PUBLIC_IOFRAMEBUFFER_PATH_UNAVAILABLE** for the active M5 external display:
public CG mapping returns null and independent registry queries find no
IOFramebuffer/I2C interfaces. No count-call IOReturn or zero mask is fabricated
when no target exists. See [the public-path evidence and limits](docs/research/public-dp-native.md).
This branch does not change the private-path gates or claim absent native AUX/MST
hardware, and has not been merged into main.

For a fresh clone, first build the probe and create your own public capture:

```sh
python3 tools/capture_baseline.py --probe build/macmst
```

The collector prints a new UTC-named directory. Substitute that directory for
`YYYYMMDDTHHMMSSZ` when running the attachment-free static inspection:

```sh
python3 tools/inspect_iodp.py --baseline artifacts/probes/YYYYMMDDTHHMMSSZ --server
```

This resolves symbols but never invokes private IODP functions or updater code.
It retains raw bytes, declared cache-fixup chains and LLVM cross-checks. Optional
`--server` reads/decompresses the local arm64 boot image in memory and requires
a running-kernel UUID match; it never loads the image or weakens security.
The [RPC-03 readiness gates](docs/research/dcp-dpcd-rpc-03.md#readiness-gates)
must be satisfied before a separately approved one-byte read at `0x000` is
considered. The proposed `macmst experimental dpcd-read` command is not implemented.

Historical capture identities, hashes, binary UUIDs and preferred addresses in
the reports are deliberate provenance, not reusable device handles or portable
call targets. Raw captures, copied upstream sources, Apple binaries, builds and
local editor configuration are excluded from Git. A fresh clone does not contain
those artifacts; reproduce observations locally and check hardware/OS identity
before comparing findings. No Apple binary is distributed by this project.

- [Execution plan and verification](docs/research/README.md)
- [Evidence ledger and exact sources](docs/research/evidence-ledger.md)
- [M5/DCP stack baseline](docs/research/m5-display-stack.md)
- [Native AUX investigation](docs/research/aux-access.md)
- [Dock observations](docs/research/dock-observations.md)
- [Connected/disconnected differential and graph](docs/research/external-dock-diff.md)
- [IODP API and M2-02 readiness](docs/research/iodpdevice-api.md)
- [ABI-02 lifecycle, dispatch and remaining safety gates](docs/research/iodpdevice-abi-02.md)
- [RPC-03 request/reply, wait and cancellation contract](docs/research/dcp-dpcd-rpc-03.md)
- [DPDV authorization analysis](docs/research/dpdv-authorization.md)
- [Public DisplayPort-native API and M5 enumeration](docs/research/public-dp-native.md)
- [Protocol constants and decoding](docs/research/displayport-mst.md)
- [Language/architecture ADR](docs/adr/0001-language-and-architecture.md)

## License

No project license has been selected or included. This baseline does not grant
a reuse license. Linked upstream projects retain their own licenses.