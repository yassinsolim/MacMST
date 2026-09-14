# M4Q: M5 Observer Capability Gap Qualification

## Objective

Determine whether a passive, scientifically useful T8142/M5 DCP observer is a
contained engineering task or a platform-enablement project. This is observation
infrastructure research and design only, not a new assessment of whether MacMST
works. No implementation is written, built, installed or executed.

The scope excludes m1n1/Asahi installation or boot, hypervisor/tracer execution,
DFU, boot-policy or security changes, DCP commands, DPCD operations and display
transitions. It also excludes new T8142 packetizer, source-controller,
cardinality, payload-table/ID, register, timing-generator or sideband analysis.
An unavailable observation dependency is a blocker, not permission to reopen
that work.

## Frozen MacMST Baseline

M4Q began on clean `research/m5-sacrificial-dynamic-design` at
`95f9f4300fd3e7aec417e8e727bd8cd57714fb98`, with matching upstream and
ahead/behind 0/0. All 37 existing remote head/tag/peeled identities matched the
protected local refs. No M4Q branch already existed.

| Protected Baseline | Identity |
| --- | --- |
| Completed M4P | `95f9f4300fd3e7aec417e8e727bd8cd57714fb98` |
| M3E0 conclusion | `a6a5dc122563c1d4dc481a09bf70848eea61fa78` |
| Main/origin-main | `c5bc1b1bacd7742a4bbc1b54285336e9d51302a5` |
| Annotated m5-mst-static-ceiling-v1.0 object | `08234296452af2f9d5056cfc743e79801cef92e9` |
| Ceiling peeled commit | `c5bc1b1bacd7742a4bbc1b54285336e9d51302a5` |

`research/m5-observer-gap` was created directly from M4P. No merge is needed or
performed. The [M4P design](m5-sacrificial-dynamic-design.md) is frozen at SHA-256
`919a15d8e6de182c7c0719bc5cbb0ca079f5372c2f90e0c8167b52b210fd78b0`.
The [M3E0 conclusion](m5-mst-static-conclusion.md) and M3A-M3D reports remain
references only, not new reverse-engineering targets.

M4P's `SACRIFICIAL_EXPERIMENT_REQUIRES_UNAVAILABLE_CAPABILITY` means that its
qualified observer was not established, not that m1n1 lacks all M5 support.
Preserve `PUBLIC_TELEMETRY_INSUFFICIENT`,
`PASSIVE_DCP_IPC_CAPTURE_REQUIRES_PLATFORM_WORK`,
`M5_M1N1_DYNAMIC_PATH_PARTIAL`, `EXACT_M5_HARDWARE_REQUIRED`,
`STIMULUS_REQUIREMENT_UNRESOLVED` and `WIRE_ANALYZER_OPTIONAL_HIGH_VALUE`.

`STATIC_PACKETIZER_ANALYSIS_FROZEN` and
`NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED` remain permanent.
`RETIRED_ON_DAILY_USE_M5` and `NOT_READY_FOR_DPCD_TEST` remain unchanged.
The consumed M2F marker and both historical result hashes were verified intact;
the M2G DPCD-read attempt marker is absent. No hardware observation was performed.

## Minimum Observer Contract

The observer must correlate existing runtime information along this chain:

```text
physical DPTX instance
  -> host command/event
  -> DCP endpoint/channel
  -> runtime source/object/device identity
  -> timing or payload operation, where present
```

It need not decode all DCP firmware internals, instantiate a second source or
send a command. It must preserve enough information to distinguish a source
identity from an endpoint, service channel, downstream port or sequence number.

| Contract Item | Minimum Required Evidence |
| --- | --- |
| Physical owner | Proven mapping from observed transport/service to one physical DPTX, with address-space and boot-generation provenance; a channel named DPTX is insufficient |
| Host event and transport | Direction, endpoint, service/channel, command identifier, request/reply association and relevant lifecycle events |
| Semantic identity | A documented runtime source/object/device key scoped to that physical owner, not an assumed one-to-one host proxy relationship |
| Relevant operation | Raw request/reply bodies plus existing timing/mode/payload fields when present, with the exact schema version and undecoded bytes retained |
| Observation quality | Timestamp units, ordering and uncertainty; boot/lifetime generations; complete lengths, wrap/drop/error reporting and a capture-only behavior audit |

For eventual MacMST evidence, two simultaneous independently identified sources
under one owner or an explicit same-owner host-to-DCP source identity space
greater than one could satisfy M4P. Two sequential modes, two endpoints or two
records aliasing one source cannot. A valid one-source trace can still validate
instrumentation; it need not prove multi-stream capability.

The minimum development artifact is therefore a raw, correlated transport
record plus a small justified owner/identity mapping, not a full firmware object
inspector. If the mapping is absent from existing artifacts and exports, record
that uncertainty instead of deriving it through new frozen-firmware analysis.

### Initial Dependency Check

Fresh `git ls-remote ... HEAD` queries on 2026-09-14 returned m1n1
`b4654b32941d51afdb77579d63e7cb1aa6c03ecc` and Asahi docs
`715664a269937fe83293f46bbbeaae6094cb504e`. These happen to equal M4P's pins;
they were checked again, not assumed current.

Working hypothesis: the existing m1n1 DCP observer requires the traced workload
to run under its hypervisor, even though generic decoding and ADT parsing do
not. The [Tracer.trace implementation](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/trace/__init__.py#L118)
installs handlers with `hv.add_tracer`; the [HV mapping implementation](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/hv/__init__.py#L256)
tracks MMIO maps and updates hypervisor mappings. This is not a public macOS
process-attachment API.

The discriminating check is whether a published alternative mode retains a
passive transport observer around normally booted macOS without requiring the
same guest/boot support. An active bare-metal DCP client is not such a mode.
The final guest classification must distinguish this implementation dependency
from an unsupported claim that every conceivable observer requires m1n1.

## Current T8142 Platform Support

The current pins are m1n1 `b4654b32941d51afdb77579d63e7cb1aa6c03ecc` and
docs `715664a269937fe83293f46bbbeaae6094cb504e`, rechecked for M4Q. SUPPORTED
applies only to the exact capability named in its row. GENERIC_INFRASTRUCTURE_PRESENT
is not T8142 validation; PARTIAL means concrete groundwork exists but does not
close the target contract; NOT_IDENTIFIED is a bounded source-review result.

| Capability | T8142 Status | Evidence And Limit |
| --- | --- | --- |
| SoC ID recognized | SUPPORTED | src/soc.h defines T8142/0x8142 and an early UART target. This is recognition, not a guest-boot claim |
| CPU bring-up definitions | PARTIAL | src/chickens.c and src/midr.h contain M5 Hidra E/P IDs; src/smp.c includes T8142. The initial commit reports confirmed/tested IDs and SMP offset, but M5 uses the unfinished shared features_m4 profile and NULL per-core initialization callbacks |
| ADT parsing | PARTIAL | Generic parser plus a committed fix explicitly motivated by the M5 14-inch MacBook Pro's size-less reg properties. Parsing a property does not guarantee that get_reg can turn every such value into an address/size mapping |
| MMIO mapping | GENERIC_INFRASTRUCTURE_PRESENT | ADT get_reg/translate, HV.trace_device and HV.pt_update provide address translation and trace mappings; no complete J704AP observer map is qualified |
| ASC/RTKit infrastructure | GENERIC_INFRASTRUCTURE_PRESENT | Existing ASC register/management/endpoint machinery and passive ASCTracer; active StandardASC boot/send APIs are not passive attachment |
| Hypervisor boot | PARTIAL | EL2/VHE, stage-2 translation, feature guards and M4-aware CPU paths exist. T8142 is missing from HV.map_essential's CPU-start interception selection; no qualified target boot receipt identified |
| macOS guest boot | NOT_IDENTIFIED | Pinned guide supports 13.5 M1/M2 and 14.8.3 M1-M3, explicitly no pinned M4-or-newer target. No qualified J704AP/25G83 guest found |
| SPTM handling | NOT_IDENTIFIED | Guide identifies running SPTM as required to boot newer XNU; the inspected guest loader/start path has no identified SPTM/TXM guest-integration contract |
| DCP endpoint discovery | PARTIAL | ADT name/alias lookup, RTKit endpoint announcements and EPIC service announcements exist, but endpoint roles, node/DART selection and T8142 applicability need qualification |
| DCP tracer | PARTIAL | Existing trace_dcp.py captures relevant traffic with fixed endpoint classes, ADT naming and DART assumptions; not a validated T8142 capture path |
| EPIC tracer | GENERIC_INFRASTRUCTURE_PRESENT | Header/subheader, service announcement, request/reply and buffer decoding exist; current M5 ABI/semantic compatibility is not established |
| DPTX tracer | GENERIC_INFRASTRUCTURE_PRESENT | trace_dptx.py selects three named PHY nodes for generic MMIO tracing, not discovery of firmware source ownership or qualified T8142 tracing |

Primary recognition evidence is [Initial support for T8142](https://github.com/AsahiLinux/m1n1/commit/b72e664f7df3d53a960dc95972fcb5d1a069bd9e),
which changes only src/chickens.c, src/midr.h, src/smp.c and src/soc.h. Its
reported testing is narrower than a complete M5 macOS guest. The
[ADT parsing fix](https://github.com/AsahiLinux/m1n1/commit/c3def7d3c4a26d7799ddbcea4ab3ed5ab90a7e6c)
is specifically M5-motivated. These are positive support facts, not erased by
missing support documentation.

The [shared CPU feature profile](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/src/chickens.c#L111)
still asks which M4 features are available and uses SLEEP_NONE; the M5 entries
reuse it. [Standalone SMP selection](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/src/smp.c#L280)
does include T8142. Neither fact establishes sleep/wake or guest compatibility.

## M5 Hypervisor Blockers

This is a bounded blocker/qualification table, not an invented list of failing
subsystems. B1-B3 prevent calling the current path qualified. Q1-Q5 are inspected
areas for which this review cannot claim a separate actual T8142 failure. The
table does not claim to enumerate every bug mentioned by upstream.

| Item | Source And Current Implementation | Scope | What Prior M4 Work Solves | Required Qualification |
| --- | --- | --- | --- | --- |
| B1: newer XNU security-monitor boot contract | The pinned hypervisor guide explicitly requires SPTM running for M4 and newer. HV.load_macho loads a Mach-O/raw guest; HV.start enters hv_start. No qualified SPTM/TXM lifecycle, privilege and memory-ownership integration is identified in that path | Platform-wide, before useful DCP observation | Shared newer-core guards and reset-vector handling, not a published running SPTM plus macOS guest | An upstream-supported newer-platform guest architecture and demonstration; not a tracer-only change or proposed security bypass |
| B2: supported macOS guest/version | Guide names numerous bugs and pins no M4+ target; Mac17,2's frozen target is 26.6.2/25G83. The loader's selected code adaptation is for M3 IDs, not a target-specific M5 guest contract | Platform-wide compatibility and qualification | M3 guest/loader experience does not qualify M4 or M5 | A supported target version, boot/exception/device initialization and stable guest receipt; unspecified bugs remain unspecified |
| B3: T8142 guest CPU-start interception | HV.map_essential selects chip IDs including 0x8132/0x8140 but not 0x8142, then logs CPUSTART unknown and skips installing that hook. Standalone src/smp.c already includes T8142 | Platform-wide guest secondary-CPU path | M4 shares the existing CPU_START_OFF_T8112 standalone group; the T8142 commit reports a tested SMP offset | Reconcile the guest hook with verified standalone/platform data and validate it. This omission does not prove boot CPU failure or solve B1/B2 |
| Q1: CPU initialization/security state | features_m4 is deliberately partial; M5 uses it. HV and C code guard some locked Apple sysregister operations and use reset-vector read emulation | Platform-wide unknown completeness | Real shared M4 guards/profile exist | Validate required guest operations; NULL core callback alone is not evidence of failed CPU bring-up |
| Q2: MMU, traps and M5 memory features | src/hv.c configures VHE/stage 2; src/hv_vm.c derives PA size and implements mappings; src/memory.c provides the host MMU. No specific M5 failure is shown here | Platform-wide qualification, coupled to B1 | Generic mapping/trap machinery and newer-core guards | Do not infer a new MMU implementation is required. Apple documents M5 memory-integrity features, but that alone does not demonstrate a tracer blocker |
| Q3: interrupt controller | src/aic.c implements AIC2/AIC3, with ADT-supplied AIC3 offsets/strides; src/hv_aic.c contains interception support | Platform-wide qualification | Newer interrupt-controller infrastructure exists | Establish target applicability; no independently demonstrated T8142 AIC defect identified |
| Q4: SEP interactions | src/sep.c implements a small ASC-backed random-number service, not a proof of full guest SEP/boot compatibility | Platform-wide unknown, not a DCP-specific blocker | No checked evidence that an M4 SEP fix closes M5 guest needs | No separate SEP blocker is asserted without a target failure or authoritative requirement |
| Q5: ADT and display/DCP initialization | Generic ADT translation and a specific M5 parser fix exist. HV.start changes the guest ADT and shuts down the framebuffer before entering the guest | Platform/device qualification | Parsing and previous guest handoff machinery transfer as prior art | A running target guest must initialize the normal display path; do not mistake boot framebuffer presence or an active bare-metal DCP client for this proof |

Exact B3 source: [HV.map_essential](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/hv/__init__.py#L1563).
Its fallback is observable in source without booting anything. Exact B1/B2
support contract: [Supported macOS versions](https://github.com/AsahiLinux/docs/blob/715664a269937fe83293f46bbbeaae6094cb504e/docs/sw/m1n1-hypervisor.md#supported-macos-versions).
The [guest loader](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/hv/__init__.py#L1904)
uses its M3 load hook only for enumerated M3 IDs; this is not evidence that M5
needs the same patch. No patch is implemented or proposed as a bypass.

Apple's [operating-system integrity documentation](https://support.apple.com/guide/security/operating-system-integrity-sec8b776536b/web),
observed 2026-09-14, describes SPTM at a higher privilege level than XNU and TXM
as its lower-privilege policy component, including early-boot page-table
protection. This explains why B1 is not an EPIC parser task. TXM is a dependency
to qualify within B1, not a separately demonstrated T8142 bug. Security reduction
is neither proof of compatibility nor authorized by M4Q.

## Guest Requirement

**MACOS_GUEST_REQUIRED** for the identified public m1n1-based path observing
the existing macOS-to-DCP workload. This is a code-path dependency, not proof
that every conceivable future software/hardware observer must use a guest.

| Model | Evidence | Contract Result |
| --- | --- | --- |
| A: macOS guest under m1n1 | run_guest.py constructs HV, loads the payload, installs scripts and calls HV.start; tracer events come from hypervisor MMIO mappings | The concrete existing architecture, subject to B1-B3 and target qualification |
| B: proxy around normally booted macOS | USB proxy connects to resident m1n1; no documented attachment API installs these mappings beneath an already-running stock macOS | Not an identified alternative. A separate recording Mac is not an observer inside the target |
| C: another m1n1 boot mode | Standalone proxy/chainload modes can load payloads and drive hardware; a raw payload can also run under HV | Standalone execution does not preserve the normal macOS workload plus passive hooks; a raw HV guest is still a guest |
| D: ASC monitor without full macOS guest | Framing/decoding can be reused offline; StandardASC/DCPClient actively boot endpoints/send requests. No qualified resident passive transport tap around stock macOS is identified | Active bare-metal traffic would change the stimulus and cannot replace observation of existing macOS source events |
| E: impossible without any hypervisor | Existing Tracer.trace depends on HV.add_tracer and stage-2 hooks, but this does not exclude a future supported Apple export or independent observer | No universal impossibility claim. Such an alternative would require its own identified access/data contract |

The [launcher](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/tools/run_guest.py#L55)
and [HV.start](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/hv/__init__.py#L1966)
are the controlling path. [HV.pt_update](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/hv/__init__.py#L291)
maps SYNC/HOOK modes to trap handlers and ASYNC modes to software translation
entries. ASYNC refers to event delivery, not guest independence. The `novm`
branch disables stage-2 VM behavior; it is not evidence of a detached passive
tracer retaining the same contract.

The [m1n1 user guide](https://github.com/AsahiLinux/docs/blob/715664a269937fe83293f46bbbeaae6094cb504e/docs/sw/m1n1-user-guide.md)
distinguishes proxy, payload/chainload and macOS hypervisor use. The
[active ASC path](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/fw/asc/__init__.py#L92)
starts endpoints and management; merely reusing it would not satisfy capture-only
requirements. No alternative removes the current guest-enablement dependency
on the strength of the reviewed evidence.

## DCP Tracer Portability

Portability is classified by layer, not by the filename alone. None of these
classifications establishes that the layer has been validated on T8142.

| Existing Component | Portability Class | Transferable Part / Limit |
| --- | --- | --- |
| Tracer, HV.add_tracer and HV.pt_update | HYPERVISOR_DEPENDENT | Existing hook registration and event delivery; requires the target guest and stage-2 observation environment |
| BaseASCTracer mailbox hooks | HYPERVISOR_DEPENDENT | Observes guest inbox/outbox accesses, rather than independently polling a live stock-macOS mailbox |
| RTKit management message interpretation | SOC_AGNOSTIC | Existing endpoint bitmap/start/power-event framing can be reused if the same transport contract applies; target validation still required |
| ADT parsing and range translation | SOC_AGNOSTIC | Generic parser and get_reg/translate infrastructure, including the M5-motivated parsing fix; missing property semantics are not supplied automatically |
| DCP node, register range and DART/SID selection | PLATFORM_ADDRESS_DEPENDENT | Alias/naming conventions and first-child SID assumption require exact target topology data |
| DART register/backend selection | PLATFORM_ADDRESS_DEPENDENT | Existing t8020/t6000/t8110 backends and cached translations; a different compatible string/layout must not be guessed |
| AFK ring and shared-buffer handshake | DCP_ABI_DEPENDENT | GetBuf_Ack and InitTX/InitRX determine buffer addresses/layout; capture must include compatible initialization and preserve generation state |
| EPIC header/subheader and service announcement | DCP_ABI_DEPENDENT | Channel, category, opcode, sequence and EPICName/EPICUnit interpretation; header/layout assumptions are not an M5 ABI promise |
| EPIC service-specific and IOMFB call decoders | DCP_ABI_DEPENDENT | Known command groups, replies and mode/display methods transfer only with matching message version/semantics |
| Text/hex formatting and offline record correlation | SOC_AGNOSTIC | Reusable host processing, but current printed output is not a complete loss-accounted evidence record |
| Source identity to physical-DPTX binding | UNKNOWN | No qualified T8142 ownership contract supplied by the above layers |

The [ASC tracer](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/trace/asc.py#L100)
defaults to SYNC and observes mailbox accesses; its management observer records
endpoint advertisements without starting endpoints on its own. The active
RTKit/EPIC client libraries also contain send/boot APIs, so reuse must distinguish
pure structure definitions from active clients.

[AFKRingBufSniffer](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/hv/trace_dcp.py#L52)
keeps its own read cursor and reads through DART. This is useful capture prior
art, not a full noninterference proof: synchronous hooks, cached translations,
buffer lifetime, loss, abort and cleanup behavior still require qualification.
The guest launcher itself performs platform setup and state changes. Passive
DCP observation does not mean a modification-free boot environment.

The [version matrix](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/constructutils.py#L803)
has firmware-profile entries through V14_7, not an identified 25G83/macOS 26
profile. Version comparisons use membership in that matrix. Simply inventing
a newer version label cannot establish compatible layouts; neither does this
matrix alone establish how a particular target would report its version.

## T8142 Endpoint Discovery

**T8142_DCP_DISCOVERY_NEEDS_PLATFORM_DATA**.

The current path is partially data-driven, not a generic discovery theorem for
any T8142 topology. The missing inputs below are observation-platform data,
not a request to decode packetizer registers or reopen firmware analysis.

| Discovery Layer | Current Source Behavior | Exact Missing Qualification |
| --- | --- | --- |
| DCP ASC node/ranges | get_alias/get_dcp_device use ADT aliases or dcp0/dcp fallback and /arm-io naming; the script separately traces register range 1 | Selected J704AP external-DCP node/alias, usable ASC register range ordering and mapping to the physical external path |
| DCP/display DART nodes | Names are formed from the selected DCP alias and dcp-to-disp substitution | Actual DART association and both node paths for that target, not extrapolated from a different SoC |
| DART stream and layout | dcp_sid is the first child node's reg; DART wrapper selects t8020/t6000/t8110 compatible backends | Correct SID among actual children, translation context, compatible string/register layout and accessible shared-memory address space |
| RTKit endpoints | Management.EPMap records announced endpoint numbers; DCPTracer assigns a fixed endpoint-class table | T8142 endpoint role/ABI agreement with that table; announcement of a number alone does not identify its protocol |
| EPIC services/channels | EPICEp.handle_report_init maps EPICName plus EPICUnit to a channel and a known/fallback decoder | Actual service announcements and their target-specific semantic identities; no automatic source-controller meaning |
| AFK rings | GetBuf_Ack captures DVA; InitTX/InitRX capture offsets/sizes; the sniffer reads through the chosen DART | Complete compatible initialization, safe address translation and buffer generation/lifetime; late capture cannot assume it saw initialization |
| DPTX-related service | Endpoint 0x2a is assigned DPTXPortService; DPDev/DPAV roles are also fixed | Service role and remote-port target mapping to the physical DPTX, separate from source identity |

Exact implementation: [node selection](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/hv/trace_dcp.py#L26),
[fixed endpoints and SID](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/hv/trace_dcp.py#L1393),
[DART selection](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/hw/dart.py#L18)
and [passive ring initialization](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/hv/trace_dcp.py#L113).
No new target ADT or runtime capture is made here. Existing frozen path names
are useful constraints, not proof that this particular tracer's naming/SID
assumptions hold. No new DART backend is declared necessary without target data.

The script explicitly disables endpoint 0x23's generic decoder for the DCP
iBoot service used by m1n1 because it is incompatible. That is a concrete
warning against treating standalone iBoot display activity as interchangeable
with macOS DCP traffic, not evidence about M5 stream capability.

## Trace Data Sufficiency

**DCP_TRACE_SCHEMA_EXTENSION_REQUIRED** for the minimum evidence record.
This conclusion follows from actual output omissions, independently of whether
an unobserved M5 message contains the missing source semantics.

| Field | Existing Tracer Exposes? | Needed For MacMST? |
| --- | --- | --- |
| Endpoint/channel | Yes: mailbox endpoint, EPIC channel and direction | Yes, scoped to the capture/boot and selected physical owner |
| Call opcode | Yes: EPIC category/type, standard-service group/command and IOMFB tag | Yes; raw value plus version-qualified name |
| Object/service ID | Partial: service name, EPICUnit and channel map; no established firmware source-object identity | Yes; service identity is correlation, not automatically a source key |
| Request body | Read from TX buffer; unknown handlers may hex-dump, known handlers choose what to print | Yes, preserve the complete raw body and framing regardless of handler |
| Reply body | Read from RX buffer; some known handlers discard the body; IOMFB dumps depend on verbosity/optional dumpfile | Yes, complete raw data with request/reply/generation association |
| Timing/mode payload | Known IOMFB mode/display call definitions and raw relevant bodies, if emitted | Yes where present; no assumption that one mode field denotes a second timing context |
| Stream index | No qualified T8142 source-stream field identified in the checked definitions | A source key or equivalent explicit identity contract is needed; do not relabel channel/sequence as stream index |
| Device ID | Partial: getDeviceMatchingData reply is hex-dumped, services have names/units | Needs documented scope and meaning before a device key can stand for source membership |
| DPTX index | Partial: remote-port target prints CORE/ATC/DIE/CONNECTED fields and selected ADT path | Requires a proved physical-owner mapping; these fields are not a source count |
| Payload/VC identity | Raw bytes could retain fields if emitted; no qualified same-owner source/payload binding found | Needed only for payload-based evidence; not mandatory if another explicit source identity contract suffices |

[EPICHeader/EPICCmd](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/fw/afk/epic.py#L36)
define the existing channel/sequence and buffer/length envelope.
[EPICEp.handle_cmd/handle_reply](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/hv/trace_dcp.py#L381)
read buffers and dispatch to service handlers, but the full envelope/body is
not unconditionally retained. For example,
[getLocation_reply/getUnit_reply](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/hv/trace_dcp.py#L269)
only print a method name. EPIC timestamp fields exist but their presence is not
a qualified clock/ordering contract. The current optional IOMFB dump is not a
complete EPIC capture record.

The smallest definite extension is a raw record emitted before semantic
dispatch: complete headers/bodies, direction, endpoint/channel, sequence and
buffer/generation association, target/version provenance, clock units/error
and explicit capture gaps. Preserve unknown data instead of manufacturing a
decoder. Qualification must also address synchronous stall behavior and buffer
reuse. No implementation or synthetic tracer execution is performed in M4Q.

## Ownership Schema

**OWNERSHIP_SCHEMA_UNRESOLVED**.

Existing artifacts can justify transport/service correlation and candidate
physical-port fields. They do not yet justify the entire mapping from physical
DPTX to runtime source/controller identity to timing/payload operation.

| Smallest Mapping Step | Existing Material | What Remains Missing |
| --- | --- | --- |
| Selected transport to physical DPTX | Frozen MacMST external-path observations and ADT-based tracer selection | A target-specific, same-boot physical-owner attribution for the selected tracer instance |
| Endpoint to service/channel | RTKit endpoint map, EPICName/EPICUnit announcements, known service descriptors | Target ABI agreement and complete lifecycle/generation record |
| Service to physical port/device | DCPDPTXRemotePortTarget, getDeviceMatchingData, getLocation/getUnit callbacks | Returned values plus an independently justified meaning; a service unit or port is not automatically a source |
| Source key to relevant operation | Known DCP/IOMFB operation names and preserved raw request/reply data | A semantic source key scoped to one physical owner, its lifetime and operation binding |

The [remote-port decoder](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/hv/trace_dcp.py#L1107)
names CORE/ATC/DIE/CONNECTED fields. They locate a connection target according
to that decoder, not a firmware source-controller instance. The separate
[active DCPAV definitions](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/fw/dcp/dcpav.py#L53)
encode a different connectTo call layout/group; do not combine their field
meanings without matching the actual API/version. They are evidence only, never
a proposed private stimulus.

The frozen [M3D ownership result](m5-dcp-stream-ownership.md#stream-ownership-result-and-viability)
and [M4P contract](m5-sacrificial-dynamic-design.md#success-criteria) explicitly
leave runtime membership unresolved. Already documented host method names and
firmware diagnostics can label an operation, but cannot turn that unresolved
relationship into a source-identity oracle. No new analysis of those firmware
objects or their fields is performed.

The minimum additional decoding task, once a platform exists, is to preserve
the presently dropped replies and match an independently supplied source/owner
contract to existing runtime keys. It is not yet known whether that contract
can be recovered from existing artifacts/exports alone. Therefore neither
derivability nor the necessity of new firmware reverse engineering is proved.
If the only route requires new frozen-T8142 analysis, stop: that route is outside
MacMST's authorization, not an implicit next patch.

## Stimulus Validation

**OBSERVER_VALIDATION_STIMULUS_UNRESOLVED** for the full minimum owner/source
contract, not because two streams must first be demonstrated. Ordinary actions
are credible validation stimuli for the lower observation layers; the remaining
gap is an independent semantic oracle for even one source-to-owner mapping.

| Ordinary Action | Observer Property It Could Validate | Limit |
| --- | --- | --- |
| Hub attach | Endpoint/service activity, HPD/connection events and candidate physical-path correlation | Does not by itself prove the candidate service key is a source identity |
| Hub detach | Disconnection and teardown/generation boundaries | No firmware-source lifetime conclusion from host teardown alone |
| Downstream monitor attach/detach | Device/matching-data and connection-change correlation | A downstream device or port is not a source instance |
| Sleep/wake | Restart/resume capture generations and retained/replaced transport state | Higher platform qualification burden; not needed for the first observer validation |
| Resolution change | A known mode operation and its request/reply association on one source | Sequential modes are sufficient for this instrumentation check, not evidence of two contexts |
| Refresh-rate change | Distinguishable mode/request data and temporal correlation | Same source can be reconfigured; no multi-stream inference |

Existing [hotPlugDetectChangeOccurred/connectTo decoders](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/hv/trace_dcp.py#L1125)
and [set_display_device/set_digital_out_mode definitions](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/fw/dcp/ipc.py#L798)
support these testable expectations on matching ABIs, not a tested M5 workflow.
Their command identifiers vary by version. No action is performed here.

Question 1, instrumentation: once the physical/source key has an independent
contract, ordinary one-source changes could validate the mapping and decoder
without private commands or a second source. Currently transport validation is
plausible while full source-attribution validation remains unqualified. No
evidence establishes that private stimulus is required.

Question 2, multi-stream capability: a correct trace of one ordinary source is
not sufficient. M4P's `STIMULUS_REQUIREMENT_UNRESOLVED` remains; observing only
one source cannot establish an architectural maximum. Keep instrumentation
validation and positive multi-stream evidence as separate acceptance stages.

## Minimal Development Delta

This is a hypothetical, dependency-ordered delta, not an implementation plan
or permission to modify upstream code. Only one platform edit is locally
identifiable from a concrete omission. Other rows distinguish definite
observation changes from conditional qualification work; they are not a claim
that every listed file must be patched.

| Component | Existing Support / Owning Files | Required Delta | Confidence |
| --- | --- | --- | --- |
| SoC/CPU description | src/soc.h, src/midr.h, src/chickens.c, src/smp.c already identify T8142 | No new SoC-ID definition justified. Qualify the shared feature profile; do not invent a separate M5 initialization routine | High recognition; incomplete feature coverage |
| Guest secondary CPU interception | proxyclient/m1n1/hv/__init__.py, HV.map_essential | Add the verified T8142 selection to the guest CPU-start mapping only after checking the existing standalone data/semantics; no edit made here | High that the omission exists; not proof of complete guest fix |
| Newer XNU/SPTM guest environment | proxyclient/tools/run_guest.py; HV.init/load_macho/start; src/hv.c, src/hv_exc.c, src/hv_vm.c own loading, traps and mappings | Establish the supported boot/monitor/guest contract first. The exact changes and whether additional platform modules are needed are not yet bounded | High that this dependency is unqualified; unknown exact patch set |
| ADT and target selection | proxyclient/m1n1/adt.py; trace_dcp.py get_alias/get_dcp_device | Supply/validate exact selected DCP/DART/range/SID mapping. Modify selection only where actual target data disproves current assumptions; no generic ADT rewrite justified | High selection assumptions; target delta conditional |
| DART access | proxyclient/m1n1/trace/dart.py and hw/dart.py with existing backends | Validate target compatible/layout, stream count, translation and invalidation behavior; a new backend is required only if existing backends do not match | Conditional; do not infer missing hardware support from an unknown compatible string |
| Passive transport capture | proxyclient/m1n1/trace/__init__.py, trace/asc.py and trace_dcp.py | Preserve mailbox/envelope data and qualify capture delays, buffer lifetimes, shutdown and loss. Do not blindly switch SYNC to ASYNC: event timing and buffer reuse matter | High evidence-contract gap; runtime bounds unqualified |
| Raw DCP/EPIC record | trace_dcp.py AFKEp/EPICEp/EPICServiceTracer/DCPCallChannel | Emit complete raw records before handler dispatch, including currently discarded replies; retain unknown fields and correlate request/reply/lifetime generations | High, directly grounded in current output omissions |
| Decoder/version compatibility | proxyclient/m1n1/fw/afk/epic.py, fw/dcp/ipc.py and constructutils.py | Validate the target's envelope and version profile, then extend only documented mismatches; adding a version label alone is not a port | Existing boundaries known; exact M5 ABI delta unknown |
| Ownership interpretation | trace_dcp.py service maps/remote-port handlers and fw/dcp/dcpav.py definitions as evidence | Derive a minimal mapping only from legitimate existing contracts/artifacts and captured keys. No invented source-ID decoder or new firmware analysis | Unknown until the semantic contract exists |
| DPTX PHY tracer | proxyclient/hv/trace_dptx.py | Not required for the smallest IPC observer. Do not expand its register coverage or introduce packetizer tracing | High exclusion from the minimum contract |

Thus a small CPU-start selection fix plus raw logging is not the complete
observer patch set. B1/B2 have to be resolved before those contained changes
can produce a useful M5 capture. No new file/module for SPTM is invented here,
and no existing SPRR/GXF branch is assumed to solve SPTM merely by name.

## Platform vs MacMST Work

### Platform Enablement

Required for any researcher using this m1n1 architecture to observe the normal
M5 macOS DCP workload:

- A qualified T8142 newer-XNU/SPTM guest environment with explicit boot/security
  prerequisites and stable exception/CPU/device initialization.
- Correct guest CPU-start interception and target ADT/MMIO/DART/SID mappings.
- Compatible RTKit/AFK/EPIC observation and non-interfering raw-buffer access,
  including initialization coverage, capture loss and bounded stop behavior.
- A pinned, recoverable tool/OS combination and off-target recording/recovery
  readiness. M4P's recovery design remains a prerequisite, not a completed test.

### MacMST Observer

Required specifically for the frozen ownership question after the platform
works:

- A complete provenance-preserving record and minimal physical-DPTX/service/key
  correlation, reusing generic capture improvements where appropriate.
- An independently justified source identity and lifetime/operation binding;
  preserve UNKNOWN if only service or downstream-device identities are visible.
- One-source validation of identity, mode and teardown behavior using ordinary
  actions, distinct from any later positive multi-stream evidence.
- Evaluation against the frozen M4P criteria without active DCP commands,
  private stimulus or reopened firmware packetizer research.

The blocking dependency is in platform enablement, not a new MacMST driver or
MST algorithm. Some raw-record work is useful upstream to everyone; classifying
it here does not make it a reason to build the entire missing platform inside
MacMST. Ownership uncertainty is an additional MacMST gate, not proof of a
second large firmware project.

## Current M5 Enablement Momentum

**ACTIVE_M5_ENABLEMENT** as planning evidence from concrete commits, not a claim
of a ready M5 hypervisor/observer. The three base-M5-relevant commits below were
verified as ancestors of the newly pinned m1n1 main revision.

| Commit / Date (UTC) | Concrete Contribution | Scope Limit |
| --- | --- | --- |
| [c3def7d3c4a26d7799ddbcea4ab3ed5ab90a7e6c](https://github.com/AsahiLinux/m1n1/commit/c3def7d3c4a26d7799ddbcea4ab3ed5ab90a7e6c), 2026-01-19 | ADT reg parsing without parent size/address annotations, explicitly motivated by the M5 14-inch MacBook Pro | Parser groundwork, not qualified physical-owner mapping |
| [fcaf4765c443d4e7432e470e40c25a1801217f40](https://github.com/AsahiLinux/m1n1/commit/fcaf4765c443d4e7432e470e40c25a1801217f40), 2026-05-15 | Power-management support labeled M4 Pro/Max, A18 Pro and M5 | Platform groundwork, not a guest-boot or DCP tracing receipt |
| [b72e664f7df3d53a960dc95972fcb5d1a069bd9e](https://github.com/AsahiLinux/m1n1/commit/b72e664f7df3d53a960dc95972fcb5d1a069bd9e), 2026-07-19 | Initial T8142 IDs/UART/SMP support; commit reports confirmed/tested CPU IDs and startup offset | Limited reported bring-up evidence, not a full Mac17,2 guest |
| [9bfdf8aeca30ba8dee1897ec73713da89e7623b9](https://github.com/AsahiLinux/m1n1/commit/9bfdf8aeca30ba8dee1897ec73713da89e7623b9), 2026-08-16 | SARTv4 support, explicitly observed on M5 Pro/Max T6050 | Related M5-family progress only; not T8142 DART/guest proof |

### Development Branches And Discussion

All 21 official m1n1 branch names/heads and all three docs branch heads were
listed in bounded pages. Branch names alone were not treated as capability.
The `darwin` branch head `e19e74be8b7d5f3643cbb4237ee6b8ba2a7d8578` is a
2021-11-08 assembler/macOS-host compatibility change, not current M5 enablement.

The recent `hv-sprr` head
`1c98fd09817cede0043d25c95fb540dbd683ef18` is materially relevant infrastructure
work: its three commits dated 2026-08-30 add SPRR/GXF emulation and reduce big
hypervisor lock use. Relative to current main it is three commits ahead and
five behind. Its delta spans 14 files, including new src/hv_sprr.c and
proxyclient/m1n1/hv/sprr.py, with launcher/exception/mapping integration.
[The emulation commit](https://github.com/AsahiLinux/m1n1/commit/bc1ea450f6a80f4da351047c0a4ddf916bfa2964)
and its [activation path](https://github.com/AsahiLinux/m1n1/blob/1c98fd09817cede0043d25c95fb540dbd683ef18/proxyclient/tools/run_guest.py#L49)
are concrete work, not an issue-comment promise. The branch includes guest-text
adaptation infrastructure; no branch code is applied here.

The inspected branch code and commit description do not supply a qualified
SPTM/TXM-enabled T8142 macOS guest contract or success receipt. The missing
contract is not disproved solely by a keyword miss, and this review does not
claim the branch is irrelevant or cannot contribute. Its existence strengthens
the case for treating guest enablement as upstream platform work rather than
assuming a finished environment or reimplementing it in MacMST.

The most recently updated ten m1n1 issues were also checked. Their selected
guest/tracing reports did not provide a qualified T8142 observer receipt.
[Issue 506](https://github.com/AsahiLinux/m1n1/issues/506) asks about macOS 15 on
M1; its member response is issue-tracker guidance, not a capability statement.
No issue comment is used to establish M5 support or lack of support, and the
remaining issue history/forks are not claimed exhaustively searched.

### Linux And Published Support

A fresh Linux HEAD query returned
`77cb8f24c2381a8abb7272d7bbdec548d6426a8a`. The pinned
[Apple platform-description directory](https://github.com/AsahiLinux/linux/tree/77cb8f24c2381a8abb7272d7bbdec548d6426a8a/arch/arm64/boot/dts/apple)
has 225 entries, including T8132/M4 descriptions but no T8142-named description
in that directory. Targeted commit searches for T8142/M5 returned no result;
this is a search limitation, not a whole-tree or hardware-absence proof.
No new Linux display-driver or DCP implementation scan is performed.

The pinned [support overview](https://github.com/AsahiLinux/docs/blob/715664a269937fe83293f46bbbeaae6094cb504e/docs/platform/feature-support/overview.md)
links M1-M4; the [M4 support page](https://github.com/AsahiLinux/docs/blob/715664a269937fe83293f46bbbeaae6094cb504e/docs/platform/feature-support/m4.md)
still lists many features as TBA. That public status must not erase newer
code-level groundwork or be extended into a claim of M5 impossibility. The
guest guide's recent history includes July 2026 updates while its support
contract still has no pinned M4+ target.

## Hardware Purchase Decision

**SACRIFICIAL_M5_PURCHASE_PREMATURE** for MacMST's observer objective today.

A second base-M5 machine would eventually allow target bring-up and testing,
but it would not provide the absent supported guest/monitor contract or the
source-identity oracle. There is no qualified, contained observer implementation
path ready to execute merely upon acquisition. The one identifiable CPU-start
selection fix and raw-log extension do not change that.

This is not a judgment that hardware has no value to an independently staffed
upstream platform project. Such a project has a different goal, risk budget and
approval. For MacMST, wait for actionable upstream capability evidence before
purchase. Existing `EXACT_M5_HARDWARE_REQUIRED` remains the eventual target
control; the daily-use M5 is not a substitute development machine.

## Engineering Surface

These are engineering-surface classifications, not elapsed-time, staffing or
code-size estimates. Conditional portability work is distinguished from the
unqualified platform dependency it would follow.

| Required Surface | Scope | Reason |
| --- | --- | --- |
| M5 boot/hypervisor support | LARGE | Supported newer-XNU/SPTM guest contract, CPU/trap/memory/device qualification and recovery precede capture; this is platform work. Exact subsystem changes remain unbounded |
| DCP transport observation | MODERATE | Existing ASC/DART/AFK machinery can be reused once the platform works, but target mapping, initialization coverage, raw data preservation, buffer lifetime and bounded capture need qualification |
| Trace decoder portability | UNKNOWN | Definite raw-record omissions are bounded; the target's envelope, firmware profile and relevant service ABI compatibility are not qualified |
| Ownership schema | UNKNOWN | Candidate service/port/device keys exist, but their mapping to one physical owner's runtime sources is not established from existing artifacts |
| Stimulus validation | MODERATE | Ordinary one-source correlation and lifecycle checks have an identifiable shape; source-semantic acceptance remains dependent on the missing oracle, not on creating two streams |
| Recovery/tooling | MODERATE | M4P identifies a second host, exact recovery topology, backups and a documented recovery path; target guest/tool qualification and rehearsal remain undone |

Overall scope: **PLATFORM_ENABLEMENT_PROJECT** for the identified m1n1 path.
This classification does not pretend to know the complete blocker set or assert
that each generic subsystem needs rewriting. The decisive prerequisite is a
currently unqualified platform/guest architecture, so bounding only the tracer
patches would understate the project. Ownership work remains an independent
unknown even after that prerequisite is delivered.

## Observer Decision

Primary result: **M5_OBSERVER_REQUIRES_MAJOR_PLATFORM_ENABLEMENT**.

| Decision Requirement | Current Evidence |
| --- | --- |
| Sufficient T8142 observation environment | Not established; the concrete passive path requires a controlled macOS guest and the upstream guide identifies an unresolved newer-platform SPTM requirement |
| Bounded missing components | CPU-start selection and raw-record preservation are identifiable; the supported guest/monitor contract and exact ABI/ownership work are not bounded to those changes |
| No major platform subsystem first | Not met: boot/monitor/guest enablement precedes the observer, with active upstream virtualization work rather than a qualified M5 target |
| Ownership derived without frozen firmware work | Unresolved. No new firmware reverse engineering is asserted necessary or authorized |
| Hardware materially enables an actionable observer step now | Not established for a contained MacMST task; possession alone would move the project into upstream platform bring-up |

The result is based on the identified path's platform dependency, not merely
the absence of an M5 feature page, a missing SoC constant or an issue comment.
It is not a proof that every possible future observer needs major enablement.
The exact amount of B1/B2 work remains unknown, but its platform-wide ownership
and position before useful capture are established well enough not to call
this a contained observer task. Unresolved source semantics are an additional
gate, not invented evidence of a required large firmware-reversing effort.

### Source Provenance

All sources were checked on 2026-09-14. Public code was read as data only, never
imported, built or executed. The table binds the decisive file contents to
immutable revisions and SHA-256 values. Mutable branch/issue/API metadata is
date-observed evidence, not a stable support guarantee.

| Pinned Source | Raw SHA-256 |
| --- | --- |
| [Asahi guest guide](https://github.com/AsahiLinux/docs/blob/715664a269937fe83293f46bbbeaae6094cb504e/docs/sw/m1n1-hypervisor.md) | `2f84ce6e0a04c04b55ec8d8fc77fbc11281844d1a9358b5deb049c7819937bab` |
| [Asahi user guide](https://github.com/AsahiLinux/docs/blob/715664a269937fe83293f46bbbeaae6094cb504e/docs/sw/m1n1-user-guide.md) | `9bf9f2142bf11c2d203e469dc41fa4a5b76c0bb26af7e7fff86a9c7116f58df4` |
| [Support overview](https://github.com/AsahiLinux/docs/blob/715664a269937fe83293f46bbbeaae6094cb504e/docs/platform/feature-support/overview.md) | `0f217fa291492a6037402e17697a9bfb8f9aa6eb2700f89f58c5fa11a90aa6cb` |
| [M4 support page](https://github.com/AsahiLinux/docs/blob/715664a269937fe83293f46bbbeaae6094cb504e/docs/platform/feature-support/m4.md) | `f1f06c04144136e239b265e30a7b92d973c68fc4d3e41ac215ea015ba4e9d5f5` |
| [SoC IDs](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/src/soc.h) | `3569ce0f11ad808f724bf0c050b1fc8381dd199791ec95729f411ad8c2359bca` |
| [CPU features](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/src/chickens.c) | `80a84b63d6d90b4495543b90ac4dc7451dfe73129f7dc791b4220bc80b99c00a` |
| [Standalone SMP](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/src/smp.c) | `173ae51dd860d1b075a071d78d06945e3ed929910ce06ab0f76cd6b9e261371b` |
| [AIC implementation](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/src/aic.c) | `a192556a285229af685faef3ebd9f3adb44dfcda2dde77093288a9acbd77b7b6` |
| [HV interrupt handling](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/src/hv_aic.c) | `29d5deed4b4ded3d0678e467f5502662a4bbd345c88ec53cba1a636faa4ecbe2` |
| [HV entry](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/src/hv.c) | `764adf7001dd94bdd017c57b70893c87369716bf0034e64f7bf70dc9a74cd1cd` |
| [HV exceptions](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/src/hv_exc.c) | `672ad27dbd417903f2efdb68100a1432208566ec93373016c75af2101996333d` |
| [HV stage-2 mapping](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/src/hv_vm.c) | `b8a4a5bc4c8637f82faa787725f9c7b50b4668497801eb5a485e7816eaaf7338` |
| [Host MMU](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/src/memory.c) | `a016b37ea588a984b2d1b26d0592fa2e1694c837854c9dcd02839595c928bd2d` |
| [SEP helper scope](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/src/sep.c) | `4b971267541c3d9969a0a837c5b8d1ad913912239a121f68ef247ba9d95b1ade` |
| [Guest launcher](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/tools/run_guest.py) | `9cc718e1896014dfd17f899053a55d4fc0f16fa917ccb1cf498f516d1d07dd88` |
| [HV Python control](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/hv/__init__.py) | `071fb88638b66ac030c1eaf84f5dfdbf19733cb5ad547a8a09355b6e1af33fa0` |
| [ADT parser](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/adt.py) | `b1d0c1af0ea83f73b9e6003efb9b42a4892cb35be8efb9c7566d3512c1846a3f` |
| [Trace framework](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/trace/__init__.py) | `f272076446ecf1c60c8d7847e72649c9361032a51dbe830aa16cf0544f4602c1` |
| [ASC tracer](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/trace/asc.py) | `0a90aa0cdfcf546c50034e347959242b430a8c7b42c03d9c78d317e44430c5d2` |
| [DART tracer](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/trace/dart.py) | `3806589c64f6771104603c17488ea9836f5101deb73835527983d4bd6f583ba4` |
| [DART backend selection](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/hw/dart.py) | `a7fbb5771b77128a16ea7eced4bc4058c02d8f1c1838ed9359f2e2ba37fe5387` |
| [Active ASC distinction](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/fw/asc/__init__.py) | `2cdee0d6633c86b74259483f6a1d1f8be37b6a4fdb5966987e64f77545c3cdbb` |
| [DCP tracer](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/hv/trace_dcp.py) | `52e9748886f81e52b5f92861c08ad2d8302d7609a515caa453b1f72faca0d8a5` |
| [DPTX PHY tracer](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/hv/trace_dptx.py) | `22a384a8c6c223030de6921f1ab693906221ac79f323c3f4eb35a1eb144461d7` |
| [EPIC structures](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/fw/afk/epic.py) | `e8382ad46b6fe3bc5cedc53275fd03ed727e247dbb5dafe7c5f9b61f871baa5e` |
| [DCP call definitions](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/fw/dcp/ipc.py) | `20e51135c9121b3cf45be919109277d65f52f4fe00bb611e4738c4f450a10960` |
| [DCPAV service definitions](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/fw/dcp/dcpav.py) | `a9f408a5d6b55889e77dd84ab63e40a1d6a2f418ea4bdd49fe5972b6884c3555` |
| [Decoder version matrix](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/constructutils.py) | `8e3b56d4a7c31575faae6f373211bb2b6690ab4bd4f374db840c2d346cb4262d` |
| [SPRR branch C emulation](https://github.com/AsahiLinux/m1n1/blob/1c98fd09817cede0043d25c95fb540dbd683ef18/src/hv_sprr.c) | `2cd283337d45d4325fb9871e53cf010dfcca3c3a10cec61a8f54494552a9fb7d` |
| [SPRR branch HV control](https://github.com/AsahiLinux/m1n1/blob/1c98fd09817cede0043d25c95fb540dbd683ef18/proxyclient/m1n1/hv/__init__.py) | `8024331d3572692bf42b443910e18f9052c66a9e6b5794605bb3d5ab3a192fa4` |
| [SPRR branch launcher](https://github.com/AsahiLinux/m1n1/blob/1c98fd09817cede0043d25c95fb540dbd683ef18/proxyclient/tools/run_guest.py) | `806e42cbbc1e46b0fa18c7c41888baec87aa1bd857e4c6f9ad46774fd5564c18` |
| [SPRR branch text adaptation](https://github.com/AsahiLinux/m1n1/blob/1c98fd09817cede0043d25c95fb540dbd683ef18/proxyclient/m1n1/hv/sprr.py) | `8254c1c26ac1292e84a26d9b0257fe9e416def0e630873a5dca8ff5c3c7c53fb` |

The nontruncated pinned m1n1 tree response has SHA-256
`dfea31ff3cc7e5c440cd67b951a70fa708fed0d86c9cf609b4ea8971583d57bf`;
the docs tree response has
`f35980e97f34923b3304fe6a8a9f98d9d8f6a9eb9fdef5b67cf16c990956baca`.
The Linux platform-directory response has
`a7913d9782be3a003518ae022daf797df57c977694f8d5997dd654b5eabfd9b4`.
The main-versus-hv-sprr comparison response has
`619f056b53979392ebfd5c4e0d943f355a47cf7e5bcbc754b3815f3e609ec335`.
These API-response digests identify the review observations, not immutable
serialization guarantees for later API requests. Git object/file identities
above are the reproducible source anchors.

### Validation Scope

Required checks are source provenance, document structure/classifications,
links/anchors, Git scope, historical refs and frozen report/safety-marker hashes.
Ad hoc document/source checks parse text and metadata only. They do not import
upstream Python, compile an observer, build or run m1n1, invoke any tracer or
perform a hardware operation. Successful validation is evidence of a consistent
research record, not a working guest, observer or recovery path.

## Project Recommendation

**Wait for upstream M5 enablement.** Do not make MacMST responsible for the
missing guest/monitor platform, purchase a sacrificial machine for a supposedly
contained observer task, or begin M4R implementation planning on this evidence.
No implementation plan or code is produced in M4Q.

The trigger for a new qualification decision is a supported T8142/Mac17,2
macOS guest/observation path with a pinned working version, explicit security
and boot prerequisites, and credible passive DCP buffer capture. Reassess the
small record/discovery deltas and existing-artifact ownership mapping then.
Basic observer validation may use one ordinary source; it need not await a
multi-stream demonstration. Unknown ownership semantics must still remain
unknown until independently justified.

Any future upstream platform contribution would require a separate project and
approval; it is not the work assigned to MacMST here. Existing platform progress
is a reason to preserve the boundary and consume qualified results, not to
claim the environment is already ready. New independent evidence could change
this decision, but no current observation or experiment is authorized by it.

The daily-use policy remains `RETIRED_ON_DAILY_USE_M5` and
`NOT_READY_FOR_DPCD_TEST`. Preserve `STATIC_PACKETIZER_ANALYSIS_FROZEN` and
`NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED`, the consumed M2F
marker/receipts and the absent DPCD-read marker. No boot, DFU, security change,
tracer, DCP/DPCD command, display transition or new firmware analysis occurred.