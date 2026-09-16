# M5P3: Passive Runtime Topology Differential

## Objective

Compare the public runtime display/topology objects with the ordinary USB-C hub
disconnected and, only after the owner's confirmation, connected in its normal
mirrored state. The project objective remains independent external displays
from one base M5 through ordinary DisplayPort MST hardware without DisplayLink
or special multi-DP Thunderbolt hardware. This milestone observes existing
macOS behavior; it does not enable MST or change display configuration.

**Completed M5P3:** `PASSIVE_RUNTIME_TOPOLOGY_PARTIAL`. The owner-confirmed
attach exposes one external device/service/video tuple under DCPEXT0, one
VG248 logical display record and a non-tunneled USB-C DP transport state.
Preexisting controller/port units remain, and source ownership stays opaque.
The selected next route is `TARGETED_PUBLIC_LOG_OBSERVATION_WARRANTED`, for a
separately scoped future read of existing logs only. No log query is run here.

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

**DISCONNECTED_BASELINE_VALIDATED**. This checkpoint was completed in the first
invocation, when connected results and the next-route decision were still
pending. Its evidence is preserved below; the subsequent confirmed connected
capture and conclusions are recorded in the following sections.

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

**CONNECTED_SNAPSHOT_VALIDATED**. The owner explicitly replied
`connected and mirrored` after the disconnected baseline and hard pause.
Only then did the identical frozen collector run its 42 public queries, from
`2026-09-16T11:27:47.121356+00:00` to `2026-09-16T11:27:48.163283+00:00`.
All commands succeeded, boot metadata and the relevant hierarchy matched at
both ends, and the filtered inputs reproduced the normalized snapshot.
The OS/build and model/SoC remain 26.6.2/25G83, Mac17,2 / Apple M5.

Generation `m5p3-connected-01` contains 250 relevant objects, 67 ancestor-context
objects and two public display records: the built-in Color LCD and an online
VG248 record with vendor/product `0x0469:0x24a5`, display ID `2`, and naturally
reported `1920 x 1080 @ 60.00Hz`. These are captured values, not injected modes
or globally stable identities. The user confirms both physical monitors show
the usual duplicated image; the capture does not independently see both panels.

The VG248 profiler record has no retained built-in/connection-type field.
Consequently, the frozen normalizer preserves `builtin=null`, reports one
unknown display location and zero *explicitly classified* external records.
That counter is **not evidence that no external display is present**. The new
VG248 record and newly exposed External DP/AV registry objects must be assessed
together. Its `spdisplays_mirror=spdisplays_off` is a macOS logical-display flag,
not a measurement disproving the owner's two-panel duplicated-image report.

The USB profiler retains zero hub candidates while the registry exposes four
matching USB hub-descriptor candidates. Those observation channels remain
separate; the profiler zero does not cancel the registry evidence. Original
raw USB profiler output was not retained, so no reason for that discrepancy
is inferred and no extra query is issued. Neither descriptor count identifies
DP branches or source streams. Both snapshots and capture-code hashes remain
unchanged; all following work is offline analysis of this pair.

## Runtime Object Diff

The [complete differential](../../artifacts/runtime/m5p3/analysis/differential.json)
is generated from the two hash-validated snapshots with the frozen
`diff_snapshots` function. Its [analysis manifest](../../artifacts/runtime/m5p3/analysis/manifest.json)
binds all 14 capture-file hashes, the capture-code hashes and policy, separates
retention scope, and records property-name changes. Both snapshots are in the
same boot. Every object still has a capture-local `RUNTIME_OBJECT_ID`; no
`STABLE_SEMANTIC_ID` was inferred or promoted across reconnect.

| Diff label | Relevant records | Ancestor-context records | Interpretation |
| --- | --- | --- | --- |
| `PERSISTENT` | 228 | 50 | Same recorded class/registry ID in both snapshots within this boot; not permanence |
| `CREATED_ON_CONNECT` | 22 | 17 | Newly represented in the filtered graph; context additions are not proof of new allocations |
| `REMOVED_ON_CONNECT` | 0 | 0 | No retained object disappeared in this pair |
| `PROPERTY_CHANGED` | 1 | 0 | Retained values only, excluding omitted values and name-only changes |
| `CHILD_ADDED` | 3 | 2 | Existing records gained retained child edges |
| `PROVIDER_CHANGED` | 0 | 0 | No captured existing-object provider change |
| `IDENTITY_RECREATED` | 0 | 0 | No unique class/path correspondence with a changed ID selected |

Labels can overlap: an object can be both persistent and changed. The raw
diff's 39 additions include **17 additional ancestor-context records**, which
may already have existed but were pruned from the disconnected filtered graph.
Only the 22 relevant additions enter the separate-class cardinality deltas.
Even those labels mean observed within this comparison interval, not continuous
tracing of allocation time or proof that every change was caused by the hub.

The existing `AppleDCPExpert` `0x10000043e`, with retained `role=DCPEXT0`,
changes raw `DCPPowerState` from **0 to 4**. The numeric values are not renamed
to undocumented power-state meanings. Existing endpoint records
`0x10000064c`, `0x10000064e` and `0x100000673` gain retained children.

The persistent `IOMobileFramebufferShim` `0x10000096c`, matched as
`dispext0,t8142`, additionally exposes seven **property names**:
`DPTimingModeId`, `DisplayAttributes`, `DisplayHeight`, `DisplayWidth`,
`PreferredTimingElements`, `TimingElements`, and `Transport`. These values
were outside the frozen value allowlist and were not retained. Thus the raw
diff's single value-change count does not mean other native properties stayed
unchanged. Likewise retained `DisplayHints={}` can result from filtering its
nested keys, not an empty native dictionary. No extra property read or altered
normalizer is used to fill these gaps.

## Physical Topology

The strongest supported graph has two observation planes: a DCPEXT0
service-advertisement hierarchy and a USB-C port-state hierarchy. Registry
ancestry is not silently converted into physical source ownership.

| Edge / relationship | Confidence | Evidence and limit |
| --- | --- | --- |
| Mac17,2 / Apple M5 -> retained IOService hierarchy | `VERIFIED_RUNTIME` | Public model/CPU metadata and tree; T8142 board attribution carried from the frozen baseline |
| `RTBuddy(DCPEXT0)` -> added display-facing AFK service records | `VERIFIED_RUNTIME` | Captured ancestry chain, not necessarily a direct parent edge; exact AFK -> proxy edges below |
| Added DCPEXT0 display-facing records -> newly online VG248 logical record | `STRONG_RUNTIME` | Same confirmed attach interval, one new external tuple and one new matching monitor record; no direct registry-ID/display-ID binding retained |
| One physical DPTX owner -> this DCPEXT0 tuple / selected remote port | `UNKNOWN` | No independently qualified physical-owner key, source membership or selected crossbar-connection record |
| Selected remote-port UFP -> USB-C port 4 | `UNKNOWN` | Four remote-port/UFP objects persist, but their selected peer/address binding is not retained |
| `AppleHPMInterfaceType10` `0x1000007f0` -> transport record `0x10000ddcc` | `VERIFIED_RUNTIME` | Exact IOService provider -> child edge |
| Transport record -> USB-C port 4 DP state | `VERIFIED_RUNTIME` | Exported `Port-USB-C@4/DisplayPort`, active/HPD/lane/rate/tunnel values; public state, not a wire capture |
| USB-C port-state change and four USB hub descriptors -> owner-connected ZMUIPNG assembly | `STRONG_RUNTIME` | Correlated confirmed attach and historical non-unique descriptors; the USB data and DP paths are not the same graph edges |
| Hub assembly -> one exposed VG248 logical sink record | `INFERRED_RUNTIME` | Owner topology plus the new logical display; no downstream port-address enumeration retained |
| One MST branch -> separately addressed sink A and sink B | `UNKNOWN` | No DP branch/port identities or second downstream sink record established; no branch node inserted |

Transport record `0x10000ddcc` reports these raw values:

| Property | Connected raw value | Scope |
| --- | --- | --- |
| `ParentPortNumber` / `ParentBuiltInPortNumber` | 4 / 4 | macOS port numbering, not a source index |
| `ParentPortType` / description | 2 / `USB-C` | Public port type |
| `Active` | true | Exported transport state |
| `HPD_State` / description | 2 / `High` | Not a directly sampled AUX/main-link signal |
| `LaneCount` / `MaxLaneCount` | 2 / 2 | Lane count, not source count |
| `LinkRate` / description | 4 / `8.1 Gbps (HBR3)` | Preserve raw enum 4 separately from the exported per-lane rate text |
| `TransportType` / description | 5 / `DisplayPort` | Public transport type |
| `Tunneled` | false | Non-tunneled state of this recorded USB-C path only |
| `SinkCount` | 1 | Public transport count, not enumeration of every physical panel or proof of one source |
| `Role` / description | 2 / `Source` | Port role, not an independently justified source identity |

The older `0x100000ab9` transport remains the inactive built-in HDMI path.
It must not be combined with the new USB-C entry to claim two connected links.

Four newly retained `IOUSBHostDevice` records have class descriptor
`bDeviceClass=9`: `0x10000ddcf` is VID:PID `05e3:0625`, `0x10000dde6` is
`05e3:0610`, `0x10000de0b` is `1a40:0801`, and `0x10000de93` is `05e3:0618`.
Their exact immediate providers are respectively `0x100000a62`,
`0x100000a60`, `0x10000ddf0`, and `0x10000de17`. These
`VERIFIED_RUNTIME` parent edges describe a USB hub hierarchy. They do not
enumerate four DP branches, identify a unique brand/model, or expose the two
ASUS panels as independent downstream DP sinks.

## Sink Cardinality

**ONE_LOGICAL_SINK_ONLY**, scoped to the newly exposed connected display path.
One new VG248 display record and the new USB-C `SinkCount=1` are visible;
there is one external DP device/service tuple. The built-in Color LCD is a
separate display and is excluded from the hub sink count. No second separately
identified downstream sink or per-branch port map appears in the retained data.

This classification describes public visibility, not the actual number of
powered physical panels. The owner explicitly confirms two panels showing
the usual duplicated image. The snapshot cannot locate that duplication or
disprove a hidden downstream sink. No inference of one hardware source or an
architectural one-stream maximum follows.

## Host Object Cardinality

Exact runtime classes remain separate. Global DP/AV counts become two because
the preexisting embedded object persists and **one** external object is added
per type, not because two new external display paths appear.

| Object type | Disconnected | Connected | Delta | Interpretation |
| --- | --- | --- | --- | --- |
| `DCPDPControllerProxy` | 5 | 5 | 0 | Same five IDs; preexisting controller units |
| `DCPDPDeviceProxy` | 1 | 2 | +1 | Embedded retained, one new External/Unit 0 |
| `DCPDPServiceProxy` | 1 | 2 | +1 | Embedded retained, one new External/Unit 0 |
| `DCPAVControllerProxy` | 5 | 5 | 0 | Same five IDs |
| `DCPAVDeviceProxy` | 1 | 2 | +1 | Embedded retained, one new External/Unit 0 |
| `DCPAVServiceProxy` | 1 | 2 | +1 | Embedded retained, one new External/Unit 0 |
| `DCPAVVideoInterfaceProxy` | 1 | 2 | +1 | Embedded retained, one new External/Unit 0 |
| `DCPAVAudioInterfaceProxy` | 0 | 1 | +1 | Adjacent audio object, not a second video source |
| `DCPAVAudioDriver` | 0 | 1 | +1 | Audio driver child, not a display-source object |
| `AppleDCPDPTXRemoteHDCPAuthSessionProxy` | 0 | 2 | +2 | Providers advertise HDCP1 and HDCP2, both EPICUnit 0; not two sinks/sources |
| `AFKEPInterfaceKextV2` | 29 | 37 | +8 | Added service advertisements, all in DCPEXT0 ancestry |
| `AppleDCPDPTXRemotePortProxy` | 4 | 4 | 0 | Same IDs and retained values; two units in each external ancestry group |
| `AppleDCPDPTXRemotePortUFP` | 4 | 4 | 0 | Same child IDs; selected route still unknown |
| `AppleDPTXController` | 2 | 2 | 0 | Host class count, not a physical-owner/source proof |
| `AppleDPTXNub` | 4 | 4 | 0 | Host nub count, not firmware object cardinality |
| `AppleDCPExpert` | 3 | 3 | 0 | DCPEXT0 object's retained power value changes 0 -> 4 |
| `AppleDCPLinkServiceSoC` | 3 | 3 | 0 | Same existing host link services |
| `AppleT8142DisplayCrossbar` | 1 | 1 | 0 | Same crossbar ID; allocation/connection count not retained |
| `IOMobileFramebufferShim` | 3 | 3 | 0 | Same shims; dispext0 gains seven retained property names |
| `IOPortTransportStateDisplayPort` | 1 | 2 | +1 | Inactive HDMI plus newly active USB-C port 4 |
| Target-descriptor `IOUSBHostDevice` | 0 | 4 | +4 | Filtered USB hub candidates, not all attached USB devices |
| Public profiler display records | 1 | 2 | +1 | Built-in plus one VG248 logical record |
| Expected VG248 vendor/product records | 0 | 1 | +1 | Not a unique physical serial identity |
| `IODPTXPort` superclass query matches | 16 | 16 | 0 | Overlaps actual subclasses above; do not sum as new objects |
| Exact `IOFramebuffer` query matches | 0 | 0 | 0 | Does not negate the three mobile framebuffer shims |
| Exact `IODPSwitchAllocationState` query matches | 0 | 0 | 0 | Non-registry internal allocation state not measured |
| Exact `DCPDPVirtualDevice` / `IODPVirtualDevice` queries | 0 / 0 | 0 / 0 | 0 / 0 | Kept separate query results, not firmware absence evidence |
| Independently qualified physical DPTX owners | Unknown | Unknown | Unknown | Neither RTBuddy groups nor host class names supply the ownership contract |
| Selected DPTX-port/crossbar connection records | Unknown | Unknown | Unknown | Port objects exist; selected peer/connection membership not retained |
| CoreDisplay `DisplayPipe` object instances | Unknown | Unknown | Unknown | Public display records and shim names are not these private object instances |

No registry entry ID is a stable reconnect identity. Persistence here means
the same ID/class in this same boot and these two captures only. No source
creation follows from any count in this table.

## EPICUnit Topology

**EPIC_UNIT_TOPOLOGY_UNRESOLVED**, for the requested unit-to-sink-to-physical-DPTX
relationship. There is positive, narrower evidence: **all eight newly retained
AFK service advertisements use Unit 0 under DCPEXT0**. That is not the same as
showing that the entire connected route has only one EPIC unit, because its
preexisting controller/remote-port Units 0 and 1 both persist without a retained
selected-port binding. No two downstream sink identities can be assigned to
distinct EPIC units, and no single physical DPTX owner is qualified here.

| Captured ancestry group | AFK objects before -> after | Named EPIC pairs before -> after | Unit set |
| --- | --- | --- | --- |
| DCP | 11 -> 11 | 10 -> 10 | 0, unchanged |
| DCPEXT0 | 9 -> 17 | 8 -> 16 | 0 and 1 both preexist; added records all 0 |
| DCPEXT1 | 9 -> 9 | 8 -> 8 | 0 and 1, unchanged |

New AFK -> proxy edges below are `VERIFIED_RUNTIME` immediate IOService edges.
`EPICProviderClass` is the retained advertisement string, not an independently
observed firmware allocation or a host runtime class identity. All entries have
retained `EPICLocation=External`, `EPICUnit=0` and `role=DCPEXT0`.

| AFK runtime ID | `EPICName` | `EPICProviderClass` string | Child runtime ID / actual class |
| --- | --- | --- | --- |
| `0x10000dee5` | `dcpav-device-epic` | `DCPDPDevice` | `0x10000dee7` / `DCPAVDeviceProxy` |
| `0x10000dee8` | `dcpav-service-epic` | `AppleDCPDP2HDMI` | `0x10000deea` / `DCPAVServiceProxy` |
| `0x10000deeb` | `dcpdp-service-epic` | `AppleDCPDP2HDMI` | `0x10000deef` / `DCPDPServiceProxy` |
| `0x10000deed` | `dcpdp-device-epic` | `DCPDPDevice` | `0x10000def1` / `DCPDPDeviceProxy` |
| `0x10000def2` | `dcpav-video-interface-epic` | `DCPAVSimpleVideoInterface` | `0x10000def6` / `DCPAVVideoInterfaceProxy` |
| `0x10000def4` | `dcpav-audio-interface-epic` | `DCPAVAudioInterface` | `0x10000def7` / `DCPAVAudioInterfaceProxy` |
| `0x10000df02` | `dcpdptx-hdcp-auth-session` | `AppleDCPDPTXHDCP1Controller` | `0x10000df06` / `AppleDCPDPTXRemoteHDCPAuthSessionProxy` |
| `0x10000df04` | `dcpdptx-hdcp-auth-session` | `AppleDCPDPTXHDCP2Controller` | `0x10000df07` / `AppleDCPDPTXRemoteHDCPAuthSessionProxy` |

The two HDCP advertisements have the same EPIC name and unit, and their proxy
paths have the same textual name; their distinct runtime IDs and advertised
provider classes must not be collapsed or reinterpreted as two video sources.
The DP/AV service advertisements share the parent service record
`0x1000006b5`, while their device advertisements share `0x10000069d`.
Those relationships help identify the host service tuple. They do not supply
a physical-owner ID or prove the meaning of `AppleDCPDP2HDMI` beyond the
observed string; its name alone is not an MST-branch or mirror-fallback proof.

## Virtual Device Runtime

**VIRTUAL_DEVICE_RUNTIME_NOT_OBSERVED**, scoped to the captured classes,
advertisements, retained property values and relevant property names. Exact
`DCPDPVirtualDevice` and `IODPVirtualDevice` class queries return zero in both
snapshots. No retained virtual-device/display/EDID-related runtime object or
advertisement is identified; therefore there is no qualifying parent, child,
unit, appearance-time or instance-count record to provide for that object.

The `DCPDPDevice` EPIC provider string is not `DCPDPVirtualDevice` and must not
substitute for it. Query absence and filtered-value absence do not prove that
a firmware-internal or non-registry virtual object does not exist. M5P2
`VIRTUAL_DEVICE_ROLE_UNRESOLVED` remains unchanged.

## Mirror Model

**MIRROR_RUNTIME_MODEL_UNRESOLVED**. The useful refinement is one newly exposed
external DP/AV device/service/video tuple and one new logical VG248 record,
not two external tuples. It is not sufficient to claim that **all** relevant
runtime transport objects collapse to one path: four remote-port/UFP objects,
multiple controller units and three framebuffer shims persist, and the
selected binding among them is not retained.

The embedded display and device tuple are excluded when considering the hub.
DP and AV views of a device, audio and HDCP objects, and preexisting port
infrastructure must not be added together to manufacture multiple mirrored
display/source paths. Conversely, the one visible logical sink does not prove
one physical source. Software cloning, multiple same-content sources and
downstream duplication are still undistinguished. The owner's duplicated-image
confirmation is compatible with the logical `spdisplays_mirror=spdisplays_off`
flag. M5P2 `MIRROR_SOURCE_MODEL_UNRESOLVED` therefore remains.

## Same-DPTX Source Evidence

**PASSIVE_SAME_DPTX_SOURCE_EVIDENCE_NOT_ESTABLISHED**. No observed identity is
independently justified as a source context, and no qualified physical-owner
key ties two such identities together. Multiple monitors, one sink counter,
multiple EPIC services/units, two HDCP versions, existing framebuffers and
display records do not satisfy the source-semantics requirement.

The differential narrows **host object lifecycle and routing context**, not
source/timing-generator cardinality. There is no source-payload binding, active
payload allocation, per-source timing ownership or independently measured VC
traffic in these public snapshots. No M5P1 real-evidence gate is promoted; raw
public runtime topology is not an observer IPC capture. The frozen physical
DPTX/source membership question remains open, not disproved.

## Runtime Discriminator

**PASSIVE_RUNTIME_TOPOLOGY_PARTIAL**. This is new, useful runtime evidence:
controller/port Units 0 and 1 preexist the hub, while an External Unit 0
device/service/video tuple, specific provider-class advertisements, active
non-tunneled USB-C state and one logical sink appear in the connected view.
The DCPEXT0 power-value change and dispext0 property-name additions corroborate
that local association. These facts exclude treating all preexisting units as
attach-created monitor/source instances.

The evidence does not yet materially distinguish the number of independently
timed sources under **one physical DPTX**, because the selected port/owner and
source semantics remain unknown. This warrants a partial result rather than
either claiming a source-ownership discriminator was found or discarding the
new topology as uninformative. Retention gaps are explicit; no claim is made
that every public property or possible passive method is insufficient.

## Recommended Next Route

**TARGETED_PUBLIC_LOG_OBSERVATION_WARRANTED**. The differential identifies a
concrete lifecycle question: how the new DCPEXT0/Unit 0 DP/AV device/service
advertisements and `AppleDCPDP2HDMI` service label relate to the **preexisting**
remote-port units when the owner connects the hub. Snapshot endpoints cannot
show that ordering or association. Existing kernel messages for those named
classes may supply it; their availability and completeness are unverified.

This route is chosen because of the identified object lifecycle, not because
it is convenient. No private method has acquired a safe observation/call
contract. A wire capture remains a possible later independent evidence source,
but this milestone has not linked the runtime service tuple to a selected
physical owner for such correlation. A broad platform observer is not selected
by default while this narrower public lifecycle question remains testable.

### Proposed Future Predicate

Proposal only, **not executed**. No logger configuration, debug enablement,
new stimulus or broad log collection is authorized by this proposal.

```text
process == "kernel" AND (
	eventMessage CONTAINS[c] "DCPDPDeviceProxy" OR
	eventMessage CONTAINS[c] "DCPDPServiceProxy" OR
	eventMessage CONTAINS[c] "DCPAVVideoInterfaceProxy" OR
	eventMessage CONTAINS[c] "AppleDCPDPTXRemotePortProxy" OR
	eventMessage CONTAINS[c] "AppleDCPDP2HDMI"
)
```

For a future milestone, first consider only the already-completed UTC interval
`2026-09-16T11:11:59Z` through `2026-09-16T11:27:49Z`, with a maximum of
1,000 matching records / 2 MiB retained filtered text. Apply strict privacy
filtering; do not retain unrelated device identities, user data or infer a
registry-ID/kernel-pointer equivalence from a numeric resemblance. Existing
messages would need an explicit identity-bearing link or lifecycle order to
improve the graph. Timestamp proximity alone does not bind source ownership.
Empty/redacted/expired output would mean the proposed log channel did not
qualify, not a hardware negative. Stop on privilege requirements; no sudo,
private tracing, debugger attachment or firmware analysis fallback.

## Capture Provenance

Both snapshots used the same committed capture/normalization code and policy.
Each stores
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

The final suite has 33 synthetic tests (29 at the disconnected checkpoint),
covering all requested diff/ambiguity
cases, raw-type/privacy preservation, root parsing, fixed-command gating,
mocked full capture, hash validation and inconsistent hierarchy rejection.
The four follow-up cases cover an online display without a location field,
HDCP1/HDCP2 advertisements sharing one EPIC unit, newly retained ancestor context,
and refusal to compare different normalization-code hashes. The frozen collector
and its privacy helper were not edited after the disconnected acquisition.
The 124 M5P1 tests and 12 M5P2 receipt tests remain intact. The strict 16-action
build from phase one remains current (`ninja: no work to do` in phase two),
and all three offline CTests pass after the connected analysis. Seven existing
privacy tests and 24 selected host-parser regressions also passed during M5P3:
200 distinct focused synthetic tests total. No native probe/test executable or
firmware test method was run. Python byte compilation passes.

Two initial attempts stopped at the first hierarchy parser because the current
public root class is `IORegistryEntry`, not the older assumed `IORegistryRoot`.
Each completed six public metadata/hierarchy queries and wrote no artifacts.
One additional property-free tree query inspected only root class/ID metadata.
The structural-root/privacy regression passed before the fix was committed and
the successful 42-query capture ran. These were local parser repairs, not
permission failures; no privileged/private fallback or connected capture occurred.

### Connected And Differential Receipts

The successful connected acquisition used clean commit
`127c670b109b07e6251da3b6653407b18cefb689`; its collector/helper bytes match
the disconnected source hashes above exactly. Generation is
`m5p3-connected-01`, and its UTC acquisition window is
`2026-09-16T11:27:47.121356+00:00` through
`2026-09-16T11:27:48.163283+00:00`. Both captures have the same public boot-time
token, model/SoC and OS/build. Each manifest records all 42 successful public
queries in the same order, including their original-output SHA-256 and byte
count. The 84 command slots in the final pair do not include the 13 earlier
metadata/tree diagnostic queries described above.

| Connected artifact | SHA-256 |
| --- | --- |
| [snapshot.json](../../artifacts/runtime/m5p3/connected/snapshot.json) | `47e12a90724e96efee5b2b4bf23c31d79db02a5b8d350d2a06fe97e14a7ae6a8` |
| [registry-tree.json](../../artifacts/runtime/m5p3/connected/registry-tree.json) | `b725b2c91af183c2d24b9255244669b1d9f675b734cf3615eb3a5559f2016cc9` |
| [registry-properties.json](../../artifacts/runtime/m5p3/connected/registry-properties.json) | `f8e3e0f0bd447b08e0ca3dc10953e90eb655e0cd15922dadb2a63259ce2fc1f6` |
| [system-profiler.json](../../artifacts/runtime/m5p3/connected/system-profiler.json) | `da37426b9e75de6465853b1715f40e3404c2298dafa03f700ba8f4950ea4de94` |
| [topology-summary.json](../../artifacts/runtime/m5p3/connected/topology-summary.json) | `e9ab1da3f08c90e3d1069940baa1c769c5a830982e55851d5c591ba5c46c5933` |
| [manifest.json](../../artifacts/runtime/m5p3/connected/manifest.json) | `592b5a621682a7909fcab67b35382f703542ce5bed8bb989e2aed574d6d9b03d` |
| [hashes.json](../../artifacts/runtime/m5p3/connected/hashes.json) | `5f0f9f16bb7fe1f1107dc0d53a42bca8168a33d05c7a653afba1b054145cb9c2` |
| [analysis/differential.json](../../artifacts/runtime/m5p3/analysis/differential.json) | `0babe6c788657c1cd19da436b3148852f8b5e781847c848e5f7499c10f1ba331` |
| [analysis/manifest.json](../../artifacts/runtime/m5p3/analysis/manifest.json) | `e467caf3cca3ee0f652065c048d82dd6a94c330f0b7d4ffd7aedb9b5bc79cfd1` |

The analysis manifest binds all 14 immutable capture files and the exact
differential hash. Its supplemental property-name changes are set differences
of `relevant_property_names` for common registry IDs. Event counts are grouped
by the recorded `scope`, keeping ancestor-context additions separate from
relevant objects. Neither supplement recovers omitted values or asserts source
identities. Both snapshots reproduce exactly from their retained filtered
inputs; the differential reproduces deterministically from that pair.

Historical connected acquisition command, run only after the user's explicit
confirmation; it is not authorization to recapture or overwrite the evidence:

```sh
python3 tools/runtime_display_snapshot.py capture --state connected \
	--generation m5p3-connected-01 --output artifacts/runtime/m5p3/connected \
	--confirmation 'connected and mirrored'
```

Offline reproduction requires no display/device access:

```sh
python3 tools/runtime_display_snapshot.py validate artifacts/runtime/m5p3/connected
python3 tools/runtime_display_snapshot.py diff \
	artifacts/runtime/m5p3/disconnected artifacts/runtime/m5p3/connected
python3 -X dev -W error -m unittest discover -s tests -p test_runtime_display_snapshot.py
cmake --build build-m5p3-offline
ctest --test-dir build-m5p3-offline -L offline --output-on-failure
```

Acquisition-time pending labels in the immutable snapshots describe their
state when captured, before offline interpretation. They are not rewritten to
manufacture a completed result; this report supplies the qualified conclusions.
These are public runtime topology records, not DCP IPC payload traces. M5P1
schema v1 and all 31 golden fixtures remain unchanged, with zero real-evidence
source-ownership gate passes. Original unfiltered stdout was not retained;
hash integrity does not recover discarded fields or prove complete topology.

## Hardware State

The first invocation ended after the validated disconnected baseline with
`READY_FOR_HUB_CONNECTION`. That pause was respected. The owner then replied
`connected and mirrored`, authorizing the identical connected public-query
capture. The hub and both monitors remain in that owner-confirmed normal
configuration; no further physical stimulus or configuration change is requested.

Only the ordinary owner-directed hub connection and normal macOS attach
behavior occurred as the physical stimulus. MacMST issued no private
user-client/DPDV/framebuffer method, DCP command, AUX/DPCD transaction, EDID or
timing injection, payload allocation, debugger operation, sleep/wake/lid
experiment, security/boot change or m1n1 operation. No sudo was used. Existing
user-client objects in the registry were observed as metadata, not opened.
The operating system's normal attach processing is not a MacMST command test.
No unified log collection or new static host/firmware call-graph analysis was
performed. The future log predicate above remains a proposal only.

Preserve `RETIRED_ON_DAILY_USE_M5`, `NOT_READY_FOR_DPCD_TEST`,
`STATIC_PACKETIZER_ANALYSIS_FROZEN` and
`NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED`.
`OFFLINE_OBSERVER_PIPELINE_READY` remains, with zero real-evidence gate passes.
The new authorization covers public passive observation and ordinary hub
connection only; all other daily-use safety restrictions remain intact.

`M5_OBSERVER_CODE_NOT_READY_FOR_TARGET_TEST` and
`SACRIFICIAL_M5_STILL_PREMATURE` are not promoted. Public observation success
does not establish native independent MST operation or revive any retired
selector. The consumed M2F marker and both retained receipts are preserved;
the M2G DPCD-read attempt marker remains absent.

Work stays on `research/m5-passive-runtime-topology`, based directly on the
published M5P2 HEAD, with local commits only. No merge, PR, tag change or push
is performed. Both runtime captures remain ignored local artifacts; historical
M5P1/M5P2 evidence and tool bytes are preserved. The completed conclusion is
partial **topology evidence**, not a partial or fabricated connected capture.