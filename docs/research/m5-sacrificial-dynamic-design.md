# M4P: Sacrificial Dynamic Observation Design And Go/No-Go Gate

## Objective

Design one future observation architecture for the frozen runtime ownership
question and determine whether its prerequisites actually exist. This milestone
is research/documentation only. No tracing session, dynamic experiment, display
transition, boot action, installation, private command or security change is
performed on this or another machine.

Working feasibility hypothesis: existing DCP tracing research is useful prior
art, but a validated M5-compatible observer and guest platform are necessary
before the design can be READY. The cheap discriminating check is current
upstream support documentation and the observer's published input/output
contract, not another T8142 firmware analysis. A supported normal-security
facility emitting complete same-DPTX source membership could disconfirm the
need for a research hypervisor. That facility must be identified, not assumed.

## Frozen Static Baseline

The actual starting branch was research/m5-mst-static-conclusion at
**a6a5dc122563c1d4dc481a09bf70848eea61fa78**, clean, upstream synchronized and
ahead/behind0/0. Main/origin-main were
**c5bc1b1bacd7742a4bbc1b54285336e9d51302a5**. Permanent annotated
**m5-mst-static-ceiling-v1.0**, object
**08234296452af2f9d5056cfc743e79801cef92e9**, still peels to that main.
All36 existing remote head/tag/peeled identities matched local refs. No M4P
design or implementation branch existed; no merge was required or performed.

Research/m5-sacrificial-dynamic-design was created directly from the conclusion
commit. The [M3E0 conclusion](m5-mst-static-conclusion.md) is unchanged,
SHA-256 `d227c74904217f23033943efd0d261a8108989361c072b982b67d0b01153016c`.
M3A-M3D reports and source artifacts are references only, not reopened analyses.

Preserve MACMST_STATIC_FEASIBILITY_INCONCLUSIVE,
MACMST_ARCHITECTURAL_VIABILITY_UNRESOLVED,
M5_DCP_STREAM_OWNERSHIP_UNRESOLVED and
M5_DCP_MST_PACKETIZER_PRESENT_BUT_STREAM_BINDING_UNRESOLVED.
**STATIC_PACKETIZER_ANALYSIS_FROZEN** and
**NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED** remain in force.
No payload-ID, generator, packetizer, selector, vtable, function-boundary,
cardinality, sideband or host-firmware search is part of M4P. If a candidate
experiment needs more retained-T8142 disassembly to be specified, it fails this
design gate; the static work does not resume.

## Exact Runtime Question

**Runtime source-controller membership of one physical T8142 DPTX register owner.**

Prefer direct observation of source-controller membership, ideally with timing,
payload and host-to-DCP identity correlation. Two objects on different DPTX
owners, two log events, sequential replacement or a downstream MST port list
do not answer the question. A useful observer must distinguish simultaneous
source lifetimes under the same physical owner from a single source being
reconfigured. No live object layout or pointer is inferred from static addresses.

## Candidate Observation Methods

### Public And Event-Driven Telemetry

**PUBLIC_TELEMETRY_INSUFFICIENT** for the exact question with the surfaces
identified so far. M3E0's bounded registry/log check is reused, not rerun.
IORegistry matching/termination notifications could timestamp host proxy
appearance during ordinary attach/detach, and existing signposts/logs could
add correlation. They do not automatically report firmware-internal object
creation, dormant membership or independent timing. A host proxy or signpost
ID is not a source-controller identity without an explicit producer contract.

Sysdiagnose and Apple diagnostics may package richer existing events, but no
public M5 ownership schema or full DCP IPC dump contract was identified. They
are supporting evidence, not a reason to collect sensitive diagnostic bundles
or trigger transitions now. Apple signpost documentation describes producer-
emitted IDs and metadata, not arbitrary tracing of uninstrumented DCP objects.
Event-driven collection cannot recover a field that is never exported. An
ordinary transition showing one object remains inconclusive about a second
source that might be created only after a different host request.

### Existing Tracing Versus Internal Firmware State

Supported Instruments System Trace is the lowest-invasiveness macOS candidate
for scheduling, activity and existing-event correlation, not a proven membership
observer. kdebug trace records carry values chosen by their producers; generic
trace availability does not guarantee constructor arguments or IPC buffers.
DTrace privilege/provider restrictions, KDK availability and kernel debugger
access require separate qualification. Root is not a substitute for absent
tracepoints, private entitlement or an observer inside a different processor.

Most importantly, the source-controller objects described by the frozen
baseline live in DCP firmware. Counting similarly named macOS proxy constructors
or observing XNU IOService attachment does not directly count those objects.
Host tracing can close a success criterion only through a documented, correlated
firmware export or a runtime IPC identity contract. No such contract is assumed.

## DCP IPC Observation

**PASSIVE_DCP_IPC_CAPTURE_REQUIRES_PLATFORM_WORK**.

The pinned public [DCP tracer](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/hv/trace_dcp.py)
is concrete prior art for observing macOS-generated traffic on supported guests.
AFKRingBufSniffer reads existing TX/RX shared buffers through DART mappings and
maintains its own read cursor. EPICEp logs channel, type, version, sequence,
category and message length, tracks service announcements, and reads command/
reply payload buffers. DCPCallChannel tracks named call channels, tags, lengths
and request/reply data. This demonstrates an observer architecture, not tested
compatibility with M5,25G83 or its current memory mappings.

The [ASC tracer](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/trace/asc.py)
observes guest mailbox accesses and management/syslog endpoints. The short
[DPTX tracer](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/hv/trace_dptx.py)
selects PHY register nodes; it is not a ready-made DCP object-membership tracer.
These run in a host-side research hypervisor environment, not as an observer
executing inside DCP. A host hypervisor's memory visibility does not automatically
include all firmware objects or protected DCP address spaces.

| Desired Datum | What Existing Prior Art Supports | Missing M5 Qualification |
| --- | --- | --- |
| RTKit/ASC endpoints and mailbox words | Existing direction/endpoint/message observers | Supported guest boot, mailbox mapping and loss/ordering validation |
| EPIC channels, command/group IDs and raw buffers | Existing service map and buffer sniffer | M5 endpoint/buffer/ABI applicability and noninterference validation |
| DPTX instance identity | Selected device path and some decoded port-target fields | Proved same-physical-transmitter attribution; channel number is not stream ID |
| Timing configuration messages | Raw request/reply capture where exported | Current semantic schema; two formats may be conversion stages, not two sources |
| Object IDs, stream indices and payload bindings | Only if actual traffic carries them | No established M5 identity space or simultaneous-source contract |
| Firmware source-controller membership | Not directly enumerated by this tracer | Explicit firmware export or equivalent proved ownership semantics |

No passive macOS facility with a documented complete EPIC/RTKit buffer export
was identified. No commands are injected and none of these scripts is run.
The underlying research libraries also expose write-capable APIs; a future
observer needs an independently audited capture-only configuration. Prior art
must not be labeled non-invasive merely because one class is named Sniffer.

## m1n1 / Asahi Status

The public repository HEADs checked for this design are:

| Repository | Pinned Revision |
| --- | --- |
| AsahiLinux/m1n1 | b4654b32941d51afdb77579d63e7cb1aa6c03ecc |
| AsahiLinux/docs | 715664a269937fe83293f46bbbeaae6094cb504e |
| AsahiLinux/linux | 77cb8f24c2381a8abb7272d7bbdec548d6426a8a |
| apple-oss-distributions/xnu | f6217f891ac0bb64f3d375211650a4c1ff8ca1ea |
| apple-oss-distributions/dtrace | 4e57fe5c4dcf71e455817e7f26fc1f68e6eb4fe2 |

The Linux revision is recorded for provenance only. M4P does not perform a new
Linux DCP implementation audit or use that revision to claim M5 support.

The immutable [m1n1 hypervisor guide](https://github.com/AsahiLinux/docs/blob/715664a269937fe83293f46bbbeaae6094cb504e/docs/sw/m1n1-hypervisor.md)
lists macOS13.5 on M1/M2 and14.8.3 on M1-M3 as supported targets. It explicitly
says M4 and newer have no pinned target because of bugs and the requirement
for SPTM to run when booting XNU. This does not demonstrate a working M5/T8142
macOS26.6.2 guest. The [feature overview](https://asahilinux.org/docs/platform/feature-support/overview/)
lists M1-M4 pages; the attempted M5 page returned404. That missing page is a
documentation gap, not an architectural incapability proof.

The guide's existing guest setup also requires a custom boot object and lowered
per-volume security, including SIP changes and boot arguments. It is not a
normal-security tracing session or a modification-free Tier2 method. Those
instructions are not reproduced as a runnable recipe and are not executed.
Further checks in M4P concern only public observer/platform support contracts.

**M5_M1N1_DYNAMIC_PATH_PARTIAL**. The same pinned m1n1 revision explicitly
defines T8142 in [src/soc.h](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/src/soc.h)
and M5 Hidra E/P-core entries in [src/chickens.c](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/src/chickens.c).
Those are positive platform-recognition facts. They do not establish J704AP
research boot, supported macOS26 guest execution, DART/DCP tracing correctness,
or access to firmware-internal ownership. An M5 feature-page404 is not used to
erase this partial support. M4/M5 entries and generic tracers are insufficient
to call the dynamic path AVAILABLE.

No M5 guest version is pinned in the current guide, no J704AP DCP-observation
success recipe was identified in the checked support documents, and no M5
experiment is attempted. The known older-platform installation route changes
boot/security state; it cannot satisfy a no-boot-modification prerequisite.

## macOS Instrumentation Options

Classification refers to the stated facility/data scope, not a successful test
on this Mac. No provider enumeration, Instruments session, sysdiagnose, profile
installation or tracing command was run. The baseline-comparable target version
is macOS26.6.2 build25G83 on J704AP. A compatible Xcode/Instruments version is
required; the installed Xcode26.6 is not evidence of privileged trace access.

| Candidate | Classification | Version And Access Requirements | Data And Ownership Limit |
| --- | --- | --- | --- |
| Public IORegistry notifications and existing logs/signposts | USABLE_WITH_NORMAL_SECURITY | Existing public APIs; logging since macOS10.12, signposts since10.14; account/diagnostic permissions apply | Published host properties and producer-emitted IDs/metadata, not arbitrary arguments, buffers or DCP lifetimes |
| Instruments System Trace / Time Profiler | USABLE_WITH_NORMAL_SECURITY | Compatible Xcode/Instruments; system-wide collection may request administrator/developer authorization; protected-target restrictions remain | Scheduling, CPU stacks/timing and existing events. No complete DCP membership or IPC-buffer schema identified; samples do not count constructor instances |
| kdebug / ktrace existing tracepoints | USABLE_WITH_NORMAL_SECURITY | Pinned release policy permits root ownership subject to trace-owner arbitration; special non-root entitlement is DEVELOPMENT/DEBUG-only in this source | Timestamp/debug ID and producer-supplied words; pointers only if legitimately emitted. No identified source-attachment or full EPIC payload event |
| DTrace permitted process/user probes | INSUFFICIENT_DATA | Provider/build dependent; privilege, protected-process and SIP restrictions; M5 provider set not tested | Allowed probe data only; no unrestricted protected/kernel arguments or firmware constructors |
| DTrace FBT/kernel arguments | REQUIRES_SECURITY_REDUCTION | Default SIP disallows kernel address/memory access; FBT also needs unsafe-kernel-text permission. SIP reduction alone is insufficient; M5 availability unproved | Host entry/return arguments if available, not an observer inside DCP; no hooks or patching proposed |
| Existing IOService lifecycle tracepoints | INSUFFICIENT_DATA | Existing accessible tracepoints only; no injection | Host attach/terminate events need an explicit firmware export contract to prove source membership |
| Apple sysdiagnose, Graphics Diagnostic/TimingSnoop and ARTrace | INSUFFICIENT_DATA | Public index lists them; detailed Graphics/ARTrace downloads require Apple sign-in. Exact25G83 schema/privileges not verified | Diagnostic availability is not a controller-count or IPC-content contract; no tool/profile downloaded or run |
| KDK plus kernel debugger | UNAVAILABLE | No qualified M5 ownership observer. Exact matching KDK and supported debug connection required; catalog account-gated; boot/security requirements unverified for25G83 | Host symbols are not a DCP observer; no target-specific route established |
| Custom tracing kext | REQUIRES_SECURITY_REDUCTION | Recovery approval, Reduced Security, AuxKC/reboot; signature still required with SIP on | Adds host code, violating this design's modification-free observer constraint; no complete DCP visibility established |
| DriverKit extension | INSUFFICIENT_DATA | macOS10.15+; device-family entitlements, signing and system-extension approval | User-space driver scope, not arbitrary kernel/DCP access or a tracing substitute |
| Apple-private ownership telemetry | UNAVAILABLE | No legitimate target-specific access contract or entitlement identified; macOS26.6.2 applicability, privileges and security prerequisites unknown | An explicit export could be decisive, but neither its existence nor its schema is established by this review; no private call is proposed |

The [DTrace manual](https://github.com/apple-oss-distributions/dtrace/blob/4e57fe5c4dcf71e455817e7f26fc1f68e6eb4fe2/cmd/dtrace/dtrace.1)
disallows kernel address values/memory under default SIP.
[dtrace_subr.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/dev/dtrace/dtrace_subr.c)
checks CSR policy and `ml_unsafe_kernel_text` for FBT. Neither root nor a
suggestion to disable SIP establishes useful tracing; no such change is
authorized. The [ktrace owner checks](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/kern/kern_ktrace.c)
and [kdebug interface](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/kern/kdebug.c)
are published source contracts, not attestation of running-build events.

Apple's [System Trace presentation](https://developer.apple.com/videos/play/wwdc2016/411/)
describes scheduling, virtual memory and locking, not an M5 DCP schema.
[Signposts](https://developer.apple.com/documentation/os/recording-performance-data)
contain deliberately emitted IDs/metadata. [DriverKit](https://developer.apple.com/documentation/driverkit)
is a user-space framework; [Apple silicon kext policy](https://support.apple.com/guide/security/kernel-extensions-in-macos-sec8e454101b/web)
requires security/reboot changes. Facility availability is not sufficient data.

### Prerequisite Matrix

N means not required by the stated mode, Y required, C conditional, U not
established for M5/25G83. U is a blocker, not permission. No private user-client
calls are included in public APIs. KDK UNAVAILABLE above means an unqualified
observation route, not a claim that Apple publishes no matching KDK.

| Method | Root/Admin | SIP Change | Reduced Security | Boot Args | KDK | Kernel Debugger | Custom Kext | DriverKit | Binary Patch | Private Entitlement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Public notifications/logs/signposts | C | N | N | N | N | N | N | N | N | N |
| Instruments existing traces | C | N | N | N | N | N | N | N | N | N for public access; Apple collector privileges not transferable |
| Raw existing kdebug/ktrace | Y on release policy | N | N | N | N | N | N | N | N | N for root; non-root exception not assumed |
| Restricted DTrace process probes | C | N | N | N | N | N | N | N | N | N; protected targets restricted |
| FBT/kernel argument tracing | Y | Y or authorized restricted access | U | U | C | N | N | N | May patch kernel text; not accepted | U for Apple-internal exception |
| Existing IOService events | C | N | N | N | N | N | N | N | N | U if private export |
| sysdiagnose / graphics / ARTrace | C/U | U for gated tools | U | U | N/U | N/U | N/U | N | U | U |
| KDK/kernel debugger | Y | U | U | C | Y for matching symbols/development image | Y | N | N | U; software breakpoints not modification-free | U |
| Custom tracing kext | Y | N if properly signed | Y | C | C | N | Y | N | U; hooking rejected | C signing/access requirements |
| DriverKit extension | C | N for approved signed use | N | N | N | N | N | Y | N | Device entitlements required; no private DCP access supplied |
| Apple-private ownership telemetry | U | U | U | U | U | U | U | U | U | U; no legitimate access contract supplied |
| Documented m1n1 guest route | Y/Recovery owner | Y | Downgraded security/custom boot | Y in guide | Optional | Optional host debug, not DCP debug | N | N | U; no patch-free guarantee | Not a substitute for platform support |

No identified normal-security method supplies the required A-D ownership
evidence. Higher privilege does not repair missing firmware exports, semantic
identity or a supported M5 guest platform.

## Hardware Requirements

**EXACT_M5_HARDWARE_REQUIRED** for this specified experiment, as an
experimental-control choice, not a theorem excluding every alternate board.

- Exact target: a separate base-M5 14-inch MacBook Pro, Mac17,2, with T8142 and
  J704AP identity checked against the frozen baseline. Apple's [model list](https://support.apple.com/en-us/108052)
  identifies Mac17,2 as the2025 base-M5 model. M5 Pro/Max are not interchangeable.
- Alternate board: Apple's [Air model list](https://support.apple.com/en-us/102869)
  includes M5 Mac17,3 and Mac17,4. Product branding does not establish CPID,
  firmware/DPTX identity or J704AP equivalence. No alternate board equivalence
  was established here; substitution requires independently supplied evidence,
  not new frozen-T8142 analysis. SAME_T8142_PLATFORM_SUFFICIENT is not selected.
- M4/older: supported-platform trials can validate methodology, capture loss,
  timestamps and recovery, not T8142 architecture. M4 also lacks a pinned guest
  in the current guide; M1-M3 are the documented methodology targets.

Minimum resources are the exact sacrificial Mac, a second recovery/recording
Mac, a known-good data/charging cable, independent backup/log storage and the
ordinary hub/sink arrangement whose single physical link is being attributed.
No hardware is purchased, provisioned or modified here.

## Recovery Requirements

Recovery readiness precedes approval; it is not a claim that faults cannot occur.

1. Use an expendable target with no sole copy of data. Verify an independent
	backup and recovery procedure before any future change. Record board, OS,
	firmware identity and stock startup choice. A second APFS volume is not a
	backup: DFU restore can erase the shared internal storage.
2. Have a second working Mac with macOS14 or later, Internet access, power and
	free storage. Apple's [current Finder recovery guide](https://support.apple.com/en-us/108900)
	says32GB should suffice and may require a host software update for a newer
	target. Plan an up-to-date compatible host, not reliance on an old minimum.
3. Use a direct USB-C data-and-charging cable, not a Thunderbolt3 cable. The
	base14-inch M5 MacBook Pro's [DFU port](https://support.apple.com/en-us/120694)
	is the rightmost USB-C port when facing its left side, unlike several older
	models. Keep both Macs powered; use target MagSafe where applicable. Follow
	Apple's current DFU instructions only during separately authorized recovery.
4. Keep owner login/Activation Lock credentials and FileVault personal recovery
	material secure outside the target, never in traces, Git or assistant prompts.
	[FileVault](https://support.apple.com/guide/security/volume-encryption-with-filevault-sec4c6dc1b6e/web)
	is not a backup; a recovery key cannot undo cryptographic erasure. Leave
	FileVault unchanged; disabling it is not a design prerequisite.
5. If observation or macOS stalls, stop stimuli and preserve host-side evidence.
	Follow an approved ordinary shutdown/reboot and stock-startup/recovery path.
	Forced power-off may lose unsaved data. A user-space timeout does not prove
	DCP cancellation or immediate recovery.
6. If ordinary recovery fails, use Finder DFU Revive first, intended to repair
	firmware/recovery without erasing data. If revive fails, Restore erases the
	Mac and restores firmware/OS, requiring approval and the verified backup.
	Apple Configurator is historical recovery tooling; the old guide redirected
	to a general guide here. Finder is the verified current path, not an invented
	Configurator/M5 recipe. Neither path is executed now.
7. Restore may install newer available firmware/OS. Exact25G83 recovery/downgrade
	is not guaranteed. Re-record identity and invalidate same-build comparisons
	if it changes. Failure to enter DFU or recover means stop and seek service,
	not improvised boot arguments, NVRAM changes or repeated private operations.

| Risk Class | Meaning And Assessment |
| --- | --- |
| REBOOT_RISK | Responsiveness loss/restart. Low added risk for supported telemetry; potentially high/unknown for unqualified low-level observation |
| OS_RESTORE_RISK | Failure to boot/recover software configuration; may require DFU revive or erasing restore, not necessarily physical damage |
| DATA_LOSS_RISK | Unsaved data, corruption or full internal-volume erasure; independent backup and credentials mandatory |
| HARDWARE_DAMAGE_RISK | No identified permanent-damage mechanism for ordinary public observation, not guaranteed zero. Unvalidated low-level code/power/thermal faults or bad cabling are not bounded by DFU; uncontrolled MMIO/power changes rejected |

This is recovery planning, not authorization to change boot or security.
A backup or sacrificial label cannot make an unavailable observer safe to run.

## Stimulus Requirements

**STIMULUS_REQUIREMENT_UNRESOLVED**.

Ordinary operation might expose two already-created source contexts, or an
explicit source-identity contract, without requesting a second active stream.
Alternatively, macOS might instantiate/export only the source it uses. Neither
behavior has been demonstrated on the target. A trace containing one source
cannot discriminate those possibilities. Thus a meaningful second-stream
stimulus is neither proved necessary nor proved unnecessary.

| Ordinary Supported Action | Potential Information | What It Does Not Establish | Initial Design Use |
| --- | --- | --- | --- |
| Attach the ordinary hub with two connected sinks | Link/host object creation, service announcements, normal configuration requests | That macOS requests two independent source contexts on that link | One future attach, only after all observer gates pass |
| Detach that hub | Teardown and lifetime boundary | A concurrent second source; replacement is not multiplicity | One future normal detach only while responsive |
| Attach/detach a downstream sink | Topology/EDID changes and reconfiguration | Source creation rather than branch port handling | Not in the initial bounded run |
| Sleep/wake | Suspend/resume and new lifetime generations | A second simultaneous source; addresses can be reused | Not in the initial run; expands power-state risk |
| Supported lid open/close | Internal/external display policy changes | Same-DPTX membership; separate internal/external owners are not comparable | Not in the initial run |
| System Settings resolution or refresh change | Timing-state changes on an existing source | Two independent timing contexts rather than sequential modes | Not in the initial run |

These are proposed supported user actions, not instructions to perform them in
M4P. A capability provider must identify why an ordinary attach can expose A-D
evidence before the future experiment is accepted. If an unsupported private
display API, forced MST enable, source allocation, DPCD operation or injected DCP
message is necessary, the initial design remains blocked. Do not add that
stimulus, retry the retired selector or reopen static analysis to construct it.

## External Wire Observation

**WIRE_ANALYZER_OPTIONAL_HIGH_VALUE**.

An external analyzer on the exact upstream physical DisplayPort link could
correlate AUX/MST messages, payload allocation and main-link virtual-channel
traffic with software timestamps. Full main-link capture with distinguishable
concurrent payload/timing state is necessary to claim independent packetization;
AUX-only traffic, MSTM enable, allocation acknowledgements or an ACT indication
cannot establish it. This is an evidence requirement, not a qualified analyzer
product or purchase recommendation.

Wire observation cannot name internal source-controller instances or repair an
absent host-to-DCP identity contract. Conversely, a qualified internal/IPC
observation satisfying A-D need not depend on a wire analyzer. Insertion may
alter USB-C/DP negotiation, lane rate, signal integrity or timing; any future
analyzer must support the negotiated topology without changing it and document
its own clock uncertainty and loss. No analyzer is connected or purchased here.

## Experiment Tiers

The ladder is a design classification, not permission to begin at Tier 0 or to
escalate automatically. Every runtime tier is unexecuted in M4P.

| Tier | Information And Method | Risk | Prerequisites | Stop Conditions |
| --- | --- | --- | --- | --- |
| Tier 0: public telemetry | Existing registry properties/notifications, public display descriptions and permitted logs; reuse frozen observations here | Low added software risk; privacy and diagnostic load remain | Documented normal-security APIs and a defined field schema | Missing same-owner/source identities: record insufficient data, do not reinterpret display counts |
| Tier 1: supported tracing | Instruments, existing signposts and permitted kdebug events; host timing/lifecycle correlation | Collection overhead, dropped events, possible system responsiveness effects | Compatible supported collector, ordinary authorization, no security/boot change, known emitted fields | Protected-data denial, missing object/IPC fields, trace loss or responsiveness change; no privilege escalation |
| Tier 2: research reboot/recovery without kernel or firmware modification | Potential rebooted observation environment with independently demonstrated read-only access; none qualified for the target question | Reboot and recovery burden; method-dependent stall risk | Identified M5 method, known boot/security requirements, no binary patch or firmware change, recovery readiness | No capable observer or an undisclosed boot/security change. The published m1n1 route does not qualify as a normal-security Tier 2 shortcut |
| Tier 3: reduced-security/kernel-level or hypervisor observation | Potential host IPC buffers/arguments; firmware membership only through a proven export contract | Potential hangs, watchdogs, failed boot, restore/data-loss exposure and observer effects | Separate explicit approval, exact M5 support, capture-only audit, bounded recovery, documented identity schema | Any prerequisite unknown, patch/write requirement outside approval, missed/lost events, unexpected reset, heartbeat/deadline failure |
| Tier 4: active DCP/MST manipulation | Injected private commands, source allocation, DPCD writes or payload programming | Unbounded here; can alter hardware state | Outside M4P and the recommended initial experiment | Do not enter this tier; no implementation, selector or command is authorized |

No available Tier 0-2 method has been shown to resolve the frozen opacity.
Tier 3 is not accepted merely because the target is sacrificial. In particular,
the published m1n1 guest workflow requires custom boot/security changes and
does not currently supply a qualified J704AP/25G83 observer. Tier 4 is excluded.

## Success Criteria

A future observation may satisfy the runtime question only through one or more
of these four positive results, with the attribution checks below:

| Criterion | Required Positive Observation |
| --- | --- |
| A | Two distinct runtime source-controller instances with overlapping lifetimes, each attached to the same physical T8142 DPTX register owner |
| B | Two independent timing contexts concurrently bound to that same physical DPTX, not two snapshots of one changing timing context |
| C | Two simultaneous payload/source records under that same DPTX with independent source attribution, not two slots or aliases of one source |
| D | An observed runtime host-to-DCP message/API proving an explicit source identity space greater than one on the same DPTX, with semantics establishing independently addressable source contexts |

For D, two arbitrary integer values, sequence numbers, channel IDs, downstream
port numbers or a wide field alone are not proof. The message contract must
identify a source dimension and its same-DPTX scope. If concurrent instantiation
is not observed, report D as an identity-contract result, not as demonstrated
simultaneous output or an A-C result.

All accepted results require raw bytes/events alongside decoded values; exact
machine, board, OS/build and firmware identity; observer revision/configuration;
the physical cable/port/hub/sink map; timestamp units and clock error; capture
start/end and sequence coverage; and the source of each decoding rule. An
accepted owner identity must distinguish physical DPTX instances, not assume
that an IPC endpoint, host IOService or register-address-looking value is one.

Object pointers require a lifetime generation and create/attach/detach evidence
or a documented atomic membership snapshot. Pointer reuse, proxy references and
sequential destruction/recreation do not prove concurrency. Independent state
must be distinguished from two references to the same source. Record dropped
events, buffer wrap, reboot generations and observer effects; gaps spanning the
claimed relationship make that claim inconclusive. Do not derive a missing
decoder or owner map through further frozen T8142 reverse engineering.

A-D would narrow the architectural uncertainty. None alone proves a usable
macOS MST implementation, two independently displayed images, driver safety or
the correctness of active source programming.

## Failure / Inconclusive Criteria

- One controller, one timing context, source ID 1 or one payload record is
	inconclusive, even during several ordinary transitions. It is not a
	demonstrated one-stream architectural limit.
- Branch topology/sideband traffic, MSTM enable, one ACT-like event or a payload
	table update without source ownership is inconclusive; those mechanisms are
	already inside the frozen static baseline.
- Two host services, displays, IPC channels, endpoints or downstream ports are
	inconclusive without an explicit same-physical-DPTX source relationship.
- Sequential modes, replacement objects, pointer reuse, duplicate event
	delivery or two records aliasing one source do not meet A-C.
- Capture of mailbox words without needed buffers, unknown message layouts,
	unverified owner mapping, redacted identities, dropped intervals or a trace
	begun after unobservable object creation leaves membership unresolved.
- A boot failure, unsupported guest, protected-data denial, hung target or
	observer-induced reset is an instrumentation failure, not evidence against
	M5 MST. Preserve that failure and stop; no automatic retries or escalation.
- An ordinary stimulus that never requests or reveals a second source cannot
	exclude dormant capability. Neither negative IPC nor negative wire evidence
	alone proves physical source cardinality.

The primary feasibility and ownership results therefore remain unresolved
unless the exact positive evidence is obtained. An inconclusive future run must
not become another open-ended static investigation or active experiment.

## Risk Matrix

Daily-use and sacrificial safety below describe suitability for a future
approved purpose, not authorization or a promise of safety. No method runs now.
Restore risk includes erasure and exact-build reproducibility loss; hardware
damage is separately assessed in Recovery Requirements.

| Method | Target Evidence | Daily-Use Safe? | Sacrificial Safe? | Security Changes | Reboot Risk | Restore Risk | Evidentiary Strength |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Public IORegistry notifications | Host IDs/properties/lifecycles | Generally low added risk; not authorized now | Conditional on public APIs only | None | Low added | No expected increase | Insufficient for firmware membership |
| Existing unified logs/signposts | Producer-defined timing/metadata | Generally low added risk; privacy review | Conditional on bounded collection | None for permitted data | Low added | No expected increase | Supportive unless a complete export is supplied |
| Instruments System Trace/Time Profiler | Host schedules, stacks, emitted events | Not accepted as a new session in M4P | Conditional on supported collector and load limits | None for supported scope | Low to method-dependent | No expected increase for supported use | Correlation, not DCP object enumeration |
| Existing kdebug/ktrace and IOService events | Fixed event arguments and host lifecycle | No new collector approved | Conditional; do not displace an active trace owner | Root/authorization, not automatically SIP reduction | Overhead/stall possible | Low expected; not tested | Missing same-owner source schema |
| sysdiagnose/Graphics Diagnostic/ARTrace | Diagnostic package or listed graphics trace | No new diagnostic/profile approved | Unknown until collector contract qualified | Gated tool requirements unverified | Load/method dependent | Unverified for gated tools | Exact data and ownership semantics unverified |
| Restricted DTrace process probes | Allowed user/process events | Not approved for this question | Conditional but insufficient | No reduction for allowed scope | Method dependent | No expected increase for allowed scope | Does not observe DCP constructors |
| DTrace FBT/kernel arguments | Potential host function arguments | No | Unqualified on target | Restricted access and unsafe-kernel-text prerequisites; SIP alone insufficient | Potential stall/panic | Possible if boot/debug setup changes | Host data only, firmware ownership unproved |
| KDK/kernel debugger | Host symbols, state, possible breakpoints | No | Unqualified on target | Build/debug/boot policy unverified | Expected reboot; stopping kernel can stall system | Possible | Does not automatically expose DCP-internal state |
| Custom tracing kext | New host instrumentation | No | Not accepted by this design | Reduced Security, approval, AuxKC/reboot | Elevated/unknown | Possible | Adds risk without a proven ownership export |
| DriverKit extension | Entitled user-space device scope | No installation approved | Not justified as this observer | Signed/entitled system extension | Approval/lifecycle dependent | Not qualified here | No arbitrary display/DCP access |
| m1n1 passive host IPC architecture | Mailbox/shared buffers if target mapping works | No | Not yet qualified | Custom boot/security changes in published route | High/unknown on unsupported guest | Credible revive/restore risk | Potential D, only with validated source semantics |
| Apple-private ownership telemetry | Unknown; potentially explicit export | No private calls approved | Unavailable to this review | Private entitlement/producer contract unknown | Unknown | Unknown | Cannot credit an unavailable schema |
| External wire analyzer | AUX and, if capable, main-link payload/timing | No insertion approved | Conditional on suitable non-disruptive equipment | No Mac security reduction inherent | Link disruption possible | No expected increase from passive wire observation | High-value correlation, not internal object identity |
| Active DCP/MST manipulation | Alters the state being investigated | No | Out of scope | Undetermined; never presumed acceptable | Unbounded here | Unbounded here | Excluded initial stimulus, regardless of potential data |

## Recommended Experiment

Exactly one future architecture is retained: **M4P-IPC-OWNERSHIP-01**, a
qualified M5 passive host-to-DCP IPC observation with a pre-established
same-DPTX source-identity contract, during one ordinary hub attach/detach.
**Blocked design, not an executable recipe.** The existing m1n1 tracer is prior
art for this architecture, not the missing qualified M5 implementation.

| Design Element | Requirement |
| --- | --- |
| Machine | Separate base-M5 Mac17,2/T8142/J704AP; no daily-use target; recovery host and independent backups ready |
| OS | Stock target macOS 26.6.2 build 25G83 for baseline comparison. If unavailable or unsupported, stop; another build requires an explicitly revised scope and cannot silently replace the baseline |
| Tool And Security | A pinned, independently validated M5 observer/guest combination with a capture-only audit. No currently checked revision meets this requirement. A custom-boot/hypervisor route belongs in Tier 3 with separate approval; no SIP/AMFI/Secure Boot/Gatekeeper/NVRAM changes are supplied or authorized here |
| Observer | Capture both directions of the relevant mailbox and shared-memory IPC without injecting messages, acknowledging on behalf of a peer, changing producer buffers or altering display state. Record endpoint/channel discovery, complete lengths/buffers and request/reply generations |
| Semantic Prerequisite | A legitimate independently supplied runtime/API schema must map source identities and the physical DPTX owner, capable of criterion D. A-C may be credited only if the same capture contains a proven membership/timing/source export. Do not substitute host proxy counts |
| Stimulus | One ordinary attach of the known hub with two connected sinks, followed by one normal detach only while responsive. No sleep/wake, lid, mode cycling or private second-stream command in this initial run |
| Data | Raw mailbox words and shared buffers, direction, clocks/units/error, service maps, full source/owner fields, event loss/wrap, observer health, hardware/OS/firmware identities and physical topology; decoded output always references raw offsets and schema provenance |
| Acceptance | A-D only, with lifetime/independence/attribution rules above. IPC-only D needs explicit same-owner source semantics, not guessed IDs. Preserve uncertainty about actual independent output |
| Duration And Volume | Proposed administrative caps: 30 seconds baseline, at most 60 seconds after attach, then detach and at most 30 seconds tail; hard 180-second session cap including transitions and a 256 MiB non-overwriting raw-data cap. These are resource budgets, not measured liveness guarantees |
| Abort | Stop on first missed validated 5-second observer heartbeat budget, trace gap, decoder/layout mismatch, unexpected write, unsupported target, privacy leak, display/OS stall, watchdog/reset, deadline or storage cap. Preserve incomplete data; do not retry, extend the cap or add stimuli |
| Recovery | Stop collection/stimuli, preserve off-target evidence, then approved stock reboot/recovery. If necessary Finder DFU revive, erasing restore only with separate consent and verified backup; service escalation if recovery fails |

Before approval, the observer provider must demonstrate that capture is
non-blocking or provide a justified bound on interception delays, and that
stopping the host recorder does not leave guest/DCP execution suspended. A
five-second external heartbeat and wall-clock limit do not cancel an in-flight
DCP operation or prove that the Mac can recover. Unbounded synchronous traps
or unknown cleanup behavior fail qualification.

Also required before approval: actual evidence that the ordinary stimulus can
expose the identity contract or existing membership. With neither a qualified
observer nor a known informative stimulus, a sacrificial trial has no credible
decisive observation yet. Public-only timing collection is not recommended as
a substitute experiment, and an unavailable schema is not authorization for
more T8142 disassembly. No part of this architecture was built or executed.

## Go/No-Go

Primary result: **SACRIFICIAL_EXPERIMENT_REQUIRES_UNAVAILABLE_CAPABILITY**.

The architecture is specified conditionally, but the execution gate is closed:

| Gate | Evidence And Decision |
| --- | --- |
| Target hardware | Exact target identified, but a separate sacrificial unit and recovery kit have not been provisioned or validated in M4P |
| M5 execution platform | Public m1n1 source recognizes T8142/M5; the pinned guest guide does not provide a supported M4-or-newer macOS target. Recognition is not usable J704AP/25G83 guest support |
| Decisive observer | No identified normal-security export of complete membership, and no validated M5 passive IPC observer with a source/physical-owner schema. Host tracing alone cannot observe code executing inside DCP |
| Informative stimulus | Ordinary operation may or may not expose dormant contexts/source identity; a meaningful second-stream stimulus remains unresolved and private control is excluded |
| Bounded risk/recovery | Apple's recovery path is documented, not rehearsed here. Capture delay/cleanup behavior, exact-build recovery and target-specific observer effects remain unqualified |

Unavailable means not identified and qualified within the checked public
sources and this task's constraints, not proof that Apple or every researcher
lacks such a capability. A published supported M5 observer with complete
same-owner semantics and bounded behavior could change the decision. Providing
that capability would be a separate approved task. Documentation completeness,
CPU recognition, a recoverable older guest or theoretical observability cannot
open this gate. The scientific question remains worth a decisive observation,
but its required capability must exist before hardware risk is accepted.

### Public Source Provenance

Reviewed 2026-09-14. The following immutable revisions and raw-file SHA-256
values identify the sources used; public source was retrieved in memory, never
executed or installed. Source-level findings are not attestations that the
target macOS binary implements the same revision or exposes every facility.

| Source | Raw-File SHA-256 |
| --- | --- |
| [Asahi macOS hypervisor guide](https://github.com/AsahiLinux/docs/blob/715664a269937fe83293f46bbbeaae6094cb504e/docs/sw/m1n1-hypervisor.md) | `2f84ce6e0a04c04b55ec8d8fc77fbc11281844d1a9358b5deb049c7819937bab` |
| [m1n1 src/soc.h](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/src/soc.h) | `3569ce0f11ad808f724bf0c050b1fc8381dd199791ec95729f411ad8c2359bca` |
| [m1n1 src/chickens.c](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/src/chickens.c) | `80a84b63d6d90b4495543b90ac4dc7451dfe73129f7dc791b4220bc80b99c00a` |
| [m1n1 trace_dcp.py](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/hv/trace_dcp.py) | `52e9748886f81e52b5f92861c08ad2d8302d7609a515caa453b1f72faca0d8a5` |
| [m1n1 trace/asc.py](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/m1n1/trace/asc.py) | `0a90aa0cdfcf546c50034e347959242b430a8c7b42c03d9c78d317e44430c5d2` |
| [m1n1 trace_dptx.py](https://github.com/AsahiLinux/m1n1/blob/b4654b32941d51afdb77579d63e7cb1aa6c03ecc/proxyclient/hv/trace_dptx.py) | `22a384a8c6c223030de6921f1ab693906221ac79f323c3f4eb35a1eb144461d7` |
| [XNU kern_ktrace.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/kern/kern_ktrace.c) | `92f5140bcadb3e12104321ca7848b153706692df5f400499c59a0c772eb3c919` |
| [XNU kdebug.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/kern/kdebug.c) | `78462b3da149422449650780fbb1ed6921803407b867e1548521828f4d6962d1` |
| [XNU dtrace_subr.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/dev/dtrace/dtrace_subr.c) | `1469e313ed1732f7cdfee246a3639cef0768637032c47609142099cac96e11c8` |
| [XNU dtrace.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/dev/dtrace/dtrace.c) | `cdfe2fc5c78623d1a8ab4a9960fa39c86963a9024e16a3849808af92ff8c50ef` |
| [XNU fbt.c](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/dev/dtrace/fbt.c) | `52914300e7366f8a677a5659fcc429db7f01bd806cd9ccd43414c814ded99a12` |
| [Apple DTrace manual](https://github.com/apple-oss-distributions/dtrace/blob/4e57fe5c4dcf71e455817e7f26fc1f68e6eb4fe2/cmd/dtrace/dtrace.1) | `bb92b5c4389002d76d0387f8641d49c6565b37a8858d22d79a059a933e2becc6` |

The live Apple pages linked above are mutable, observed on the same date.
Relevant page dates: MacBook Pro/Air identification, 2026-07-02; Finder
revive/restore, 2026-06-16; DFU port table, 2026-03-10; FileVault security,
2026-01-28; Apple silicon kext/SIP security pages, 2021-02-18. The System Trace
presentation is from WWDC 2016, not a current M5 support certification.

The [Apple Profiles and Logs index](https://developer.apple.com/feedback-assistant/profiles-and-logs/)
listed Graphics Diagnostic, ARTrace/ktrace and sysdiagnose. Its
[Graphics Diagnostic instructions](https://developer.apple.com/services-account/download?path=/OS_X/OS_X_Logs/Graphics_Diagnostic_Logging_Instructions.pdf),
[ARTrace instructions](https://developer.apple.com/services-account/download?path=/OS_X/OS_X_Logs/ARTrace_Logging_Instructions.pdf)
and the [KDK catalog](https://developer.apple.com/download/all/?q=Kernel%20Debug%20Kit)
redirected to Apple sign-in; no authenticated content was read, and no missing
schema or target availability is inferred from that access limitation alone.
The archived kernel-debug guide returned navigation only. A missing guessed
source/page path was corrected or excluded; HTTP 404 is not evidence of a
hardware limit. [Apple SIP policy](https://support.apple.com/guide/security/system-integrity-protection-secb7ea06b49/web)
also distinguishes SIP from hardware kernel integrity protection; removing
one restriction cannot be presumed to remove the others.

### Documentation Validation Scope

Required gates are section/classification consistency, source/hash provenance,
local links, unchanged frozen reports and safety markers, and exact protected
Git references. M4P does not build or test code, run firmware tools, enumerate
hardware or exercise an observer. Passing document checks verifies the design
record, not M5 runtime functionality or recovery reliability.

## Current Daily-Use M5 Policy

No dynamic experiment, tracing session, display transition, recovery rehearsal,
boot component, kernel/firmware patch, private display call, DCP command or
security change is authorized or performed in M4P. Do not run even a no-open
mode of the historical DPDV helper/parent as part of document validation.

Selector 0 remains **RETIRED_ON_DAILY_USE_M5**. The global gate remains
**NOT_READY_FOR_DPCD_TEST**. The consumed M2F attempt marker and both historical
result files remain unchanged; the M2G DPCD-read attempt marker remains absent.
No new hardware capture has been created.

**STATIC_PACKETIZER_ANALYSIS_FROZEN** and
**NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED** remain permanent.
M3A-M3D and the M3E0 conclusion are preserved, not amended by new analysis.
There is no M4 differential, renewed host MST scan, payload-ID/timing/controller
cardinality work, selector research, sideband analysis or packetizer extension.

The only open question remains: **Runtime source-controller membership of one
physical T8142 DPTX register owner.** The conditional architecture in this
document does not authorize executing it, weakening protections on any machine,
or treating the daily-use M5 as sacrificial hardware.