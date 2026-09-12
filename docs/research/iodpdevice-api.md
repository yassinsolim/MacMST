# IODPDevice API Investigation (Milestone 2A)

**Historical A1 report.** [M2A-ABI-02](iodpdevice-abi-02.md) now resolves CF
cleanup, authenticated caller bindings and the host DPDV/selector-0 path.
Readiness remains NOT_READY_FOR_DPCD_TEST because complete-reply/bounded-wait
assurance and native read-only DCP semantics remain unestablished. The text below
preserves what was and was not established during A1.

## Verdict

**NOT_READY_FOR_DPCD_TEST**

We have a repeatably associated External DCPEXT0 path and substantial local
wrapper-ABI evidence. We have not established the complete object lifecycle or
the server-side behavior of the DPDV user-client open and selector 0 on that
External DCPDPDeviceProxy. No IODP object was constructed and no private function
was invoked. Native AUX and MST source support remain `UNKNOWN`.

## Evidence And Reproduction

- **A1**, definitive static capture:
  `artifacts/probes/iodp-static-20260912T012026Z/iodp-static.json` and manifest.
  Contains raw instruction bytes, independent LLVM disassembly, named caller
  methods, import lists, exact raw C strings, text hashes, and image identities.
- **G2**, graph/support-flag capture:
  `artifacts/probes/20260912T012137Z/`, 33 read-only commands, no failures.
- **C1/D1/C2**, controlled upstream cable experiment:
  [external-dock-diff.md](external-dock-diff.md). The active device is the
  owner-identified ZMUIPNG hub, not the earlier HP dock.
- Host: Apple M5, macOS 26.6.2 (25G83), SDK 26.5, arm64e cached libraries.

```sh
python3 tools/inspect_iodp.py --baseline artifacts/probes/20260912T012137Z
```

This tool runs Apple's `dyld_info` against cached images and the installed
Xcode `libLTO.dylib` public LLVM disassembler against selected raw code bytes.
It uses `ctypes` only to resolve IOKit symbols and call LLVM's public decoding
functions. It does not load updater libraries for execution, invoke IODP/IOAV
functions, open device clients, attach to the kernel, or alter system settings.
Captured library UUIDs are binary identities, not machine/device identifiers.

| Local image | Binary UUID |
| --- | --- |
| `/System/Library/Frameworks/IOKit.framework/Versions/A/IOKit` | `12372585-DF92-33EF-B632-714FAA13260A` |
| `/usr/lib/updaters/libPS190Updater.dylib` | `890D3A6A-FE7B-3D04-BA1F-B6EAE4D0071C` |
| `/usr/lib/libdpfu.dylib` | `B9E57F34-C7CA-3BBD-806C-4A8D0C67CB21` |

`PRIMARY_SOURCE`: A1 contains 14 complete IOKit function blocks. All their
instructions are covered by raw bytes and independently decoded. The PS190
constructor, reader, deallocator and enumerator also have complete raw-byte
coverage. One additional Objective-C messaging stub falls outside the captured
text section and is explicitly marked incomplete, not used as ABI proof.

## Symbol Inventory

`VERIFIED_ON_M5`: all **97** IODP-prefixed names collected from the current SDK
and cached exports resolve in this process. None was invoked. A1's `symbols`
array lists every name, SDK presence, cached export offset and runtime result.
Symbol presence does not establish whether an unexamined symbol is a function,
its prototype, or whether an operation is safe.

| Family | Names | Scope |
| --- | --- | --- |
| IODPController | 21 | Create/location/service, AV controller, lane/rate getters and setters, drive/training/security controls. |
| IODPDevice | 19 | Create/location/service, AV device/controller, link/revision/error getters, DPCD read/write, update controls. |
| IODPService | 9 | Create/location/service, AV service/device, sink/error getters, retrain. |
| IODPPort | 10 | Create/service, AV root/address/type/virtual getters, virtual DPCD/EDID and event setters. |
| IODPHDMIControllerPort | 8 | Create/service, address/type, PCON/HPD/port controls. |
| IODPHDMIController | 1 | GetPCONStatus. |
| Other IODP names | 29 | Link/clock/rate/format/training helpers; unassessed ABI. |

The 19 device names are: `IODPDeviceCreate`, `IODPDeviceCreateWithLocation`,
`IODPDeviceCreateWithService`, `IODPDeviceGetAVDevice`, `IODPDeviceGetController`,
`IODPDeviceGetLinkTrainingData`, `IODPDeviceGetMaxLaneCount`,
`IODPDeviceGetMaxLinkRate`, `IODPDeviceGetRevisionMajor`,
`IODPDeviceGetRevisionMinor`, `IODPDeviceGetSupportsDownspread`,
`IODPDeviceGetSupportsEnhancedMode`, `IODPDeviceGetSymbolErrorCount`,
`IODPDeviceGetTypeID`, `IODPDeviceReadDPCD`, `IODPDeviceSetUpdateMode`,
`IODPDeviceSetUpdated`, `IODPDeviceTypeString`, `IODPDeviceWriteDPCD`.

## Candidate Confidence

Confidence is limited to this image/ABI. None is a newly declared public API.

| Function | Symbol Exists | Prototype Confidence | Evidence | Safe To Invoke Here? |
| --- | --- | --- | --- | --- |
| IODPDeviceCreateWithService | Yes | High for two input argument roles and pointer return; lifecycle incomplete | A1 complete wrapper, CFRuntime allocation, service retain, IOServiceOpen | No |
| IODPDeviceReadDPCD | Yes | High for register/marshalling shape; no verified transport semantics | A1 complete wrapper, raw bytes, LLVM cross-check, public IOConnectCallMethod declaration | No |
| IODPDeviceWriteDPCD | Yes | Not validated for use | Export and static sibling wrapper only | Absolutely prohibited |
| IODPDeviceCreate | Yes | Partial; one allocator-like input and default discovery helper | A1 wrapper | No; unqualified discovery can select the internal panel |
| IODPDeviceCreateWithLocation | Yes | Partial; not promoted to a typed declaration | A1 wrapper | No; prefer a verified explicit service target |
| IODPDeviceGetAVDevice | Yes | Partial; returns cached pointer from object | A1 two-instruction body | No object exists; ownership not independently proven |
| IODPDeviceGetController | Yes | Partial; can lazily obtain/cache a controller | A1 wrapper | No; Get does not necessarily mean a pure field read |
| IODPServiceCreateWithService | Yes | Partial; opens a different client type | A1 wrapper | No |
| IODPServiceGetDevice | Yes | Partial; cached pointer or parent lookup + device creation | A1 wrapper; actual graph differs from a simple device/service chain | No |
| IODPControllerCreateWithService | Yes | Export only in this analysis | SDK/runtime inventory | No |
| Other IODP getters/helpers | Yes, inventoried | Not assessed | SDK/runtime inventory | Not approved |

## Read Wrapper: What The Machine Code Shows

`PRIMARY_SOURCE`: `_IODPDeviceReadDPCD`, cached export offset `0x20eb0`,
preferred image address `0x18487eeb0`, has 35 instructions in A1.

| Observation | Evidence In Wrapper |
| --- | --- |
| First input is an object pointer, not an io_service_t integer | Loads a 32-bit connection from `[x0 + 0x14]`. |
| Address is consumed as 32 bits | `mov w8, w1`, then stores zero-extended x8 as one uint64 scalar. |
| Third input is the output-buffer pointer | Original x2 is stored in the ninth IOConnectCallMethod argument slot. |
| Fourth input is a 32-bit requested length | Unsigned comparison of w3 with 4096; local output size is the minimum. |
| Kernel method selector is zero | w1=0 before IOConnectCallMethod; one scalar input; no input structure. |
| Buffer and local size are output-structure parameters | Ninth/tenth public-call arguments are the original buffer and a size_t pointer. |
| Return is propagated from IOConnectCallMethod | w0 is not replaced before normal return; stack-canary checks do not modify it. |
| Actual returned size is not exposed by this wrapper | Local size is passed by pointer to IOConnectCallMethod, then discarded. |

`INFERRED`, high confidence for this machine ABI, **not an approved header**:

```c
// INFERRED FROM THIS LOCAL IMAGE. DO NOT COMPILE OR INVOKE WITHOUT THE GATES BELOW.
CFTypeRef IODPDeviceCreateWithService(CFAllocatorRef allocator, io_service_t service);
kern_return_t IODPDeviceReadDPCD(CFTypeRef opaque_device, uint32_t address,
                               void *output_buffer, uint32_t requested_length);
```

The exact private typedef name is not recovered; CFTypeRef denotes the inferred
opaque CF object, not permission to cast arbitrary pointers. Do not substitute a
registry handle for it or manually construct its fields.

`UNKNOWN`: native AUX versus cached/abstracted data, address validation in the
driver, transfer chunking, return-code meanings specific to this service, and
short-read behavior. The wrapper does not visibly mask the address to 20 bits,
check the buffer for null, or reject length zero. Its 4096-byte cap is **not**
the DisplayPort AUX wire-payload size. A future one-byte test must retain return
code and an initially recognizable buffer value; success alone is not sufficient
if the returned byte was not actually changed.

The public SDK `IOKitLib.h` lines 825 onward define IOConnectCallMethod's ten
arguments. A1's register/stack mapping is interpreted against that declaration,
not against a guessed private selector signature. No IOConnect call was executed.

## Creation, Ownership, And Target Binding

`PRIMARY_SOURCE`: `_IODPDeviceCreateWithService` at image offset `0xa67c4`
contains 150 instructions. It rejects a null service, calls IOAVObjectConformsTo
for `IODPDevice`, creates a CFRuntime instance, retains the service, and stores
the service handle at offset `0x10`. It calls IOServiceOpen with type
`0x44504456` (`DPDV`) and stores the connection at offset `0x14`. It releases the
new CF object on open failure and returns null. It also calls
IOAVDeviceCreateWithService and reads AV properties.

Exact raw C strings, independently located in A1, establish the conformance-key
composition `%s%s` + `IODPDevice` + `UserInterfaceSupported`. The External
DCPDPDeviceProxy in G2 reports `IODPDeviceUserInterfaceSupported=true`.

`INFERRED`: a successful result is a caller-owned CF object, conventionally
released with CFRelease, separate from the caller's own IORegistry reference.
The type is registered via CFRuntime and the failure path uses CFRelease. The
full finalizer/close path and its effects are **not yet established**.

The subsidiary AV constructor independently checks `IOAVDeviceUserInterfaceSupported`
and can open a type-0 client. In G2 that flag appears on the sibling
DCPAVDeviceProxy, while the DCPDPDeviceProxy exposes the DP flag. Absence of the
AV flag on the selected DP node and the constructor's nullable subsidiary path
need explicit interpretation before relying on a partially populated object.
Do not call a constructor just to discover which branch it takes.

`PRIMARY_SOURCE`: IODPServiceGetDevice looks up the service's parent in the
`IOService` plane before calling the device constructor and caching the result.
`VERIFIED_ON_M5`: the observed DP service's immediate parent is its AFK EPIC
interface, **not** the sibling DCPDPDeviceProxy. Therefore the intuitive
service->GetDevice route is not proven for this proxy graph. Direct construction
from a freshly enumerated External DCPDPDeviceProxy is the candidate route;
it has not been executed or declared safe.

No retain/ownership deduction authorizes opening a user client. Apple's public
IOServiceOpen documentation states that it invokes family-specific newUserClient
behavior. The M5 DP-family implementation of that behavior remains the key gap.

## Real Caller Investigation

The local Apple PS190 updater imports IODPDeviceCreateWithService,
IODPDeviceReadDPCD, IODPDeviceWriteDPCD and CFRelease. Static named methods include:

| Method | Observed Argument/Object Evidence | Limit |
| --- | --- | --- |
| `-[PS190IODPDevice initWithService:rootPath:]` | Saves Objective-C argument x2 as the service; forwards it in x1 with an allocator-like x0; stores the returned pointer at self+8 and checks null. | Branch targets an authenticated shared-cache stub; final binding not independently resolved. |
| `-[PS190IODPDevice readRegisterAddress:buffer:length:]` | Loads stored pointer from self+8 into x0; moves ObjC address x2->x1, buffer x3->x2, length x4->x3; tests a 32-bit return code for zero. | Consistent with the read wrapper, but shared-stub binding must still be corroborated. |
| `-[PS190IODPDevice dealloc]` | Loads that same stored pointer, conditionally calls a stub, then clears it. CFRelease is imported. | CFRelease target is strongly suggested, not proven by an incorrect disassembler label. |
| `+[PS190IODPDevice allDevices]` | Static enumerator preserved for later service-selection analysis. | Not executed and not accepted as an M5 dock-binding recipe. |

For example the raw BL at `0x286076954` in the reader reaches stub
`0x286086068`; A1 preserves raw bytes, independently calculated target and stub
instructions. The stub uses an authenticated indirect branch through a shared
cache slot. No guessed function pointer was called to resolve it.

`INFERRED`: the PS190 methods provide meaningful independent corroboration of
the four-argument shape and opaque-object flow. They are not a fully resolved
call-site proof until the shared-cache binding and lifecycle are accounted for.

Public-source search outcomes:

- Apple IOKitUser and AllRez searches did not locate a typed ReadDPCD caller.
  This is search scope, not proof that no caller exists.
- [EthanArbuckle's iOS 26.1 generated libdpfu listing](https://github.com/EthanArbuckle/iPhone18-3_26.1_23B85_Restore/blob/90aa0cfe59d9682b4265e1354c8b19ec3c7823ab/usr/lib/libdpfu/libdpfu.mm)
  contains calls printed without argument recovery. It is a lead, not a
  trustworthy C prototype or M5/macOS behavioral proof.
- [hack-different symbol-server](https://github.com/hack-different/symbol-server/blob/bb3690a37cbb439b6a08858c3cb6d8c59be3ddd1/symbols/macOS/6ee8e46b02f0b03c9fbb6c2a1cf7cf93_libPS190Updater.dylib)
  identified the PS190 import family. Local current-image analysis, not this
  older symbol list, supplies A1's instruction evidence.
- Historical SDK/symbol archives and blacktop ipsw-diffs confirm names/change
  history only; no prototype confidence was derived from symbol counts.

## Tool Limitations

- LLDB could not pause an owned `macmst --help` process at main. No security
  settings, signing policy, privileges, or debugger permissions were changed.
  Static dyld_info inspection succeeded without attachment.
- dyld_info mislabels some cached external stubs and prints misleading pretty
  C-string addresses. Raw section bytes plus LLVM decoding are retained to
  distinguish these problems from actual program behavior.
- `dyld_info -objc` did not yield usable PS190 type encodings in this cached
  image. No Swift or Objective-C prototype was invented to fill the gap.
- Authenticated shared-cache stub targets/finalizers and DPDV server dispatch
  were not resolved. The collector flags incomplete raw coverage explicitly.
- No updater executable, kernel collection, DCP firmware image, or private
  user-client selector was run, patched, loaded, or fuzzed.

## M2-02 Gates And Next Experiment

| Gate | Result |
| --- | --- |
| Repeatable External dock-associated path | Established for this C1/D1/C2 cycle, with owner-confirmed hub/port. |
| Device creation register ABI | Strong local evidence; full subsidiary-object/cleanup lifecycle incomplete. |
| Read register/buffer/length ABI | Strong wrapper evidence; caller stub resolution and short-read semantics incomplete. |
| Target's DPDV open and selector-0 semantics | UNKNOWN; server/firmware behavior not established. |
| No unexpected state changes from the tested path | Not established; no private transport/open experiment performed. |

M2-02 is **withheld**, not implemented. If these gaps are closed and the next
experiment is explicitly approved, its first requested operation must be exactly
**one byte at DPCD 0x000**, not a 16-byte block or MST_CAP at 0x021. The byte must
be recorded raw; no particular revision value is assumed. A command resembling
`macmst dpcd read 0x000 1` does not currently exist and must not be presented as
working. Later addresses, writes, sideband messages, retraining and default/internal
target fallback are not part of that first experiment.

**Next: M2A-ABI-02, static lifecycle/dispatch verification.** Using the same
recorded image identities, resolve the PS190 reader/constructor/deallocator
authenticated stubs, then trace the IODP CF finalizer and the DP family's
`newUserClient(type=0x44504456)` and selector-0 dispatch. Establish the expected
External service, error/buffer contract, and whether open/read can alter link
state. Do not execute those methods. Expected result is a source-backed read-only
dispatch/lifetime contract; a write/retrain path, unsupported binding, ambiguous
target or inaccessible implementation leaves M2-02 blocked. Do not weaken macOS
security to obtain it.