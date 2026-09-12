# DisplayPort Capability Preparation

`PRIMARY_SOURCE`: Linux v6.12, `include/drm/display/drm_dp.h`, defines the
following receiver/DPCD addresses and AUX opcodes. These are protocol facts,
not observations of this Mac or dock. MacMST uses constants and independently
written decoding logic, not a copied Linux implementation.

| Address/Opcode | Symbol | Interpretation |
| --- | --- | --- |
| `0x000` | `DP_DPCD_REV` | DPCD revision nibbles, not automatically the complete DP feature set. |
| `0x001` | `DP_MAX_LINK_RATE` | Legacy link-rate code. |
| `0x002` | `DP_MAX_LANE_COUNT` | Lower five bits; enhanced framing bit 7, TPS3 bit 6. |
| `0x005` | `DP_DOWNSTREAMPORT_PRESENT` | Downstream port presence bit 0. |
| `0x007` | `DP_DOWN_STREAM_PORT_COUNT` | Lower four bits; not independently measured physical monitors. |
| `0x00e` | `DP_TRAINING_AUX_RD_INTERVAL` | Bit 7 indicates extended receiver capability fields. |
| `0x021` | `DP_MSTM_CAP`, `DP_MST_CAP` | Bit 0 advertises MST on the addressed receiver/branch. Bit 1 is single-stream sideband messaging, not bit 0. |
| `0x111` | `DP_MSTM_CTRL`, `DP_MST_EN` | State-changing MST enable control. Do not write in this phase. |
| `0x1000/0x1200/0x1400/0x1600` | `DP_SIDEBAND_MSG_*_BASE` | MST down-request/up-reply/down-reply/up-request buffers. No messages sent. |
| `0x0/0x1` | `DP_AUX_I2C_WRITE/READ` | I2C-over-AUX requests. |
| `0x8/0x9` | `DP_AUX_NATIVE_WRITE/READ` | Native AUX requests with a DPCD address space. |

Legacy rate codes `0x06`, `0x0a`, `0x14`, `0x1e` correspond to 1620, 2700,
5400, 8100 Mbit/s per lane before channel-coding overhead. Code zero can mean
the supported-rate table is needed. UHBR uses additional capability definitions;
MacMST does not reinterpret unfamiliar codes as legacy rates or usable bandwidth.

The decoder consumes 16 bytes starting at `0x000` and an optional separately
read byte from `0x021`. Two different address spaces must never be conflated:
an I2C chip/register argument of `0x21` is not a native DPCD read at `0x00021`.
Missing `0x021` produces an unknown optional value, not `mst_capable=false`.
Reserved lane/rate values remain raw with no invented normalized result.

`UNKNOWN`: no DPCD byte was read from this M5 or its dock. All decoder tests use
synthetic data. Even a valid `DP_MST_CAP=1` response would prove receiver/branch
advertisement, not a source MST packetizer, payload scheduling, stream generation,
or macOS integration. Native AUX alone would also be insufficient.

Source: [Linux v6.12 DisplayPort definitions](https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/include/drm/display/drm_dp.h),
commit `adc218676eef25575469234709c2d87185ca223a` (S01 in the evidence ledger).