# M5P6 AUX Access Contact Package

Prepared 2026-09-18. **UNSENT.** These are user-controlled outreach drafts, not
sent messages, reservations, purchase requests or hardware-experiment approval.
The current hub and both monitors must remain connected and unchanged.
Technical findings and acceptance gates are in the
[qualification report](m5-aux-access.md).

## Routing

Start with one UCalgary inventory enquiry and one Unigraf regional technical
enquiry. Use Ellisys as a conditional alternative and GRL for a staffed-session
quote when needed. Do not mail every listed person or office. Unigraf's listed
USA/Canada representative is Ellisys Corporation, so ask that office to route
the alternative internally before sending a duplicate request.

| Draft | Public contact | Source / limitation |
| --- | --- | --- |
| Unigraf | sales.usa@unigraf.fi, attention DPA-400 applications engineering | [Official USA/Canada channel](https://www.unigraf.fi/reseller/); loan availability is not established |
| Ellisys | sales.usa@ellisys.com, attention Type-C Tracker applications engineering | [North America sales network](https://www.ellisys.com/sales/distributors.php); use only if the Unigraf contact has not already routed the request |
| UCalgary | sse.technical.services@ucalgary.ca | [Schulich Technical Services](https://schulich.ucalgary.ca/research/labs-and-tech-support/technical-services-team); no analyzer inventory or external access assumed |
| Commercial lab: GRL | info@graniteriverlabs.com, attention North American DP/USB-C debug team | [DP service page](https://www.graniteriverlabs.com/en-us/displayport-standards-service) lists DPA-400 for MST testing; [current contact](https://www.graniteriverlabs.com/en-us/contact) identifies Santa Clara headquarters, not confirmed unit location |

The material below each Subject line is the draft message. Add the sender's
normal signature when sending. Replies should identify exact equipment and
evidence, not just say "supports DisplayPort". No claim of university/company
affiliation is made. Any required account, quote acceptance or physical visit
remains the user's separate decision.

## Unigraf

To: sales.usa@unigraf.fi

Subject: DPA-400 USB-C dock qualification and temporary access in Canada

Hello Unigraf applications team,

I am seeking low-cost temporary access, accessible from Calgary, Alberta, to
observe one normal attach lifecycle between a MacBook USB-C DisplayPort Alt
Mode source and a multifunction USB-C MST dock with two monitors. Two-lane
DP HBR3 and USB 3.x may coexist. I need passive upstream AUX/MST evidence,
not video/pixel capture, certification or traffic generation.

Your current page lists DPA-400 2.1 product 065055 and USB-C cable 546109,
while manual v13 lists USB-C Y-cable 546127. Your download table lists 2.1.10.
Could an applications engineer confirm the following, including the offered
hardware/firmware, software/license and controller-OS requirements?

1. Can DPA-400 observe a USB-C DP Alt Mode source connected to a multifunction
   MST dock? Which cable/fixture is current, 546109 or 546127? Please provide
   its source/dock connector genders and supported diagram, including docks
   with a captive USB-C host plug.
2. Does that complete fixture pass USB 3.x concurrently with two DP HBR3 lanes
   in both orientations, and what high-speed rates are explicitly supported?
3. Does it preserve CC, VBUS, Vconn, PD and Alt Mode negotiation without acting
   as a policy engine? What power/current ratings and power-off behavior apply?
4. Can it observe bidirectional SBU/AUX without injecting traffic or changing
   HPD/Attention? Please identify AUX loading and any active repeater/drive
   behavior, including start/reset defaults.
5. Can full raw AUX requests and replies be exported with timestamps, direction,
   opcodes, addresses, lengths, data and reply status? Which formats retain
   those fields, and is a sample/specification available?
6. Does the current licensed software reassemble and decode MST LINK_ADDRESS,
   remote DPCD/I2C/EDID, ENUM_PATH_RESOURCES, ALLOCATE/QUERY_PAYLOAD and
   CONNECTION_STATUS_NOTIFY, including port/RAD/VCPI/PBN fields?
7. Are original raw sideband fragments retained/exportable when a message is
   unknown, incomplete or CRC-invalid, including retries and failed replies?
8. Is capture overflow or dropped data explicitly reported in saved files,
   separately from malformed AUX-packet errors? What happens when the host stalls?
9. Are the manual's 14 MByte buffer, 32 microsecond timestamps and 0.5 ms per
   request/reply limits current? What are the practical burst/sustained limits?
10. Can recording start before attach and run continuously through one normal
    lifecycle, provisionally up to 180 seconds? How is arming/zero-loss coverage
    verified, and what settings must be disabled to avoid filtering/truncation?
11. Is a demonstration, evaluation or loan unit with the correct fixture
    available for Canada? Please separate any shipping/deposit/access charges;
    I am not requesting a purchase.
12. Can you offer remote-assisted or staffed analysis if a physical Mac/dock
    setup is provided at an agreed location, without active compliance tests?
13. Is there a Canadian distributor or engineering lab with a suitable complete
    setup, or a North American referral if Canadian access is unavailable?

An existing shareable raw capture plus its full report would let me validate
offline ingestion before arranging hardware access. Please distinguish
documented specifications from items requiring a compatibility check.

Thank you.

## Ellisys

To: sales.usa@ellisys.com

Subject: Type-C Tracker Standard DP: AUX export and Canadian temporary access

Hello Ellisys applications team,

I am seeking temporary access from Calgary to a Type-C Tracker Standard DP
(CTR1-A-STD-DP), or Pro, for one normal MacBook-to-USB-C-MST-dock attach
lifecycle. Two-lane HBR3 and USB 3.x may coexist. The requirement is passive
upstream SBU/AUX observation; no certification, video capture, injected AUX,
EDID changes or display-setting changes are requested.

Could you confirm the exact supported cable/fixture and connector genders,
both-orientation HBR3/USB3 pass-through, unchanged CC/PD/Vconn/HPD behavior,
and non-injecting operation including reset and power-off states?

I also need a raw **AUX** export sample/specification with direction, timestamps,
request/reply bytes, addresses, errors and explicit capture-loss/overflow status.
Your FAQ's CSV/binary example refers to USB 2.0 Low Level Items; does the same
or another documented export cover all AUX bytes and incomplete/unknown MST
sideband fragments? Does native decode include LINK_ADDRESS, remote DPCD/I2C,
resources and payload allocation? Please specify buffer/rate/long-capture
limits, filtering defaults, software version, required licenses and viewer/API
availability for offline analysis.

Is a Canadian demo/loan, distributor session or North American staffed test
available with the complete configuration? A shareable example file and written
qualification first would be useful. Please quote any temporary-access charges
separately; I am not asking to purchase equipment.

Thank you.

## UCalgary

To: sse.technical.services@ucalgary.ca

Subject: Equipment enquiry: passive USB-C DisplayPort AUX observation

Hello Schulich Technical Services,

Could you help identify the appropriate equipment custodian for a small
DisplayPort interoperability measurement? I am seeking an existing or
borrowable Unigraf DPA-400 with its supported USB-C fixture, Ellisys Type-C
Tracker DP edition, or an equivalent qualified passive AUX observer in Calgary.
I am not assuming the university owns one.

The setup is a MacBook USB-C DP Alt Mode source and a USB-C MST dock with two
monitors. Two-lane HBR3 and USB 3.x may coexist. The proposed measurement is
one normal attach lifecycle, with no resolution/mirror changes, injected AUX
commands or certification work. It needs exportable raw AUX/MST requests and
replies, timestamps and capture-loss information, not a video analyzer image.

Is supervised one-off access possible, or is there a relevant lab/contact you
could refer me to? Please advise eligibility, any staff/access fees, and whether
the exact supported fixture/software is available. I am not requesting a new
electrical tap, cable modification or general-purpose probe setup.

Thank you.

## Commercial Lab

To: info@graniteriverlabs.com

Subject: One-off passive USB-C AUX/MST capture, not certification

Hello GRL DisplayPort/USB-C team,

Your DisplayPort service page lists Unigraf DPA-400 among the MST test
equipment. Could you offer a small staffed passive-observation session for a
customer-owned MacBook and USB-C MST dock, with Canadian access preferred or
a North American location if needed?

The proposed scope is one normal attach lifecycle to two monitors. Two-lane
HBR3 and USB 3.x may coexist. No certification, reference-sink emulation,
traffic injection, EDID/HPD manipulation or display-setting changes are needed.
The deliverable is the untouched raw AUX capture plus a lossless transaction
export/report covering requests/replies, direction/timestamps, MST topology,
remote DPCD/EDID, resources, payload allocation and table/ACT status, with
explicit capture-loss and configuration information.

Please confirm which location and actual analyzer/license/USB-C fixture can
provide this. The current Unigraf product page lists USB-C cable 546109 while
manual v13 lists 546127, so the supported part, genders and unchanged
CC/PD/USB3/HBR3 behavior need confirmation. Could you share an existing export
sample and overflow/buffer limits before a session is arranged?

Please indicate whether one-off non-certification work on customer hardware is
accepted, the smallest staffed-session charge, lead time, and any shipment or
supervised-visit requirements. If only native-DP observation is available,
please describe the existing setup and costs separately; it would be a
different controlled experiment requiring approval. This is an enquiry, not a
booking or permission to alter hardware.

Thank you.

## Return Package

Useful replies contain: exact offered unit/model/version/license; correct cable
and supported topology diagram; two-lane HBR3/USB3/CC/PD/HPD and non-injection
confirmation; raw sample and format/viewer rights; loss/buffer/rate behavior;
and actual location, access terms, total cost and earliest availability.
Remove credentials and private contact details before bringing replies back
for analysis. Do not send proprietary samples beyond their permitted audience.

No reply, quote, sample, booking, available unit or permission has yet been
received through this package. `USER_OUTREACH_REQUIRED`; `AUX_ACCESS_NOT_READY`;
`DO_NOT_PURCHASE_ANALYZER_YET`; `KEEP_CURRENT_HUB_CONNECTED`.