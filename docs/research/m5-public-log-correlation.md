# M5P4: Targeted Public Display Lifecycle Log Correlation

## Objective

Correlate narrowly scoped historical public kernel messages with the immutable
M5P3 attach differential. Seek explicit lifecycle ordering, typed identifiers,
downstream discovery and policy decisions, without converting monitor, sink,
endpoint, proxy, framebuffer or unit counts into source-stream counts.
The objective remains independent external displays from one base M5 through
ordinary USB-C/DisplayPort MST hubs without DisplayLink or special multi-DP
Thunderbolt hardware. This milestone is observation only.

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

`PENDING_HISTORICAL_QUERY`. No historical result or storage-expiry claim yet.
A successful empty scoped query would not distinguish non-emission, filtering,
suppression, redaction or expiry. Query/access failures must not be described
as expired storage. Historical retention labels will be qualified by the exact
command outcome and returned matching records.

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

## Lifecycle Sequence

`PENDING_HISTORICAL_QUERY`. Any eventual sequence edge must distinguish
`VERIFIED_LOG`, `STRONG_LOG`, `INFERRED_LOG` and `UNKNOWN`; event times alone
do not establish causality, a shared object or an unlogged transition.

## Runtime Object Correlation

`PENDING_HISTORICAL_QUERY`. Targets are the immutable DCPEXT0/Unit 0 external
device/service/video tuple, preexisting remote ports, dispext0 framebuffer,
USB-C port 4 transport and VG248 logical display. Only explicitly typed
registry IDs can match that ID namespace; pointers are not registry IDs.
Class/ancestry/unit combinations are correspondence candidates, not unique
identities. Never correlate through timestamp proximity alone.

## Downstream Entity Evidence

`PENDING_HISTORICAL_QUERY`. Search the scoped messages only for explicitly
identified second downstream entities, EDID/GUID/port/branch enumeration,
discard/ignore/duplicate decisions and payload/VC mentions. A numeric sink or
port label does not alone mean a second entity, and a second entity is not
an independent source stream.

## Source Identity Evidence

`PENDING_HISTORICAL_QUERY`. Explicit log source labels and DPTX assignments
are retained as statements requiring semantic review, not automatically
accepted source contexts or a same-owner positive gate. Unit 0 is not a source.

## Mirror Policy

`PENDING_HISTORICAL_QUERY`. Mirror/clone keywords or capability flags without
an actual decision do not establish policy. The user's duplicated-panel image
is not proof of a logged software mirror decision.

## MST Policy

`PENDING_HISTORICAL_QUERY`. Generic MST vocabulary is not a gate. A positive
requires an explicit rejection, enforced limit or disabling/fallback decision
that materially restricts MST/multiple streams in the relevant context.

## Runtime Discriminator

`PENDING_HISTORICAL_QUERY`. No result is selected before reviewing available
historical messages and their identity/ordering limitations.

## Recommended Next Route

`PENDING_HISTORICAL_QUERY`. First assess sufficiency without changing hardware.
If historical evidence is insufficient, stop at `READY_FOR_LOG_RECONNECT_CYCLE`.
Do not start a log stream or ask the user to unplug before that explicit pause.
Any later approved cycle uses the same narrow predicate, one logging session,
separately recorded user-transition and log-event timestamps, and one normal
unplug/replug. No cycle has occurred in M5P4.

## Capture Provenance

`PENDING_HISTORICAL_QUERY`. Retain the exact command, predicate, UTC bounds,
reader commit/hash, query status/limits, filtered raw messages, normalized
records, correlation candidates, file hashes and manifest under
`artifacts/runtime/m5p4/historical/`. No overwrite of that or M5P3 evidence.
Tests use synthetic logs and mocked acquisition; no CTest performs a public
query or hardware operation.

## Hardware State

The hub remains connected in the owner's normal mirrored configuration.
M5P4 has performed no new MacMST topology capture, physical change, log stream,
private display operation, m1n1 or firmware work. Preserve
`RETIRED_ON_DAILY_USE_M5`, `NOT_READY_FOR_DPCD_TEST`,
`STATIC_PACKETIZER_ANALYSIS_FROZEN`,
`NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED` and
`OFFLINE_OBSERVER_PIPELINE_READY`. Log visibility and compilation do not prove
independent external displays work on one physical DPTX.