# Milestone 2A: External Dock Differential

## Stage 1 Gate

`VERIFIED_ON_M5`: the topology gate passed at 2026-09-12T00:49:57Z. The unchanged
Milestone 1 probe reports one external logical display and External DP/AV objects
under DCPEXT0, alongside an active USB-C DisplayPort transport. No private API
was invoked.

- Historical internal-only reference **B03**: `artifacts/probes/20260912T003142Z/`.
- Initial connected observation **C1**: `artifacts/probes/20260912T004957Z/`.
- Both manifests' 19 artifact hashes verified; C1 completed 32 read-only commands
  with no failures. The probe binary and sources match B03 exactly.
- Commands: `build/macmst probe --json` and
  `python3 tools/capture_baseline.py --probe build/macmst`.

B03 is a historical internal-only observation, not a controlled disconnected
member of this experiment. The initial prompt named an HP dock; the owner
subsequently corrected the active hardware to a **ZMUIPNG 14-in-1 USB-C hub**,
Amazon ASIN **B0FWJZCX5G**, on the Mac's **right-side USB-C socket**. The owner
confirmed that both external panels are VG248 models and show the same image.
No HP dock identity is claimed for C1 or C2.

The owner supplied the listing's claims of two HDMI outputs plus DisplayPort,
10 Gbit/s USB ports, and SST mirroring on macOS. These are owner-supplied vendor
claims, not independent measurements or primary evidence of M5 limitations.
[The product URL](https://www.amazon.ca/dp/B0FWJZCX5G) could not be fetched because
certificate validation failed; no certificate/security check was bypassed.

## Observed Delta

| Observation | B03 | C1 | Interpretation |
| --- | --- | --- | --- |
| Internal logical displays | 1 | 1 | Unchanged. |
| External logical displays | 0 | 1 | New active 1920x1080 at 60 Hz display; profiler name VG248. |
| AppleDCPExpert | 3 | 3 | Same objects; one object's selected properties changed. |
| DCPAVControllerProxy / DCPDPControllerProxy | 5 / 5 | 5 / 5 | No selected-field changes. |
| DCPDPDeviceProxy | 1 Embedded | 1 Embedded + 1 External | External object under dispext0, Unit=0. |
| DCPDPServiceProxy | 1 Embedded | 1 Embedded + 1 External | Separate service endpoint under dispext0, Unit=0. |
| DCPAVServiceProxy | 1 Embedded | 1 Embedded + 1 External | External service also reports user-interface-supported=true. |
| DPTXRemotePortProxy / RemotePortUFP | 4 / 4 | 4 / 4 | Existing objects, unchanged selected properties; presence alone is not connection evidence. |
| DisplayPort transport-state objects | 1 | 2 | Inactive HDMI remains; active USB-C port 4 appears. |
| IOUSBHostDevice | 0 | 10 | USB topology visible; includes GenesysLogic hubs and ASIX Ethernet. |
| IOFramebuffer / IOI2CInterface / IOAVService class matches | 0 / 0 / 0 | 0 / 0 / 0 | Still no legacy-class matches; not an absence claim about the library APIs. |

No previously selected registry object disappeared between B03 and C1. The
external logical display reports `in_mirror_set=false`; profiler likewise reports
mirroring off. This describes macOS's logical display model, not whether two
physical panels downstream of one source display show identical images.

## External Candidate And Port Evidence

`VERIFIED_ON_M5`: C1 exposes the following objects; IDs are transient:

| Object | Entry ID (decimal) | Location | Unit | Parent endpoint |
| --- | --- | --- | --- | --- |
| DCPDPDeviceProxy | 4296579088 | External | 0 | dispext0:dcpdp-device-epic:0, DCPEXT0Endpoint8 |
| DCPDPServiceProxy | 4296579087 | External | 0 | dispext0:dcpdp-service-epic:0, DCPEXT0Endpoint9 |
| DCPAVServiceProxy | 4296579086 | External | 0 | dispext0:dcpav-service-epic:0, DCPEXT0Endpoint9 |

The device and service are not a direct parent/child chain. Their paths share
`dcpext0@F6E00000 / iop-dcpext0-nub / RTBuddy(DCPEXT0)` and split into different
AFK/EPIC endpoints. Their provider class is `AFKEndpointInterface`.

The new transport object (entry ID 4296578791) is in a different registry branch:

```text
nub-spmi-a1 / AppleSPMIController / hpm3@C / AppleHPMARMSPMI
  AppleHPMDeviceHALType3@C / Port-USB-C@4 / DisplayPort
```

| Published property | Raw value | Published description / Limit |
| --- | --- | --- |
| Active | true | Reported active transport. |
| ParentPortNumber / ParentPortType | 4 / 2 | USB-C; physical chassis position not yet mapped. |
| HPD_State | 2 | High. |
| LaneCount / MaxLaneCount | 2 / 2 | Reported for this transport, not total M5 capability. |
| LinkRate | 4 | 8.1 Gbps (HBR3). This is an Apple enum, not a DPCD link-rate byte. |
| SinkCount | 1 | Published sink count, not independently counted physical monitors. |
| Tunneled | false | Reported non-tunneled DP path; not a claim about every dock function. |

`INFERRED`: the shared DCPEXT0/Unit context makes the External device and service
a candidate pair. Simultaneous appearance of the port, display and services is
supporting evidence, but repeatable physical correlation and actual relationships
are required before attributing the pair to the dock or calling any private API.

## Correlation Status

The owner unplugged only the upstream cable and then reconnected the same hub
to the same right-side socket, keeping the downstream connections unchanged.
The owner again confirmed both VG248 panels showed the same image after reconnect.
No software link/HPD/display configuration command was sent.

| State | Capture | External logical displays | External DP device/service/AV service | Active USB-C DP transport | USB devices |
| --- | --- | --- | --- | --- | --- |
| C1 connected | `20260912T004957Z` | 1 | 1 / 1 / 1 | Port 4 | 10 |
| D1 owner-disconnected | `20260912T010227Z` | 0 | 0 / 0 / 0 | None | 0 |
| C2 owner-reconnected | `20260912T010346Z` | 1 | 1 / 1 / 1 | Port 4 | 10 |

All three captures completed 32 read-only commands without errors; all artifact
hashes were verified. The Embedded device/service/AV objects remained present.
The External controller and remote-port proxy objects persisted across disconnect,
so their mere presence is not evidence of an active sink.

| Object | C1 entry ID | D1 | C2 entry ID |
| --- | --- | --- | --- |
| External DCPDPDeviceProxy | 4296579088 | Absent | 4296595301 |
| External DCPDPServiceProxy | 4296579087 | Absent | 4296595299 |
| External DCPAVServiceProxy | 4296579086 | Absent | 4296595294 |
| Active USB-C DisplayPort transport | 4296578791 | Absent | 4296594994 |

`VERIFIED_ON_M5`: those objects and the external logical display disappear on
the owner-confirmed disconnect and return on reconnect. C2 repeats the DCPEXT0
paths, External/Unit=0 properties and the published two-lane HBR3, SinkCount=1,
HPD=High, non-tunneled port-4 state. IDs change and must not be reused as handles.

`INFERRED` (strong, experiment-scoped): this External DCPEXT0 DP/AV path is
associated with the observed ZMUIPNG hub connection. The device/service pairing
is supported by the shared RTBuddy/processor ancestor, Unit and matching endpoint
labels, not by a direct parent/child relationship. The separate HPM/USB-C branch
is associated by the controlled transition, not an invented direct registry edge.

`UNKNOWN`: the MST branch silicon and which physical panel's EDID is represented
by the single logical VG248. Physical mirroring is owner-observed; no main-link
packet capture or DPCD read has established the internal hub implementation.

## Explicit Registry Graph (G2)

G2 is `artifacts/probes/20260912T012137Z/`: the updated non-invasive probe adds
immediate parent/child identity and selected interface-support flags. It completed
33 read-only commands without errors. It is a subsequent connected snapshot,
not a replacement for the unchanged-binary C1/D1/C2 experiment.

`VERIFIED_ON_M5`: below each endpoint are AFK wrappers followed by an
`AFKEPInterfaceKextV2` parent. The proxy's declared provider is
`AFKEndpointInterface`; its actual immediate parent's runtime class is the KextV2
subclass. DP and AV proxies listed here have no IOService children in G2.

```text
dcpext0@F6E00000 / AppleASCWrapV6 / iop-dcpext0-nub / RTBuddy(DCPEXT0)
  Endpoint5
    dispext0:dcpdp-controller-epic:0 -> DCPDPControllerProxy (External, Unit 0)
    dispext0:dcpdp-controller-epic:1 -> DCPDPControllerProxy (External, Unit 1)
    dispext0:dcpav-controller-epic:0/1 -> DCPAVControllerProxy
  Endpoint8
    dispext0:dcpdp-device-epic:0 -> DCPDPDeviceProxy (External, Unit 0)
    dispext0:dcpav-device-epic:0 -> DCPAVDeviceProxy (External, Unit 0)
  Endpoint9
    dispext0:dcpdp-service-epic:0 -> DCPDPServiceProxy (External, Unit 0)
    dispext0:dcpav-service-epic:0 -> DCPAVServiceProxy (External, Unit 0)
  DPTX port endpoint branches
    dispext0:dcpdptx-port-epic:0/1 -> AppleDCPDPTXRemotePortProxy
      AppleDCPDPTXRemotePortUFP (the actual child)

Separate HPM branch
  AppleHPMInterfaceType10 (Port-USB-C, registry path location @4)
    IOPortTransportStateDisplayPort (active, HPD high, 2 lanes, HBR3, not tunneled)
```

G2 exposes `IODPDeviceUserInterfaceSupported=true` on the DP device,
`IODPServiceUserInterfaceSupported=true` on the DP service, and
`IOAVDeviceUserInterfaceSupported=true` on the AV device sibling. The flags
describe advertised interfaces, not successful user-client opens. Link rate,
lane count and sink count are recorded on the transport object, not copied into
the DP device as if those were its own properties. Missing properties remain
unknown; Unit numbers in different interface families are not automatically a
port mapping.

The USB hub devices have separate USB host-port ancestry. Selected examples:

| Descriptor | VID:PID | USBSpeed raw | Parent runtime class | Child hub driver |
| --- | --- | --- | --- | --- |
| GenesysLogic USB3.2 Hub | 05e3:0625 | 5 | AppleUSB30XHCIARMPort | AppleUSB30Hub |
| GenesysLogic USB2.1 Hub | 05e3:0610 | 3 | AppleUSB20XHCIARMPort | AppleUSB20Hub |
| USB 2.0 Hub | 1a40:0801 | 3 | AppleUSB20HubPort | AppleUSB20Hub |
| USB2.0 Hub | 05e3:0618 | 3 | AppleUSB20HubPort | AppleUSB20Hub |

These are USB descriptor identities, not the MST chip identity. The remaining
USB peripherals are not needed to name the DP target. USB relationship names are
redacted in the new probe; registry IDs and classes permit graph comparisons.
The profiler USB section remained empty even while IOKit enumerated ten devices;
therefore an empty SPUSBDataType result must not be interpreted as disconnection.
The sanitized Thunderbolt section has only three host bus records. The active
DP object's `Tunneled=false` is the direct evidence for this DP path; the records
do not prove every possible Thunderbolt/USB4 capability of the hub.

## Probe Interpretation

The CLI derives External candidates only from successful observations with an
External location, valid numeric Unit and a common exact RTBuddy processor path.
It rejects cross-core/Unit matches and marks multiple matches ambiguous. A single
device/service pair concurrent with one external logical display and one active
external transport is labeled `INFERRED_SINGLE_ACTIVE_EXTERNAL_CONTEXT`, never
verified physical association from one snapshot alone. The C1/D1/C2 document
supplies the stronger temporal evidence. No private object is acquired, and the
CLI always reports DPCD read capability as `UNVERIFIED`.

See [iodpdevice-api.md](iodpdevice-api.md) for the ABI findings and the still-blocked
first private-read experiment.