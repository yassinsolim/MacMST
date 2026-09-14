# MacMST

Experimental investigation of native DisplayPort MST on Apple Silicon,
currently targeting Apple M5. **Whether native MST can be enabled is unknown.**
MacMST is at the research/probe stage: it does not enable MST or make private
DPCD calls, and it is not an MST driver or DisplayLink replacement.
The default executable is a public read-only probe. A separately gated, opt-in
DPDV open/close helper now exists. After an initial preflight stop and explicitly
renewed authorization during recovery, it completed one open/immediate-close with
unchanged public display state. No selector or DPCD operation was performed.

## Build And Probe

Prerequisites: Xcode/Command Line Tools with a C++20 compiler, CMake, and Ninja
(or another CMake generator). Tests and the independent capture tool also use
Python 3.9 or newer. No third-party libraries are downloaded.

```sh
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug -DMACMST_ENABLE_HARDWARE_TESTS=OFF -DMACMST_ENABLE_DPDV_OPEN_EXPERIMENT=OFF
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

The unit suite also includes a mock-only isolated helper, with crash/timeout,
protocol, descriptor and reaping checks. Run it alone with
`ctest --test-dir build -R '^mock_helper_isolation$' --output-on-failure`.
It is not linked into production macmst and does not open any display interface.
A watchdog result is not evidence of kernel/DCP cancellation.

The [DPCD decoder](src/displayport/dpcd/capabilities.hpp) has no macOS dependency.
It decodes synthetic or future acquired receiver bytes, not a fabricated AUX
transport. On non-Apple hosts CMake builds the generic library/tests, not the
macOS CLI; that cross-platform build has not yet been executed here.

## Research Status

| Area | Current Status |
| --- | --- |
| External DCPDP path | Identified for the recorded M5/hub topology. |
| IODP read ABI | Substantially reconstructed through static analysis. |
| DPDV selector-0 path | RETIRED_ON_DAILY_USE_M5; historical reconstruction is not an available transport. |
| DCP RPC safety | Static expansion of this transport stopped after M2I; critical gates remain unresolved. |
| Public framebuffer/I2C route | Unavailable on the recorded active M5 external path; no type-4 advertisement observed. |
| Isolated DPDV open-check | One open/immediate-close runtime validated with zero selectors; in-flight-read teardown remains unproved. |
| One-byte selector readiness | NOT_READY_FOR_ONE_BYTE_DPCD_READ; NO_TRANSPORT_READY. |
| In-flight read termination | INFLIGHT_READ_TERMINATION_NOT_PROVEN; no guaranteed response-independent completion/drain of the DCP context wait. |
| Exact W06 wake/removal proof | W06_WAKE_STATE_UNRESOLVED; abandon this selector transport on the daily-use Mac. |
| Native DPCD access | Not yet exercised. |
| MST control baseline | M5_DCP_FIRMWARE_MST_CONTROL_EVIDENCE_FOUND_PACKETIZER_UNRESOLVED; identified M5 firmware has MST codec/topology and payload controls. |
| One-link MST packetizer | M5_DCP_MST_PACKETIZER_PRESENT_BUT_STREAM_BINDING_UNRESOLVED; concrete source slot-table and activation code found, but independent multi-stream binding and an architectural one-stream limit remain unproved. |
| Final stream ownership | M5_DCP_STREAM_OWNERSHIP_UNRESOLVED; MACMST_ARCHITECTURAL_VIABILITY_UNRESOLVED. Static packetizer expansion stopped after M3D. |
| Static feasibility ceiling | MACMST_STATIC_FEASIBILITY_INCONCLUSIVE; STATIC_PACKETIZER_ANALYSIS_FROZEN; NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED. |
| Evidence handoff | SACRIFICIAL_DYNAMIC_EXPERIMENT recommended conceptually on a separately approved non-daily-use system; no experiment authorized or performed. Implementation resume gates A-E are unmet. |
| Sacrificial design gate | [M4P](docs/research/m5-sacrificial-dynamic-design.md): SACRIFICIAL_EXPERIMENT_REQUIRES_UNAVAILABLE_CAPABILITY. No qualified M5 ownership observer or informative ordinary stimulus established; no experiment or security change performed. |
| Observer development scope | [M4Q](docs/research/m5-observer-gap.md): M5_OBSERVER_REQUIRES_MAJOR_PLATFORM_ENABLEMENT for the current m1n1 path. Wait for upstream M5 guest/observation support; sacrificial purchase is premature. No implementation or experiment performed. |

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
Complete-reply/firmware semantics and selector-call authorization remain unresolved.
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
That investigation was integrated into main by merge
`dd439c80f7b1190f0e033dcf1a19242de2bd3039`, with both completed research branches
retained. It does not change the private-path gates or claim absent AUX/MST hardware.

M2C on `research/dpdv-isolation-safety` traces current user-client close/death,
deferred finalization and AFK command release, and adds a test-only mock helper.
Its [separate open-check matrix](docs/research/dpdv-isolation-safety.md#open-check-readiness-matrix)
remains **NOT_READY_FOR_ISOLATED_DPDV_OPEN_CHECK**. No private open or selector
was invoked, and **NOT_READY_FOR_DPCD_TEST** is unchanged. The proposed
`macmst experimental dpdv-open-check` command is not implemented.

M2C was integrated into main by merge
`a7dc7d647e3e8fccb2e40e5cd56e3f9a8410697b`, with its branch and the baseline tag
retained. M2D on `research/dpdv-open-path-proof` now separates
[pre-selector open/close work from method dispatch](docs/research/dpdv-open-path.md).
The user-client gate is passive and provider close is owner-guarded, but meaningful
indirect/lifecycle gaps leave **CALL_GRAPH_INCOMPLETE**. The
[applicability matrix](docs/research/dpdv-open-path.md#gate-applicability-matrix)
does not automatically import selector cancellation risks into open-only.
The isolated-open result remains not ready; no private backend or transaction
was added, and the DPCD gate is unchanged.

M2D is integrated by merge `73e0caaaf079b2177d5207f2320c5fc61dac9117`.
M2E on `research/dpdv-open-final-proof` identifies the ordinary shared workloop,
proves local removal for a never-used native gate, and separates task ownership
from provider-open ownership. The alternate user-server factory route remains
unexcluded. The [current 20-gate matrix](docs/research/dpdv-open-path.md#m2e-applicability-matrix)
therefore remains **NOT_READY_FOR_ISOLATED_DPDV_OPEN_CHECK** for specific
ownership/work/close uncertainties, not generic graph incompleteness.

M2E is integrated by merge `ce28518eb301592ed6dd3d2b75d152b1a8e54970`.
The focused [M2E.1 runtime discriminator](docs/research/dpdv-open-path.md#m2e1-runtime-userserver-discriminator)
on `research/dpdv-userserver-discriminator` verifies native provider provenance,
but no tested public marker proves the private userServer field's value.
It returns **USER_SERVER_RUNTIME_STATE_UNRESOLVED** and stops static expansion;
both not-ready gates remain unchanged. No private open or privileged inspection
was performed.

M2E.1 is integrated at `1fc8f0241acec829fa732503c13a9ab588e26fb0`, tagged
`pre-dpdv-open-v0.2` before adding the real helper. [M2F](docs/research/dpdv-open-check.md)
on `experiment/dpdv-open-check` built and audited the isolated open-only tools,
but its fresh dry-run preflight found both displays inactive and DP LinkRate=0.
It stopped before helper selection: **EXPERIMENT_NOT_RUN**, zero opens/closes,
no retry. **NOT_READY_FOR_DPCD_TEST** remains unchanged.

After a new recovery request and explicit approval on 2026-09-13 UTC, the committed
no-open check passed and one real DPDV open/close returned success with no sampled
public display change. [The runtime record](docs/research/dpdv-open-check.md#recovery-and-renewed-authorization)
establishes **DPDV_OPEN_CLOSE_RUNTIME_VALIDATED**, not a null userServer or safe
selector path. The one-shot marker is consumed; no retry. The global
**NOT_READY_FOR_DPCD_TEST** gate remains unchanged.

That runtime state is integrated at `3f5f0cd887ed2ef5c8dbadc9abb278792c3150be`
and annotated as `dpdv-open-runtime-v0.3`. [M2G's one-byte reassessment](docs/research/selector0-one-byte-readiness.md)
on `research/selector0-one-byte-readiness` compares both transports and checks the
exact selector-0/address-0x000/length-1 contract. It finds
**NO_TRANSPORT_READY** and **NOT_READY_FOR_ONE_BYTE_DPCD_READ**: one byte does
not bound the kernel wait, recover the lost reply length or establish read
cancellation. The pure revision classifier and short-reply tests do not implement
a transport. M2G repeats no private open/close and creates no read-attempt marker.

M2G is integrated at `2b1565ee61337a368d75980af281621a5959000e`, tagged
`selector0-safety-v0.4`. [M2H's in-flight termination investigation](docs/research/inflight-read-termination.md)
on `research/inflight-read-termination` traces the exact stack-context wait,
command ownership, concurrent close, task death and disconnect paths. It reports
**INFLIGHT_READ_TERMINATION_NOT_PROVEN**. The raw uninterruptible/no-deadline
wait has no proved response-independent completion-and-drain contract; conditional
error synthesis and list cleanup are different paths. Constant 500 remains an
opaque firmware parameter, not a demonstrated host deadline. No transport or
readiness gate is promoted, and no private operation or read helper is added.

M2H is integrated at `1a014d8d3c3cd35ed5381160b809cf4803d79d69`, tagged
`inflight-read-safety-v0.5`. [M2I's exact W06 proof](docs/research/w06-wake-or-strand.md)
on `research/w06-wake-or-strand` establishes the stack context/event and confirms
that suspicious cleanup targets this read's pending list. It does not prove the
required cleanup-trigger ordering or universal callback quiescence:
**W06_WAKE_STATE_UNRESOLVED**. **Further static expansion of this selector
transport is stopped; abandon it on the daily-use Mac.** No selector test or
another generic graph-search milestone is proposed. NO_TRANSPORT_READY and both
not-ready execution gates remain unchanged; no proven unsafe lifetime claim or
M5 hardware capability conclusion is inferred from the unresolved result.

M2I is integrated at `a882c1dc75501c03347050f1cdb91c38df2af39d`, tagged
`selector0-retired-v0.6`. Selector 0 is **RETIRED_ON_DAILY_USE_M5**.
[M3A source feasibility](docs/research/m5-mst-source-feasibility.md) pivots to the
M5 source implementation: a pinned Linux signature oracle and static scan of 13
kernel/11 userspace images find no qualified host sideband codec, topology model
or payload allocator. The DCP firmware stream-to-payload packetizer remains
opaque, so the result is **M5_MST_SOURCE_FEASIBILITY_UNRESOLVED**, not a finding
that M5 cannot implement MST. The global gate is **NOT_READY_FOR_DPCD_TEST**.
No private operation, new selector transport or hardware experiment is proposed.

M3A is integrated at `24f2d1c3065ec0d7f80b5a53077f3e169f79368f`, tagged
`m5-mst-host-scan-v0.7`. [M3B's firmware investigation](docs/research/m5-dcp-firmware-mst.md)
uses the exact 25G83 BuildIdentity for Mac17,2/J704AP, which references
`Firmware/dcp/t8142dcp.im4p`. Range-only extraction and offline analysis identify
a real MST sideband codec, routed topology and payload/ACT control primitives.
The result is **M5_DCP_FIRMWARE_MST_CONTROL_EVIDENCE_FOUND_PACKETIZER_UNRESOLVED**:
multiple independently timed streams on one DPTX link are not established.
M3A's host negative is preserved; the firmware is not byte-identical to the
selected M4 image, although the MST diagnostics and exact CRC leaves are shared.
M3B's then-next ownership question was examined in M3C/M3D and is now frozen.
Selector 0 remains **RETIRED_ON_DAILY_USE_M5**; no private operation occurred.

M3B is integrated at `c89bf66bac79893f4e6910e10d4a1126775edce7`, tagged
`m5-dcp-mst-control-v0.8`. [M3C's one-link packetizer investigation](docs/research/m5-dcp-mst-packetizer.md)
traces the source record, selected-device descriptor, register-table writes and
ACT trigger in the retained M5 firmware. Result:
**M5_DCP_MST_PACKETIZER_PRESENT_BUT_STREAM_BINDING_UNRESOLVED**.
The recovered path replaces one table using payload ID 1; neither that literal
nor its 64 slot fields proves an architectural stream limit or multi-stream
support. M3C authorized one final packetizer-object ownership pass, completed below.
No private operation or hardware experiment occurred; selector retirement and
**NOT_READY_FOR_DPCD_TEST** are unchanged.

M3C is integrated at `5beb1ac304a1715dc9fb7cad9b3322819b8fd140`, tagged
`m5-dcp-packetizer-v0.9`. [M3D's final ownership proof](docs/research/m5-dcp-stream-ownership.md)
finds runtime controller registration, collection-based attachment, scalar
selected-device replacement and scalar current timing. It proves neither
multiple concurrent source contexts on one physical DPTX nor a hard one-stream
architectural limit: **M5_DCP_STREAM_OWNERSHIP_UNRESOLVED** and
**MACMST_ARCHITECTURAL_VIABILITY_UNRESOLVED**. The single remaining opacity is
runtime source-controller membership of one physical T8142 DPTX register owner.
**Stop static packetizer expansion.** No M3E graph search or M4A host-control
discovery is proposed. M3C's packetizer baseline, selector retirement and DPCD
gate remain unchanged; M3D performed zero hardware/private display operations.

M3D is integrated at `c5bc1b1bacd7742a4bbc1b54285336e9d51302a5`, permanently
tagged `m5-mst-static-ceiling-v1.0`. [M3E0's static conclusion and handoff](docs/research/m5-mst-static-conclusion.md)
freezes **MACMST_STATIC_FEASIBILITY_INCONCLUSIVE** without weakening the proven
MST control/source packetizer or claiming a global single-stream limit.
The frozen opacity is:
**Runtime source-controller membership of one physical T8142 DPTX register owner.**
The handoff compares exactly four new evidence sources
and recommends only a separately risk-reviewed **SACRIFICIAL_DYNAMIC_EXPERIMENT**
on a non-daily-use system. No experiment is implemented or executed; all
[implementation resume gates](docs/research/m5-mst-static-conclusion.md#implementation-resume-gate)
remain unmet. **STATIC_PACKETIZER_ANALYSIS_FROZEN** and
**NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED** apply.

For a fresh clone, build the probe before optionally creating a public capture:

```sh
python3 tools/capture_baseline.py --probe build/macmst
```

The collector prints a new UTC-named directory. The following source-feasibility
commands are historical reproduction examples, not authorized next work after
the static ceiling:

```sh
python3 tools/scan_mst.py --inventory --output artifacts/probes/m3a-local/inventory.json
python3 tools/scan_mst.py --kernel-image com.apple.iokit.IODisplayPortFamily --output artifacts/probes/m3a-local/dp.json
```

This parses local image files, requires a running-kernel UUID match and never
invokes private IODP functions or updater code. See the
[M3A reproduction and scope](docs/research/m5-mst-source-feasibility.md#tooling-provenance-and-reproduction).
Earlier static/selector investigation commands and next-step proposals are
historical, not instructions to resume packetizer analysis or that transport. The proposed
`macmst experimental dpcd-read` command is not implemented.

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
- [M2C isolation, teardown and open-only safety](docs/research/dpdv-isolation-safety.md)
- [M2E.1 discriminator and historical open-only proofs](docs/research/dpdv-open-path.md)
- [M2G one-byte selector contract and 19 readiness gates](docs/research/selector0-one-byte-readiness.md)
- [M2H in-flight read lifetime, waits and termination result](docs/research/inflight-read-termination.md)
- [M2I exact W06 wake/removal proof and mandatory stop](docs/research/w06-wake-or-strand.md)
- [M3A M5 MST source feasibility and firmware boundary](docs/research/m5-mst-source-feasibility.md)
- [M3B identified M5 DCP firmware, MST controls and packetizer limit](docs/research/m5-dcp-firmware-mst.md)
- [Pinned MST source signature oracle](docs/research/mst-source-signatures.json)
- [Protocol constants and decoding](docs/research/displayport-mst.md)
- [Language/architecture ADR](docs/adr/0001-language-and-architecture.md)

## License

No project license has been selected or included. This baseline does not grant
a reuse license. Linked upstream projects retain their own licenses.