# M5 Display Stack Baseline

See [the ledger](evidence-ledger.md) for capture times, classifications, and exact
source revisions. This combines the M5 baseline and DCP research to avoid
duplicated architecture documents.

Milestone 2A subsequently observed and correlated an External DCPEXT0 path through
the owner-controlled ZMUIPNG hub cycle. The [differential and actual graph](external-dock-diff.md)
preserve that newer evidence. The observations below remain the internal-only
Milestone 1 baseline; the [IODP API investigation](iodpdevice-api.md) supersedes
the earlier symbol-only ABI status without claiming native AUX functionality.

## What Is Actually Exposed

`VERIFIED_ON_M5` (E001, E003-E010): Mac17,2 reports an Apple M5 GPU and one
online built-in display. Public IORegistry reads expose these software paths:

```text
AppleARMPE / arm-io / AppleSoCIO
  dcp0-expert     -> AppleDCPExpert
  dcpext0-expert  -> AppleDCPExpert
  dcpext1-expert  -> AppleDCPExpert
  dcp            -> AppleASCWrapV6 -> iop-dcp-nub -> RTBuddy(DCP)
    disp0:dcpav-service-epic:0 -> DCPAVServiceProxy [Embedded]
    disp0:dcpdp-device-epic:0  -> DCPDPDeviceProxy  [Embedded]
    disp0:dcpdp-service-epic:0 -> DCPDPServiceProxy [Embedded]
  dcpext0 / dcpext1 -> RTBuddy(DCPEXT0/1) -> AFK endpoints
    AppleDCPDPTXRemotePortProxy -> AppleDCPDPTXRemotePortUFP
```

The tree is abbreviated; B03 preserves exact paths and transient registry IDs.
There are four remote-port proxy/UFP instances across the two DCPEXT paths.
These are not four verified external outputs or four source streams.

`UNKNOWN`: total physical scanout engines, independent hardware stream inputs,
MST packetizers, hidden routing constraints, and how all paths map to M5 physical
USB-C connectors. Registry names/counts alone cannot establish those properties.

`VERIFIED_ON_M5`: the sole published DisplayPort transport-state object describes
HDMI port 3 and reports an inactive link. It must not be relabeled as the active
USB-C dock. No external logical display was observed in B01-B03.

## DCP And The Application Processor

`PRIMARY_SOURCE` (S04/S05): Asahi/m1n1 describe firmware-facing DPTX callbacks for
lane count, link rate, drive settings, HPD, and PHY/port association. Asahi's
`struct dptx_port` includes PHY and mux references as well as lane/rate state.
Its `dcpavserv_copy_edid` uses an AFK/EPIC service call to retrieve EDID data.

`INFERRED`: the similarly named RTBuddy/AFK/EPIC services visible on this M5 are
consistent with a firmware-mediated display path. This does not verify identical
firmware protocols, call numbers, layouts, or physical routing to older SoCs.
Asahi service group/command numbers are not macOS IOConnect method selectors.

`PRIMARY_SOURCE` (S08): Asahi documents both DCP/DCPEXT, DP Alt Mode and USB4
tunneling, with chip-specific routing restrictions. It states No MST. Its table
contains M1-M3 and unresolved M4 rows, but no M5 entry. Preserve that contrary
claim and its evidence scope; do not use it to close the M5 investigation.

## Host Interfaces

`VERIFIED_ON_M5` (E007, E008, E013, E014): AV and DP service/device proxies and
their library symbol families coexist. IOAVServiceUserInterfaceSupported=true
is a published property of the embedded AV service. It does not demonstrate an
authorized client connection or any successfully completed bus transaction.

`PRIMARY_SOURCE` (S06/S07): IOAVService-based DDC tools use private C functions
with I2C chip/register arguments. `IOAVService` is a userspace CFTypeRef in those
declarations, not necessarily a literal IORegistry class. A zero IOAVService
class match therefore does not refute IOAVService library availability.

`UNKNOWN`: whether this OS's IODPDeviceReadDPCD can bind to an external M5 device,
whether it performs a live native AUX read or a cached/abstracted operation,
and what permission/firmware requirements apply. See [AUX investigation](aux-access.md).

## MST Versus Multiple Display Paths

`PRIMARY_SOURCE` (S01/S02): receiver MST capability, native AUX access, topology
management, and a source capable of carrying MST are separate requirements.

`INFERRED`: multiple DCPEXT objects or multiple USB4 display tunnels would not by
themselves demonstrate multiplexing multiple streams onto one DP link. Likewise,
DDC communication, an EDID, a tiled-display hint, or the DPCD-read symbol does not
establish source payload scheduling/packetization. The firmware could offer AUX
while exposing only SST scanout; the opposite claim also requires evidence.

`UNKNOWN`: no DCP firmware image, source-specific MST scheduler/packetizer code,
or actual MST main-link output has been examined. No firmware was extracted,
patched, loaded, or reconfigured.