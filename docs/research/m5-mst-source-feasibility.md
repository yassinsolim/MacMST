# M3A: Apple M5 MST Source Feasibility

## Scope And Retirement

The question is whether the current M5 display stack contains source-side
DisplayPort MST machinery, not whether the attached hub advertises MST.
Selector 0 is **RETIRED_ON_DAILY_USE_M5**. Its investigation is not reopened,
wrapped, improved or executed. **NOT_READY_FOR_DPCD_TEST** remains in force.
The consumed M2F marker stays intact and the DPCD read-attempt marker stays absent.

This milestone permits static analysis and public read-only observation only.
No DPDV open, IOConnect method, IODP API, IOI2C/AUX/DPCD/sideband transaction,
mode change, link training, payload allocation or display reconfiguration is run.
No firmware or security setting is changed. Multiple controllers, displays or
Thunderbolt tunnels alone do not establish MST on one physical DisplayPort link.

## Integration And Retirement Tag

The starting research/w06-wake-or-strand branch was clean at
`b18ffd118f405ee7f91ce630a140086818ff4649`, equal to upstream. Both M2I commits,
six changed UTF-8 blobs and five documentation paths were audited. Main was
`1a014d8d3c3cd35ed5381160b809cf4803d79d69`. Historical refs, the consumed M2F
marker and both M2F result receipts matched; the read marker was absent.

M2I was merged --no-ff as `a882c1dc75501c03347050f1cdb91c38df2af39d`, message
`merge: retire unresolved selector-0 DPCD transport`. Parents are
`1a014d8d3c3cd35ed5381160b809cf4803d79d69` and
`b18ffd118f405ee7f91ce630a140086818ff4649`; the merge tree equals M2I. Main was
pushed, followed by annotated tag `selector0-retired-v0.6`, object
`55b7f703fe11b396e6b159d76fcc84cc31ec6b6d`, peeling to the merge. Its message is
`MacMST selector-0 transport retired on daily-use M5 after unresolved W06 wake and callback-quiescence proof.`
Both remote identities were verified before creating
research/m5-mst-source-feasibility from that tagged merge. Historical branches
and tags remain unchanged.

The host identity check at 2026-09-14T01:49:57Z reported macOS 26.6.2 (25G83),
kernel UUID `447D769E-1CB7-3086-A0B4-32226837B587`, unchanged from the M5 baseline.
The observed UTC time, rather than the earlier prompt date, timestamps this work.

## Evidence Rubric: Defined Before Apple Search

Strong evidence requires a DisplayPort-attributed implementation or control
surface, with an exact owning image, function and data-flow context. Candidates:

- Explicit MST terms that resolve to DP-specific behavior, not an unrelated acronym.
- Code using MST-specific register/window clusters as DP addresses, not offsets.
- Sideband header/CRC/opcode processing connected to MST message transport.
- Branch GUID plus route-address/port topology tied to a DP source link.
- PBN, VCPI/payload IDs, slot tables and payload-update/ACT state transitions.
- Multiple independent timing/stream encoders mapped to payload IDs on one link.

Literal hits and constant hits are discovery leads, not conclusions. A name can
establish a named control concept without proving its body, firmware execution or
M5 packetizer. A negative bounded search is not a silicon-absence theorem.

Weak evidence includes generic stream/payload/bandwidth terminology, DSC slices,
framebuffer/display-pipe allocation, multiple DP ports/controllers and independent
Thunderbolt DP tunnels. These are explicit negative controls. ACT must be a DP
payload activation sequence, not a substring of action/active; PBN/RAD must be
protocol fields, not arbitrary symbols or small integers.

Confidence labels are VERIFIED_ON_CURRENT_M5_STACK (observed current component
identity or public fact), STRONG_STATIC_EVIDENCE, WEAK_STATIC_EVIDENCE,
NEGATIVE_SEARCH_RESULT and UNKNOWN. Static presence in a current image is not
proof its MST code is used by the selected M5 endpoint. Implementation evidence
requires both MST protocol/control machinery and one-link stream-to-payload
packetization. Host controls alone leave the packetizer unresolved; opaque or
incomplete firmware can prevent a meaningful complete-stack classification.

## Pinned Linux Protocol Oracle

Current torvalds/linux HEAD was pinned before Apple scanning as
`704340f1cd0dcef829eb62f5b48ae95a2ce17bdf`. Retained files under ignored
artifacts/sources/m3a/linux are drm_dp.h, drm_dp_mst_helper.h,
drm_dp_mst_topology.c, drm_dp_helper.c and i915/display/intel_dp_mst.c.
They are source evidence only, not compiled or executed. Existing v6.12
`adc218676eef25575469234709c2d87185ca223a` remains the historical comparison.

Initial exact constants from current
[drm_dp.h](https://github.com/torvalds/linux/blob/704340f1cd0dcef829eb62f5b48ae95a2ce17bdf/include/drm/display/drm_dp.h):

| Concept | Register / Value | Discriminator |
| --- | --- | --- |
| MST capability | DP_MSTM_CAP=0x021, DP_MST_CAP=bit 0 | Receiver capability, not source packetizer evidence by itself |
| Branch GUID | DP_GUID=0x030 | Needs GUID-sized/routing/topology context |
| MST control | DP_MSTM_CTRL=0x111; MST_EN=bit 0, UP_REQ_EN=bit 1, UPSTREAM_IS_SRC=bit 2 | Source enabling/sideband role, stronger when connected to topology |
| Payload allocation | DP_PAYLOAD_ALLOCATE_SET=0x1c0, START_TIME_SLOT=0x1c1, TIME_SLOT_COUNT=0x1c2 | Adjacent ID/start/count operations, not one isolated integer |
| Payload/ACT status | DP_PAYLOAD_TABLE_UPDATE_STATUS=0x2c0; TABLE_UPDATED=bit 0, ACT_HANDLED=bit 1 | Requires update/activation/poll ordering |
| Sideband windows | DOWN_REQ=0x1000, UP_REP=0x1200, DOWN_REP=0x1400, UP_REQ=0x1600 | Cluster plus DP access/header/CRC behavior |
| Topology requests | LINK_ADDRESS=0x01, CONNECTION_STATUS_NOTIFY=0x02, ENUM_PATH_RESOURCES=0x10 | Small opcodes need packet-format context |
| Payload requests | ALLOCATE_PAYLOAD=0x11, QUERY_PAYLOAD=0x12, RESOURCE_STATUS_NOTIFY=0x13, CLEAR_PAYLOAD_ID_TABLE=0x14 | Cluster and PBN/payload association |
| Remote operations | REMOTE_DPCD_READ/WRITE=0x20/0x21, REMOTE_I2C_READ/WRITE=0x22/0x23 | Sideband routing required; generic local DPCD is not remote MST access |
| Negative controls | DP_DSC_SUPPORT=0x060; DP_SINK_COUNT=0x200 | DSC or sink count alone does not establish MST |

The local falsifiable hypothesis is that a scoped function-level scan can
distinguish MST-specific control/codec/payload evidence from generic display and
IPC terms using these combinations and their source-backed state transitions.
The cheap discriminating checks are a positive signature fixture and unrelated
small-integer/string controls, followed by inspection of candidate argument flow.
An unqualified single constant or broad string hit must fail that evidence test.