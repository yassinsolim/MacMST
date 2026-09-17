# M5P4: Targeted Public Display Lifecycle Log Correlation

## Objective

Correlate narrowly scoped historical public kernel messages with the immutable
M5P3 attach differential. Seek explicit lifecycle ordering, typed identifiers,
downstream discovery and policy decisions, without converting monitor, sink,
endpoint, proxy, framebuffer or unit counts into source-stream counts.
The objective remains independent external displays from one base M5 through
ordinary USB-C/DisplayPort MST hubs without DisplayLink or special multi-DP
Thunderbolt hardware. This milestone is observation only.

Result: **PUBLIC_LOG_RUNTIME_PARTIAL**. The scoped history is retained and
provides sufficient attach lifecycle evidence for this milestone without a
new reconnect: **HISTORICAL_LOG_EVIDENCE_SUFFICIENT**. The proposed next route
is **EXTERNAL_DP_PROTOCOL_CAPTURE_WARRANTED**, as a separate capture-planning
decision, not permission to attach an analyzer, change hardware, or issue AUX
commands now. Same-DPTX independent sources remain unestablished.

Local hypothesis: messages naming the newly qualified M5P3 device/service
classes may explicitly relate attach-created external records to preexisting
remote-port objects. The exact historical query below is the discriminating
check. Absent identity-bearing/lifecycle statements would leave that hypothesis
unestablished, not prove that the hardware cannot produce multiple streams.

## Safety Boundary

The hub is currently owner-reported connected with both monitors in their normal
duplicated-image behavior. Leave it connected. Do not change resolution,
refresh, mirror, lid or sleep state. No physical action is requested for the
historical phase. Only `log show` with the exact predicate/window, local command
help, public metadata, immutable capture reads, offline analysis/tests and Git
provenance/publication are permitted here. Info/debug/signpost display options
include already retained records; they do not enable new logging.

No sudo, log-collection archive, logger configuration, user-client open,
private IOKit/framebuffer method, DPDV selector, DCP/AUX/DPCD request, EDID/timing
injection, payload allocation, kernel memory read, debugger, firmware, m1n1 or
boot/security change. There is no live-stream implementation in this first
phase. Permission failures are recorded, with no elevated/private fallback.

## M5P3 Baseline

The clean local branch `research/m5-passive-runtime-topology` at
`369b5e5f202640f906904d2dc91413bd1b0930f3` was audited and published exactly
as-is before M5P4. Its four linear commits remain `b7ec4b8`, `060cf50`,
`127c670` and `369b5e5`, directly above M5P2
`5aed45b9458be08ba05b24804d9439644ccb7c2c`. Publication used an explicit
branch-only refspec with `push.followTags=false`; upstream equals HEAD, 0/0.
All 44 preexisting published head/tag/peeled identities are unchanged; 45
local/remote identities match after publication. No merge or PR was created.
The M5P4 branch is `research/m5-public-log-correlation` from that exact HEAD.

All 14 immutable snapshot inputs and both analysis files match their retained
hashes; the differential reproduces from the pair. No new M5P3 capture exists
in its artifact root, and none is made here. The consumed M2F marker and both
historical receipts are unchanged; the M2G DPCD-read marker remains absent.
M5P1/M5P2/M5P3 offline CTest passes 3/3 before publication.

Preserve M5P3's one new VG248 logical record and External DCPEXT0/Unit 0
DP/AV tuple, persistent controllers/remote ports, two-lane HBR3 representation,
non-tunneled USB-C transport and SinkCount 1. Virtual-device runtime and
independent source identities were not established. The existing result is
`PASSIVE_RUNTIME_TOPOLOGY_PARTIAL`, not same-DPTX multi-source proof.

## Predicate

Exactly the M5P3 [proposed predicate](m5-passive-runtime-topology.md#proposed-future-predicate),
including its case-insensitive message matching:

```text
process == "kernel" AND (
    eventMessage CONTAINS[c] "DCPDPDeviceProxy" OR
    eventMessage CONTAINS[c] "DCPDPServiceProxy" OR
    eventMessage CONTAINS[c] "DCPAVVideoInterfaceProxy" OR
    eventMessage CONTAINS[c] "AppleDCPDPTXRemotePortProxy" OR
    eventMessage CONTAINS[c] "AppleDCPDP2HDMI"
)
```

| Selection | Reason and limit |
| --- | --- |
| Process `kernel` | Host kernel proxy/port lifecycle; no WindowServer or other process expansion |
| Subsystem | No original restriction; preserve returned public subsystem metadata without inventing a known logging subsystem |
| Category | No original restriction; preserve returned categories without guessing one |
| `DCPDPDeviceProxy` | One newly exposed external device proxy in M5P3 |
| `DCPDPServiceProxy` | One newly exposed external DP service proxy |
| `DCPAVVideoInterfaceProxy` | New external video-interface proxy, distinct from a source identity |
| `AppleDCPDPTXRemotePortProxy` | Preexisting remote-port Units 0 and 1; selected relationship unknown |
| `AppleDCPDP2HDMI` | New DP/AV service provider advertisement, not independently proved source or MST policy |

The tool verifies the documented predicate before acquisition. It does not
add generic MST/HPD/display terms to the query. Such vocabulary is searched
only **within** the selected messages. No syntax repair or semantic broadening
has been required.

## Historical Window

`M5P3_LOG_WINDOW_START = 2026-09-16T11:11:59Z`

`M5P3_LOG_WINDOW_END = 2026-09-16T11:27:49Z`

This is the documented **950-second** window, not hours of logs. Disconnected
capture: `2026-09-16T11:11:59.782377+00:00` through
`2026-09-16T11:12:00.725762+00:00`. Connected capture:
`2026-09-16T11:27:47.121356+00:00` through
`2026-09-16T11:27:48.163283+00:00`. Both are from the same M5P3 public boot
token, model Mac17,2 / Apple M5, macOS 26.6.2 / 25G83.

The physical unplug-to-plug transition time was not timestamped by M5P3; the
owner confirmation preceded the connected capture. A small arbitrary margin
before that capture could exclude the real attach. Therefore use the smallest
already documented full bracket with subsecond rounding margins. Do not
represent capture start as a `USER_TRANSITION_TIMESTAMP`, or confuse a log's
`LOG_EVENT_TIMESTAMP` with a user-confirmed transition point. UTC offsets are
explicit in the command; no local-time reinterpretation is used.

## Historical Availability

**M5P3_HISTORICAL_LOGS_RETAINED**. The exact query succeeded without elevated
access on `2026-09-17T08:27:13.813595+00:00` through
`2026-09-17T08:27:16.309107+00:00`, exit 0, with 424,989 stdout bytes and zero
stderr bytes. It returned **477 predicate/window-matching records**, within
the 1,000-record / 2 MiB budget. One additional parsed item did not pass the
scope filter and was not retained; its content is not used as evidence.
No timeout, truncation, privilege failure or expiry notice occurred. Presence
of these matching records proves scoped historical availability, not complete
logging of every display event or complete storage retention.

All retained records report process `kernel`; subsystem and category strings
are empty. There are 164 `Default`-level and 313 `Error`-level records. Nine
retained sender paths name the AppleDCPDPTXProxy kernel image and 155
name DCPAVFamilyProxy; the other 313 sender paths were outside the initial
system-path allowlist and are omitted. Do not infer the actual emitting image
or a firmware origin for those records from their filename-like message text.
An `Error` log level alone does not establish a failed call or policy rejection.

The intake's `redacted_record_count=313` means **metadata omission**, not
hidden message bodies: every privacy note is `NON_SYSTEM_SENDER_PATH_OMITTED`.
Zero records were dropped for private content, and no retained message-body
identifier was redacted. The exact message text remains in the raw-filtered
projection and normalized records. The initial rule-based event labels are
conservatively `UNKNOWN_EVENT`; method-style log text is reviewed explicitly
below instead of interpreting that label as absence of lifecycle information.

## Log Normalization

The [offline analyzer](../../tools/display_log_analyze.py) keeps explicit UTC
timestamps at nanosecond precision, process, system sender-image path, returned
subsystem/category/level, raw message text, available activity/signpost IDs,
thread/process IDs and capture generation. Missing IDs stay null. Full original
stdout is hashed, then discarded. Retained `raw-filtered.ndjson` is a structured
allowlisted projection: original message text is preserved unless a documented
identifier redaction is necessary. It is not an unredacted complete system dump.

Records containing unrelated home paths/network destinations are dropped;
serial/GUID-style values are redacted, not reconstructed. Normalized records
bind the retained raw projection hash and original canonical-record hash.
Unrecognized or redacted statements remain `UNKNOWN_EVENT`. Explicit-only
vocabulary covers link/HPD/transport, service/device/display/sink lifecycle,
mode/mirror, stream creation/rejection, MST detection/disable and policy.
Keyword mention alone is not an action or a policy decision. Automated matches
require full scoped-message review before becoming report findings.

Input order is retained. A separate timestamp ordering marks equal timestamps
as unordered, and never proves causation. The reader is bounded to 1,000
records, 2 MiB stdout, 64 KiB per line and a 60-second finite query. Limits,
malformed data or inaccessible output cannot produce a complete negative claim.

The final [offline method review](../../artifacts/runtime/m5p4/review/observations.json)
groups all 477 messages into **49 printed class/method pairs**, preserves four
opaque object-token groups and extracts **14 explicit field observations**.
It separates message redaction (0) from sender metadata omission (313).
These observations deliberately use narrower names such as
`REPORTED_AGGREGATE_SINK_COUNT_CHANGE` and
`REPORTED_LINK_ROLE_NOT_SOURCE_ID`, not an invented source-creation event.
The original acquisition files and their conservative classifications are not
overwritten. One processed-method name, such as `GetVirtualDeviceMode<1a>`,
does not reveal a returned value or prove a virtual-device instance.

## Lifecycle Sequence

The retained messages span `2026-09-16 11:26:43.240117+0000` through
`2026-09-16 11:27:48.309970+0000`. All 476 adjacent timestamp comparisons are
strictly increasing in the retained output. That is `VERIFIED_LOG` **log-time
order**, not cross-thread causality, event completeness or user transition time.
Every activity ID is raw 0, every process ID is 0, and no signpost ID is
retained. Zero activity values are not a unique activity tying the records
together. Thread IDs are retained for local ordering context, not source IDs.

Indices below are the immutable zero-based `input_index`, not a physical or
source index. Dates are all 2026-09-16 UTC. Quoted fields are exact retained
message text; source-like filenames/line numbers are printed annotations,
not new source-code or firmware inspection.

| Record | UTC time | Observed statement | Qualified meaning |
| --- | --- | --- | --- |
| 0 | 11:26:43.240117 | `AppleDCPDPTXRemotePortProxy<0x100000810>::validateConnection: enter: die0::dispext1::core0 -> die0::atc3::dpphy (role=0, supportsHPD=1)` | `VERIFIED_LOG` explicit route labels and opaque object token, not a physical-owner contract |
| 1 | 11:26:43.244977 | Same token/route, `validateConnection: exit`, `ret=0x00000000` | `VERIFIED_LOG` reported validation return, not proof that two streams can bind |
| 2 | 11:26:43.245008 | Same token, `connectTo: die0::dispext1::core0 -> die0::atc3::dpphy` | `VERIFIED_LOG` one logged connection request; not two logical-source assignments |
| 11 | 11:26:43.247935 | Same token, `powerChangeDone_block_invoke: powerstate 0 -> 1` | `VERIFIED_LOG` raw transition; undocumented enum meaning not invented |
| 13 / 16 | 11:26:45.124767 / .130183 | `AppleDCPDP2HDMI::handleStart result=1`; `::start result=1` | `VERIFIED_LOG` service-method results, not allocation/constructor or EPIC announcement receipts |
| 17 | 11:26:45.140180 | `::handleSinkCountChanged oldCount=0 newCount=2 add=1 remove=0` | `VERIFIED_LOG` reported aggregate count change; distinct downstream identities unproved |
| 19 / 20 / 21 | 11:26:45.140218 / .140391 / .140417 | `Enumerating elements`; `Downstream port type is HDMI; initial downstream sink type is HDMI`; `copyEDID _virtualEDIDMode=0` | `VERIFIED_LOG` EDID-processing context, not two EDIDs or a physical branch map |
| 27 | 11:26:45.164947 | `DCPDPServiceProxy<0x10000deef>::handleMessage: ... Processed ForwardMessage<0>` | First retained DP-service proxy message; first message is not creation time |
| 39 / 40 | 11:26:45.165328 / .165332 | `maxWidth=1920 maxHeight=1080 maxDepth=8bpc`, pixel-rate limits; `tiled=NO` | Display capability/hint text, not a logged mode selection or mirror decision |
| 42 | 11:26:45.165934 | `_current.displayAllocation: extraPipes=0, mainUFP=0, peerUFP=0` | `VERIFIED_LOG` raw allocation diagnostic; zero fields are not a policy prohibition or source capacity |
| 65 / 82 | 11:26:45.189721 / .210350 | `CR DONE` / `EQ DONE`, `laneCount=2 linkRate=8100000000 bps` | `VERIFIED_LOG` reported training state/rate, consistent with M5P3 public two-lane/HBR3 state |
| 83 | 11:26:45.211357 | `runLinkTrainingStateMachine Link training ret=0x00000000` | `VERIFIED_LOG` reported training return |
| 89 / 92 / 95 | 11:26:45.263290 / .266560 / .268760 | `handleAddInterfaces videoInterface=0x9b`; `audioInterface=0x9e`; `addInterfaces ret=0x00000000` | Typed video/audio interface tokens, not two video-source contexts or host registry IDs |
| 96 / 109 | 11:26:45.604496 / .610007 | `prepareLinkGated type=Video source=Upstream`; `startLinkGated type=Video source=Upstream` | Link-role value matches M5P2's role concept, not an independent source ID |
| 113 / 114 | 11:26:45.612456 / .612566 | First retained `DCPAVVideoInterfaceProxy<0x10000def6>` / `DCPDPDeviceProxy<0x10000def1>` forwarding messages | Proxy activity after video start; creation/announcement order is not known |
| 130 / 139 / 144 | 11:26:45.627875 / .628839 / .661496 | Audio `startLinkGated source=Upstream`; `linkStable=YES`; `didStartLinkGated ret=0x00000000` | Reported link-start sequence; no independently identified stream or logical-display publication |
| 159 through 472 | 11:26:49.887395 through 11:27:48.291822 | Content-protection retries/failure `ret=0xe00002c1`, interleaved checks and proxy forwarding | Content-protection diagnostics, not an MST/source-limit decision; no remediation attempted |

The timestamps narrow the logged attach activity to roughly 11:26:43-45 UTC,
within the already chosen bracket. This is new log evidence, not a retroactively
invented user plug timestamp. No narrower second query was run afterward.

### Sequence Edges

| Edge | Confidence | What is, and is not, connected |
| --- | --- | --- |
| HPD/physical insertion -> route validation | `UNKNOWN` | No explicit insertion/HPD transition is returned by this predicate; `GetSupportsHPD` is a processed method name, not an HPD event |
| Route validation entry -> exit | `STRONG_LOG` | Same printed object token, route labels and thread; reported result 0, without typed registry-ID equivalence |
| Validation exit -> `connectTo` -> power-change messages | `STRONG_LOG` | Same repeated log object token and compatible route/power statements; hardware completion semantics not proved |
| Route/power phase -> `AppleDCPDP2HDMI` start | `INFERRED_LOG` | Compatible provider class from M5P3 plus route-token/class candidate and ordered logs; no explicit common request/activity ID |
| Service start -> aggregate sink count -> EDID processing | `STRONG_LOG` | Same named service class, same thread 406, ordered method diagnostics; individual sink/object identity still unknown |
| Sink/EDID handling -> DP device or EPIC service creation | `UNKNOWN` | Start/method activity is not a constructor, advertisement or publish timestamp |
| EDID/allocation -> training -> interface-add -> link-start results | `STRONG_LOG` | Same named service's method sequence and explicit reported values, not a proof of source cardinality |
| Video link-start -> video/device proxy forwarding | `INFERRED_LOG` | Matching M5P3 class/token candidates and ordered compatible messages; forwarding payload/recipient identity unclosed |
| Link-start results -> VG248 logical display publication | `UNKNOWN` | No `DISPLAY_CREATED`/`DISPLAY_ATTACHED` publication record; later M5P3 profiler presence is separate runtime evidence |
| Logical publication -> mirror/MST policy result | `UNKNOWN` | No explicit such decision in these scoped messages |

**HISTORICAL_LOG_EVIDENCE_SUFFICIENT** applies to this bounded lifecycle
investigation, not to every primary question or the project objective. There
is enough routing, service, sink/EDID, training and interface/link-start history
to assess the next evidence source. Repeating the physical attach merely to
seek the same public records is not justified. No live stream or reconnect is
performed; the live-cycle gate is not taken.

## Runtime Object Correlation

The [review artifact](../../artifacts/runtime/m5p4/review/observations.json)
records candidate correspondences based on explicit repeated log tokens and
class names, **not matching timestamps alone**. None of the 477 records
explicitly labels its object token `IORegistryEntryID` or `registry entry id`.
Thus the intake's exact typed-registry-ID correlation count remains zero.

| Printed log class/token | Records | Same-spelling M5P3 registry/class candidate | Qualification |
| --- | --- | --- | --- |
| `AppleDCPDPTXRemotePortProxy<0x100000810>` | 40 | Existing External/Unit 0 remote-port proxy under DCPEXT0 in both snapshots | `INFERRED_LOG` candidate; log-token namespace not independently verified |
| `DCPDPServiceProxy<0x10000deef>` | 34 | Newly exposed External/Unit 0 DP service in connected snapshot | `INFERRED_LOG` candidate; first message not creation time |
| `DCPAVVideoInterfaceProxy<0x10000def6>` | 31 | Newly exposed External/Unit 0 video-interface proxy | `INFERRED_LOG` candidate, not a source context |
| `DCPDPDeviceProxy<0x10000def1>` | 59 | Newly exposed External/Unit 0 DP device proxy | `INFERRED_LOG` candidate, not a separately counted physical sink |

These four groups account for all 164 messages with retained system sender
paths; 313 other messages print `AppleDCPDP2HDMI` but no comparable object
token. That name matches M5P3's explicit DP/AV service `EPICProviderClass`
advertisement. It is useful class-level corroboration, not proof of a unique
firmware allocation, sender image or a particular runtime object instance.
The `IOAV[...]` / `DCPAV[...]` counters are diagnostic sequence labels in the
text; they are not used as source, registry, sink or request identities.

Do not equate the route's **`dispext1`** with the registry ancestry
**`DCPEXT1`**. The same-spelling token candidate is under **DCPEXT0** in M5P3.
Likewise **`atc3`** is not automatically macOS **USB-C port 4** or a known DPTX
register owner. These namespaces differ and their mapping is not established
by incrementing an index or reusing a class name. The route labels constrain a
future correlation experiment, but do not close the physical-owner edge.

M5P3's dispext0 framebuffer record, EPIC units and VG248 display ID are not
explicitly printed in a qualifying typed-identity form in these logs. The
logs report the same two lanes and 8,100,000,000 bps rate class as the public
snapshot, and capability limits compatible with its 1920x1080 display. Those
are compatible technical attributes, not unique display/source IDs. No new
IORegistry query, static formatter analysis or private call is used to close
the missing identity contract.

## Downstream Entity Evidence

**SECOND_DOWNSTREAM_LOG_EVIDENCE_UNRESOLVED**. Record 17 is meaningful new
evidence, not merely a number in an unrelated diagnostic:

```text
[DCPDPService.cpp::2799] DCPAV[93446] AppleDCPDP2HDMI::handleSinkCountChanged oldCount=0 newCount=2 add=1 remove=0
```

The named service reports an aggregate sink-count change to **2**, whereas
the later public USB-C transport object in M5P3 reports **SinkCount 1**. Both
raw values are preserved. Their counting scope, intermediate representation
and relationship are **not** established. Do not silently reconcile them by
assuming one is a bitmask, includes a branch, counts physical panels, or is
the same counter as the public transport property. `add=1` is not assumed to
mean the arithmetic count difference or a separately identified added sink.

This does not yet identify another downstream GUID, second EDID, second
downstream port or separately bound connection path. The scoped history has
one `copyEDID` method record with `_virtualEDIDMode=0`, and initial/final
downstream type text `HDMI`; it contains no retained EDID bytes or unique sink
identity. Generic color/timing/audio element enumeration is not an MST branch
or per-port topology census. No explicit second-sink discard/ignore, clone,
payload/VC allocation or MST topology record was found in the 477 retained
messages. The correct result is unresolved rather than an unsupported claim
that two identified entities were logged, or that no material second-sink
signal exists. Neither the count 2 nor count 1 is a source-stream count.

## Source Identity Evidence

**PUBLIC_LOG_SOURCE_IDENTITIES_NOT_ESTABLISHED**. Six start/prepare records
print `source=Upstream` for Video or Audio, consistent with the IOAV link-role
concept recovered in M5P2. Audio versus Video is a link type, not two video
sources. No message states `source 0 -> DPTX0`, `source 1 -> DPTX0`, or an
equivalent pair of independently identifiable source contexts under one owner.

The route `die0::dispext1::core0`, video interface token `0x9b`, audio interface
token `0x9e`, `link[0]Stable=YES`, allocation values and repeated proxy tokens
are preserved in their printed namespaces. None is promoted to an independent
source identity. Processed `GetVirtualDeviceMode<1a>` conveys no returned
mode value, and `_virtualEDIDMode=0` refers to the logged EDID operation rather
than proving the presence/absence of `DCPDPVirtualDevice` instances.
M5P3's scoped `VIRTUAL_DEVICE_RUNTIME_NOT_OBSERVED` is not overwritten by these
method names. No same-DPTX source gate or M5P1 real-evidence pass is established.

## Mirror Policy

**PUBLIC_LOG_MIRROR_POLICY_UNRESOLVED**. There is no explicit mirror/clone
selection, sink-collapse/ignore decision or single-stream fallback in the
retained scoped messages. `tiled=NO` is display-hint state, not a mirror policy.
`extraPipes=0, mainUFP=0, peerUFP=0` is a reported allocation diagnostic, not
an enforced maximum, immutable hardware limit or a reason explaining the
duplicated panels. Capability pixel-rate/size limits do not identify the
number of source contexts or prove the selected desktop configuration.

The historical owner-confirmed duplicated panels and the M5P3 logical mirror
flag remain separate observations. These logs do not determine whether the
duplication is software cloning, multiple sources sharing content, or downstream
behavior. The existing mirror-source/runtime-model uncertainty remains.

## MST Policy

**PUBLIC_LOG_MST_POLICY_GATE_UNRESOLVED**. No retained message explicitly
rejects MST/multiple streams, enforces a maximum stream count, rejects a
non-tunneled topology, or forces a branch into SST/clone mode. The service name
`AppleDCPDP2HDMI`, non-tunneled M5P3 state and zero `extraPipes` diagnostic
do not constitute such a decision. No policy patch or host-control experiment
is justified from those names/values alone.

The explicit failure `handleProtectLink failed (ret=0xe00002c1). Retrying.`
is in content-protection handling. It is not identified as an MST prohibition,
source-allocation rejection, or explanation of mirroring. It remains an
observed scoped diagnostic; no unrelated protection/driver change is attempted.

## Runtime Discriminator

**PUBLIC_LOG_RUNTIME_PARTIAL**. The historical pass improves attach ordering,
provides a concrete route-label request, shows sink-count/EDID handling before
link training and interface startup, and exposes a count-2 diagnostic that
M5P3's point-in-time public SinkCount 1 did not contain. It also records an
allocation state and separates normal link-role words from source identities.

It does not establish exact object-constructor order, EPIC advertisement time,
typed identity equivalence across logging/registry namespaces, logical-display
publication, two downstream entity identities, mirror/MST policy or independent
source ownership under one physical DPTX. Those are explicit gaps, not grounds
to rerun static packetizer work or claim architectural impossibility.
The local hypothesis is partly supported at class/route/lifecycle level;
the strongest identity-binding version remains unproved.

## Recommended Next Route

**EXTERNAL_DP_PROTOCOL_CAPTURE_WARRANTED**. Historical lifecycle evidence is
sufficient to make this next-route decision without a new public-log cycle.
The cleanest new discriminator is now a separately designed **passive wire
correlation** on the one ordinary Mac-to-hub DP link: distinguish actual
downstream topology/EDID transactions and simultaneous main-link VC/timing
traffic from the service's aggregate `newCount=2` and the host's one logical
sink. The logged two-lane 8.1-Gbps training/start phase supplies concrete
correlation landmarks; it does not prove a particular instrument is ready.

This recommendation is capture **planning**, not execution, purchasing,
disconnecting, inserting instrumentation or changing display behavior now.
A future plan must qualify equipment, link integrity, privacy, correlation
method and recovery/safety boundaries, and obtain separate approval. It must
observe only the OS's existing traffic, never submit AUX/DPCD, inject timing,
enable MST or allocate payloads. A full main-link measurement would be needed
to distinguish simultaneous video streams; AUX/control messages alone cannot
prove two independently timed outputs. Failure to observe a second stream in
one ordinary mirrored run would still not establish architectural impossibility.

No host policy/control route is selected because no relevant policy decision
was found. No newly qualified safe private source-creation/observation API was
established. The remaining question is not solved merely by choosing a more
powerful platform observer, so m1n1 is not selected by default. External wire
evidence can test the concrete downstream/stream question independently of the
unproved internal token namespaces, though internal object ownership may remain
unresolved afterward.

No live logging session or reconnect cycle has occurred or is required for
this historical pass. The conditional live-cycle pause is **not triggered**.
If a future milestone separately authorizes such a cycle, it must still use
one narrow session and separate `USER_TRANSITION_TIMESTAMP` from
`LOG_EVENT_TIMESTAMP`; no authorization is implied here.

## Capture Provenance

The exact command, predicate, UTC bounds, reader commit/hash, query status,
limits, filtered raw messages, normalized records, correlation candidates and
artifact hashes are retained under
[artifacts/runtime/m5p4/historical](../../artifacts/runtime/m5p4/historical).
This is the one historical query, executed at clean reader commit
`5c86873d12e2e8cf41bcdc148bf42a8d42c97b71`. Its tool SHA-256 is
`bf722511a1cc193aeea975b9bb1c83a359f7f1503e723ca4a023bfd1a33f04f2`.
Capture generation is `m5p4-historical-01`. No historical file is overwritten.

The follow-up review is strictly offline, committed at
`5a9050dbdfe10415f1962e26a215e801dc513a35`. Its tool SHA-256 is
`550a3ab9982bc9db429ccaf3bc3b93c27d2c60286139f0f6e27a5c33cbea1a05`.
It checks all six historical artifact hashes, raw/normalized message binding,
the unchanged predicate and complete-query flag, and all 14 M5P3 capture input
hashes before extracting method fields. The eight M5P4 artifacts below are
ignored local evidence, not published raw logs or substituted M5P3 snapshots.

| Artifact | SHA-256 |
| --- | --- |
| [historical/raw-filtered.ndjson](../../artifacts/runtime/m5p4/historical/raw-filtered.ndjson) | `c25308db88bb6704b82c11f3a46585c1b0791145efc62f03031c9098f8150ad2` |
| [historical/normalized.json](../../artifacts/runtime/m5p4/historical/normalized.json) | `1aedb463892ef9b3b1bf515031d2eead40f23a34198d4555d6cbcfff7298d074` |
| [historical/analysis.json](../../artifacts/runtime/m5p4/historical/analysis.json) | `d98f20a72122b7710aca944bc472cbe27036520b673cc1ff072a83c927e33dbb` |
| [historical/correlations.json](../../artifacts/runtime/m5p4/historical/correlations.json) | `0a3533abfd298a82a8248083179d5d201e0ce754942482b7cc1032d446f5b7b9` |
| [historical/manifest.json](../../artifacts/runtime/m5p4/historical/manifest.json) | `07b6be75fd071fa3a70bc6d870eb9e30bdb1247de18723f33ab5938288362b4c` |
| [historical/hashes.json](../../artifacts/runtime/m5p4/historical/hashes.json) | `24554eefacb0c58c2db64cbe0d2f40ef0c024dfbd03d67b526279505e18588ee` |
| [review/observations.json](../../artifacts/runtime/m5p4/review/observations.json) | `d0549ad4f8ad075e356bc21cadc687f84dec416abbf975dbb3cef3b4f5c60aca` |
| [review/manifest.json](../../artifacts/runtime/m5p4/review/manifest.json) | `65bd2d9b7bec3acbb480423330c063065e0079f2229a0d03a84201be74846a65` |

Original query stdout SHA-256 is
`1840bc8c1bb578ee16be839955e0374db62791411efeb7aefaaf814589ec05a0`;
424,989 observed bytes were parsed transiently, then discarded. The retained
raw projection is 211,310 bytes. Record canonical-source hashes are not hashes
of the original serialized NDJSON line; the complete observed stdout hash is
the exact byte receipt. Projection hashes bind retained fields/message text.
No serial/home/document/network content was encountered requiring message
redaction in this capture, and no private content was reconstructed. Omitted
sender paths and the excluded parsed item cannot be recovered from a digest.

The authoritative M5P3 document remains byte-identical, SHA-256
`954e45deb728b57cba33afb5b75b57a6cfe01bc8cfb5c5db40a2df9ecf712715`.
Its two snapshots, differential, generation/code hashes, safety records and
historical claims are preserved. They supply the historical machine/OS context;
no new MacMST topology capture or running-image attestation was made in M5P4.

### Reproduction

The exact acquisition command is also in the manifest. This is a record of
the already-run query, not a request to rerun it or change the hub:

```sh
/usr/bin/log show --style ndjson --timezone UTC --no-pager --no-backtrace \
    --info --debug --signpost \
    --start '2026-09-16 11:11:59+0000' --end '2026-09-16 11:27:49+0000' \
    --predicate 'process == "kernel" AND (
        eventMessage CONTAINS[c] "DCPDPDeviceProxy" OR
        eventMessage CONTAINS[c] "DCPDPServiceProxy" OR
        eventMessage CONTAINS[c] "DCPAVVideoInterfaceProxy" OR
        eventMessage CONTAINS[c] "AppleDCPDPTXRemotePortProxy" OR
        eventMessage CONTAINS[c] "AppleDCPDP2HDMI"
    )'
```

Offline reproduction of the field review requires no log-store or hardware
access; it reads only the retained evidence and validates input hashes:

```sh
python3 tools/display_log_analyze.py review
python3 tools/display_log_analyze.py analyze artifacts/runtime/m5p4/historical/raw-filtered.ndjson
python3 -X dev -W error -m unittest discover -s tests -p test_display_log_analyze.py
python3 -m py_compile tools/display_log_analyze.py tests/test_display_log_analyze.py
cmake -S . -B build-m5p4-offline -G Ninja -DCMAKE_BUILD_TYPE=Debug \
    -DMACMST_ENABLE_HARDWARE_TESTS=OFF -DMACMST_ENABLE_DPDV_OPEN_EXPERIMENT=OFF
cmake --build build-m5p4-offline
ctest --test-dir build-m5p4-offline -L offline --output-on-failure
```

Reanalyzing the raw projection cannot recover original canonical-source hashes
or discarded sender metadata; the immutable normalized record preserves those
acquisition-time notes. The field review validates and preserves them rather
than laundering a filtered reread into a new complete raw capture.

### Verification

All **31 log tests** pass, including every requested timestamp/filter/redaction,
second-sink/policy/source ambiguity, missing-activity and reconnect-order case,
plus the observed count-2/allocation/role/token distinctions. Tests use synthetic
logs and mocked acquisition; they do not require the ignored real captures.
The strict 16-action build with hardware and DPDV experiment options OFF passes.
The existing observer (124), host receipt (12), snapshot/diff (33) and new log
(31) suites total **200 tests in four offline CTest entries**. No native
display/probe/test binary is run. Python compilation and editor diagnostics pass.

A mocked capture initially failed because macOS's temporary directory has a
symlink ancestor. The test fixture now resolves its temporary root; the real
no-symlink output guard was not weakened. The same focused tests then passed
before the historical query ran. There was no failed public-log query or
elevated fallback. The historical reader was committed before acquisition;
the later change added only hash-checked offline review, not another query.

## Hardware State

The hub remains connected in the owner's normal mirrored configuration.
M5P4 performed one unprivileged bounded historical `log show` and otherwise
offline analysis, tests/builds, documentation and authorized Git operations.
There was no new MacMST topology capture, physical change, log stream,
private display operation, m1n1 or firmware work. Preserve
`RETIRED_ON_DAILY_USE_M5`, `NOT_READY_FOR_DPCD_TEST`,
`STATIC_PACKETIZER_ANALYSIS_FROZEN`,
`NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED` and
`OFFLINE_OBSERVER_PIPELINE_READY`. Log visibility and compilation do not prove
independent external displays work on one physical DPTX.

The logged `connectTo`, training, interface operations, queries, closes and
content-protection retries are **historical OS behavior**, not commands issued
by MacMST during M5P4. Observing them is not a new private-call experiment.
The consumed M2F marker and both retained receipts remain unchanged; the
M2G DPCD-read attempt marker is absent. No source-schema/fixture change, real
source-ownership evidence pass, platform target-readiness or purchase promotion
occurs. `M5_OBSERVER_CODE_NOT_READY_FOR_TARGET_TEST` and
`SACRIFICIAL_M5_STILL_PREMATURE` remain.

M5P3 is published exactly at the audited HEAD. M5P4 remains on its separate
research branch with local commits, no merge/PR/tag changes and no M5P4 push.
Historical availability and lifecycle sufficiency do not authorize the proposed
external capture plan's hardware steps. Leave the hub connected; no reconnect
instructions or live-cycle pause are needed for this completed historical pass.