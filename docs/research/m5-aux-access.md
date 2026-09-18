# M5P6 AUX Analyzer Qualification and Temporary Access

Research and outreach preparation only, 2026-09-18. No messages
sent, equipment purchased/inserted, signals captured or display state changed.

## Objective

Find the least-cost practical route to one trustworthy upstream M5-to-MST-branch
AUX capture. The objective remains independent external displays through ordinary
USB-C / DisplayPort MST, without DisplayLink or separate Thunderbolt DP tunnels.
M5P5's AUX-layer decision is frozen; this is equipment/access qualification,
not another theoretical feasibility or static Apple analysis.

## M5P5 Baseline

[M5P5](m5-dp-observation-plan.md) was audited and published unchanged at
`54d30598f013b617282375d5295a6b37269fb5b9` on
`research/m5-dp-observation-plan`, upstream equal, 0/0. Its two linear commits,
clean tree, 13 retained source/document hashes and Linux pin
`238650ef6c7c7cca08e032527329424c9fbd70e5` passed verification.
M5P4 remains published at `db517239b496168b05490a6c3d71af1f88329382`.
All 46 prior published head/tag/peeled identities were preserved; publication
added only M5P5. No merge, PR or tag update occurred.

The existing hardware-disabled build completed 16 build actions; all four
offline CTests passed (124 observer, 12 host, 33 topology, 31 log tests: 200).
M5P3/M5P4 captures, all 477 historical records and review, consumed M2F marker
and receipts match their recorded hashes. The M2G DPCD-attempt marker is absent.
No native display executable was run. The current hub stays connected/mirrored.

## W1 Requirements

Frozen W1 questions, in requested order:

1. Is a `DP_MSTM_CAP` read observed, with reply and raw value?
2. Is `DP_MST_EN` enabled in `MSTM_CTRL`, with accepted request or state read?
3. Is MST sideband traffic sent/received, with recoverable raw fragments?
4. What does a complete `LINK_ADDRESS` reply report?
5. How many downstream ports are represented, excluding the input port?
6. Which paths report a peer/device present, including legacy/converter flags?
7. Which paths receive remote DPCD/EDID transactions and successful replies?
8. Is `ENUM_PATH_RESOURCES` issued and what resources are reported?
9. Is `ALLOCATE_PAYLOAD` issued and accepted or rejected?
10. How many distinct, concurrently retained nonzero payload IDs exist?
11. What requested/accepted PBN and local slot start/count are recorded?
12. Are payload-table update and receiver ACT-handled status observed?
13. Is `CONNECTION_STATUS_NOTIFY` or equivalent wire activity observed that
    could inform the historical count transition, without assuming a binding?

Mandatory: upstream bidirectional AUX over the actual USB-C DP Alt Mode path;
preserved orientation, CC/PD/Alt Mode, HPD, SBU, main lanes, two-lane HBR3 if
negotiated, and USB3 coexistence if used. Recover direction, native/I2C request
type, address, lengths, replies, data, sideband bytes and ordering. Preserve raw
or lossless exports, timestamps, capture limits, buffer and explicit loss state.
A GUI alone is insufficient. No main-link pixels/video decode is required.

## DPA-400 Qualification

Status vocabulary: `VERIFIED_SUPPORTED` means explicitly stated by a primary
manufacturer source for its stated configuration, not verified on this Mac.
`LIKELY_SUPPORTED` is an inference, insufficient for a mandatory readiness gate.
`UNRESOLVED` means missing evidence; `NOT_SUPPORTED` means an explicit limit.

Primary sources checked 2026-09-18:

- **D1:** [current product page](https://www.unigraf.fi/product/dpa-400-displayport-aux-channel-monitor/),
  including the expanded/raw HTML option descriptions, not only its summary.
- **D2:** [download catalogue](https://www.unigraf.fi/downloads/), DPA-400 table.
- **D3:** [manual v13, 2023-09-06](https://www.unigraf.fi/app/uploads/2023/04/DP-2.1-AUX-Channel-Monitor-User-Manual.pdf),
  still linked by the current [documents catalogue](https://www.unigraf.fi/documents/).
- **D4:** [January 2023 datasheet](https://www.unigraf.fi/app/uploads/2020/02/DPA-400-Data-Sheet-01-2023.pdf).

**New compared with M5P5:** D1 explicitly lists product number **065055** for
DPA-400 2.1 and **546109** for "DPA-400 Cable for USB-C". D3 pp. 8-9 instead
specifies **546127** for the USB-C Y-cable and **546126** for native DP. The
relationship between 546109 and 546127 is not documented in these sources;
neither is silently treated as a replacement, equivalent SKU or typo.
D2 lists GUI/FW bundle **2.1.10**, with displayed date **6.5.2025** (raw date
preserved). Downloads require an account; no login, package retrieval or
software installation occurred. Manual screenshot versions are not current
firmware receipts.

| Requirement | Classification | Exact evidence / remaining condition |
| --- | --- | --- |
| Current marketed model/order number | VERIFIED_SUPPORTED | D1: DPA-400 2.1, product 065055. Website internal product/SEO IDs are not hardware SKUs. |
| Current public software bundle | VERIFIED_SUPPORTED | D2: 2.1.10 GUI and FW bundle, date 6.5.2025. This verifies the catalogue entry, not installed unit contents. |
| Current board/firmware/FPGA revisions | UNRESOLVED | D3 p. 8 says versions share hardware; p. 28 screenshot shows historical GUI 2.1 [R0], firmware 1.2.0, FPGA 1.6.0. No 2026 unit revision/firmware attestation. Ask for the offered unit's receipt and release notes. |
| Exact USB-C accessory order configuration | UNRESOLVED | D1 546109 versus D3 546127, with no public reconciliation. Both must appear in the request to applications engineering. |
| Source-side/sink-side USB-C connector genders | UNRESOLVED | D3 p. 8 illustrates P1/P2 USB-C endpoints, appearing plug-like, but provides no gender/mechanical specification. Do not infer a supported extension/coupler. |
| Instrument-side connectors | VERIFIED_SUPPORTED | D3 appendix A: DP input/output receptacles; monitor legs shown in the Y-cable diagram. AUX/HPD observation is distinct from the bypassed high-speed path. |
| USB-C DP Alt Mode AUX monitoring | VERIFIED_SUPPORTED | D1's USB-C section states observation between two USB-C devices using its special cable; D3 p. 7 identifies two USB-C Alt Mode ports. |
| Explicit SBU routing and both orientations on offered accessory | UNRESOLVED | AUX-over-USB-C necessarily uses the Alt Mode AUX path, but accessory continuity/polarity handling and both-orientation validation are not specified. No electrical inference is promoted to fixture qualification. |
| Bidirectional AUX messages | VERIFIED_SUPPORTED | D3 pp. 7, 19-22: source and sink requests/replies, Native/I2C records, raw data and reply outcomes. |
| Non-injecting monitoring function | VERIFIED_SUPPORTED | D3 p. 7 explicitly states the DPA-400 does not participate in communication. This is a documented operating claim, not a powered/off-state electrical test. |
| AUX loading, high impedance and failure behavior | UNRESOLVED | No input impedance/capacitance, bias/leakage, power-off loading or isolation specification establishes a true passive electrical tap for this assembly. |
| CC/PD/Vconn/VBUS preservation | UNRESOLVED | No offered-cable power ratings, CC continuity, PD-role participation or policy-engine description. Native DP power-pin statements do not establish USB-C VBUS/PD behavior. |
| USB3 concurrent with DP | UNRESOLVED | Neither USB3 lane pass-through nor a two-lane multifunction-dock qualification is explicitly specified. USB control/power for the analyzer is not this feature. |
| Exact two-lane HBR3 pass-through on this dock | UNRESOLVED | External main-lane bypass is documented, but no assembly-specific rate/lane/USB3 test or loss budget closes this requirement. |
| HBR3 through the unit's main-link electronics | NOT_SUPPORTED | D3 p. 8 says hardware is not compatible with HBR2 or higher; appendix A gives 2.7 Gbit/s for the buffered direct path. Do not route HBR3 through it. |
| Maximum rate of the bypass cable assembly | UNRESOLVED | D4 says compatible with DP 1.1-2.1 and uses bypass for high rates. Protocol-version decode support is not a measured PHY rate rating for either USB-C part number. |
| Native HPD pass-through/monitoring | VERIFIED_SUPPORTED | D3 pp. 7, 17, 31-32: HPD state/timestamp capture and common HPD_IO access. |
| USB-C HPD/Attention preservation and observation | UNRESOLVED | Native HPD functionality does not specify how PD status/Attention crosses or is exposed by the USB-C cable. Ask whether CC needs a separate observer for context. |
| Ability to alter HPD/AUX and safe reset defaults | UNRESOLVED | No injection UI is documented; appendix B labels HPD_IO an output/common HPD signal and other outputs for expansion. That does not prove absence of drive paths or failure effects. Require a supported non-injecting setup and no external signal connection. |
| Native versus I2C, address, request/reply and data | VERIFIED_SUPPORTED | D3 pp. 20-22 describes Type, From, Data hex, addressed DPCD fields and ACK/NACK/DEFER outcomes. Direction can be connector-based or inferred from payload. |
| Deterministic direction recovery for USB-C fixture | UNRESOLVED | D3 p. 19's connection-independent mode is a heuristic. Obtain exact port mapping, direction-basis documentation and a sample with unambiguous request/reply pairs. |
| Raw AUX bytes retained in the GUI | VERIFIED_SUPPORTED | D3 p. 21 Data column and p. 30 report hex-dump example; raw request/reply bytes are shown, not merely decoded labels. |
| MST sideband decode as a product feature | VERIFIED_SUPPORTED | D1 and D3 pp. 8, 19-20 explicitly describe Sideband CH support from 1.2 onward. Confirm the loaned unit's license. |
| Complete multi-fragment MST reassembly/CRC semantics | UNRESOLVED | Generic sideband decode does not document fragmentation/retry/reordering/CRC-failure retention behavior. A complete sample is mandatory. |
| Named LINK_ADDRESS decode | LIKELY_SUPPORTED | Falls within advertised MST sideband decoding, but the inspected sources do not enumerate its field coverage. Require a routed, multi-port reply example. |
| Named remote DPCD/I2C decode | LIKELY_SUPPORTED | DPCD/EDID and sideband are advertised; exact REMOTE_DPCD/REMOTE_I2C route and raw export fields are not independently demonstrated. |
| Named payload allocation/query decode | LIKELY_SUPPORTED | Advertised sideband category; verify VCPI, port, PBN and request/reply correlation in a sample, not from a feature name. |
| Raw unknown/undecoded sideband export | UNRESOLVED | Raw AUX display makes recovery plausible, but the export contract for unknown/CRC-invalid/incomplete messages is not specified. |
| Timestamp resolution | VERIFIED_SUPPORTED | D3 appendix A: 32 microseconds. Printed fractional digits do not establish finer precision or unique ordering. |
| Internal buffer size | VERIFIED_SUPPORTED | D3 appendix A: 14 MByte. D4's virtually unlimited capture wording concerns continued acquisition/host storage, not infinite device memory. Confirm applicability to 2.1.10. |
| Documented acquisition rate | VERIFIED_SUPPORTED | D3 appendix A: transactions as fast as 0.5 ms per request plus reply; input transitions up to 8000/s. Not a guaranteed continuous export throughput or minimum legal AUX spacing. |
| Maximum practical burst/sustained rate and duration | UNRESOLVED | D3 p. 18 warns the buffer can fill faster than host download. No worst-case traffic/host-load test or maximum lifecycle duration is specified. |
| Continuous download/start-stop operation | VERIFIED_SUPPORTED | D3 pp. 16-18: manual start/stop, automatic host download, pending-byte display and download pause; restarting clears device and GUI data. |
| Explicit overflow/drop indication | UNRESOLVED | No dropped-record counter, overflow marker or stop-on-full contract established. D3 p. 20 Error lines mean malformed AUX packets, not capture loss. Buffered=0 after download does not prove zero earlier drops. |
| Binary save/reload and HTML report | VERIFIED_SUPPORTED | D3 pp. 28-30: GUI-readable binary and HTML containing Transaction List lines and per-line Message details; screenshot includes HEX Dump. |
| CSV/structured API/binary format specification | UNRESOLVED | The report dialog screenshot shows CSV-related controls, but no normative CSV columns, binary layout, stable HTML schema or export API is documented. No parser is invented. |
| All raw required fields survive export | UNRESOLVED | Need original sample with fragments/retries/errors and expected byte/record counts; a screenshot is not a parseable lossless export. Export range/filter settings also matter. |
| Host requirements documented by manual | VERIFIED_SUPPORTED | D3 pp. 9, 31: Windows 10/8/7, USB virtual serial driver, USB power; driver installation needs administrator privileges on the lab controller. |
| Current Windows 11/macOS/Linux and offline viewer rights | UNRESOLVED | 2.1.10 catalogue does not resolve supported OS versions, driver signing, viewer-only use or transferable licensing. No installation on the daily-use M5 is proposed. |

The qualification stops at the missing mandatory facts, not at an assumption
that this hardware cannot work. Primary documentation is enough to justify an
applications-engineer question and sample request, not `AUX_ACCESS_READY`.

## DPA-400 USB-C Topology

`DPA400_TOPOLOGY_COMPATIBILITY_UNRESOLVED`.

```text
Proposed, not assembled:
M5 USB-C receptacle
   -> official USB-C through/bypass accessory, exact part and genders unconfirmed
   -> ZMUIPNG upstream connection, captive/detachable mating details unconfirmed
    -> both currently connected monitors

Accessory AUX monitor legs -> DPA-400 DP input/output
DPA-400 control/power USB   -> separate laboratory controller
```

D3 p. 8 depicts USB-C through endpoints P1/P2 with monitor legs P3/P4.
The high-speed stream bypasses the unit; it is not a source -> active DPA-400
repeater -> dock design. Whether the accessory is wholly passive on CC/PD/AUX,
and its receive loading/power-off effects, still need specifications. Powered
measurement electronics can monitor without injecting protocol traffic; that
is different from proving zero loading or electrical isolation.

The drawing appears to show plugs at both USB-C ends. That is a visual lead,
not a confirmed connector-gender specification. The retained MacMST dock notes
identify ZMUIPNG 14-in-1, ASIN B0FWJZCX5G, but do not establish the upstream
cable's exact mating arrangement. If the dock has a captive plug and the
official accessory also ends in a plug, direct connection would not be proved.
Do not choose a coupler, gender changer or a new hub to conceal this uncertainty.
Ask Unigraf for the supported diagram for a multifunction dock, including any
official additional fixture and both USB-C orientations. No physical inspection
requiring movement has been requested.

| Critical cable question | Current answer |
| --- | --- |
| Passes every high-speed lane needed for DP and USB3? | UNRESOLVED: bypass exists, continuity/lane assignment/rating not published in the inspected material. |
| Concurrent USB data and two-lane HBR3? | UNRESOLVED: source-to-dock multifunction operation is not separately specified. |
| Source-to-dock versus source-to-display? | LIKELY_SUPPORTED: D1 says any two USB-C-enabled devices, but that general claim does not qualify this dock, PD or cable fit. |
| SBU/AUX both directions? | VERIFIED_SUPPORTED for the general USB-C AUX monitoring claim; exact SBU polarity/loading and direction basis remain UNRESOLVED. |
| VBUS/CC/PD/Vconn pass-through without policy engine? | UNRESOLVED: require ratings and explicit no-participation statement for the accessory, not just the analyzer. |
| High-impedance observer or active repeater? | Documented AUX nonparticipation and external main-link bypass; impedance and accessory active components UNRESOLVED. Direct main-link buffering is not permitted for HBR3. |
| HPD/Attention unchanged and no drive? | Native HPD monitoring documented; USB-C PD/HPD transport and reset/failure behavior UNRESOLVED. |
| Extra fixtures needed? | Official USB-C accessory and separate controller required; whether extra supported mating hardware is needed for this dock is UNRESOLVED. |

Discriminating outcome of this DPA-first pass: the current sources do not close
the mandatory topology/export/loss gates, and they expose a cable-part-number
conflict. This justifies direct qualification before money or lab time, not
another theoretical AUX study. No forced topology adaptation is yet justified.

## Ellisys Qualification

`ELLISYS_W1_REQUIREMENTS_PARTIAL`.

Current sources: [technical data](https://www.ellisys.com/products/ctr1/technical.php),
[edition/order table](https://www.ellisys.com/products/ctr1/purchase.php),
[FAQ including its expanded answers](https://www.ellisys.com/products/ctr1/faq.php),
[downloads](https://www.ellisys.com/products/ctr1/download.php) and the
[brochure retained in M5P5](https://www.ellisys.com/products/download/ctr1_brochure.pdf).
The minimum order candidate is **CTR1-A-STD-DP**, Type-C Tracker Standard DP;
**CTR1-A-PRO** also includes DP. Standard HDMI/TB/TCPC editions do not become
DP-capable merely by having a USB-C connector. No current software build or
offered-unit firmware/license receipt was obtained; software download
instructions require a contact request, which was not submitted.

| W1 property | Classification | Source-backed scope / gap |
| --- | --- | --- |
| USB-C SBU/AUX and DP Alt Mode | VERIFIED_SUPPORTED | Technical page explicitly lists AUX over SBU and DP Alt Mode; correct DP/Pro edition required. |
| CC/PD and orientation observation | VERIFIED_SUPPORTED | PD 3.1/VDMs, CC/Vconn/SBU/Vbus measurements and automatic orientation detection are listed. Observing negotiation is not independently validating electrical transparency. |
| Passive high-speed pass-through | VERIFIED_SUPPORTED | Technical page and FAQ explicitly describe passive, nonintrusive gigabit-pair pass-through, typically up to 20 Gbit/s or better on most systems. This is a qualified typical claim, not a guarantee. |
| Current two-lane HBR3 plus USB3 concurrently | LIKELY_SUPPORTED | Passive pair pass-through makes it plausible; no exact dock/cable/orientation matrix, insertion-loss result or HBR3-plus-USB3 acceptance test was obtained. |
| Connector arrangement | VERIFIED_SUPPORTED | Two USB-C test receptacles plus separate control USB-C port. Brochure describes a supplied analysis cable for routing. This may fit a captive dock plug better than a plug-to-plug Y-cable, but exact assembly and cable part number still need confirmation. |
| Offered cable PN, VBUS/PD rating and nonparticipation | UNRESOLVED | Technical page voltage measurement ranges are not through-current ratings, power-off safety or proof of no PD policy engine. Require exact cable/assembly specification and reset defaults. |
| HPD over DP status/Attention | LIKELY_SUPPORTED | DP Alt Mode/VDM decoding can expose this context; named HPD/IRQ decode and preservation for the offered setup must be shown. No assumption of a native HPD wire at USB-C. |
| Bidirectional AUX/direction basis | UNRESOLVED | AUX capture is explicit; exact source/reply discrimination, turnaround ambiguity and direction metadata/export need a sample. |
| Raw AUX/sideband bytes | LIKELY_SUPPORTED | Brochure describes detailed raw views and multiple exports across protocols; no complete AUX-specific export or field contract inspected. |
| Native MST message decode/reassembly | UNRESOLVED | No explicit LINK_ADDRESS/REMOTE_DPCD/REMOTE_I2C/ALLOCATE_PAYLOAD coverage or CRC/fragment rules in these pages. AUX support alone is not proof of built-in MST decoding. |
| Timestamp information | VERIFIED_SUPPORTED | Technical page lists 5 ns timing resolution and timestamps printed with 1 ns precision. Precision is not resolution/accuracy; request AUX-specific timing/order semantics. |
| Buffer size/full-buffer behavior | UNRESOLVED | Real-time host upload is described; hardware buffer capacity, host-stall behavior and recovery contract not established. |
| Capture-loss/overflow indication | UNRESOLVED | Packet/error detection and USB filters are listed, but no AUX dropped-record/overflow marker contract is published here. |
| Long continuous lifecycle capture | LIKELY_SUPPORTED | Real-time upload implies a suitable operating model, not a demonstrated sustained AUX rate or guaranteed loss-free duration. |
| AUX export/API format | UNRESOLVED | FAQ's affirmative text/CSV/binary answer explicitly selects USB 2.0 Low Level Items. It must not be repurposed as AUX format proof. Remote automation API is listed, not its AUX export schema. |
| Main-link video/MTP decode | NOT_SUPPORTED | High-speed pairs are passed through rather than captured by this product's listed protocol engines. Not required by W1. |
| Controller platforms/viewing | VERIFIED_SUPPORTED | Technical page lists Windows 7 or later, Linux or macOS, free full-featured viewer and lifetime updates. Specific current build/platform support and license on an available unit still need a receipt. |

An Ellisys sample containing native AUX requests/replies, multi-fragment MST,
unknown/failed transactions and deliberate lab-side overrun evidence could
close the key data-quality gaps. Any sample-generating activity is the
provider's own separate lab work, not authorization to manipulate this Mac.

## Other Qualified Instruments

No instrument has yet met every W1 gate. This short table contains plausible
W1 candidates, not a list of already qualified available systems.

| Candidate | Current USB-C topology | AUX raw capture | MST decode | Loss indication | Export | Access practicality | W1 fit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DPA-400 2.1 065055 plus manufacturer-confirmed USB-C accessory | Unresolved cable PN/genders/PD/USB3 | Raw AUX display/report documented | Generic sideband documented; named/reassembly coverage needs sample | Unresolved | Binary/HTML; full-byte sample needed | Exact USA/Canada channel and online demo route; no loan terms yet | Leading dedicated candidate, not ready |
| Ellisys CTR1-A-STD-DP / PRO | Test receptacles/SBU support documented; assembly qualification open | Raw protocol views documented; AUX export not verified | Native MST reassembly unconfirmed | Unresolved | USB2 CSV/binary FAQ is not AUX specification | North America sales route; no available unit or terms confirmed | Credible alternative, partial |
| Teledyne LeCroy quantumdata M42de HBR3 00-00264 with Passive Probing 95-00222 and required capture licenses | Native-DP and USB-C passive operation documented; exact dock/USB3 cable setup still needs approval | AUX Channel Analyzer capture documented | MST negotiations/decode documented | W1 raw-export loss behavior unconfirmed | Saved ACA logs; exact lossless export/schema and offline license need sample | Staffed lab or evaluation access preferred; no Canadian unit located | Could satisfy W1 in passive mode, excess main-link capability not a purchase justification |

The [current M42de page](https://www.teledynelecroy.com/protocolanalyzer/quantumdata-m42de.aspx)
still explicitly separates T.A.P.4 passive monitoring from reference-source/sink
emulation. The [retained datasheet](https://www.teledynelecroy.com/files/pdf/quantumdata-m42de-datasheet.pdf)
identifies passive option 95-00222; source/capture option 95-00226 must be checked
for the offered configuration. Do not substitute the analyzer's own AUX reads,
EDID editing, link-training controls or automated CTS for passive observation.

The [current UCD-500 Gen3 page](https://www.unigraf.fi/product/displayport-2-video-generator-analyzer-ucd-500/)
was rechecked, but its "Link Analyzer (Monitor)" label and reference-device
functions still do not establish the needed nonparticipating assembly and
loss/export contract. It is not retained as a qualified W1 route unless its
provider supplies that evidence. No broader product catalogue, PD-only
instrument, DIY tap or renewed Apple static analysis is pursued.

## Manufacturer Access

| Route | Verified public contact/access fact | Not established |
| --- | --- | --- |
| Unigraf USA and Canada | [Official reseller directory](https://www.unigraf.fi/reseller/) lists Ellisys Corporation, Gilbert, Arizona, for USA & Canada; sales.usa@unigraf.fi, +1 480 339 7170 ext. 106 | A Canadian inventory location, loaner/evaluation terms, local demo unit, rental price or availability |
| Unigraf applications-engineer/online demo | [Online demo page](https://www.unigraf.fi/book-a-demo/) offers a scheduled remote demonstration, typically via Teams; DPA-400 product page links it. [Contact form](https://www.unigraf.fi/contact-us/) routes technical/product questions | A demo is not a loan, a Mac trace, or a guarantee of analysis using customer-supplied hardware |
| Ellisys North America | [Official sales network](https://www.ellisys.com/sales/distributors.php): sales.usa@ellisys.com, +1 480 339 7170, Gilbert, Arizona | Standard DP stock, Canadian evaluation shipment, supported exact cable or discounted one-off service |
| Teledyne LeCroy | Current M42de product page provides demo/contact/quote routes | Passive-option inventory, Canada loan/rental and the complete W1 assembly/export license |

Start with one Unigraf USA/Canada inquiry. Unigraf's listed regional organization
is also Ellisys Corporation, so ask that contact for the appropriate alternative
referral instead of sending duplicate requests to several offices. Request a
sample export and written topology/loss answers before arranging shipment or
lab time. Ask explicitly about a Canadian evaluation unit, distributor demo,
remote-assisted measurement with a physical customer setup, and Canadian labs
already using the equipment. No published loan entitlement or response time
was found, and no correspondence or web form was sent.

## University Access

**Smallest sensible contact:**
**sse.technical.services@ucalgary.ca**, published on the
[Schulich Technical Services team page](https://schulich.ucalgary.ca/research/labs-and-tech-support/technical-services-team).
It identifies a Manager of Technical Services and an Undergraduate Laboratory
Manager, so a single request to the team can be routed to the equipment owner.
Do not individually contact the faculty list, department head, research chairs
and makerspace staff. If that team redirects the enquiry, the
[ESE office](https://schulich.ucalgary.ca/electrical-software/contacts),
ese@ucalgary.ca, is a documented fallback, not a second simultaneous mailing.

| UCalgary lead | Verified relevant public evidence | What is not established |
| --- | --- | --- |
| Electrical and Software Engineering research facilities | [Official directory](https://schulich.ucalgary.ca/electrical-software/research/research-facilities) lists Embedded System Research Laboratory, Analog Electronics Research Laboratory, Fully integrated Systems and Hardware Laboratory, RF labs and Microsystems Hub | No DPA-400, CTR1, DP/USB-C AUX analyzer or suitable export/fixture inventory was identified. A lab name is not instrument ownership or visitor permission. |
| Schulich Technical Services | Public team/contact page provides a central technical-support mailbox and lab-management roles | Whether they own, can borrow or know the custodian of a suitable protocol analyzer; individual/student/external access, supervision, cost and schedule |
| Microsystems Hub, Calgary | [Official page](https://schulich.ucalgary.ca/research/labs-and-tech-support/microsystems-hub) describes open-access micro/nanofabrication and characterization for academic/industry clients and low-volume R&D | Open access does not imply DP capture capability. No suitable DP protocol analyzer/fixture is established; fabrication equipment is not a reason to design a tap here. |
| Research/industry referral | [Schulich Research and Innovation team](https://schulich.ucalgary.ca/research/meet-research-and-innovation-team) offers a business-development route | Not needed for the initial inventory question; no partnership, eligibility or free access assumed |

No public source reviewed establishes a UCalgary DisplayPort analyzer. This is
a bounded public-inventory result, not a claim that none exists behind lab
doors. Ask the technical team for an already-owned or borrowable complete
receive-only system and a supervised one-off session. University borrowing is
potentially cheapest if an existing suitable system and permission exist;
neither fact is confirmed. No accounts, room bookings or messages were created.

## Calgary / Canada Lab Access

The bounded search found **no confirmed Calgary/Alberta provider offering this
exact passive USB-C AUX/MST capture**. It did find local referral/rental
contacts and a North American lab with a published DPA-400 equipment claim.
All locations/capabilities below are scoped to the cited sources, not assumptions
that equipment can be moved between an organization's branches.

| Organization / location | Actual documented capability | Customer-owned hardware and one-off work | W1 conclusion / evidence |
| --- | --- | --- | --- |
| Schulich Technical Services and Microsystems Hub, Calgary | Electronics/research support route; open-access micro/nano prototyping and characterization at the Hub | Hub explicitly serves academia/industry; external Mac/dock testing and one-off AUX session unconfirmed | First local inventory enquiry only; university sources above. No analyzer ownership claim. |
| Testforce, Calgary/Edmonton contact coverage; service centre Pickering, Ontario | Test-and-measurement distribution, live product demos, rental/leasing through TRS-RenTelco; calibration/repair in Ontario | Customer instrument calibration/repair is documented, not testing a customer's Mac/dock. A staffed protocol-debug service is unconfirmed | [Contact page](https://www.testforce.com/contact/) lists Calgary +1 403 247 3725, Edmonton +1 780 328 0987, sales@testforce.com; [services](https://www.testforce.com/services/) and [rental/leasing](https://www.testforce.com/rental-leasing/). Ask only for an exact model/fixture referral or rental, not assume it is a DP test house. |
| Fidus Systems, Ottawa and Kitchener-Waterloo, Ontario | [Signal/power-integrity services](https://fidus.com/services/signal-power-integrity/) include high-speed system analysis, characterization and multi-channel oscilloscopes to 40 GS/s | Customer engineering services are explicit; a one-off retail Mac/dock trace and suitable AUX decoder/fixture are not | Credible Canadian engineering referral, not a verified AUX capture provider. [Contact](https://fidus.com/contact/) requires capability/scope confirmation before cost discussion. |
| Granite River Labs, North American enquiry to Santa Clara, California | [DP service page](https://www.graniteriverlabs.com/en-us/displayport-standards-service) explicitly offers DP Alt Mode/HBR3/MST debugging for sources, sinks, adapters and hubs; its MST-equipment list names Unigraf DPA-400 | Client samples/debugging services are documented; a non-certification one-attach job on a customer Mac is subject to acceptance/quote | Strongest commercial lead. DPA-400 is a service-wide published equipment claim, not confirmed Santa Clara inventory or USB-C accessory ownership. [Current contact page](https://www.graniteriverlabs.com/en-us/contact): 3000 Lakeside Drive, Santa Clara, +1 408 406-5299; service page gives info@graniteriverlabs.com. |
| Allion, North American contact in San Diego, California | [Debug consulting](https://www.allion.com/issue_analysis_debugging_consulting_service/) explicitly covers electrical/protocol/interoperability issues and DP/PD | Customer problem reproduction and debugging are offered; one-off price, exact location of DP equipment and observer-only contract unconfirmed | Secondary referral if the closer/specific routes fail. [North America contact](https://www.allion.com/contact/): service@allion.com. No assumed DPA-400/CTR1 ownership. |

The [VESA ATC directory](https://vesa.org/displayport-developer/compliance/)
corroborates GRL/Allion DisplayPort testing, but it is not proof of every
facility's inventory or of non-certification access. GRL's own current contact
page gives a different Santa Clara address/phone from VESA's older directory;
use the provider's current contact route and confirm the actual work location.

Screened exclusions/limits: Element's
[Calgary laboratory](https://www.element.com/locations/the-americas/calgary)
advertises environmental/food analysis, not DP/USB-C work; it is not a W1 lead.
The ACAMP website could not be qualified because its TLS certificate failed
verification; no insecure bypass was used and no present capability/availability
is asserted. A general search returned unrelated retail-electronics results;
none were used. No computer-repair businesses, generic makerspaces or unrelated
RF instruments are substituted for a qualified protocol observation system.

## Rental and Used Market

| Channel / check | Result on 2026-09-18 | Consequence |
| --- | --- | --- |
| Testforce / TRS-RenTelco | Canadian live-demo and rental/leasing route is explicit. [DPA-400 site search](https://www.testforce.com/catalogsearch/result/?q=DPA-400) returned no result. A direct M42d catalogue-path check did not yield a usable listing. | Neither result establishes stock or market-wide absence. Ask the regional contact about 065055 plus corrected USB-C cable, CTR1-A-STD-DP, or a fully licensed passive M42de package. |
| CMC Microsystems Equipment Rentals, Canada | [Public catalogue](https://www.cmc.ca/equipment/) requires a Research Subscription and offers short-term access to a high-value equipment pool; subscriber pricing/application are separate. It lists scopes and probes but no named DPA-400/CTR1/M42de in the inspected catalogue. | Useful institutional referral if UCalgary has eligibility, not a ready AUX observer. Do not rent a scope/probe and improvise electrical access. No subscription or rental application submitted. |
| Electro Rent, North America | [Rental](https://www.electrorent.com/us/services/rent-test-equipment) and [certified pre-owned](https://www.electrorent.com/us/services/buy-used-test-equipment) channels are active; prices/stock/options are configuration-dependent | No matching complete DPA-400, Ellisys DP or passive quantumdata lot/rental was verified. Prices for unrelated scopes/RF instruments are excluded from this cost model. Canada shipment/terms need confirmation. |
| Used Unigraf DPA-400 | [Canadian marketplace query](https://www.ebay.ca/sch/i.html?_nkw=Unigraf%20DPA-400) was blocked with HTTP 403 | No `USED_LISTING_PRICE` or available unit established; ask manufacturer about a supported ex-demo/refurbished unit only after topology/export qualification. |
| Used Ellisys CTR1 | [Canadian marketplace query](https://www.ebay.ca/sch/i.html?_nkw=Ellisys%20CTR1) was blocked with HTTP 403 | No priced/available DP-licensed unit verified. The edition/license matters; another CTR1 edition is not automatically suitable. |
| Used quantumdata M42de | [Canadian marketplace query](https://www.ebay.ca/sch/i.html?_nkw=quantumdata%20M42de) was blocked with HTTP 403 | No priced/available passive configuration verified. A generator-only chassis, HDMI instrument or older model is not a substitute for the required DP options. |

Search/retrieval limits are explicit, not a claim that the used market is empty.
No numerical price band can responsibly be derived from these results.
A future rental/used quote must itemize the exact analyzer, firmware/software,
transferable or temporary licenses, controller, original supported cable/fixture,
viewer/export rights, calibration/functional evidence, delivery/return terms
and Canadian shipping/taxes/insurance. Require a representative export and
right to reject a nonfunctional/incomplete package before financial approval.
"Powers on" and an inexpensive chassis without its cable/license are insufficient.

## Cost Model

No acceptable complete W1 system has a `PUBLIC_PRICE_VERIFIED` or
`USED_LISTING_PRICE` in this survey. New equipment and services are
`QUOTE_REQUIRED`; no quotation has been requested or received. DPA-400 web
metadata contains a zero-price placeholder while the visible page requires a
quote: it is not a free analyzer. CMC subscriber pricing is not public pricing.

| Preference | Cost class / condition | Practical next check |
| --- | --- | --- |
| 1. Existing institutional lab | Potentially no incremental equipment charge, but not a verified free offer | One UCalgary inventory/permission enquiry; include staff time/visitor rules and fixture availability |
| 2. Manufacturer demo/loan | QUOTE_REQUIRED for any loan, shipping, deposit or assistance; online-demo route documented but price not stated | Unigraf regional applications engineer resolves cable/export/loss and supplies a sample before hardware arrangements |
| 3. Inexpensive staffed capture | QUOTE_REQUIRED; no hourly/session estimate invented | GRL one-attach passive AUX scope, not certification; include setup, operator, export and analysis time |
| 4. Rental / short lease | QUOTE_REQUIRED, inventory/options unconfirmed | Testforce Calgary/Edmonton or Electro Rent checks a complete supported package, minimum term and landed Canadian cost |
| 5. Used purchase | No verified priced lot; do not extrapolate from other instruments | Supported license/cable plus return rights must make the whole package useful |
| 6. New purchase | QUOTE_REQUIRED; no compelling cost/access case | Last resort after temporary routes fail and every mandatory qualification gate closes |

Compare **total experiment cost**, not chassis price: equipment/access charge,
cables/fixtures/licenses, controller/operator time, shipping/customs/tax,
insurance/deposit exposure, and required analysis/export support. Separately
compare response time, earliest available session and failure/rework risk.
No dollar amounts, turnaround promises or cheap-native-DP claim are fabricated.
An already-owned qualified system can beat a nominally cheaper purchase.

## Native-DP Fallback

`ACCESS_PATH_DEPENDS_ON_AVAILABLE_EQUIPMENT`.

```text
Future approved fallback only:
base M5 USB-C
  -> native DisplayPort Alt Mode adapter
  -> native DP AUX observation/bypass fixture
  -> genuine native-DP MST branch
         -> sink A
         -> sink B
```

**Adapter requirements:** the M5 supplies native DisplayPort through Alt Mode;
no DisplayLink, USB graphics driver/rendering device, additional Thunderbolt
tunnel or HDMI-to-DP conversion. Prefer documented DP 1.4/HBR3 and MST/AUX
pass-through, unmodified downstream EDID/DPCD, preserved HPD IRQ and known
retimer/redriver/mux behavior. The PD negotiation electronics do not have to
be absent, but an undocumented active conversion path is unacceptable. A
four-lane-only adapter changes the baseline's two-lane/USB3 capacity and must
be treated as a different controlled condition, not secretly forced to match.

**Branch requirements:** genuine DP MST with at least two downstream outputs,
preferably native DP, no USB graphics. Obtain vendor/chipset and firmware
identification where documented; do not infer a branch chipset from USB hub
VID/PID. Require known MST discovery/resource behavior and adequate bandwidth
for the intended unchanged monitor modes. Actual monitor variants/connectors
must be checked against documentation before choosing downstream cables.
Prefer existing lab-owned adapters/branches and their known interoperability
records. No consumer SKU, purchase or kit construction is selected now.

Use the approved native-DP fixture/bypass for the chosen analyzer; an instrument
with DP sockets is not automatically HBR3-transparent. For DPA-400, direct
main-link electronics remain excluded. The fallback removes USB-C fixture
complexity at the observation point, but still depends on the M5's Alt Mode
adapter negotiation upstream. It may select a different internal route; no
same-DCP binding was established by M5P5.

| Comparison | A: current ZMUIPNG with USB-C observer | B: native-DP fallback |
| --- | --- | --- |
| Analyzer availability | Dedicated DPA/CTR1 candidates and a documented regional enquiry; exact assembly not confirmed | May be easier if a lab already has native-DP AUX equipment and a branch; none secured |
| Added equipment/cost | Correct USB-C observation accessory, controller and possibly official mating fixture | Alt Mode adapter, native DP fixture/cables and MST branch, possibly new sink cabling; not automatically cheaper |
| Signal/negotiation complexity | Must preserve CC/PD, orientation, SBU and DP/USB3 coexistence | Native observation is simpler, but adapter lane allocation/HPD and branch compatibility still matter |
| Scientific value | Directly tests what the existing branch presents and what the M5 requests in this setup | Tests a controlled ordinary-MST source case; changes branch firmware, lane sharing and possibly HDMI conversion |
| Historical-count relevance | Best path for current-hub presentation, still no retroactive software-counter binding | Cannot reproduce or explain the original hub's count semantics by itself |
| Cost/decision trigger | Prefer when a qualified loan or inexpensive staffed session is available | Prefer only if a complete qualified native setup is already accessible or materially cheaper, and the narrower scientific scope is accepted |

Neither availability nor total-cost evidence currently ranks A or B absolutely.
Do not buy the fallback kit merely because consumer adapters are inexpensive.
First learn what the university/provider can supply; preserve current-hub
analysis as the preferred scientific question when costs/access are comparable.

## Export Compatibility

No leading analyzer's full public file-format specification or real sample was
obtained. **No import adapter, stub, electrical collector or decoder was
implemented.** Documented human-readable output is not permission to invent
column names or reverse a proprietary binary layout by guesswork.

| Candidate | Known exports | Evidence needed before implementation |
| --- | --- | --- |
| DPA-400 | GUI-readable binary and HTML containing transaction lines/message details, with a raw HEX Dump example. Manual screenshot has CSV-related controls without a column specification. | One original binary plus full-range unfiltered HTML (and CSV if supported by 2.1.10); format/build versions, count/byte conservation, unknown and failed sideband fragments, timestamp units, direction basis and explicit loss markers. No assumption of a JSON API or public binary schema. |
| Ellisys Std DP | Brochure says raw views and multiple export formats; FAQ specifies text/CSV/binary only for USB 2.0 Low Level Items; original trace/viewer and remote API described generally. | Exact AUX export menu/format and sample, all request/reply bytes, per-record direction/timing, buffer/drop markers and whether MST decode is present. An .NET/API name or USB payload sample does not establish AUX fields. |
| M42de passive configuration | AUX Channel Analyzer logs can be saved for offline analysis; UI provides decoded transactions. | Native ACA file plus any lossless interchange export, software/license/viewer requirements, raw AUX/sideband byte coverage and capture-loss semantics. An image/video log is not the AUX dataset. |

### Offline Sample Acceptance

Ask the provider for an existing shareable example, preferably two downstream
MST paths, **not** a newly authorized experiment on this Mac. Hash the original
files before normalization; retain format/version and licensing/provenance.
Require a description of expected message/byte counts and any deliberate
negative cases. Do not execute scripts embedded in HTML exports.

Normalize to the independent M5P5 wire namespace, not the DCP ownership schema:

| Normalized field | Required rule |
| --- | --- |
| `timestamp` | Preserve original ticks/unit, precision/resolution, ordering index, wrap and clock provenance. Equal timestamps do not imply one event. |
| `direction` | Source-to-branch, branch-to-source or unknown, plus connector/heuristic basis. Do not infer solely from proximity. |
| `aux_type`, `address`, `request`, `reply` | Preserve native/I2C address space, opcode/MOT, requested/transferred lengths and separate native/I2C response bits. Unknown is not ACK. |
| `raw_bytes` | Original request/reply/fragment bytes or exact immutable export reference. Unknown fields stay raw with null decoded fields and a reason. |
| `sideband_message_type`, `rad`, `port` | Only after complete request/reply reassembly, route/generation, length and CRC qualification; preserve all contributing AUX records. |
| `payload_id`, `pbn`, `slot_count` | Distinguish requested versus accepted allocation, start slot, removals, resets and simultaneously retained IDs. No source-identity inference. |
| `loss_state` | Explicit zero/nonzero/unknown with buffer/drop/truncation/filter evidence. Missing loss metadata is unknown, never zero. |
| `decoder`, `decoder_version` | Vendor parser and later adapter version, field basis and untouched source/export hashes; no invented provenance. |

Acceptance cases: native and I2C read/write/reply, ACK/NACK/DEFER/retry,
fragmented LINK_ADDRESS, remote EDID offset/segment and DPCD, resource/PBN
allocation, slot-table update and ACT status; unknown message, partial/CRC-bad
fragment, missing reply, sequential versus concurrent ID reuse, startup/reset,
late capture, clock tie/wrap and documented overrun. A sample need not be an
M5 trace to test import fidelity. Synthetic later fixtures must remain labeled
synthetic. Approval of an importer does not approve hardware insertion.

## W1 Procedure

**NOT AUTHORIZED TO RUN IN M5P6.** The current hub remains connected. The
following begins only after `AUX_ACCESS_READY` is supported by receipts **and**
the owner separately approves the exact one-attach experiment on the identified
machine. Access readiness is not daily-use-machine safety approval.

Before the numbered lifecycle, a qualified operator and owner must approve:
exact analyzer/firmware/software/license/controller/cable/fixture diagram;
connector genders/orientation, PD/USB3/HBR3 limits and non-injecting mode;
known capture-loss behavior; and a plan for stopping safely. Use a separate
lab controller, not new analyzer drivers on the daily-use M5. No external
trigger/GPIO connection, fabricated AUX transaction, reference sink, emulation,
HPD drive, EDID change or forced link training is allowed.

The approved initial state is **hub disconnected from the Mac**. Arrange the
manufacturer-approved fixture and dock-side connections while the upstream
Mac link is absent; leave the Mac-facing leg disconnected until step 3.
Keep both monitors and their normal settings fixed. Any required power/cabling
change must have been specified in that separate approval, not improvised.
Record the actual future OS/build/topology; the September 16 snapshots remain
historical, not a claim that the environment is still identical.

1. **Begin capture on the lab controller.** Capture raw native/I2C AUX and all
    sideband-buffer traffic, plus available PD/HPD context. Disable capture
    filters/truncation; record the configuration. Use immediate/manual start
    rather than relying on a potentially missing HPD trigger.
2. **Verify armed/running state before attach.** Retain the instrument status,
    start marker, clock, buffer/loss counters and operator timestamp. Do not
    generate traffic to test arming on the M5. The provider's prior sample/bench
    qualification establishes that the chosen settings retain early traffic.
3. **Connect the hub once.** Complete the one approved upstream connection to
    the same M5 port via the already arranged fixture. Record this physical
    action and orientation. Do not connect a second output/tunnel or cycle power.
4. **Observe normal macOS behavior.** Make no resolution, refresh, mirroring,
    EDID, power/lid/sleep or software display-control change; issue no AUX/DPCD
    command or private/native probe. Only normal macOS-generated transactions
    are observed. Note any unexpected PD/reset/retraining behavior.
5. **Allow mirrored displays to settle.** Proposed bounded observation is
    through stable normal behavior plus 10 seconds, with an overall 180-second
    post-attach cap, subject to the provider confirming that buffer/streaming
    capacity safely covers it. These are experiment bounds, not vendor limits.
    If the link never settles or data is lost, stop at the cap/abort condition;
    do not retry the attach. Record what actually happened.
6. **Stop capture.** Preserve stop reason, final loss/buffer counters, original
    record count and any remaining download state. Drain/export according to
    the qualified vendor procedure without restarting acquisition. DPA-400's
    restart clears stored data. No second attach or exploratory UI action.
7. **Hash raw capture before analysis.** Preserve the original native file and
    all lossless exports, software/configuration receipt and operator log; hash
    exact bytes with SHA-256 on the lab/offline system. Keep raw EDIDs and other
    potentially identifying fields private; any publication is a separate
    redaction/release decision. Original bytes are never overwritten.
8. **Decode offline.** Validate hashes and coverage, then apply W1.1-W1.8 in
    order. Keep unresolved/unknown results. Do not feed analyzer output back
    into a hardware control path or upgrade synthetic evidence to real.

Abort conditions include unqualified fixture behavior, unexpected PD role/power
changes, source/sink emulation, injected transactions, display instability,
capture overflow, absent arming proof or ambiguous direction. A failed capture
is a preserved result, not permission for another cable cycle. Any physical
removal/recovery is owner-controlled under the preapproved stop plan. A quiet
or cached lifecycle can remain inconclusive despite an electrically sound rig.

## W1 Analysis Gates

First validate evidence integrity: intended upstream point, one generation,
source/reply direction, armed-before-attach coverage, no unknown loss/filtering,
complete requests/replies, length/CRC checks and immutable exports. Then answer
the gates in this **exact order**. Each result cites raw records and reports
observed, not observed within the qualified interval, or inconclusive. No W1
gate has been executed in M5P6.

### Gate W1.1

**Did macOS enable MST?** Record `DP_MSTM_CAP` read/reply separately from
`MSTM_CTRL`/`DP_MST_EN` write and acceptance or state read. Sideband traffic and
advertised capability alone do not establish enabled MST mode. Record the
presence, direction and complete reassembly of sideband traffic here too.

### Gate W1.2

**What did LINK_ADDRESS report?** Bind each complete reply to its request/RAD,
generation and branch GUID. Preserve nports and all descriptors, not only a
GUI summary or aggregate sink count. No response is not a zero-port reply.

### Gate W1.3

**How many downstream ports had peers/devices?** Separate input/output,
physical/logical/internal ports, peer type, MCS, DP/legacy presence and
descendant branches. Distinct port paths are not necessarily physical panels
or independent source streams. Include CONNECTION_STATUS_NOTIFY and equivalent
observed HPD/IRQ/status transitions without guessing their software meaning.

### Gate W1.4

**Which paths received remote DPCD/EDID traffic?** Report attempted and
successful remote accesses separately, with port/RAD/address/length, EDID
offset/segment/data and checksum/coverage. Same EDID bytes can occur on two
paths; missing reads can reflect caching. Retain failures, retries and PHY
power/lifecycle messages if naturally present.

### Gate W1.5

**How many payload IDs did macOS allocate?** Include ENUM_PATH_RESOURCES
request/reply full/available PBN first, then ALLOCATE_PAYLOAD/QUERY_PAYLOAD
and replies. Distinguish attempted IDs from accepted nonzero concurrently
retained VCPIs. Account for removal, clear/reset, reused IDs and NAKs.

### Gate W1.6

**What PBN/slot values were requested?** Preserve requested/accepted PBN and
the local payload ID/start/count writes, actual rate/lane/coding context and
table epochs. Zero-count removal/reset is not an additional stream. Never
equate an Apple software link-rate enum with a wire DPCD code.

### Gate W1.7

**Was ACT/payload-table completion observed?** Match table writes, updated
status and receiver ACT-handled status to the current update epoch. A stale
set bit or missing earlier reset is insufficient. AUX reports the receiver's
control state; it does not capture the ACT packet or prove transmitted video.

### Gate W1.8

**Can protocol topology explain M5P4 `newCount=2` versus M5P3 `SinkCount=1`?**
Compare branch-presented paths, observed DPCD `SINK_COUNT`/ESI values, EDID
routes and notifications with separately scoped software observations. Consider
scope, conversion/internal ports, sampling-time and cache hypotheses. A future
notification cannot be claimed to be the historical September 16 event; raw
numeric equality does not bind either software counter to a DPCD field.
"Still unresolved" is valid even after a successful new capture. Do not
request another log cycle or private probe to force an answer.

Only after all eight answers and their limits are recorded may a later decision
consider main-link capture. Two qualified accepted allocations/current ACT
status make actual VC transmission a useful next question. One allocation,
explicit NAK, no enabled MST, or a branch exposing one path instead directs
attention to the last observed control step. Incomplete/lost AUX data is not
automatically a reason to buy a full main-link analyzer. Internal M5 source
ownership remains a separate unproved contract.

## Access Readiness

`AUX_ACCESS_NOT_READY`.

| Mandatory readiness receipt | Current state |
| --- | --- |
| Specific available analyzer, unit/version/license | Candidate models documented; no offered/bookable unit receipt |
| Exact original cable/fixture and supported topology | DPA-400 546109/546127 conflict and mating/electrical details unresolved; Ellisys fixture details incomplete |
| Current USB-C dock compatibility | No confirmed two-lane HBR3/USB3/CC/PD/orientation/power-off assembly evidence |
| Raw/lossless export | Documented output features, no accepted complete sample/format contract |
| MST sideband observability | DPA-400 category support explicit; complete named-message/raw-fragment coverage not yet accepted |
| Buffer/rate/loss/overflow contract | Some documented limits, but no explicit zero-loss/overrun receipt for any available configuration |
| Actual access path and terms | Named regional contacts and lab leads, no confirmed dates, permission, price or loan terms |
| No speculative electrical work | No supported final assembly yet; DIY/couplers/probing remain excluded |

Define `AUX_ACCESS_READY` only when **all** rows are satisfied for one specific
available configuration, with a provider's dated written answers, cable diagram,
sample/export acceptance and access terms. `LIKELY_SUPPORTED`, catalogue
presence or a model in a general lab equipment list cannot pass a missing row.
Even readiness would require a separate owner-approved W1 physical/safety gate.

## Recommendation

`TEMPORARY_DPA400_ACCESS_FIRST`.

This prioritizes a **qualification and temporary-access request**, not a claim
that a unit is already available. DPA-400 remains the narrowest documented
AUX/MST instrument, now with a precise current product number, a known cable
conflict to resolve, a listed USA/Canada contact, and a commercial lab that
explicitly names it. A full DP analyzer or a new fallback kit is not required
before these inexpensive enquiries.

Recommended sequence, with no messages sent by the assistant:

1. Ask UCalgary Technical Services once whether an existing qualified system
    can be used under supervision. This preserves the free-existing-access
    preference without assuming affiliation or permission.
2. Request Unigraf applications-engineer answers and a sample through its
    USA/Canada channel. Ask for evaluation/loan/demo or a Canadian owner referral;
    do not accept a sales quote as technical qualification. This can proceed
    while the local inventory enquiry is pending.
3. If needed, ask GRL for the smallest staffed passive AUX session using its
    documented DPA-400 route, exact work location and supported USB-C fixture.
    No certification membership or automated compliance campaign is needed for
    the requested scope; whether GRL accepts that scope must be confirmed.
4. Use Ellisys Std DP as the alternative if its exact fixture/raw/loss answers
    are stronger or temporary access is cheaper/faster. Ask the shared regional
    organization for routing to avoid duplicate outreach.
5. Only then check a complete Canadian rental package via Testforce; choose
    native DP only if equipment actually available makes it the better controlled
    experiment. Do not move to used/new purchase without a new decision.

The next decisive deliverable is a vendor/lab reply plus raw example file and
assembly/access receipt, **not more theoretical AUX research**. If a provider
cannot disclose raw bytes, loss status or a supported cable path, reject that
offer for W1 and use the next route. The existing setup stays untouched while
these nonphysical gates are resolved.

## Purchase Gate

`DO_NOT_PURCHASE_ANALYZER_YET`.

Mandatory topology/data-quality gates are open, no current complete price is
verified, and temporary institutional/manufacturer/lab routes have not been
ruled out. No unusually compelling purchase case exists. Do not buy a cable,
adapter/hub kit, used chassis, license or analyzer on likely support. No
purchase, paid reservation, shipping commitment or financial obligation made.

## User Action

`USER_OUTREACH_REQUIRED`.

The user must personally send the prepared technical enquiry/requests and
return responses or permitted sample files. No explicitly authorized sending
connector/action was supplied, and no email, message, contact form, demo
request or rental application was sent/submitted. Outreach is not approval
to unplug, insert an analyzer, ship the Mac or run W1. The companion contact
package, [ready-to-send drafts](m5-aux-access-contact-package.md), contains
separate Unigraf, Ellisys, UCalgary and commercial-lab drafts;
use the staged routing above, not a bulk mailing.

## Hardware State

`KEEP_CURRENT_HUB_CONNECTED`. Preserve the hub and both monitors exactly as they
are. No unplug/replug, analyzer insertion, signal capture, probe, AUX/DPCD
command, display setting change, private selector or native display-probe run.

`RETIRED_ON_DAILY_USE_M5`, `NOT_READY_FOR_DPCD_TEST`,
`OFFLINE_OBSERVER_PIPELINE_READY`, `STATIC_PACKETIZER_ANALYSIS_FROZEN`, and
`NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED` remain unchanged.
No m1n1 sibling access or firmware/boot/security change is authorized.

### Source Provenance

All current web checks were performed on 2026-09-18. The following 19 receipts
are unmodified HTTP response bodies retained locally under
[artifacts/probes/m5p6/sources](../../artifacts/probes/m5p6/sources), not
republished manufacturer documents. Hashes are SHA-256 of exact downloaded
bytes. Catalogue pages have no immutable upstream revision; their retrieval
date and hash bind this research. The two PDFs match the preserved M5P5
receipts. PDF text and illustrations were read, including the bypass diagram
and report hex dump; figures are not a mechanical/electrical specification.

| Local receipt | Public source | SHA-256 |
| --- | --- | --- |
| [unigraf-dpa400.html](../../artifacts/probes/m5p6/sources/unigraf-dpa400.html) | [D1 product/options](https://www.unigraf.fi/product/dpa-400-displayport-aux-channel-monitor/) | `227fd6ffdcb8b46d3a420477ca3e1751da6f8d65f1e505753ef29f89d0d9bc82` |
| [unigraf-downloads.html](../../artifacts/probes/m5p6/sources/unigraf-downloads.html) | [D2 current download table](https://www.unigraf.fi/downloads/) | `6e6073f1fb1a5ab43f0516659f2390b3473acd8a43b5c22dd0f375a8af3c4474` |
| [unigraf-documents.html](../../artifacts/probes/m5p6/sources/unigraf-documents.html) | [Manual catalogue](https://www.unigraf.fi/documents/) | `f2d31e337496d835d405cd9bb73d0e9c0e32a8b37f09d178ccf304c421b72ec5` |
| [dpa400-manual.pdf](../../artifacts/probes/m5p6/sources/dpa400-manual.pdf) | [D3 v13, 2023-09-06](https://www.unigraf.fi/app/uploads/2023/04/DP-2.1-AUX-Channel-Monitor-User-Manual.pdf) | `37287d0b9aae563141c47a0149f6275e1da3a3903f28a4a939108ed505ac5ad3` |
| [dpa400-datasheet.pdf](../../artifacts/probes/m5p6/sources/dpa400-datasheet.pdf) | [D4 January 2023](https://www.unigraf.fi/app/uploads/2020/02/DPA-400-Data-Sheet-01-2023.pdf) | `1e387336077159e1bac20e5125bbf6857bad1aeacc2f0fb38156939862dd285e` |
| [ellisys-technical.html](../../artifacts/probes/m5p6/sources/ellisys-technical.html) | [Tracker technical data](https://www.ellisys.com/products/ctr1/technical.php) | `36d975d20f95d898e3a1951269460f5b82d7f8ed1001a2d5e6b217b46afd13b9` |
| [ellisys-purchase.html](../../artifacts/probes/m5p6/sources/ellisys-purchase.html) | [Tracker editions](https://www.ellisys.com/products/ctr1/purchase.php) | `bf6cd263afa9017f77a08b9b17704ecdc89dd48f7a8c7b282b323bbdcc5adf9e` |
| [ellisys-faq.html](../../artifacts/probes/m5p6/sources/ellisys-faq.html) | [Tracker FAQ](https://www.ellisys.com/products/ctr1/faq.php) | `5022dc5626d980dae95fbae8ef7fb9ab86d05c5c96fb1414c9538b27f427cef6` |
| [ellisys-download.html](../../artifacts/probes/m5p6/sources/ellisys-download.html) | [Tracker download request](https://www.ellisys.com/products/ctr1/download.php) | `a291130bc568a0b801b06c724bff824e52f2dd7c42db0c733509eb4e16488480` |
| [ellisys-sales.html](../../artifacts/probes/m5p6/sources/ellisys-sales.html) | [Regional sales](https://www.ellisys.com/sales/distributors.php) | `4952fec49b98cad961f6cc4d871fa64713ea7a8775d243e0359a84290797e45c` |
| [unigraf-resellers.html](../../artifacts/probes/m5p6/sources/unigraf-resellers.html) | [USA/Canada route](https://www.unigraf.fi/reseller/) | `5b968042a43a08943bdce04c6084cdcef9bd591f6e488bb4093e0e1c133c033f` |
| [unigraf-demo.html](../../artifacts/probes/m5p6/sources/unigraf-demo.html) | [Online demo route](https://www.unigraf.fi/book-a-demo/) | `e69b7fcbea5318e4876e93b728458ee3f98c8eb745335f7102dc71ed7ddd2527` |
| [ucalgary-ese-contacts.html](../../artifacts/probes/m5p6/sources/ucalgary-ese-contacts.html) | [ESE contact](https://schulich.ucalgary.ca/electrical-software/contacts) | `b29b54196487a79c548041a37ee9d1fcecd300c59f813befdb69da35482f8084` |
| [ucalgary-ese-facilities.html](../../artifacts/probes/m5p6/sources/ucalgary-ese-facilities.html) | [ESE facility list](https://schulich.ucalgary.ca/electrical-software/research/research-facilities) | `0c0946427005f1e6e96fba290ca406d5fe8e82aa1ddcfac2f440e4f2ec6eeacf` |
| [ucalgary-technical-team.html](../../artifacts/probes/m5p6/sources/ucalgary-technical-team.html) | [Technical Services team](https://schulich.ucalgary.ca/research/labs-and-tech-support/technical-services-team) | `25eed450de0558ba144e11481974e8905a7b159222e3010e607fc227ac26360c` |
| [ucalgary-microsystems.html](../../artifacts/probes/m5p6/sources/ucalgary-microsystems.html) | [Microsystems Hub](https://schulich.ucalgary.ca/research/labs-and-tech-support/microsystems-hub) | `24d78861a4ba332f4efa88d992ae69f318b5a4ed34ea2d482b1ab659bf1cefb2` |
| [cmc-equipment.html](../../artifacts/probes/m5p6/sources/cmc-equipment.html) | [CMC rental catalogue](https://www.cmc.ca/equipment/) | `fc882f2c0258f4d16f066a429fab03cad4a3a99b8eda0a7c10a2be7c004375a8` |
| [vesa-test-centres.html](../../artifacts/probes/m5p6/sources/vesa-test-centres.html) | [VESA ATC directory](https://vesa.org/displayport-developer/compliance/) | `29cc704483f60ff4a5aa05d695493e2a2d006e8e8ea2b815206ae9bfa64cef32` |
| [grl-displayport.html](../../artifacts/probes/m5p6/sources/grl-displayport.html) | [GRL DP service/equipment](https://www.graniteriverlabs.com/en-us/displayport-standards-service) | `a6c2d5f33ff190c47fe00bcd9f6b85cc707d7530b4230b5e7c66182fea544d65` |

Other cited provider/service pages were inspected with webpage tools on the
same date; they are not given invented byte hashes. Testforce was readable
through the webpage tool but a separate byte-retention request returned 403.
ACAMP TLS failure, blocked marketplace searches and unusable catalogue paths
are recorded research limits, not proof of unsupported hardware or no stock.
No installer, private source, login or vendor-provided capture was acquired.

### Verification

Required preservation commands, run without native display executables:

```sh
cmake --build build-m5p4-offline
ctest --test-dir build-m5p4-offline -L offline --output-on-failure
```

The existing 200 offline tests pass across four CTests. Focused documentation
checks cover the exact 21 sections, 13 frozen requirements, 39 DPA-400 and
17 Ellisys status rows, eight ordered W1 gates, one eight-step future lifecycle,
four unsent drafts, 13 Unigraf questions and all four primary-source recipient
addresses. Local links/anchors and retained receipt hashes are checked;
external retrieval failures remain disclosed rather than marked valid.

The exact M5P5 two-commit audit and 13 prior receipts/Linux pin passed before
publication. Historical runtime captures/review and safety markers remain
unchanged. There are zero M5P6 wire captures, hardware probes or new
real-evidence ownership gate passes. No importer was implemented or tested;
vendor firmware, fixture transparency, actual access, price and W1 hardware
function remain unverified. Document validation and the existing build/tests
establish preservation, not electrical safety or MST functionality.