# M3D: Final DPTX Stream Ownership And Cardinality Proof

## Scope And Integration

This is the final planned static packetizer investigation. It asks how many
independently timed source contexts can belong to one physical T8142 DPTX,
and how those contexts own the already established source payload state.
M3C's packetizer facts are frozen, not rediscovered:
**M5_DCP_MST_PACKETIZER_PRESENT_BUT_STREAM_BINDING_UNRESOLVED**.
One selected-device field, one scalar record or ID 1 in one implementation
is not an architecture-wide cardinality proof.

The exact clean M3C branch/upstream was
60eec80b622b3788e83b0df78ab4eab2c65c8804. Both linear commits
c78a09bfd249a11d5e4bc1d475639ebd6ec71bf2 and 60eec80 were audited: seven text
paths, no unexpected binary/credential content, all 30 historical remote
head/tag/peeled identities and local equivalents unchanged. Retained T8142
firmware, M3C receipts, consumed M2F marker and both historical M2F receipts
matched recorded hashes; the DPCD-read marker was absent.

Authorized --no-ff merge **5beb1ac304a1715dc9fb7cad9b3322819b8fd140**, message
`merge: record M5 source packetizer investigation`, has parents
c89bf66bac79893f4e6910e10d4a1126775edce7 and exact M3C HEAD. The merge tree
equals M3C; main was pushed. Annotated **m5-dcp-packetizer-v0.9**, object
**4b8cf98419fa4678d931ad014ba16c306c2f722d**, peels to that merge. Its message is
`Verified T8142 DCP source-side MST packetizer programming; independent stream ownership remains unresolved.`
Main and tag were remotely verified before creating
**research/m5-dcp-stream-ownership** from the tag.

All investigation uses the retained exact T8142 payload offline. No firmware
download, generic firmware scan, sideband/topology rediscovery, DPCD transport,
private display operation, firmware execution/patch, security/display/cable
change or M4 comparison is part of this work. Git publication is the only
network use. Selector status remains **RETIRED_ON_DAILY_USE_M5**; global gate
remains **NOT_READY_FOR_DPCD_TEST**. Requested model/editor settings cannot be
changed or attested here and have not been modified.

## Ownership Proof And Initial Anchor

The required graph is physical DPTX L -> controller C -> selected device D,
with timing T and payload P owned along that same path. Every edge must be
qualified as ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE, OPTIONAL or UNKNOWN.
Multi-stream proof requires two concurrent source-side contexts on the same
physical owner, independent timing, distinct identities and simultaneous
packetizer references. A single-stream result requires positive architectural
closure, not a bounded absence of another path.

The first exact targets are controller constructor **0x4080a10** and
selected-device setter **0x4068ab0**. The former allocates 1,248 bytes and
installs the AppleDCPDPTXController vtable at 0x478cb28; the latter replaces
controller+312 at **0x4068b28**, after handling/releasing the old reference.
M3D's initial exact direct-reference check finds four setter callsites:
0x406836c and 0x40688c8 in region 0x4068308, and 0x4076474 and 0x4076724 in
region 0x4075c88. No direct B/BL or declared-chain reference to 0x4080a10
appears in that check. This does not establish dead code or singleton creation:
an address-materialized registration or an unclosed constructor path can evade it.

Local hypothesis: provider attachment serializes one controller's selected
device by replacement, while controller multiplicity per physical nub is
controlled by the construction/registration owner. Cheap discriminating checks
are exact constructor address references, the four setter caller contexts and
their parent/storage fields. An indexed source-controller collection on the
same nub, or a second retaining attachment path, would disconfirm a one-owner
interpretation. No cardinality is promoted before that check.

If this final pass cannot prove either architecture, the result will remain
unresolved with exactly one opacity boundary, and static packetizer expansion
will stop. No M3E firmware-graph search will be proposed.

## Controller Construction And Selected-Device Sources

The direct-call negative for 0x4080a10 is not a dead-code result. Exact address
materialization at **0x432fe60** installs the signed allocating-factory pointer
at runtime record **0x48fcb60+8**. The record's first pointer is matcher
**0x40809e8**; its remaining sixteen bytes are initialized to zero. Raw retained
data at that record is zero before initialization, so declared chained pointers
alone cannot enumerate this runtime registration. The registration window lies
inside inferred region 0x432be18; only the exact stores, not all of that large
region's runtime control flow, are qualified here.

The matcher casts its input to the DPTX nub and tests nub+328 ==1. The factory
allocates/zeros 1,248 bytes, constructs base state, installs the concrete
controller vtable, then passes provider x0 and new controller x1 to **0x4194fc8**.
That attachment helper invokes the new object's slots +96, +104 and +120 with
the provider as appropriate, returning the attached object or null. Registration
is class availability, not a proof of how many objects are instantiated per nub.

| Setter Caller | Region | Supplied Value | Qualified Local Meaning |
| --- | --- | --- | --- |
| 0x406836c | 0x4068308 | null through 0x4328b78 | Clear selection during the device-removal path when its input flag is nonzero |
| 0x40688c8 | 0x4068308 | null through 0x4328b78 | Clear selection later in the same removal path |
| 0x4076474 | 0x4075c88 | x21 through 0x4327374 | Newly constructed device candidate; nearby diagnostic says Adding device |
| 0x4076724 | 0x4075c88 | null through 0x4328b78 | Clear on the construction/activation path's cleanup branch |

The setter's helper 0x4326370 establishes x20=controller. Its only qualified
noninitialization store at 0x4068b28 replaces +312 after retain/previous-device
handling/release. These four direct callers are not an all-alias or all-indirect
writer proof. Candidate-device classes, repeated activation semantics and
controller multiplicity on the same physical provider remain separate checks.

### Per-Provider Cardinality Result

**CONTROLLER_CARDINALITY_UNRESOLVED**. The allocating factory has one recovered
runtime registration, not a demonstrated one-instance-per-nub invariant.
The factory iterator **0x4194590** visits the exact range
0x48fc0c0..0x48fcc60 in 32-byte steps (93 registration records). Those are
factory descriptions, not 93 controllers or streams. Exact direct callers are
0x418ad5c and 0x41942d4. The second belongs to dispatch region 0x4194150:
callback **0x4194428** filters factory category and predicate, builds a candidate
vector of 16-byte record/score pairs, and dispatch **0x4194308** calls a
candidate's factory with the provider. After a successful candidate, it leaves
that candidate loop, but continues the outer category iteration. The first
iterator caller is registry setup, not an independently identified second
controller allocation.

Concrete controller attach slot +104 resolves to **0x4192b04**. Argument helper
0x432b740 establishes x20=new controller and x19=provider. The method checks
membership, then constructs reciprocal collections: provider+16 includes the
controller and controller+24 includes the provider. Its checks reject the same
object's duplicate relationship, not all different controller objects of the
same class. The relation is therefore collection-capable; actual simultaneous
multiple DPTX controllers on one nub is not established merely by this generic
storage mechanism. No finite per-nub controller maximum is inferred.

The bounded exact-store scan within the identified controller implementation
0x405e000..0x4080aa8 finds only 0x4068b28 for unsigned-offset stores to +312;
paired-store matches at +304 are stack saves, not object writes. Constructor
zero-fill also initializes the field. This is useful local evidence, but it
does not close register-offset aliases, all inherited methods, repeated provider
registration or every runtime factory consumer. Further generic registry/lifetime
graph expansion is outside M3D. This missing per-physical-owner invariant cannot
be replaced by a count of static classes or factory registrations.

## Selected Device And Timing Ownership

**SELECTED_DEVICE_SCALAR_REPLACEMENT** is established for the concrete setter
and its recovered callers. Creation region 0x4075c88 reads +312 at 0x4075cbc
and branches past creation when it is already nonnull (0x4075d6c). Its
non-null candidate is a **DCPDPDevice** (1,344-byte allocation, address point
0x47a4638) or **DCPDPVirtualDevice** (1,384 bytes, address point 0x47a3db8).
Exact class getters and constructor stores qualify those identities. The device
has a DCPDPController-typed delegate at +456, as frozen in M3C. Device creation,
virtual capability setup, add/remove notifications and the same-device guards
identify a selected DP endpoint abstraction, not independently a timing generator
or source stream. A virtual device is not automatically a second source.

The concrete-controller casts 0x4084940/0x4089920 have six direct consumers.
Three observed stores retain scalar references to that same supplied controller:
0x40898d8 -> consumer+1752, 0x408f158 -> consumer+544 and 0x410c1f0 -> consumer+88.
The other consumers perform typed checks/operations. None of those callsites
allocates a second controller or establishes a source collection on one nub.
Their complete consumer-object lifetimes are not reconstructed or inferred.

**SCALAR_TIMING_STATE** applies to controller+716, an embedded 256-byte current
video-attribute cache. The M3C update caller copies the new attributes over that
same address at 0x4061f58 after table configuration. It does not index by payload
ID. Applying B through this path overwrites A in this controller's cache; this
does not rule out another controller retaining A.

| Exact Timing-State Path | Local Effect | Limit |
| --- | --- | --- |
| Constructor 0x4080a10 | Zero-fills the allocated controller, including +716 and +312 | Initialization, not an active-stream capacity rule |
| 0x4061c34 / 0x4061f58 | Copies 256-byte input x21 to controller+716 | One current cache; full provider cardinality remains unresolved |
| 0x4063534 / 0x4063558, 0x40635b8 | Copies cached attributes to output record+16, then clears the controller cache after successful stop-related calls | Exported/saved copy is not simultaneous active timing |
| 0x4068e18 / 0x406902c | Clears 256-byte current attributes on enable initialization | Power state is not payload count |
| 0x4068e18 / 0x4069128 | Calls concrete +2416 method 0x405ef94 with output controller+716 | Hardware timing readback path to be qualified separately |
| 0x4068e18 / 0x40691a4 | Clears the same cache on the local failure path | Whole scalar state, not per-stream removal |
| 0x4063784 | prepareLink uses controller+716 | Not another timing owner |
| 0x406d5c8 | updateLinkRate passes controller+716 after same selected-device and enabled-state guards | Rate update, not creation of a second stream |
| 0x4079dac | getLinkData exports the same current record | Observation/export does not establish coexistence |

Base-service **handleStartLink 0x415414c** copies 256 bytes to
service+1492+(index<<8), with validity at +1474+index. It then compares/converts
records via slots +3528/+3616/+3576, referencing diagnostics
`Second color format conversion validation failed` and
`Timing format conversion validation failed`. The compared record at +2004 is
another state representation. The exact index domain and direction/staging roles
are not fully closed; neither the indexed storage nor its conversion copies
establish independently enabled timing sources on one DPTX. This candidate
collection is **UNKNOWN**, not SOURCE_STREAMS.

## Getter Implementations

Concrete class-cast **0x40809c0** accepts AppleDCPDPTXController metadata
0x48fcea0, then tails to **DCPDPController** cast 0x4120e4c. Exact direct branch
references to that base cast contain this one derived cast; none target the
concrete cast. Adjacent and short-gap address checks for these two exact
metadata records find the known getters/casts, not another derived controller.
The base cast is not itself in a declared vtable; no base getter body is invented.

The only declared chain reference to source getter **0x40738f0** is
controller+1072 at 0x478cf58. The recovered concrete implementation emits the
same ID 1/start 0 for any eligible instance, deriving count from that instance's
scalar state. Its caller/device cannot select ID 2, 3 or 4 through this body.
Another controller instance using this implementation would still emit ID 1;
it is not automatically assigned another VC. No inherited getter override
returning a distinct ID was qualified in this exact ancestry set.

Result: **GETTER_OVERRIDE_SET_UNRESOLVED**, with one concrete implementation
found locally. Exact target/reference coverage cannot exclude an unclosed
indirect class registration, inlined cast or other runtime ownership route.
No unrelated vtable offset was treated as an override, and no whole-firmware
search for small integers was performed.

## Physical DPTX And Register Ownership

The concrete register-owning class is **AppleDCPDPTXNub**. Its constructor
0x4019bb0 stores the supplied physical descriptor at nub+312 and installs
address point 0x478b338. This is a different +312 field from the controller's
selected-device field. Controller initialization 0x407cd48 casts its provider
to that nub and stores it at controller+264. Nub initialization 0x404d364
obtains bank descriptors from its physical descriptor+24/+32/+40, installs
them at nub+280/+288/+296 through 0x40f1960, and M3C's bank-0 reader/writer
dereferences bank descriptor+8. The packetizer uses this concrete owner, not
the MST manager or a downstream port.

The image is explicitly associated with /Yggdrasill/DISP_EXT0 and DISP_EXT1
by retained BUND metadata. Both platform nodes have raw target `DCP_T8142`
and platform `IOP_ASC7`; each selects the same dcp_legacy header/image UUID.
Their MMIO arrays are separate 528-byte address/size lists. EXT0 includes
0x504000000/size0x2800000 and 0x544000000/size0x2800000; EXT1 instead includes
0x3a8000000/size0x2800000 and 0x3e8000000/size0x2800000. These are offline
firmware address spaces, not unqualified host physical addresses.

The initializer's exact nub constructor references occur at 0x432d878,
0x432d8f8, 0x432d994, 0x432da0c, 0x432da8c, 0x432dcc0, 0x432dd2c,
0x432dd9c, 0x432de10, 0x432dfb4, 0x432e020, 0x432e090 and 0x432e104.
They build statically described nub objects, not thirteen active streams.
Examples of bank descriptors at 0x48e7680 and 0x48e7740 contain base values
0x506100000 and 0x3aa100000 at +8, respectively, and size0x4184 at +16.
Those bases fall in the distinct EXT0/EXT1 MMIO ranges above. Some neighboring
descriptors are zero/unmapped; other descriptor groups have different bases.
No controller multiplicity is inferred from the number of descriptor groups.

The retained J704AP DeviceTree separately identifies dispext0,t8142 and
dispext1,t8142 with distinct host register ranges, and dcpext0/dcpext1 nub
nodes. Host-side and firmware-side address spaces are not equated. In particular,
the complete runtime platform selection that binds one of the initializer's nub
objects and its controller-client set specifically to DISP_EXT0 has not been
closed. Range containment is corroboration, not an object-identity proof.

Thus the strict requested result is **PHYSICAL_DPTX_OWNER_UNRESOLVED** for the
full DISP_EXT0-to-runtime-source-object chain, despite the proven concrete nub
class and register path. The strongest chain is:

```text
DISP_EXT0 -> T8142 dcp_legacy image and EXT0 MMIO map
			-> [runtime selection of the nub/controller client set: unresolved]
			-> AppleDCPDPTXNub physical descriptor
			-> nub bank-0 descriptor (+280), register base (+8)
			<- controller provider cast, controller+264
			<- M3C source table and activation methods
```

DISP_EXT1 has its own metadata/ranges and is only a negative control. It is not
the second stream required for same-link proof. No current machine register,
live object address, DPCD value or display topology was read in M3D.

## Timing Fields And Generator Count

Controller slot +2416 reaches **0x405ef94**, whose own diagnostic names
`getSlaveVideoLinkDataFromRegisters`. Helper 0x4325bd0 establishes x19=controller
and x20=output record. The method reads the same controller+264 bank-0 register
interface used by M3C and reconstructs one timing record. Its direct diagnostics
name horizontal/vertical total, front porch, back porch and active, and pixel
clock in Hz. They provide field meaning independently of register-number guesses.

| Record Offset | Width | Qualified Meaning | Readback Evidence |
| --- | --- | --- | --- |
| +44 | 4 | H total | bank0 offset0x5c -> store0x405f144; horizontal diagnostic0x47527b0 |
| +48 | 4 | H active | bank0 offset0x60 -> store0x405f150; same diagnostic |
| +60 | 4 | H front porch | bank0 offset0x64 -> store0x405f15c; same diagnostic argument order |
| +56 | 4 | H back porch | bank0 offset0x6c -> store0x405f174; same diagnostic |
| +52 | 4 | Additional H sync parameter; exact field name unclosed | bank0 offset0x68 -> store0x405f168 |
| +76 | 4 | V total | bank0 offset0x48 -> store0x405f0ec; vertical diagnostic0x47527ea |
| +80 | 4 | V active | bank0 offset0x4c -> store0x405f0fc; same diagnostic |
| +92 | 4 | V front porch | bank0 offset0x50 -> store0x405f10c; same diagnostic argument order |
| +88 | 4 | V back porch | bank0 offset0x58 -> store0x405f12c; same diagnostic |
| +84 | 4 | Additional V sync parameter; exact field name unclosed | bank0 offset0x54 -> store0x405f11c |
| +68, +100 | 4 each | Sync-related booleans derived from register0x44 bits0/1 | stores0x405f17c/0x405f138; polarity naming not independently closed |
| +108 | 4 | Pixel clock, Hz in this diagnostic | load0x405f818, Timing diagnostic0x4752822; complete value producer not promoted |
| +96 | 4 | Sync-rate value interpreted as signed16.16 Hz | load0x405f7f4 and divide65536; same diagnostic |
| +40 bit0 | 1 bit | Interlaced flag in this diagnostic | load0x405f810/mask1; same diagnostic |

H blank and V blank are derived as total minus active, not separately invented
fields. The M3C slot producer consumes the H timing fields and link bandwidth;
it does not introduce another timing context. Exact MSA-equivalent generator
count is not derived from these readable register fields alone.

The readback checks register0x2c bit3 or register0x44 bit4 before ordinary
timing reconstruction; its failure diagnostic says video_capture support was
removed and requires F_SEL=1. This is positive evidence of a supported input
mode, but not a named payload-to-source mapping or proof of only one physical
feed. No ID-to-timing-generator selector was recovered. Lane mapping, DSC,
color conversion, FIFO thresholds and SDP types are not counted as timing engines.

Stop-related method **0x4061444** disables selected-device infoframes and VSC,
Adaptive-Sync and brightness SDPs. Rate-update entry **0x405ee00** has a
200-byte referenced extent, beginning before an internal PAC prologue; its
timing input comes from the same cache. Neither method establishes coexistence
of a second independent source. The initial inferred-entry capture failed and
was retained; the explicit-range replay succeeded. No stop or rate update was
executed on hardware.

Results: **STREAM_GENERATOR_COUNT_UNRESOLVED** and
**SOURCE_SELECTOR_UNRESOLVED**. One unindexed readback/programming path is
observed, not a positive hardware-generator maximum.

## Collections And Same-Link Concurrency

| Candidate Collection / Field | Classification | Meaning And Limit |
| --- | --- | --- |
| Global93 factory records | UNKNOWN | Class matching/creation descriptions, not runtime sources |
| Factory callback candidate vector, stride16 | UNKNOWN | Factory record/score pairs, not controllers or timings |
| Nub/provider+16 client collection | CONTROLLERS only for the qualified controller elements; otherwise UNKNOWN | Can hold generic client relationships; no complete per-nub typed source set or maximum recovered |
| Controller+24 provider collection | PHYSICAL_PORTS for the qualified nub relationship; otherwise UNKNOWN | Reciprocal provider relationship, not multiple source streams |
| Controller+312 | Not a collection | Optional scalar selected DP endpoint; replace/clear semantics |
| Controller+716 | Not a collection | Embedded current timing state |
| Service+1492 indexed records / +2004 conversion state | UNKNOWN | Timing/conversion representations; no simultaneous per-payload activation established |
| Frozen M3B/M3C manager port collection | DOWNSTREAM_TOPOLOGY_PORTS | Not source timing ownership; not reanalyzed |
| EXT0/EXT1 nub descriptor groups | PHYSICAL_PORTS | Separate instance/address maps, not one-link streams |
| Power-controller+544 / ANX-bridge+88 references | Not a source collection | Typed scalar references to a supplied controller, not new allocations |

**SOURCE_CONTAINER_UNRESOLVED**: no qualified SOURCE_STREAMS collection belongs
to one proved physical DPTX instance. The presence of a generic client collection
does not prove multiple same-link sources; its absence from a typed reconstruction
does not prove a hard maximum.

**PACKETIZER_CONTROLLER_LOOP_UNRESOLVED**: the factory/category loops create
generic matching services, not a proved loop over source controllers feeding one
packetizer. M3C's exact caller invokes updatePayloadTable once and overwrites
the bank-0 slot table. No qualified repeated per-child update preserving another
source's timing/payload was found in the bounded source-owner paths. No global
absence theorem is claimed.

**ONLY_SOURCE_PAYLOAD_ID_1_FOUND**, in the exact concrete getter and its source
table/caller path. Source-side IDs2/3/4 were not qualified; small constants in
the selected-device construction configure endpoint properties and are not
payload IDs. Reusing the ID-1 getter in another instance would not itself assign
that instance another ID. The unclosed override/owner set prevents a hard limit.

**CONCURRENT_SOURCE_STATE_UNRESOLVED**: new selected-device creation skips an
already selected device; direct setter replacement and timing B overwrite A
locally. Neither sequential reconfiguration nor those local rules settle whether
another controller on the same physical owner can retain source A. Two distinct
EXT instances are expressly excluded from a same-link counterexample.

## Ownership Graph

| Edge | Cardinality | Evidence / Limit | Confidence |
| --- | --- | --- | --- |
| Physical T8142 DPTX L -> controller C | UNKNOWN | Runtime factory/category and physical-instance client membership not closed | MEDIUM_BOUNDARY_CONFIDENCE for local methods; global edge unproved |
| Constructed C -> nub/provider reference | OPTIONAL | Concrete provider cast stored at C+264; null causes initialization failure | HIGH_BOUNDARY_CONFIDENCE for cast/store; alias/lifetime closure separate |
| C -> selected endpoint D | OPTIONAL | One scalar field, null/replacement setter and add-if-empty path | HIGH_BOUNDARY_CONFIDENCE locally |
| C -> current timing T | ONE_TO_ONE | Embedded256-byte cache at+716, overwrite/reset/readback | HIGH_BOUNDARY_CONFIDENCE for storage; total physical source count unproved |
| D -> independent timing object T | UNKNOWN | Device delegates to controller; no independently enabled timing owner proved on D | MEDIUM_BOUNDARY_CONFIDENCE |
| C -> source scalar payload record | ONE_TO_ONE | Frozen M3C embedded16-byte record and instance getter | HIGH_BOUNDARY_CONFIDENCE for storage |
| Selected D -> returned payload descriptor P | OPTIONAL | Getter requires selected-device equality, power state and output buffer | HIGH_BOUNDARY_CONFIDENCE |
| Multiple C/D -> same physical L concurrently | UNKNOWN | No proved same-owner pair with independent timing/IDs | MEDIUM_BOUNDARY_CONFIDENCE for local evidence; concurrency unproved |

ONE_TO_ONE in this table is an embedded-field fact, not proof that only one such
controller can attach to the same physical transmitter. No MANY_TO_ONE or
ONE_TO_MANY source-stream edge is promoted from generic provider collections.

## Ownership Evidence Map

| Ownership Requirement | Result | Evidence | Confidence |
| --- | --- | --- | --- |
| Physical DPTX owner | PHYSICAL_DPTX_OWNER_UNRESOLVED | Concrete nub/register path; EXT0/EXT1 maps known, selected runtime source-client set not closed | MEDIUM_BOUNDARY_CONFIDENCE |
| Controller cardinality | CONTROLLER_CARDINALITY_UNRESOLVED | Runtime factory0x48fcb60; dispatcher and reciprocal collections do not prove singleton per nub | MEDIUM_BOUNDARY_CONFIDENCE |
| Selected-device cardinality | SELECTED_DEVICE_SCALAR_REPLACEMENT | 0x4068b28; four argument-qualified direct callers and add-if-empty branch | HIGH_BOUNDARY_CONFIDENCE locally |
| Selected-device role | DP endpoint abstraction; source-stream role unproved | DCPDPDevice/DCPDPVirtualDevice constructors, delegate and add/remove paths | MEDIUM_BOUNDARY_CONFIDENCE |
| Timing-state cardinality | SCALAR_TIMING_STATE | C+716 current cache, overwrite/clear/readback; service conversion records excluded | HIGH_BOUNDARY_CONFIDENCE locally |
| Source collection | SOURCE_CONTAINER_UNRESOLVED | Provider/client collection lacks closed same-physical-owner typed source set | MEDIUM_BOUNDARY_CONFIDENCE |
| Payload getter implementations | GETTER_OVERRIDE_SET_UNRESOLVED | One concrete ancestry-qualified getter, no qualified alternate ID implementation | MEDIUM_BOUNDARY_CONFIDENCE for set; HIGH for recovered getter |
| Distinct source payload IDs | ONLY_SOURCE_PAYLOAD_ID_1_FOUND | Exact getter and M3C source table path; not an all-path ID theorem | HIGH_BOUNDARY_CONFIDENCE locally |
| Same-link coexistence | CONCURRENT_SOURCE_STATE_UNRESOLVED | No two same-owner contexts with independent timing and simultaneous distinct payloads | MEDIUM_BOUNDARY_CONFIDENCE |
| Stream generators | STREAM_GENERATOR_COUNT_UNRESOLVED | One fixed-offset timing readback; second same-owner generator neither proved nor excluded | MEDIUM_BOUNDARY_CONFIDENCE |
| Payload-to-source selector | SOURCE_SELECTOR_UNRESOLVED | F_SEL input-mode check is not payload/source routing; concrete table reused | MEDIUM_BOUNDARY_CONFIDENCE |

## Stream Ownership Result And Viability

Primary result: **M5_DCP_STREAM_OWNERSHIP_UNRESOLVED**.

Architectural viability: **MACMST_ARCHITECTURAL_VIABILITY_UNRESOLVED**.

The positive proof closes neither branch: there is no established pair of
independently timed source contexts on one physical DPTX with distinct concurrent
payloads, and no positive architectural maximum of one controller/timing
generator/feed. The real M3C packetizer machinery and M3D's scalar concrete
paths are retained without promotion to hardware impossibility or native MST
functionality.

Exactly one remaining opacity boundary is **the runtime source-controller
membership of one physical T8142 DPTX register owner**. The unresolved physical
selection, multiplicity and same-link timing/selector results are limitations
of that ownership boundary, not separate proposed research tasks.

**STOP STATIC PACKETIZER EXPANSION.** This completes the last planned pass.
Do not create M3E as another firmware/object graph search. Do not design M4A
host-to-DCP control discovery: architectural viability was not supported.
No new hardware experiment or retired transport work is proposed.

Packetizer baseline preserved:
**M5_DCP_MST_PACKETIZER_PRESENT_BUT_STREAM_BINDING_UNRESOLVED**.
M3B's MST-control/codec/topology baseline and M3A's scoped host negatives remain
unchanged. Selector status: **RETIRED_ON_DAILY_USE_M5**.
Global DPCD gate: **NOT_READY_FOR_DPCD_TEST**.

## Boundary Confidence And Provenance

All code addresses are offline VM addresses in the identified T8142 dcp_legacy
image, UUID **18E26403-396D-3512-AF59-17E24808703A**, preferred base0x04000000.
No pointer was invoked. There is no trusted LC_FUNCTION_STARTS metadata.
HIGH_BOUNDARY_CONFIDENCE requires a declared/constructor/direct-reference anchor
plus compatible entry/return or tail flow; MEDIUM_BOUNDARY_CONFIDENCE retains
those local anchors but does not close larger outlined/error paths.
LOW_BOUNDARY_CONFIDENCE is used for an isolated window or incompletely delimited
large initializer. No FOUND or BLOCKED conclusion depends on low-confidence
regions; neither conclusion was reached.

| Decisive Region / Entry | Bytes | SHA-256 | Confidence And Corroboration |
| --- | --- | --- | --- |
| 0x4080a10 allocating controller factory | 152 | 9a64a031abdd6cf8ebadf09ce3672bb15f33719aa16fd0566f0ba5e5f1e20a77 | MEDIUM_BOUNDARY_CONFIDENCE: exact registration pointer materialization, PAC/return, allocation and concrete vtable stores |
| 0x40809e8 controller matcher | 40 | 18511c736d44abcba89cba2a4fb2400e356960fee274fe5d100e1b355bf048c8 | HIGH_BOUNDARY_CONFIDENCE: registered predicate address, PAC/return and direct nub cast |
| 0x432be18 registration/nub initializer region | 16868 | fceeddfd2cd566b8f4c0cc4969282043696c179d47f7fdc33c45b0c16c8e2a2e | LOW_BOUNDARY_CONFIDENCE for complete initializer; exact constructor calls/materialized registration stores are corroborated locally, not complete platform selection |
| 0x4194590 factory iterator | 88 | 4e32a3c9050a3c94e7cc19ed2905165c135b036c737a0e0657cfb247325251c2 | HIGH_BOUNDARY_CONFIDENCE: two direct callers, PAC/return and bounded32-byte loop |
| 0x4194150 factory dispatch region | 728 | 7a8a5de7bfd62a5fb9f5c1379507b2bc74f8d83a079fd90ae4fcecf17b7ead50 | MEDIUM_BOUNDARY_CONFIDENCE: exact iterator call and callback address, PAC/return; region includes adjacent callback-support leaves0x41943f8/0x4194420 |
| 0x4194428 match callback | 360 | 5c8ddf34d49c6cdcd75a5b0f51ea71776ab8bf2c2063ed3b63c7984b96e12947 | MEDIUM_BOUNDARY_CONFIDENCE: callback address construction, PAC/return/tail; vector growth/error paths not an object-capacity proof |
| 0x4194fc8 attach/initialize helper | 252 | e079c2a4ddd571c4aa4cdd654258b3de0163c24c2142b9953718988f6de9bd7c | HIGH_BOUNDARY_CONFIDENCE: direct factory call, PAC/return and slot96/104/120 sequence |
| 0x4192b04 reciprocal attachment | 484 | b47957dc23583f507430bff6f417f0b9bd785973551217645d9692404acbe2fe | MEDIUM_BOUNDARY_CONFIDENCE: declared controller+104 slot, receiver helper, PAC/return and exact collection stores |
| 0x4068ab0 selected-device setter | 164 | d971e67793dc4799cd0288dbf62637f97cfd509d026ccc7dcbf3eaea40431ee7 | HIGH_BOUNDARY_CONFIDENCE for replace path: four direct callers, receiver helper, PAC/return; fatal gate diagnostic does not establish all-alias closure |
| 0x4068308 device removal | 1752 | 52e763036e0e1c7e7cbcaaa9b5cfa5837fa5786df5e1bd2e1b3fa5f74616e37c | MEDIUM_BOUNDARY_CONFIDENCE: two direct setter calls, removal diagnostics and PAC/return; no generic lifecycle expansion |
| 0x4075c88 device creation | 2756 | 002793bf33e85586772042510ca2b773ad86cbc9b5c818a5835fc3f1ab1e1ecb | MEDIUM_BOUNDARY_CONFIDENCE: concrete device vtable stores, add-if-empty and direct setter calls, Adding device diagnostic |
| 0x40809c0 concrete class cast | 24 | dcc1b11c6d1e044c5a4657cce12ac8553bae043e5c7681681f1ad0ea25400e8c | HIGH_BOUNDARY_CONFIDENCE: declared class-cast slot, exact metadata/branch-to-base and local return |
| 0x4120e4c base class cast | 36 | 4e6e3927c644d430a0b8792cbfa3a8dd070704fc71a8738388ad9cc7c440d056 | HIGH_BOUNDARY_CONFIDENCE: direct concrete-cast tail, exact base metadata and local return/tail |
| 0x40898c0 controller reference consumer | 96 | dffbda340876f5f0155a9e1b514e76c94b583cc20eb14699e947fd4e47b15743 | MEDIUM_BOUNDARY_CONFIDENCE: declared method slot, direct controller cast and scalar+1752 store; consumer class role left unknown |
| 0x408f130 power-controller initialization | 1620 | 3dc741cd5f8bcb2bf990adda671e7218e2f4c3f1ec3a625ed6142ef76ba4fa65 | MEDIUM_BOUNDARY_CONFIDENCE: declared init slot/class getter and cast/store+544; entire lifetime not recovered |
| 0x410c1a0 ANX-bridge initialization | 5816 | 6fac2fd5b2dcabcbca39e6c474c360dead4ee529a8acfe1182f891b5644d027f | MEDIUM_BOUNDARY_CONFIDENCE for entry/store: declared init slot/class getter, cast/store+88; full bridge function not semantically analyzed |
| 0x4063534 timing export/clear region | 168 | acd492a46c316c16af5992cb53bc08ee7d6985c1322763706dc3ac54e38f638a | LOW_BOUNDARY_CONFIDENCE for public entry: inferred PAC boundary but no direct/chain entry reference; exact copy/clear calls are supplementary, not a limit proof |
| 0x4068e18 enable/readback | 2736 | a8bcbaf05623b246ff128989895d924aec6f484a96abbfaab253b24cc550dee8 | MEDIUM_BOUNDARY_CONFIDENCE: declared controller slot, enabling diagnostics and exact scalar-cache readback/clear calls |
| 0x415414c indexed service start | 1076 | ca15d8de55dd5fd0caa2463551d4f08021d8c36a986d6cb203494f233a1e74e8 | MEDIUM_BOUNDARY_CONFIDENCE: declared slot/direct callers, PAC/return and handleStartLink/conversion diagnostics; index semantics remain unclosed |
| 0x405ef94 timing register readback | 2636 | b7242a88fbc5e6473f6e6efa9759f2dedbb84be7b6c125bb8b8f6f73366dc563 | MEDIUM_BOUNDARY_CONFIDENCE: declared controller+2416, receiver helper and exact timing diagnostics/stores; whole clock producer/limits not proved |
| 0x4061444 stream-stop-related path | 1200 | 8e4b1ae16ebae03ba0c6cec8774f54c2593a0b9b7ae74abf402baebd98d37b81 | MEDIUM_BOUNDARY_CONFIDENCE: declared controller+2232, PAC/return and exact disable diagnostics; not independent removal proof |
| 0x405ee00 rate-update entry | 200 | 3e8733884524b6e5135d7d9f60c95136e2a07fdf9e4f76ba74879e8367889738 | MEDIUM_BOUNDARY_CONFIDENCE: declared controller+2440, initial branch/internal PAC/local return and tail before adjacent leaf |

The complete raw instructions and support bodies are retained in two final
exact-only receipts, not redistributed firmware. The source register/getter
hashes already qualified in [M3C](m5-dcp-mst-packetizer.md#function-boundaries-and-raw-evidence)
are reused and replayed, not rediscovered.

| Artifact | SHA-256 / Identity |
| --- | --- |
| M3D ownership-final/decoded.json,31 regions/13 pointer slots | 15c7c3540072bfa087ba297749b72c347a445cbc35e5c8e83ac1b7fbb740b17f |
| M3D timing-final/decoded.json,30 regions/14 pointer slots | 62b8f579283a9159ce417491c900548a9d8b8e3ed96fbcacd4d9be92ab039baf |
| Retained T8142 raw IM4P,4,223,041 bytes | 3f1424dbd80664128041bff2585e09bcf7fed9a75ac38e6c5a273f0b6494f219 |
| Retained decoded T8142 payload,16,023,552 bytes | 9c4d1b86ecbc897109235fabf6dbf0d83330e1e0f2f76ccd135484e708fefb7c |
| BuildManifest.plist | e8ff2cdd3e8ab3a668132bf9453948b70f1863b849a6185914f54a9ec25356d3 |
| Selected identity156, sorted binary plist | 94cc166baa7845901ff25b14b509dd6391745b2bf1bebd218b97fc14fb093e72 |
| J704AP raw DeviceTree IM4P | 13f4dce18ca0936616c71eb9ccbb18ad791bcc01d06d287405d5cd0b4dc2c962 |
| Decoded DeviceTree,569 nodes | 79cc631c24ced43e166c56d717083350ee4baff7b055c200c481c4d9bf4cfba5 |
| BUND ADT config,708 nodes | 609a255e040ef2185c23f49197c3c0e32636a12de32b7510e6289b8ff185c887 |
| EXT0 MMIO array,528 bytes | 33e5b2d78d19d217ed18d708800d082d2b77c5f58dcfbe66f32576bde94e7300 |
| EXT1 MMIO array,528 bytes | 85f4e8f450e3b0e081fd85c26c7d0f893c44721497f140bdc4ae3ac7f26c25e1 |
| Format7/reserved1=2 pointer metadata,8 chains/27,054 validated entries | d703ed2c278fb2ffc05d1ecc05a08275ee28f046d80ed7c48aee46bd34ff8188 |
| Frozen protocol oracle | ba7b651e9bf9d73043abc9176f6f74f464e702772dc7c7a99a63c8e43a3e3073 |

Manifest association remains Mac17,2/J704AP/CPID0x8142/BDID0x22, macOS26.6.2
build25G83, production Ap,DCP2 at Firmware/dcp/t8142dcp.im4p. The component's
SHA-384 digest
`250388ecfc4901d9fc8efa556bd88ffc58826053916dcc66252e031374bf4b4814d94747951f0eb3bc6b9038815c6012`
matches after the already qualified in-memory type override dcpf -> dcp2 at
offset13. Raw source bytes are unchanged. Original Apple source URL and
BuildIdentity fields remain in [M3B provenance](m5-dcp-firmware-mst.md#provenance-and-reproduction).
This associates a production firmware image, not byte-attested live firmware.

Current [dcp_firmware.py](../../tools/dcp_firmware.py) SHA-256:
`d627336be54752daf0ee539f5b17eb8028c7d9639e440f59c05e58a26f1f05e8`.
Current [static tests](../../tests/test_iodp_static.py) SHA-256:
`9b93a63daddd0e0f475d79c14b444439ada85a092513628ae77994fdb03130b5`.
The five other reader hashes are unchanged and embedded in both receipts.
The only tool change permits exact-only output in artifacts/probes/m3d as well
as the historical M3C root. Inputs remain retained M3B components; no broad scan
mode is added or used. A synthetic test verifies allowed/rejected output roots
before input reads. No dependency, native code or private transport changed.

## Reproduction And Validation

The two final receipts under artifacts/probes/m3d contain every requested
address, explicit size, pointer slot, image identity and raw body hash. Replay
the same requested selections into fresh M3D directories; existing receipts are
never overwritten. A minimal exact ownership replay is:

```sh
python3 tools/dcp_firmware.py \
	--components artifacts/sources/m3b/25G83-components-20260914 \
	--output artifacts/probes/m3d/ownership-replay --details-only \
	--detail-address 0x4080a10 --detail-address 0x4068ab0 \
	--detail-address 0x4194590 --detail-address 0x4192b04 \
	--detail-range 0x40809c0:24 --detail-range 0x4120e4c:36 \
	--detail-range 0x40738f0:100 --pointer-slot 0x478cb40 \
	--pointer-slot 0x478cb90 --pointer-slot 0x478cf58
```

This is a reproduction command, not a proposed next discovery milestone.
No --scan, hardware operation, firmware download or private display call is
required. All final61 region hashes, raw instructions/contiguous addresses,
direct caller sets and explicit entry-pointer references were recomputed;
all27 requested chain bindings matched and40 bodies matched prior receipts.
Failed boundary/schema exploratory checks are retained/identified as failures,
not implementation-absence evidence. The rate-update capture error was corrected
by its referenced200-byte extent; the bundle ADT was read through its actual
property schema rather than the summarized layout records.

| Required Check | Result |
| --- | --- |
| cmake --build build && ctest --test-dir build -L unit --output-on-failure | PASS; no native rebuild,9/9 unit entries,5.73s |
| cmake --build build-sanitized && ctest --test-dir build-sanitized -L unit --output-on-failure | PASS; no native rebuild,9/9 unit entries,7.68s |
| python3 -m unittest discover -s tests -p 'test_iodp_static.py' | PASS,87 methods |
| Same static command with -k m3d | PASS,1 method covering allowed/rejected output roots |
| Exact T8142 replay and decisive raw-function checks | PASS,61 regions/27 pointer slots;40 prior-body matches |
| Chained-pointer validation | PASS,27,054 declared entries; no pointer invocation |
| Retained manifest/DeviceTree/DCP decode | PASS, identity156 and original hashes/digests unchanged |
| Frozen M3C receipts, protocol oracle and native binaries | PASS, unchanged |

The unchanged native probe hash is
`450832c50446d3a430cbed2bcab7c285cddf5f6b370b2339df2cd0a33aefd89a`;
unexecuted helper hash
`d94b0a450e89daa697675d816e231994e37456ec61928fc72261ec500f153830`;
unexecuted parent hash
`f94db7e91ef670ce6c59ce73929016d2d36a5adb44fb9714f188932771b55e8b`.
No historical M2F runtime attestation is transferred to rebuilt binaries.

M2F-ATTEMPTED stays consumed, SHA-256
`2f3da1f224c0602dc46f812d3f6eb2c1560fe7a82c1a89f93eedb725b2726efc`.
The successful/stopped M2F result hashes remain
`86ee9fdd87eb631e7552b0087471a149c183667c2162e838866ce993e1dd3d04` and
`79387346acdaebed1efb2284a531de8f2cf5aad1d64915a3f5f527040ebae840`.
M2G-DPCD-READ-ATTEMPTED remains absent. No marker was created or reset.

Zero M3D DPDV opens, selector calls, private display calls, DPCD/AUX/I2C/MST
transactions, firmware execution/patches, mode/link/payload/security changes or
physical disconnects occurred. No real helper mode, including no-open mode,
and no public hardware capture ran. Software/mock/static tests establish only
their stated scope; no native MST hardware functionality was tested. Network
use is limited to the explicitly requested Git synchronization/publication.

## Git And Documentation Audit

The final pre-commit audit covers exactly seven text paths: this report, root
and research indexes, open questions, the append-only evidence ledger, the
existing firmware reader and existing static tests. All source/output changes
remain on research/m5-dcp-stream-ownership. No production/native code, CMake,
private transport, isolation helper, frozen M3A/M3B/M3C report, protocol oracle,
editor configuration or raw firmware/capture is changed. Raw receipts stay
ignored under artifacts/probes/m3d.

All local documentation links/anchors and code fences passed. Editor diagnostics
and whitespace checks reported no errors. E001-E204/S01-S65 are byte-preserved;
M3D appends E205-E215/S66-S69. Current status pages agree on the one opacity
boundary, unresolved viability and stop, without superseding the M3C packetizer
baseline or proposing another static milestone.

Before publication, all **32** remote head/tag/peeled identities matched local
refs, including main5beb1ac304a1715dc9fb7cad9b3322819b8fd140, exact M3C HEAD,
and v0.9 object4b8cf98419fa4678d931ad014ba16c306c2f722d. Publication is limited
to research/m5-dcp-stream-ownership with an explicit non-force refspec and
push.followTags=false. No M3D merge or PR is authorized. Final commit/upstream
identities are reported after push rather than claiming a future hash here.