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

**DISCONNECTED_BASELINE_VALIDATED**. First invocation only; M5P3 as a whole
remains incomplete until the owner confirms connection and the second capture
is analyzed. No connected results or final next-route classification exist.

The successful capture ran from `2026-09-16T11:11:59.782377+00:00` to
`2026-09-16T11:12:00.725762+00:00`, on macOS 26.6.2 / 25G83, model Mac17,2,
reported CPU `Apple M5`. T8142/J704AP attribution is carried from the frozen
exact-machine baseline, not a new firmware or device-memory read.

All **42 public commands succeeded**. Normalization replays exactly from the
retained filtered inputs; artifact hashes match. The relevant IOService
hierarchy and boot metadata agree before and after the sequential queries.
There are no ambiguous provider/class records, unpaired relevant property
objects or conflicting retained property values in this capture.

The public display profiler exposes **one built-in Color LCD and zero external
display records**, with zero unknown display locations. No expected ASUS VG248
vendor/product match is present. Both the USB profiler and filtered registry
selection have **zero matching hub descriptor candidates**. Together with the
owner's unplugged-state declaration, this confirms the intended disconnected
baseline. It does not establish anything about support while connected.
The naturally reported internal mode is preserved as raw profiler text
`1512 x 982 @ 120.00Hz`, with pixel-resolution token
`spdisplays_3024x1964Retina`; no mode or refresh setting was changed.

### Object Counts

The graph contains **228 relevant objects**, **50 ancestor-context objects**
and **277 unambiguous IOService parent edges**. Exact actual classes are counted
separately. Query counts may overlap through superclass matching and must not
be added to actual-class counts.

| Actual runtime class | Disconnected count | Baseline interpretation |
| --- | --- | --- |
| `AppleDCPExpert` | 3 | Host services already present; not three same-link source owners |
| `RTBuddy` | 3 | DCP, DCPEXT0 and DCPEXT1 ancestry groups |
| `DCPDPControllerProxy` | 5 | Embedded Unit 0; external Units 0 and 1 in each DCPEXT group |
| `DCPDPDeviceProxy` | 1 | Embedded Unit 0; no external instance observed |
| `DCPDPServiceProxy` | 1 | Embedded Unit 0; no external instance observed |
| `DCPAVControllerProxy` | 5 | Embedded Unit 0; external Units 0 and 1 in each DCPEXT group |
| `DCPAVDeviceProxy` | 1 | Embedded Unit 0 |
| `DCPAVServiceProxy` | 1 | Embedded Unit 0 |
| `DCPAVVideoInterfaceProxy` | 1 | Embedded Unit 0 |
| `AppleDCPDPTXRemotePortProxy` | 4 | Two per DCPEXT ancestry group; Units 0 and 1 |
| `AppleDCPDPTXRemotePortUFP` | 4 | One child of each observed remote-port proxy |
| `AppleT8142DisplayCrossbar` | 1 | Already present; no connection-record count qualified |
| `AppleDPTXController` | 2 | Host controller objects below separate nub ancestry; physical source role unproved |
| `AppleDPTXNub` | 4 | Host nubs below `AppleAUXDPTX`; not the exact firmware class name |
| `IOMobileFramebufferShim` | 3 | Existing framebuffer objects, not three independent active displays |
| `AppleDCPLinkServiceSoC` | 3 | Existing link-service objects |
| `AFKEPInterfaceKextV2` | 29 | Actual class of retained `AFKEndpointInterface` query matches |
| `IODPPortService` | 10 | Existing port-service objects, not sink/source count |
| `IOPortTransportStateDisplayPort` | 1 | Inactive built-in HDMI path; not the unplugged USB-C hub path |
| `IOMobileFramebufferUserClient` | 8 | Preexisting public tree entries; the MacMST tool opened no user client |

The `IODPTXPort` class query has **16 unique matches**: six
`AppleATCDPINAdapterPort`, four `AppleDCPDPTXRemotePortUFP`, three
`AppleATCDPAltModePort`, two `AppleDPTXCrossbarAUXOnlyUFP` and one
`AppleATCDPHDMIPort`. This is explicitly a port superclass query, not sixteen
objects with the same actual class or a source-stream count.

`AppleDisplayCrossbar`, `AppleT8142DisplayCrossbar` and `IODPSwitch` queries
refer to the **same one** crossbar object, not three crossbars.
`IOMobileFramebuffer` and `IOMobileFramebufferShim` queries refer to the same
three shims. `IOFramebuffer` has zero matches. There are zero exact query
matches for `DCPDPDevice`, `DCPDPVirtualDevice`, `IODPVirtualDevice` and
`IODPSwitchAllocationState`. Those are query-scoped observations, not proof of
absence from firmware, non-registry memory or another abstraction. A concrete
CoreDisplay `DisplayPipe` runtime object or active crossbar connection count
is **not established by this public capture**. Full separate-class and query
counts are in the retained summary.

### EPIC Baseline

Group assignment below uses the captured IOService ancestry labels
`RTBuddy(DCP)`, `RTBuddy(DCPEXT0)` and `RTBuddy(DCPEXT1)`. They are **not**
independently qualified physical DPTX owner identities.

| Ancestry group | AFK query objects | Retained EPIC name/unit pairs | Units seen | Relevant service state |
| --- | --- | --- | --- | --- |
| DCP | 11 | 10 | 0 | DP/AV controller, device, service and video-interface entries present |
| DCPEXT0 | 9 | 8 | 0, 1 | DP/AV controllers, remote ports and HDCP interfaces already present; no external DP/AV device/service/video set observed |
| DCPEXT1 | 9 | 8 | 0, 1 | Same per-class baseline pattern; a distinct ancestry group, not a second source on the same transmitter |

Three AFK records have no retained EPIC name/unit pair. Their missing values
are not invented. Multiple EPIC units are already present with no hub attached;
they cannot be counted as attached monitors or independent streams.

### Baseline Object Graph

The complete machine-readable graph is `graph.objects` / `graph.edges` in
[snapshot.json](../../artifacts/runtime/m5p3/disconnected/snapshot.json).
The following are exact selected **provider -> child** edges, all
`VERIFIED_RUNTIME` as IOService relationships only. The group column expresses
ancestry, not a direct edge to the group label or a physical main-link path.
IDs are capture-local, with no `STABLE_SEMANTIC_ID` promotion.

| Ancestry / context | Provider | Child | Retained identity |
| --- | --- | --- | --- |
| DCP | AFK `0x100004702` | `DCPDPDeviceProxy` `0x100004706` | Provider `dcpdp-device-epic`, EPICUnit 0; child Embedded/Unit 0 |
| DCP | AFK `0x1000046ff` | `DCPDPServiceProxy` `0x100004704` | Provider `dcpdp-service-epic`, EPICUnit 0; child Embedded/Unit 0 |
| DCP | AFK `0x1000046fd` | `DCPAVServiceProxy` `0x100004701` | Provider `dcpav-service-epic`, EPICUnit 0; child Embedded/Unit 0 |
| DCP | AFK `0x100004707` | `DCPAVVideoInterfaceProxy` `0x100004709` | Provider `dcpav-video-interface-epic`, EPICUnit 0; child Embedded/Unit 0 |
| DCPEXT0 | AFK `0x100000706` | `AppleDCPDPTXRemotePortProxy` `0x100000810` | Provider `dcpdptx-port-epic`, EPICUnit 0; child External/Unit 0 |
| DCPEXT0 | Proxy `0x100000810` | Remote-port UFP `0x100000813` | One observed child relationship |
| DCPEXT0 | AFK `0x100000710` | Remote-port proxy `0x100000848` | EPICUnit 1; child External/Unit 1 |
| DCPEXT0 | Proxy `0x100000848` | Remote-port UFP `0x10000084b` | One observed child relationship |
| DCPEXT1 | AFK `0x10000071e` | Remote-port proxy `0x100000766` | EPICUnit 0; child External/Unit 0 |
| DCPEXT1 | Proxy `0x100000766` | Remote-port UFP `0x10000076b` | One observed child relationship |
| DCPEXT1 | AFK `0x100000721` | Remote-port proxy `0x100000762` | EPICUnit 1; child External/Unit 1 |
| DCPEXT1 | Proxy `0x100000762` | Remote-port UFP `0x100000768` | One observed child relationship |
| Crossbar | `AppleARMIODevice` `0x1000003a2` | `AppleT8142DisplayCrossbar` `0x1000004d9` | `IONameMatched=display-crossbar,t8142` |

**Preexisting versus permanent:** all above are present while disconnected
and survive this capture's short hierarchy bracket. That supports preexistence
before the planned attach, not permanence across a later attach, reboot or
other transition. No object can yet be labeled `CREATED_ON_CONNECT`, and no
differential `PERSISTENT` classification is made from a single snapshot.

### Visibility Limits

The one transport-state entry, `0x100000ab9`, is under
`AppleHDMIPortController`. It reports built-in HDMI port number 3, `Active=false`,
`HPD_State=0`, `LaneCount=0`, `LinkRate=0` / `No Link`, `SinkCount=0` and
`Tunneled=false`. These values describe **that inactive HDMI-associated path**,
not an observed link through the disconnected USB-C hub. Its `RoleDescription`
value `Source` describes the port role, not an independent source identity.

The crossbar exports a relevant property name `supportsDualPipe`; its value
was outside the frozen value allowlist and is **not retained or interpreted**.
Similarly, `SinkDeviceID` and `SinkIEEEOUI` names are present on the embedded DP
device, but their values are not retained. This is a retention limitation, not
a claim that the properties have no values. No additional query is issued to
chase them before the required pause. The three profiler Thunderbolt context
records retain no link-status values; they establish no tunneling conclusion.

Registry paths are reconstructed from the property-free hierarchy and may use
class placeholders for omitted ancestor names. Redacted/ambiguous paths are
not used to assert recreated-identity correspondence. Raw allowlisted property
values retain their JSON type or typed plist-data hex; source semantics stay
unestablished regardless of an object's class, name, count or unit.

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

Disconnected capture code is committed at
`060cf50a1612934e8932f0974a8bf3a06b131b3d`; worktree was clean at acquisition.
The tool SHA-256 is
`d5bd8218268a7a0497f4047e8c2b11dc45448904db27b1d83dfb8d68d03ac1b0`;
unchanged privacy-helper SHA-256 is
`e078ed19a6fac47da0e0212f74de5072afe52b8d36ebb4276fd6368c29f0cda1`.
Generation is `m5p3-disconnected-01`. The public boot-time token agrees at
both ends: Unix-epoch seconds `1789299423`, microseconds `258289`. It is a
comparison token for this boot, not a permanent machine identifier.

| Retained artifact | SHA-256 |
| --- | --- |
| [snapshot.json](../../artifacts/runtime/m5p3/disconnected/snapshot.json) | `df136eb6b9edb5b3109285ec5c526af85ce37c6ebae8a7daab6a4e31ecbeee47` |
| [registry-tree.json](../../artifacts/runtime/m5p3/disconnected/registry-tree.json) | `61a1453a7614163cd3ec2fb1b519b18373979df82f0c55035ad62be40f629871` |
| [registry-properties.json](../../artifacts/runtime/m5p3/disconnected/registry-properties.json) | `ae0bc4f60c2f0678b4343540187aea109cd4480ea9df4ddb6fa844c078a80573` |
| [system-profiler.json](../../artifacts/runtime/m5p3/disconnected/system-profiler.json) | `f8db5d1b5f86a2780d326137e49647bb9708c6f49721187c2a6f57f1412c0526` |
| [topology-summary.json](../../artifacts/runtime/m5p3/disconnected/topology-summary.json) | `4388b7924aaf45124faf6d1fcc6add13d3df8f5ca0d075ff1268172894f843bf` |
| [manifest.json](../../artifacts/runtime/m5p3/disconnected/manifest.json) | `b89206c1aac350a9fcb46ad5833aa232408211b088d0901aa2bb0bfac73fd65a` |
| [hashes.json](../../artifacts/runtime/m5p3/disconnected/hashes.json) | `ce684f98c3a7f223cd90e2b78d9dd64cf73d6b9a132f233807b3d0e75f885941` |

Capture command, executed only in the unplugged state:

```sh
python3 tools/runtime_display_snapshot.py capture --state disconnected \
	--generation m5p3-disconnected-01 --output artifacts/runtime/m5p3/disconnected
```

Offline validation does not repeat the public queries:

```sh
python3 tools/runtime_display_snapshot.py validate artifacts/runtime/m5p3/disconnected
ctest --test-dir build-m5p3-offline -L offline --output-on-failure
```

The new suite has 29 synthetic tests covering all requested diff/ambiguity
cases, raw-type/privacy preservation, root parsing, fixed-command gating,
mocked full capture, hash validation and inconsistent hierarchy rejection.
The 124 M5P1 tests and 12 M5P2 receipt tests remain intact. The strict
16-action build, offline CTest registration, seven existing privacy tests and
24 selected host-parser regressions pass. No native probe/test executable or
firmware test method is run.

Two initial attempts stopped at the first hierarchy parser because the current
public root class is `IORegistryEntry`, not the older assumed `IORegistryRoot`.
Each completed six public metadata/hierarchy queries and wrote no artifacts.
One additional property-free tree query inspected only root class/ID metadata.
The structural-root/privacy regression passed before the fix was committed and
the successful 42-query capture ran. These were local parser repairs, not
permission failures; no privileged/private fallback or connected capture occurred.

## Hardware State

`PENDING_USER_CONNECTION`. Hub unplugged according to the owner at invocation
start, corroborated by the validated disconnected display/hub absence above.
The baseline and object-graph analysis are complete. **READY_FOR_HUB_CONNECTION**
is a hard pause, not permission for automated continuation. Only the owner's
explicit `connected and mirrored` reply can start the connected phase, using
the identical committed capture code and normalization. No further runtime
queries, logs, static-host expansion or hardware experiments are performed in
this first invocation. Only local baseline/tooling commits are made; no push,
merge, PR or final connected conclusion is produced.

Preserve `RETIRED_ON_DAILY_USE_M5`, `NOT_READY_FOR_DPCD_TEST`,
`STATIC_PACKETIZER_ANALYSIS_FROZEN` and
`NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED`.
`OFFLINE_OBSERVER_PIPELINE_READY` remains, with zero real-evidence gate passes.
The new authorization covers public passive observation and ordinary hub
connection only; all other daily-use safety restrictions remain intact.