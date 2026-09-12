# Dock And Display Observations

## Milestone 2A Update

The internal-only baseline below remains historical. The current hub is
owner-identified as ZMUIPNG 14-in-1, ASIN B0FWJZCX5G, not the earlier HP dock.
The owner confirms two VG248 panels showing the same image on the right-side
USB-C socket. C1/D1/C2 now demonstrates repeatable External DCPEXT0 DP/AV and
port-4 appearance, with one external logical VG248. See the [full differential
and graph](external-dock-diff.md). MST chip identity and native DPCD access remain
unknown. Vendor claims supplied by the owner are not proof of M5 limitations.

## Capture Scope

`UNKNOWN` (E011): the user reports two monitors showing the same image through
one USB-C dock. In B01-B03, profiler and the independently implemented probe
instead enumerate only the internal panel. The reported failure topology is
therefore **not reproduced**. Do not treat this baseline as a measurement of an
active mirrored two-monitor dock.

`VERIFIED_ON_M5` (E003, E007-E010): zero external logical displays, zero matched
IOUSBHostDevice objects, an Embedded AV/DP service/device, and an inactive
DisplayPort transport-state object labeled HDMI port 3. Profiler's USB section
is empty. Its three Thunderbolt bus records describe host-side infrastructure;
they do not identify an attached dock or an active DP tunnel.

An empty USB inventory alone cannot prove that a video adapter is disconnected:
DP Alt Mode is not the same thing as USB device enumeration. These captures also
cannot distinguish disconnection, an unpowered/unrecognized dock, a different
observation context, or a transient topology without a controlled recapture.

## Identification

| Requested Fact | Result | Classification / Limitation |
| --- | --- | --- |
| Manufacturer / product | UNKNOWN | No correlated dock descriptors or physical label. |
| USB VID/PID | UNKNOWN | No matched USB device; USB hub IDs would not automatically identify an MST chip. |
| USB speed | UNKNOWN | No observed negotiation; do not infer speed from USB connector shape or bcdUSB alone. |
| USB4 / Thunderbolt involved | UNKNOWN | Host controllers/bus records are not evidence of a dock connection. |
| DisplayPort Alt Mode involved | UNKNOWN | No active USB-C DP path correlated with this dock. |
| MST branch vendor / chipset | UNKNOWN | No branch DPCD/OUI/device-ID read; no software or physical identification. |
| Physical display outputs | UNKNOWN | Two user-reported attached monitors do not establish total dock output count. |
| Physical monitors attached | Two reported by user; not independently observed | UNKNOWN for the measured topology. |
| External logical displays | Zero in B01-B03 | VERIFIED_ON_M5; scoped to those snapshots. |
| macOS mirroring the pair | Not reproduced | UNKNOWN; the sole observed internal display is not in a mirror set. |

`HYPOTHESIS`: the reported dock uses MST, but macOS supplies one usable upstream
stream and the dock mirrors it. Alternative explanations include a non-MST
splitter, dock-specific fallback, routing/adapter behavior, or a differently
configured topology. Mirroring by itself is not proof of MST capability or of
the number of source packets/streams.

## Reproduction And Privacy

After the owner confirms the exact dock, physical port, cable, output labels,
monitor models, power state, and connection arrangement, run:

```sh
build/macmst probe
python3 tools/capture_baseline.py --probe build/macmst
```

The capture tool makes a new UTC-named directory under `artifacts/probes` and
records commands, selected raw properties, decoded probe fields, hashes, and
errors. It refuses to overwrite an existing capture directory. Do not add full
EDID, host/monitor serials, UUIDs, credentials, or unrelated device dumps to Git.
Review even sanitized product descriptors before sharing them publicly.

The [completed M2-01 plan](open-questions.md#m2-01-plan-completed) and recorded
results correlate the external service; do not attribute a random USB device or
the built-in HDMI object to the dock. If the chip remains unidentified after a proper connected capture,
record that limitation instead of guessing Synaptics, Realtek, or another vendor.