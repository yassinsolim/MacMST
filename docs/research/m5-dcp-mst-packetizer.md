# M3C: M5 One-Link MST Packetizer

## Scope And Integration

M3B is frozen as the MST-control baseline:
**M5_DCP_FIRMWARE_MST_CONTROL_EVIDENCE_FOUND_PACKETIZER_UNRESOLVED**.
The manager, port abstraction, sideband codec, topology, path resources and
payload/ACT primitives are established. This investigation does not repeat
broad strings/constants, codec discovery, topology research or host transport
analysis. It asks whether at least two independently timed streams bind to
distinct payloads on one physical DPTX link.

The exact clean M3B branch/upstream was
`2a2f27a373b8e52495788a767f0e5de318ed0420`. Its three commits, eight text paths
and nine changed blobs were audited; all 27 remote branch/tag identities matched
local refs. M2F's consumed marker and both historical receipts were unchanged;
the DPCD-read marker was absent. Retained raw/decoded T8142 firmware and the
final M3B receipt matched their recorded hashes.

Authorized --no-ff merge **c89bf66bac79893f4e6910e10d4a1126775edce7**, message
`merge: record identified M5 DCP MST control implementation`, has parents
`24f2d1c3065ec0d7f80b5a53077f3e169f79368f` and exact M3B HEAD. Its tree equals
M3B. Main was pushed and verified. Annotated tag **m5-dcp-mst-control-v0.8**,
object **088a10213c756a3426b625b2e5424eb6771e373f**, peels to that merge. Message:
`Verified T8142 DCP firmware MST control, sideband and topology implementation; one-link multi-stream packetizer remains unresolved.`
The tag was pushed and verified before creating research/m5-dcp-mst-packetizer.
All older branches/tags remain unchanged. Observed static start:
2026-09-14T04:44:28Z, not the earlier date in the prompt.

Selector status remains **RETIRED_ON_DAILY_USE_M5**; global gate remains
**NOT_READY_FOR_DPCD_TEST**. No DPDV open, selector, private display API,
DPCD/AUX/MST transaction, display change, firmware execution/patch, security
change or physical disconnect is permitted or performed. Firmware is reused
offline; Git synchronization is not a firmware/network acquisition.

## Packetizer Proof Model

The required chain is one physical link L with independent stream contexts S1
and S2, each owning independently configurable timing/MSA, distinct payload
identity P1/P2 and independent slot/bandwidth state, both feeding L's scheduler.
FOUND requires all seven properties together:

1. One physical DPTX owner.
2. At least two independent logical stream contexts.
3. Independent timing state.
4. At least two distinct payload or equivalent VC identities.
5. Simultaneously active source-side payload/slot records.
6. Explicit stream-to-payload binding.
7. One hardware-facing main-link scheduler selecting those sources.

A scalar-looking record or literal ID 1 in one function does not prove a
global architectural limit. Conversely, a seven-bit table field, topology
collection or multiple outputs does not establish independent source streams.
Unknown roles remain UNKNOWN_FIELD_offset; all-path alias/receiver closure is
separate from a bounded local writer list.

## Initial Source-Record Findings

The retained updatePayloadTable region **0x4063c48**, 496 bytes, SHA-256
`bde6d620e89672402dbbb416a911a3c0c710b4247e1662d349ee627ab306a3e3`, is reached
through declared slot 0x478d378. Controller construction at **0x4080a10**
allocates 1,248 bytes and stores vtable address point **0x478cb28** at receiver
+0. Slot +16 reaches 0x40809d8, returning metadata 0x48fcea0; its declared
name pointer reaches **AppleDCPDPTXController** at 0x474febd. This corrects an
initial exploratory mistake of treating the metadata address itself as a string.

Controller slot +2120 at 0x478d370 reaches **0x4063e38**, the 1,716-byte record
producer, SHA-256
`14532771dc194d2155016aa0c86c0f82b4d325511d9a4e1df64fb8cef6875d56`.
Slot +2128 is updatePayloadTable. Exact outlined helpers establish that the
latter's x0 is the controller, x1/x2 are its two input records, and output x3
passed to +2120 is controller+1044. No live receiver address is claimed.

The producer stores a scalar 16-byte record. Its own referenced diagnostic is
`slot=%d, vcpf=0x%x, forcedSF=%d, minHblankSym=%d` at 0x47523d2, with OS_LOG
counterpart at 0x4d6f4f7. At output +0 it stores a 32-bit slot value; +4 receives
a 16-bit vcpf; +8 and +12 receive forcedSF and minHblankSym. Meaning/width of
the remaining two padding bytes is not inferred.

| Controller Offset | Width | Established Local Role | Writer | Reader |
| --- | --- | --- | --- | --- |
| +1043 | 1 byte | Mode guard equal to 1 for this update path; numerical mode decoding is not a stream count | 0x4070fb4; cleared at 0x4069040 | 0x4063c64 |
| +1044 | 4 bytes | slot, as named by producer diagnostic | 0x4064418 through output x3 | 0x4063cd0 |
| +1048 | 2 bytes | vcpf, as named by producer diagnostic | 0x4064420 through output x3 | 0x4063d60 |
| +1050 | 2 bytes | UNKNOWN_FIELD_1050 | Not established | Not established |
| +1052 | 4 bytes | forcedSF | 0x4064428 through output x3 | 0x4063cd4, 0x4063d78 |
| +1056 | 4 bytes | minHblankSym | 0x4064428 through output x3 | 0x4063d74 |

M3B's informal start+count wording is superseded for this source record:
the bound at 0x4063cdc is **slot + forcedSF <=64**, not a proved arbitrary
start/count allocation record. Branch ID/start/count descriptors are a separate
structure and must not inherit these field names.

The routine clears sixteen source slot words before populating seven-bit
fields with literal ID 1. The current local hypothesis is replacement of one
active source table per invocation, not additive allocation. It would be
disproved by an applicable caller or alternate table updater that preserves
other payload IDs while binding independent timing records to this same link.
The following checks trace the exact record getter, receiver-specific caller set
and activation/removal path. No architecture-wide single-payload conclusion is made.

## Source Payload Descriptor And Hardware Table

The controller's descriptor getter is **0x40738f0-0x4073954** (100 bytes),
vtable +1072 at 0x478cf58. The activation entry is
**0x4073890-0x40738f0** (96 bytes), vtable +1080 at 0x478cf60. Activation starts
before its internal PAC prologue at 0x40738bc; the adjacent getter is a non-PAC
leaf. M3B's inferred-region heuristic therefore splits or groups these entries
incorrectly. M3C captures explicit referenced-entry ranges and retains
the pointer evidence plus all conditional returns; these are not guessed
LC_FUNCTION_STARTS entries.

The getter rejects a null output and requires the input device x1 to equal
controller+312. It also requires controller+1131 ==1. It loads eight constant
bytes at **0x433dcc0**, raw `0100000000000000`, into output+0, then writes
slot+forcedSF at output+8. The descriptor is therefore three uint32 values:
**payload ID 1, start slot 0, count=slot+forcedSF**. At 0x4128fbc, the branch
assignment path calls source delegate slot +1072 and serializes the three values
as the separate branch ID/start/count operation. The manager's allocation wrapper
0x416525c reads the low byte of this descriptor as ID and forwards it to
0x4166524. The branch serializer accepts an ID argument; its flexibility alone
is not a local source multi-ID allocator.

Controller+312 is a scalar selected-device reference. Setter **0x4068ab0**
retains the replacement, handles/releases the previous selection and writes the
new pointer at 0x4068b28. It does not append another device to an active-stream
list in that body. This is a positive scalar-path fact, not closure of every
controller subclass or alternate entry.

The sole receiver-compatible local update call identified in the selected
controller implementation is **0x4061e0c**, in **0x4061c34**. It invokes slot
+2128 once with the same controller and timing inputs, then stores the
256-byte timing record at controller+716 (call 0x4061f58). No payload-record
iteration surrounds that invocation. Other numerical slot-2128 matches use
different receiver/signature contexts and are not promoted to callers.

### Hardware-Facing Binding

Controller initialization **0x407cd48** calls the provider cast at **0x404f088**
and stores its result at controller+264. The cast uses class metadata
0x48fcdf0, whose declared name pointer identifies **AppleDCPDPTXNub**. Nub
constructor **0x4019bb0** installs vtable address point **0x478b338**.
The relevant chain entries are:

| Operation | Nub Slot | Target | Established Behavior |
| --- | --- | --- | --- |
| Write register | +296 / 0x478b460 | 0x40f15a8 | Selects bank index x3, checks index <3, loads bank mapping from nub+280+8*index then mapping+8; stores uint32 to base+offset at 0x40f15e4 |
| Set bits | +312 / 0x478b470 | 0x40f1444 | Reads register, ORs mask, forwards to the same write slot |
| Replace masked field | +328 / 0x478b480 | 0x40f12cc | Reads register, clears supplied mask, inserts value shifted by supplied bit offset, writes back |

The wrappers used by updatePayloadTable force bank index **0**. Source table
storage begins at bank-0 offset **0x2428**: sixteen uint32 words hold four
byte-spaced, seven-bit payload fields per word, for **64 representable slot
fields**. A field can encode raw values 0..127, but this does not prove 127
hardware-supported streams or payload identities. The inspected update clears
all sixteen words and populates consecutive fields with ID 1. No existing
secondary ID is preserved by this body.

The selected-device activation entry reaches wrapper **0x4060004**, then nub
slot +312, and sets bit 0 at bank-0 offset **0x2400**. It does not accept a
payload ID or iterate records. M3B's branch-update then source-activation then
ACT_HANDLED sequence remains the protocol baseline; the concrete source-bit
write is now established. A double-buffered table, hardware ACT completion
contract or multiple timing sources behind the fields is not inferred from it.

These constructor/slot/register-store relationships establish source packetizer
machinery. They do not yet establish two independent timing streams selected by
distinct payload fields on the same physical link.

## Recovered Object Layouts

Offsets are bytes from the complete object, not from secondary interface
subobjects. A named field below is an analytical name unless tied to a quoted
diagnostic. Unexamined space is not zero, unused or absent by inference.

### Manager Layout

**DCPDPTXMSTManager**, 128-byte allocation in service setup 0x4161388,
constructor-installed address point **0x47a3150**; class getter 0x4166ca0
returns metadata 0x48fd470. Initializer **0x4166b58** is 160 bytes through
0x4166bf4. The input is cast to DCPDPService, then helper 0x4191230 obtains
a related object and 0x410947c casts that object to **DCPDPDevice**. Thus +80
is a device reference, not the DP service itself or a payload container.

| Offset | Width | Role | Writer / Reader | Scope And Confidence |
| --- | --- | --- | --- | --- |
| +0 | 8 | Signed vtable pointer | Service construction / declared chain slots | Concrete manager identity |
| +80 | 8 | DP device reference | 0x4166b80 after device cast / branch operations | Type established; complete retain/alias ownership not closed |
| +88 | 8 | Port collection | 0x4166bc0 / 0x4163e18 | Selection walks pointer elements at collection+16/+24, stride 8; not a source stream array |
| +96 | 8 | 256-byte allocation used by retained M3B message assembly | 0x4166b90 / frozen M3B control evidence | Buffer size is not payload cardinality |
| +104 | 8 | Root port pointer | 0x4166bb0 after constructor with null parent | Root ownership, not a source stream |
| +112 | 4 | Link-derived fixed-point PBN factor | 0x4164070 / 0x41652e4 and following arithmetic | Used to convert descriptor count to PBN |
| +116..+119 | 1 each | Control/request/sequence state from frozen M3B; individual roles not requalified here | Frozen control bodies | Not an active-source count |
| +120 | 1 | UNKNOWN_FIELD_120 | 0x4163dfc stores input w1 | No stream or payload interpretation |

The collection factory receives initial argument 1 at 0x4166bb8. That is not
an architectural maximum of one port. The selection method **0x4163e04**
examines port+216 and returns one qualifying retained port; it does not bind
every discovered port to a distinct timing engine.

### Port Layout

**DCPDPTXMSTPort**, constructor **0x4161f28**, 240-byte allocation,
address point **0x47a1a78**; getter 0x4161e84 returns metadata 0x48fd410.
The existing M3B constructor/field receipts are reused, not topology discovery.

| Offset | Width | Role | Writer / Reader | Scope And Confidence |
| --- | --- | --- | --- | --- |
| +0 | 8 | Primary signed vtable | Constructor / class getter chain | Concrete port identity |
| +80, +88 | 8 each | Secondary interface subobjects | Constructor / 0x4161e4c dispatches through +88 | Not two display streams |
| +184 | 8 | Manager pointer | 0x4161fdc / service 0x41608c4 | Associates routing object with manager |
| +192 | 8 | Parent port pointer | 0x4161fdc / parent-derived route construction | Route hierarchy, not timing hierarchy |
| +204 | 8 | RAD route storage | 0x4162070 / frozen allocation serialization | Route bytes, not a VC identity |
| +212 | 2 | Route counters/state | 0x4162074, 0x4162080 | Exact individual byte names not promoted |
| +216 | 8 | Composite port state | 0x4161fe0 / 0x4163e38 | Used for port selection; not a stream count |
| +224 | 4 | Downstream port number | 0x4161fe4 / allocation serializer | Distinct port numbers need not mean active payloads |
| +228 | 1 relevant bit in a 4-byte combined store | Path resource flag | 0x416677c, reply byte1 bit0 | +229 and other low-half bits are zeroed by this store; not a source slot count |
| +230, +232 | 2 each | Total / available PBN | 0x416677c combines total PBN with flags; 0x4166778 stores available PBN | Branch capacity, not independent timing contexts |

No recovered field in these scoped layouts binds a second independently timed
source to a second VC. This is a missing binding, not proof that all unexamined
fields or other objects lack such a binding. The provisional port vtable walk
stopped when +344 was not a declared chain member; it is not an additional method.

### Controller And Timing Ownership

Controller +264 is the nub reference; +312 is the selected device; +716 is a
256-byte cached video-attribute record; +1044 is the scalar 16-byte source
record. Outlined helper **0x4325b38** establishes x19=controller and
x22=input x1 in the update caller; x21 preserves timing input x2. Helper
0x43270a0 reloads/authenticates this same receiver's vtable. These observations
corroborate the single +2128 invocation and timing copy, not just slot-number
similarity.

The subsequent controller slot +2072 resolves to **0x4064950**, whose exact
diagnostic names **configureVideoFIFOThreshold** at 0x4752430. It must not be
called an MSA allocator. The caller's own diagnostics mention prepareLink video
attributes, horizontal active/front porch and adaptive-sync configuration;
they establish video/link timing relevance, not two independent MSA owners.
The two indexed 256-byte records in base service 0x415414c are not promoted to
two MST streams: their index semantics and simultaneous one-link use are unclosed.

Device initialization **0x412e2d0** stores a **DCPDPController**-typed delegate
at device+456 (0x412e318), obtained through exact 44-byte cast **0x4085bb0**.
The branch descriptor/activation calls use that interface's +1072/+1080 slots.
The concrete Apple controller supplies the matching methods, but this base-class
cast alone does not close every possible delegate implementation or alias.

## Removal And Negative Controls

Source table replacement at 0x4063c48 erases all sixteen slot words before
repopulating ID 1. It cannot preserve an unrelated nonzero payload in that
invocation. That local whole-table behavior is not an independent deallocation
API or proof that all firmware removal paths are all-or-nothing.

The examined +1131 writers are whole-port power/PSR paths: 0x4067f1c directly
references disabling, deviceRemoved and failed power-off diagnostics;
0x4074740 names **exitPSRGated**; 0x4074e30 names **enterPSRGated**. Thus +1131
is power-related eligibility state, not an active-payload counter. Whole-port
power-off and object teardown cannot establish removal of payload P1 while P2
continues with its own timing. Independent payload removal remains unresolved.

DISP_EXT0/DISP_EXT1 and separate nub/controller instances are separate-output
controls, not two streams on one link. Nub register bank indices 0..2 identify
register mappings, not three streams. Multiple ports/RADs, Thunderbolt DP
tunnels, compositor planes, DSC slices, PBN availability and the 64 slot fields
are not substitutes for explicit independent timing-to-payload binding. No M4
comparison was needed for these local decisions and no older-chip limit is
transferred to M5.

## Payload ID Writer Inventory

This is the qualified writer/derivation set for the recovered source descriptor,
table updater and its branch consumers, not a theorem about every indirect
store in the firmware. Exact-address reference checks and bounded controller
field-store checks were used; there was no new generic MST string/constant scan.
Generic register writers accept arbitrary values, and base-interface casts do
not exclude other implementations. Those are explicit closure limits.

| Function / Store | Input And Destination | Classification | What It Establishes |
| --- | --- | --- | --- |
| 0x40738f0 / 0x407392c | Constant 0x433dcc0 -> output uint32 ID=1 and start=0 | SOURCE_PACKETIZER | Selected-device descriptor is hard-coded to ID 1; count at 0x407393c is slot+forcedSF |
| 0x4063c48 / calls 0x4063cfc, 0x4063d50 | Clear sixteen words, then literal 1 -> seven-bit slot fields in bank 0 | SOURCE_PACKETIZER | One nonzero ID in this table-building path; no input ID or payload-list iteration |
| 0x4063c48 / call 0x4063d24 | Literal 1 -> bank-0 offset 0x2420, low seven bits | SOURCE_PACKETIZER | Selector-like field associated with table setup; exact silicon field name not recovered |
| 0x4128fbc / 0x4129040 | Delegate descriptor uint32 ID -> branch operation byte at sp+13 | BOTH | Connects source descriptor and branch table assignment; does not select multiple source contexts |
| 0x4128fbc / 0x41290dc | Copies descriptor ID/start to caller output after source activation/status sequence | BOTH | Preserves the same scalar descriptor; no new ID allocation |
| 0x41608c4 / calls 0x4160948, 0x4160984 | Device descriptor -> stack+20 -> selected port's manager | BOTH | Connects descriptor to routed branch allocation under index==0/type==1/mode==1 guards |
| 0x416525c / 0x41652dc | Descriptor byte 0 -> w2; count and manager+112 -> PBN w3 | BRANCH_PROTOCOL | Forwards an ID and computes branch bandwidth; not a source-ID allocator |
| 0x4166524 / 0x4166558 | Argument w2 -> ALLOCATE_PAYLOAD message byte 2 | BRANCH_PROTOCOL | Serializer accepts an ID argument; no observed second simultaneous source binding |
| 0x41291c8 / 0x41291e0 | Zero halfword -> branch ID/start; count byte=63 | BRANCH_PROTOCOL | Whole branch-table reset descriptor (0,0,63), not a per-source stream-count bound |
| 0x41657a4 -> manager+232 / 0x41667e4 | Root port -> CLEAR_PAYLOAD_ID_TABLE operation | BRANCH_PROTOCOL | Whole branch clear, not independent source payload removal |
| 0x40f15a8, 0x40f12cc, 0x40f1444 | Register value/mask arguments -> mapped bank | SOURCE_PACKETIZER when called by the qualified source path; otherwise UNKNOWN | Transport of register values, not policy allocating distinct stream identities |

The scalar source record producer 0x4063e38 writes slot/vcpf/forcedSF/minHblankSym,
not a payload-ID field. The low bit ORed into 0x2424 is not counted as another
payload ID. No dynamic ID is invented from a loop's slot index, route port
number, PBN factor or the three register banks.

## updatePayloadTable And Limits

The recovered behavior, omitting diagnostics and unrelated error handling, is:

```text
if controller.mode_1043 != 1: return without table programming
produce_record(input1, timing, controller + 1044)
write bank0[0x2410] = timing-derived value
write bank0[0x2414] = 0
count = uint32(slot + forcedSF)
require count <= 64 on this path
clear 16 words beginning at bank0[0x2428], stride 4
replace bank0[0x2420] low 7 bits with 1
for slot_index in [0, count):
	replace byte-spaced 7-bit field at 0x2428 + (slot_index & ~3) with 1
write bank0[0x2424] = (vcpf << 4) | 1
write bank0[0x2468] = minHblankSym | (forcedSF << 16)
```

The 0x2410/0x2414 writes precede the count check; this pseudocode is a
data-flow summary, not executable firmware. The bound
uses 32-bit addition, not a proved arbitrary-precision capacity calculation.
The sixteen words end at 0x2464; 0x2468 is separate scalar state. Nub initializer
0x404d364 supplies bank descriptors from nub+312's provider data at +24/+32/+40;
slot +248, **0x40f1960**, stores them at nub+280+8*index. Reader **0x40f16dc**
and writer **0x40f15a8** access the same descriptor+8 base. No live physical
base address, currently selected controller instance or hardware register read
was acquired. The static source-register interface is established; live route
and scheduler behavior are not.

The evidence therefore supports these limits only: one descriptor and one
nonzero ID per invocation of this updater, 64 represented slot fields, and a
seven-bit field encoding. It does not establish a hardware maximum of one
stream, 64 streams or 127 streams. No complete alternate-writer/receiver closure,
hard capacity assertion, firmware rejection of a second stream or register
specification was recovered.

## ACT And Completion

The frozen branch path resets/assigns its table, checks status mask 1, calls
the source activation method and checks mask 2. The newly bound source operation
sets bit 0 of bank-0 register 0x2400 through nub+312's read/OR/write method.
The same selected-device and power-state guards apply to getter and activation.
No list of payloads is passed to activation, and no second timing source is
selected by the observed routine.

M3B's exact status helper 0x41290f8 can return zero after exhausting its ten
iterations. Consequently a static return-zero path is not proof that ACT was
handled, that the hardware has a committed multi-payload set, or that completion
is bounded/correct on this host. This caveat is retained without reopening the
retired selector or raw-500 transport analysis. No ACT was triggered in M3C.

## Component Results

Each result is scoped to the evidence in this report. In particular,
SINGLE_PAYLOAD_STATE_FOUND and PAYLOAD_TABLE_SINGLE_ENTRY_ONLY describe the
recovered object/function, not a global M5 maximum.

| Question | Exact Result | Scope / Discriminator |
| --- | --- | --- |
| Payload IDs | PAYLOAD_ID_RANGE_UNRESOLVED | ID 1 is fixed in the qualified source path; serializer has an argument; complete alternate-source writer closure is missing |
| Payload container | SINGLE_PAYLOAD_STATE_FOUND | Scalar controller record plus separate 12-byte descriptor; port collection is not a source payload set |
| updatePayloadTable | PAYLOAD_TABLE_SINGLE_ENTRY_ONLY | One descriptor's ID is repeated over slots per invocation; no simultaneous second identity survives this updater |
| Streams per DPTX | STREAM_CONTEXT_CARDINALITY_UNRESOLVED | Selected device and cached timing observed; all contexts/owners feeding one physical transmitter not closed |
| Stream binding | STREAM_PAYLOAD_BINDING_UNRESOLVED | One descriptor-to-table association, no explicit pair of independent timing contexts and distinct IDs |
| Independent timing | TIMING_INDEPENDENCE_UNRESOLVED | One current 256-byte timing record; indexed service records do not prove independent simultaneous output timings |
| Main-link scheduler | MAIN_LINK_SCHEDULER_UNRESOLVED | Hardware-facing slot storage and trigger established; source selection for two timing contexts not recovered |
| Independent removal | PAYLOAD_REMOVAL_UNRESOLVED | Local whole-table replacement and branch clear observed; removal of P1 while P2 continues unproved |

## Evidence Map

| Requirement | Strongest Evidence | Status And Remaining Gap |
| --- | --- | --- |
| One DPTX physical owner | Controller+264 -> typed nub -> bank-0 descriptor+8 register base | STRONG_FIRMWARE_STATIC_EVIDENCE; numerical live aperture/instance not observed |
| Payload ID range | Constant ID 1 descriptor; source slots contain literal 1; branch ID argument | PAYLOAD_ID_RANGE_UNRESOLVED beyond the qualified path |
| Multi-payload container | Scalar 16-byte source record and 12-byte descriptor; manager holds ports | SINGLE_PAYLOAD_STATE_FOUND locally; no multi-payload source container established |
| Simultaneous payloads | Sixteen slot words cleared before ID 1 repopulation | No second active payload in this path; alternate writers not closed |
| Multiple stream contexts | Selected device+312 and cached timing+716 | STREAM_CONTEXT_CARDINALITY_UNRESOLVED |
| Independent timings | Timing-dependent producer and video-attribute copy; FIFO method named exactly | TIMING_INDEPENDENCE_UNRESOLVED; no second independent MSA/timing owner |
| Stream-to-payload binding | Selected-device getter -> branch descriptor and source table | STREAM_PAYLOAD_BINDING_UNRESOLVED for two independently timed sources |
| Slot scheduler | Concrete bank-0 masked fields and direct register stores | MAIN_LINK_SCHEDULER_UNRESOLVED; field storage alone does not select two source FIFOs |
| ACT set activation | Same source object's 0x2400 bit-0 trigger after branch table update | Static single-path trigger established; set-wide commit/completion semantics unresolved |
| Independent removal | Whole-table replacement, branch clear; power/PSR excluded | PAYLOAD_REMOVAL_UNRESOLVED; no preserved second stream demonstrated |

## Packetizer Result And Next Step

Primary result: **M5_DCP_MST_PACKETIZER_PRESENT_BUT_STREAM_BINDING_UNRESOLVED**.

Can one M5 DPTX physical link carry two or more independently timed display
streams using separate MST payloads? **Not established or ruled out by M3C.**
The source packetizer-table machinery is now concrete, including typed receiver,
scalar input record, slot-field stores and source activation. The seven-part
multi-stream proof still lacks independent contexts/timings, distinct
simultaneous payload records, their binding and one-link scheduler selection.
The positive evidence also does not meet the architectural-limit bar for
M5_DCP_MST_PACKETIZER_SINGLE_PAYLOAD_ONLY.

The only next research step is **one final packetizer-object ownership pass**:
close the owners and alternate implementations of the already identified
controller/nub bank-0 table, selected-device/timing records and source FIFO
selection. Its discriminating result is either two independently timed contexts
bound to distinct simultaneously programmed IDs on the same nub/link, or positive
architectural closure limiting that owner to one. If that narrow pass remains
opaque, preserve the unresolved result and stop; do not restart broad MST,
sideband/topology, host transport, selector or lifecycle research.

M3B remains the frozen MST-control baseline:
**M5_DCP_FIRMWARE_MST_CONTROL_EVIDENCE_FOUND_PACKETIZER_UNRESOLVED**;
DCP_MST_SIDEBAND_CODEC_FOUND and DCP_MST_TOPOLOGY_MODEL_FOUND are unchanged.
M3A host-side negatives retain their original scope. No implementation/driver,
firmware patch or hardware experiment is authorized by this result.
Selector status: **RETIRED_ON_DAILY_USE_M5**.
Global DPCD gate: **NOT_READY_FOR_DPCD_TEST**.

## Function Boundaries And Raw Evidence

All addresses below belong to the identified M5 dcp_legacy image, UUID
**18E26403-396D-3512-AF59-17E24808703A**, preferred base 0x04000000.
These are offline VM addresses, not live callable pointers. There is no trusted
LC_FUNCTION_STARTS table. Confidence describes the captured function boundary,
not complete caller coverage, runtime reachability or hardware functionality.

HIGH_BOUNDARY_CONFIDENCE requires two independent local corroborators: a
constructor-bound declared vtable entry or direct branch target, plus compatible
entry/return/tail control flow. MEDIUM_BOUNDARY_CONFIDENCE retains the entry
reference and PAC/return or directly referenced role diagnostic, but the larger
outlined/error paths have not been fully closed. LOW_BOUNDARY_CONFIDENCE applies
to isolated instruction windows without a qualified full body; no primary
packetizer conclusion depends on such a window. All 50 captured regions are
hashed in the final receipts, including supporting helpers not listed here.

| Decisive Body | Bytes | SHA-256 | Boundary Confidence And Corroborators |
| --- | --- | --- | --- |
| 0x4063c48 updatePayloadTable | 496 | bde6d620e89672402dbbb416a911a3c0c710b4247e1662d349ee627ab306a3e3 | MEDIUM_BOUNDARY_CONFIDENCE: controller slot +2128, PAC/return and exact source-record call; outlined diagnostic/error exits remain qualified separately |
| 0x4063e38 record producer | 1716 | 14532771dc194d2155016aa0c86c0f82b4d325511d9a4e1df64fb8cef6875d56 | MEDIUM_BOUNDARY_CONFIDENCE: controller slot +2120, PAC and exact output-field diagnostic/stores |
| 0x40738f0 descriptor getter | 100 | 80a80db1501c91be8eee0e1ff61be01b3af302cec860f14710cb407813810d93 | HIGH_BOUNDARY_CONFIDENCE: declared +1072 entry, fully local guard/return paths and adjacent activation extent |
| 0x4073890 source activation | 96 | 0500bda5a4b4f3bf395a936d87d546274056267c075aaf224767cbc7f5b16f85 | HIGH_BOUNDARY_CONFIDENCE: declared +1080 entry, guards/internal PAC/return before adjacent getter |
| 0x4061c34 video configuration | 1676 | 1803f3634cd5fe1c746d806e23fe291c12da5a70b2697a2c22956b08656f18da | MEDIUM_BOUNDARY_CONFIDENCE: declared 0x478d3c8 entry, PAC/return and video diagnostics; helpers independently identify receiver |
| 0x4064950 FIFO threshold | 784 | 054d0805d472605209eafa70edf1afcbd36d09a3ea247c89656051f7b68a62ab | MEDIUM_BOUNDARY_CONFIDENCE: controller +2072, PAC and exact configureVideoFIFOThreshold diagnostic; not an MSA allocator |
| 0x4080a10 controller constructor | 152 | 9a64a031abdd6cf8ebadf09ce3672bb15f33719aa16fd0566f0ba5e5f1e20a77 | MEDIUM_BOUNDARY_CONFIDENCE: PAC/return, allocation and concrete vtable installation; no live construction attestation |
| 0x4068ab0 selected-device setter | 164 | d971e67793dc4799cd0288dbf62637f97cfd509d026ccc7dcbf3eaea40431ee7 | MEDIUM_BOUNDARY_CONFIDENCE: PAC/return and retain/release/store sequence; fatal diagnostic tail not a removal theorem |
| 0x407cd48 provider initialization | 3860 | 736a0d349b4c9fc571fa5703daa918ed3503ac2b2b5c0dd79b5f689cbc04d38d | MEDIUM_BOUNDARY_CONFIDENCE: PAC/return, exact cast call/store and outlined receiver helper |
| 0x4019bb0 nub constructor | 68 | a58c2b262b24bc70ca23396e6e76ea036c80acdd37bd11e055b3801c317a8905 | HIGH_BOUNDARY_CONFIDENCE: PAC/return and concrete nub vtable installation with adjacent next entry |
| 0x40f1960 bank descriptor setter | 136 | 94a03e446b382e1f5b8a0af78c8f7f09c4143f66ed9cece0b0cb508ea8d20049 | HIGH_BOUNDARY_CONFIDENCE: nub +248, PAC/return and local diagnostic branch back to body |
| 0x40f16dc register reader | 124 | 59ac1aed06ecbc67524ced1b0d21aec3690d05bf1531520b350c147f64bc3b7b | HIGH_BOUNDARY_CONFIDENCE: nub +280, PAC/return and bounded local branches |
| 0x40f15a8 register writer | 128 | 453d001ed33748114752ce3aaa03aab2ebb6b9774635678e6bc95f9265dc8856 | HIGH_BOUNDARY_CONFIDENCE: nub +296, PAC/return and direct register store |
| 0x40f1444 set register bits | 176 | 1919496ca9f04967d399279d45c320e9bd3bc23f60048d5210a21daba040ee56 | HIGH_BOUNDARY_CONFIDENCE: nub +312, PAC entry and authenticated tail to write slot |
| 0x40f12cc masked field write | 200 | 95dfb3cf30bb633840b995ea502229dcf9d095f725169bda60f6bd5571ef9b96 | HIGH_BOUNDARY_CONFIDENCE: nub +328, PAC entry and authenticated tail to write slot |
| 0x4128fbc descriptor/ACT bridge | 316 | 829236e2c1c6e1bd545988a2ef3893b48bec11a96c863b19f5f0dbc42a9b75fd | HIGH_BOUNDARY_CONFIDENCE: both constructor-bound device +1128 slots, PAC and terminal return |
| 0x41291c8 branch reset | 120 | 5c846db38d59e9aa8893a0b3a53ac82f9f36991f5a9dfca2d10baac10a148275 | HIGH_BOUNDARY_CONFIDENCE: both device +1120 slots, PAC and terminal return |
| 0x416525c descriptor-to-PBN wrapper | 420 | 0d287eb3142a4275a00de61c3b80dd5a61309873cedf16e6d2ad9b08f6b24d00 | MEDIUM_BOUNDARY_CONFIDENCE: manager +320, PAC and gated tail/return paths; not complete allocator closure |
| 0x4166524 allocation serializer | 144 | 15b561408d80b7611cd715d43c51f05268de3c67f130b7658e2d94f467d34ba8 | HIGH_BOUNDARY_CONFIDENCE: manager +264, PAC and terminal tail/return; exact five-byte message stores |
| 0x4161220 service setup | 1968 | 5a8ee298a975972f36f81107fcffc1aa1d74ae187cf6849383e9a2757585199a | MEDIUM_BOUNDARY_CONFIDENCE: PAC/return and constructor/vtable stores around manager allocation callsite 0x4161388; that callsite is not a function entry |
| 0x4166b58 manager initializer | 160 | 38091bf72680b1cd771342ccc07e2157d420f3e86bc49b9f2157ce10d22be21b | HIGH_BOUNDARY_CONFIDENCE: manager +120, PAC/return with local failure branch |
| 0x4161f28 port constructor | 412 | 366c7b7356d5b286c857fb7bf68bd88b18c77b2eaa5cc161476f130700606560 | MEDIUM_BOUNDARY_CONFIDENCE: direct initializer call, PAC and concrete port vtable/field stores |

The early payload-getter receipt failed because its entry was not an inferred
start. Explicit 96/100-byte ranges fixed that selection without changing bytes.
The first final ownership replay similarly rejected the manager allocation
callsite 0x4161388; the successful replay uses enclosing region 0x4161220.
Both failed receipts remain retained, carry errors and are not negative evidence.

## Provenance And Reproduction

Target: Apple M5, Mac17,2/J704AP, CPID 0x8142, BDID 0x22, macOS 26.6.2 build
25G83. This is the same M3B production identity 156, not a new board assumption.
The retained Apple source is
[UniversalMac_26.6.2_25G83_Restore.ipsw](https://updates.cdn-apple.com/2026SummerFCS/fullrestores/140-75212/A2A24B94-1FC1-45A3-93F7-C51B02AF1F4D/UniversalMac_26.6.2_25G83_Restore.ipsw),
with exact [M3B manifest mapping](m5-dcp-firmware-mst.md#exact-buildidentity).
M3C downloaded no firmware or external source. Public libcompression decodes
retained data; no DCP code is executed or emulated. Running firmware bytes are
not independently attested by this production-image association.

| Retained Artifact | SHA-256 / Identity |
| --- | --- |
| BuildManifest.plist | e8ff2cdd3e8ab3a668132bf9453948b70f1863b849a6185914f54a9ec25356d3 |
| Selected identity, sorted binary plist | 94cc166baa7845901ff25b14b509dd6391745b2bf1bebd218b97fc14fb093e72 |
| t8142dcp.im4p, 4,223,041 bytes | 3f1424dbd80664128041bff2585e09bcf7fed9a75ac38e6c5a273f0b6494f219 |
| Decoded payload, 16,023,552 bytes | 9c4d1b86ecbc897109235fabf6dbf0d83330e1e0f2f76ccd135484e708fefb7c |
| DeviceTree.j704ap.im4p | 13f4dce18ca0936616c71eb9ccbb18ad791bcc01d06d287405d5cd0b4dc2c962 |
| Decoded DeviceTree, 569 nodes | 79cc631c24ced43e166c56d717083350ee4baff7b055c200c481c4d9bf4cfba5 |
| Frozen M3B decoded.json | 584080efc96e05072d1b0b0172834a0f561216d07833e6eb3219831be0f5d9a3 |
| Declared format-7 chain metadata, 8 chains / 27,054 entries | d703ed2c278fb2ffc05d1ecc05a08275ee28f046d80ed7c48aee46bd34ff8188 |
| Frozen Linux oracle, revision 704340f1cd0dcef829eb62f5b48ae95a2ce17bdf | ba7b651e9bf9d73043abc9176f6f74f464e702772dc7c7a99a63c8e43a3e3073 |
| M3C source-final/decoded.json, 29 regions / 14 pointer slots | 4f2487e9529ab2ececb9c522fc5ebb61bbdb147a9a95e64d725cd914bd703876 |
| M3C ownership-verified/decoded.json, 21 regions / 17 pointer slots | e12f3103e707b89960ee0868f002e948fd46f8dc0be65cd6d39fd23d820ca7c7 |

The selected Ap,DCP2 component's SHA-384 digest is
`250388ecfc4901d9fc8efa556bd88ffc58826053916dcc66252e031374bf4b4814d94747951f0eb3bc6b9038815c6012`.
It matches only after the explicit in-memory dcpf -> dcp2 type override at
offset 13; original bytes are unchanged. DeviceTree and DCP were decoded again
offline for this integrity check. No signature/TSS or live-byte claim is added.

Final [dcp_firmware.py](../../tools/dcp_firmware.py) SHA-256:
`9b170f3d76d1eedc13ecf67d6f4de1aaa6325c8b3d91753a25f9fe6a68bc89da`.
Final [static tests](../../tests/test_iodp_static.py) SHA-256:
`8d0acc311b293b351c977b36f40cc630a8ac63580f7f9686a71b8860890f98c9`.
Each receipt also binds the unchanged ipsw_dcp, scan_mst, kernel_image,
dyld_cache and inspect_iodp readers by full SHA-256. Earlier capture-time tool
hashes are historical and are not overwritten to match final source.

Raw receipts and decoded binaries stay ignored under artifacts/probes/m3c;
the original component/manifest tree remains under artifacts/sources/m3b.
The exact requested addresses, explicit sizes and pointer slots are embedded
in each receipt. Minimal decisive replay, with a new output directory:

```sh
python3 tools/dcp_firmware.py \
	--components artifacts/sources/m3b/25G83-components-20260914 \
	--output artifacts/probes/m3c/decisive-replay --details-only \
	--detail-address 0x4063c48 --detail-address 0x4063e38 \
	--detail-range 0x4073890:96 --detail-range 0x40738f0:100 \
	--detail-address 0x40f15a8 --detail-address 0x40f12cc \
	--detail-address 0x40f1444 --pointer-slot 0x478d378 \
	--pointer-slot 0x478cf58 --pointer-slot 0x478cf60 \
	--pointer-slot 0x478b460 --pointer-slot 0x478b480 --pointer-slot 0x478b470
```

Full reproduction replays the two receipts' requested selections into new
directories. Neither --scan nor the M3B broad scan is part of M3C. Exact-mode
tests reject conflicting/empty/malformed/duplicate selections, require a
referenced explicit entry and bounds, and prove DeviceTree/broad-scan exclusion.
This is a bounded extension of the existing reader, not a generic decompiler.

## Validation

| Check | Result |
| --- | --- |
| cmake --build build && ctest --test-dir build -L unit --output-on-failure | PASS, no rebuild needed; 9/9, 5.77 s |
| cmake --build build-sanitized && ctest --test-dir build-sanitized -L unit --output-on-failure | PASS, no rebuild needed; 9/9, 7.57 s |
| python3 -m unittest discover -s tests -p 'test_iodp_static.py' | PASS, 86 methods |
| Same static command with -k m3c | PASS, 3 methods |
| Final exact-address replay | PASS, 50 raw regions / 31 declared pointer bindings; 44 regions identical to prior retained receipts |
| Raw instructions, contiguous addresses, entry references and direct callers | PASS, recomputed from unchanged identified firmware |
| Six tool hashes, manifest identity, DCP SHA-384/decode, DeviceTree and oracle | PASS, offline only |
| Native probe/helper/parent and immutable experiment guards | PASS; no binary executed for these hash checks |

The unchanged native hashes are probe
`450832c50446d3a430cbed2bcab7c285cddf5f6b370b2339df2cd0a33aefd89a`,
unexecuted helper
`d94b0a450e89daa697675d816e231994e37456ec61928fc72261ec500f153830`,
and unexecuted parent
`f94db7e91ef670ce6c59ce73929016d2d36a5adb44fb9714f188932771b55e8b`.
No older M2F runtime attestation is transferred to these rebuilt binaries.

M2F-ATTEMPTED remains consumed, SHA-256
`2f3da1f224c0602dc46f812d3f6eb2c1560fe7a82c1a89f93eedb725b2726efc`.
Successful M2F result remains
`86ee9fdd87eb631e7552b0087471a149c183667c2162e838866ce993e1dd3d04`;
the stopped result remains
`79387346acdaebed1efb2284a531de8f2cf5aad1d64915a3f5f527040ebae840`.
M2G-DPCD-READ-ATTEMPTED is absent. No new marker was created or reset.

Compilation and synthetic/mock tests are software evidence only. No public
hardware capture was needed, and no real helper mode, including no-open mode,
was run. There were zero M3C private display operations, zero DPDV opens,
zero selectors, zero AUX/DPCD/I2C/MST transactions and zero firmware/security,
mode/link/payload or physical-cable changes. Hardware MST behavior remains
untested. Editor/model settings were not changed or attested.

## Git And Documentation Audit

The final pre-commit audit is limited to seven text paths: the report, root and
research indexes, open questions, append-only evidence ledger, existing firmware
reader and existing static tests. No production/native code, CMake, selector or
isolation implementation, frozen M3A/M3B report, oracle, editor configuration or
raw firmware/capture is changed. All local documentation links/anchors and code
fences pass; no editor diagnostics or whitespace errors were reported. Historical
E001-E193/S01-S61 rows are byte-preserved; M3C appends E194-E204/S62-S65.

Before publication, all **29** remote branch/tag/peeled identities matched local
refs, including main c89bf66bac79893f4e6910e10d4a1126775edce7 and the annotated
v0.8 object 088a10213c756a3426b625b2e5424eb6771e373f. Publication is limited to
research/m5-dcp-mst-packetizer, with an explicit non-force refspec and
push.followTags=false. No M3C merge, PR, tag replacement or historical-branch
rewrite is part of this task. Post-push HEAD/upstream and protected-ref results
are reported separately so this file does not claim its own future commit hash.