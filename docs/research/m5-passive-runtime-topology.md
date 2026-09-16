# M5P3: Passive Runtime Topology Differential

## Objective

Compare the public runtime display/topology objects with the ordinary USB-C hub
disconnected and, only after the owner's confirmation, connected in its normal
mirrored state. The project objective remains independent external displays
from one base M5 through ordinary DisplayPort MST hardware without DisplayLink
or special multi-DP Thunderbolt hardware. This milestone observes existing
macOS behavior; it does not enable MST or change display configuration.

The starting branch is published `research/m5-host-stream-control` at
`5aed45b9458be08ba05b24804d9439644ccb7c2c`, directly following tool commit
`e7d4430cf510823eaf602557138b5cb53cb0bc2f` and M5P1
`ec45795561620533450ac82399fd00e42cb857fd`. The clean/upstream-equal baseline,
44 local/remote head/tag/peeled identities, 31 synthetic fixture hashes and
immutable safety markers were reconciled before creating
`research/m5-passive-runtime-topology`. No merge is performed.

The local hypothesis is that some DCP and routing objects preexist hub attach.
A public class/property hierarchy captured before and after the owner-directed
connection can distinguish retained, newly exposed and recreated objects.
Objects absent while disconnected would disconfirm their assumed preexistence;
one disconnected observation cannot establish that an object is permanent.

## Safety Boundary

Only fixed unprivileged `ioreg`, `system_profiler`, `sw_vers` and selected
`sysctl` metadata queries are permitted, plus offline MacMST parsing/tests and
Git provenance. The collector does not load inspected display frameworks, open
device/user-client handles, invoke private methods or submit DCP/AUX/DPCD work.
No native MacMST probe, DPDV helper, debugger, m1n1 or firmware tool is run.
No sudo, display-mode/EDID/timing injection, payload allocation, boot/security
change, resolution/refresh change, sleep/wake or lid-state stimulus is allowed.
There is no unified-log collection in this phase.

The [snapshot tool](../../tools/runtime_display_snapshot.py) has a fixed
42-query plan: public environment/boot metadata, a property-free IOService
hierarchy before and after, 33 named class queries at depth one, and one
display/USB/Thunderbolt profiler invocation. Original command output is hashed
but not persisted. Retained registry values use an allowlist; serials, EDID,
UUIDs, user/computer names and unrelated USB devices are omitted. Only the
four non-unique hub descriptor pairs from the historical
[hub differential](external-dock-diff.md) select USB candidates. They are not
proof of a unique physical hub, DP branch or source identity.

Every registry object has a capture-local `RUNTIME_OBJECT_ID`, class,
reconstructed IOService path, provider candidates, retained children and
relevant properties. `STABLE_SEMANTIC_ID` is not established. Same-path/class
matches with new registry IDs are only inferred correspondence candidates.
Ambiguous parents remain unresolved. Class, endpoint, framebuffer, display
and sink counts are never converted into independent source counts.

## Disconnected Baseline

`PENDING_DISCONNECTED_CAPTURE`. The owner states that the hub is unplugged.
The capture must confirm that the expected external monitor records and hub
descriptor candidates are not observed, retain a baseline object graph, and
validate all hashes and before/after hierarchy/boot consistency before the
owner is asked to connect anything.

## Connected Snapshot

`PENDING_USER_CONNECTION`. Requires the owner's explicit reply:
`connected and mirrored`. No automatic continuation is allowed.

## Runtime Object Diff

`PENDING_USER_CONNECTION`. Offline code supports `PERSISTENT`,
`CREATED_ON_CONNECT`, `REMOVED_ON_CONNECT`, `PROPERTY_CHANGED`, `CHILD_ADDED`,
`PROVIDER_CHANGED` and inferred `IDENTITY_RECREATED` correspondence. Connect
labels describe the comparison interval, not proof that every change is caused
by the hub. Same registry IDs are matched only within the same public boot
session. Differing normalization code/policies are rejected.

## Physical Topology

`PENDING_USER_CONNECTION`. Baseline IOService parent edges are registry
relationships, not automatically physical DP paths. No branch or two-sink
physical topology is inserted based on the requested target diagram.

## Sink Cardinality

`PENDING_USER_CONNECTION`. Public display records, physical sinks and source
streams are separate concepts. No connected sink classification is selected.

## Host Object Cardinality

`PENDING_USER_CONNECTION`. Compare exact runtime classes separately; do not
combine unrelated object types to produce a count of two.

## EPICUnit Topology

`PENDING_USER_CONNECTION`. Preserve raw `EPICName`, `EPICUnit`, `Location` and
`Unit` with provider/child relationships and generation. A service unit is not
an independent source or an established physical-owner identifier.

## Virtual Device Runtime

`PENDING_USER_CONNECTION`. Missing IOService matches do not prove that a
non-registry object or a firmware-internal object does not exist. Preserve
M5P2 `VIRTUAL_DEVICE_ROLE_UNRESOLVED` until new evidence qualifies its role.

## Mirror Model

`PENDING_USER_CONNECTION`. The software/hardware source model remains
`MIRROR_SOURCE_MODEL_UNRESOLVED`; the disconnected baseline cannot classify
the connected mirrored path.

## Same-DPTX Source Evidence

`PENDING_USER_CONNECTION`. A positive conclusion requires two independently
justified source identities simultaneously associated with one physical DPTX.
The parser/diff never infers that from two endpoints, units, ports, monitors,
framebuffers or display records. No connected verdict is fabricated.

## Runtime Discriminator

`PENDING_USER_CONNECTION`. Choose a discriminator result only after both
captures exist and the structural differential has been qualified.

## Recommended Next Route

`PENDING_USER_CONNECTION`. No next-route classification or log predicate is
chosen in advance. A future narrowly targeted log predicate is considered
only if the connected differential identifies a specific relevant lifecycle.

## Capture Provenance

`PENDING_USER_CONNECTION` for the connected provenance. Both snapshots must
use the same committed capture/normalization code and policy. Each stores
OS/build, machine model/SoC, commit/tool/helper hashes, generation, timestamps,
owner-declared connection state, filtered inputs, normalized graph, summary,
command stdout hashes, manifest and artifact hashes. The before/after public
hierarchy and boot checks bracket sequential queries; this is not an atomic
snapshot or proof of unchanged properties between commands.

Capture directories are local ignored artifacts under
`artifacts/runtime/m5p3/`. No raw binary, serial-bearing profiler dump or
unfiltered registry dump is published. Commands requiring privileges or failing
under the public-only policy have no private/elevated fallback.

## Hardware State

`PENDING_USER_CONNECTION`. Hub unplugged according to the owner at invocation
start. Leave it unplugged until the disconnected capture and baseline analysis
are validated. The first invocation ends with `READY_FOR_HUB_CONNECTION` and
the owner's seven physical steps; it does not run the connected phase.

Preserve `RETIRED_ON_DAILY_USE_M5`, `NOT_READY_FOR_DPCD_TEST`,
`STATIC_PACKETIZER_ANALYSIS_FROZEN` and
`NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED`.
`OFFLINE_OBSERVER_PIPELINE_READY` remains, with zero real-evidence gate passes.
The new authorization covers public passive observation and ordinary hub
connection only; all other daily-use safety restrictions remain intact.