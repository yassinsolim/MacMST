# M2G: One-Byte Selector-0 Read Readiness

## Scope

This milestone assesses only a possible future selector-0 request at DPCD address
0x000 with requested output length one byte. It does not invoke a selector,
repeat DPDV open/close, read DPCD/AUX, change the link, or perform MST operations.
The consumed M2F attempt marker remains present. A proposed separate
M2G-DPCD-READ-ATTEMPTED marker is not created. The global execution gate remains
**NOT_READY_FOR_DPCD_TEST** regardless of this static assessment.

The verified M2F runtime observation is **DPDV_OPEN_CLOSE_RUNTIME_VALIDATED**.
It establishes connection acceptance and immediate-close viability in that one
calling context. It does not establish userServer==nullptr, native/delegated
routing, absence of internal work, selector safety, DPCD safety or MST support.

## Reconciled Runtime Baseline

The actual starting branch was experiment/dpdv-open-check, HEAD/upstream
`ae0dd1b18574205315f4bdc602627dd67b88ea5c`, clean with zero divergence. Main was
`1fc8f0241acec829fa732503c13a9ab588e26fb0`. The original stopped M2F receipt and
the later successful execution receipt were both checked; the earlier zero-attempt
state is historical, not the current runtime state.

| Runtime Fact | Retained Evidence |
| --- | --- |
| Successful receipt | artifacts/probes/m2f-20260913T012947590849Z/result.json |
| Executed implementation commit | `12538ab025ce5ab097aa0cd8665932fd3054b6f4`; native implementation from d7f41b8 |
| Wall-clock bracket | Public BEFORE at 2026-09-13T01:29:48Z and AFTER at 01:29:49Z; exact open-call wall-clock timestamp is not separately recorded |
| Selected provider | DCPDPDeviceProxy, External Unit 0 under RTBuddy(DCPEXT0), with matching supported External DCPDPServiceProxy |
| Transient device/service/transport IDs | 4294971118 / 4294971117 / 4294970218; comparison evidence only |
| Helper spawns / historical open attempts | 1 / 1; one-shot source/compiled callsite, consumed marker and returned terminal frame agree |
| Open return / duration | Raw 0 / 0x00000000, 22 microseconds |
| Connection returned | Nonzero, actual Mach port name not retained |
| Selector calls | 0 |
| Close attempted / return / duration | Yes, once / raw 0 / 0x00000000 / 99 microseconds |
| Helper exit / wait status | 0 / 0 |
| Parent observation / watchdog | 14 ms, no failure trigger, no timeout, no termination signal |
| Reaping | Successful; no remaining helper |
| Frame evidence | CLOSE_SUCCEEDED, flags=63, two matching-ID frames / 128 bytes, no stderr |
| Public comparison | NO_PUBLIC_DISPLAY_STATE_CHANGE: one 1920x1080@60 external display, DCPEXT0 endpoints, HPD High, two HBR3 lanes, no tunneling, sink count 1, no public errors |

All BEFORE/AFTER manifest artifacts and semantic comparisons were verified.
The saved executed source and binary hashes match the implementation on disk;
the post-stop commit changed only sanitized documentation. No missing result was
inferred from an absent file or from the success label alone.

| Immutable Receipt | SHA-256 |
| --- | --- |
| Original stopped result, m2f-20260912T154617081227Z | `79387346acdaebed1efb2284a531de8f2cf5aad1d64915a3f5f527040ebae840` |
| Successful result | `86ee9fdd87eb631e7552b0087471a149c183667c2162e838866ce993e1dd3d04` |
| Successful BEFORE public report | `9959711b39e43f541deab60091869048865c0e637b14bfb68124582a833f4552` |
| Successful BEFORE manifest | `60267d51a7ed07417d483ffc7b0028a5cf1026847b683d59aa7bdf89ec4b18af` |
| Successful AFTER public report | `3f46486f6884b7d9f7560832c7d410c165c9ab935fe31366673e2328e8a0e1f7` |
| Successful AFTER manifest | `adda3a3d430c469ef28e855c38d532588c2cad3f0cf7c3c0b01b663e8ca3a506` |
| Consumed M2F-ATTEMPTED marker | `2f3da1f224c0602dc46f812d3f6eb2c1560fe7a82c1a89f93eedb725b2726efc` |

## Integration And Tag

All three M2F commits and 20 unique changed text blobs were audited. The single
commit after the previously published stopped state changes five sanitized
documents only; no retry, raw capture, binary or private selector machinery was
introduced. The marker remains ignored and persistent.

M2F was integrated with --no-ff as
`3f5f0cd887ed2ef5c8dbadc9abb278792c3150be`, message
`merge: record first isolated DPDV open-close runtime validation`. Parents are
`1fc8f0241acec829fa732503c13a9ab588e26fb0` and
`ae0dd1b18574205315f4bdc602627dd67b88ea5c`; the merge tree equals the audited
M2F tree. Main was pushed without force or branch deletion.

Annotated tag `dpdv-open-runtime-v0.3`, object
`9d0341216b70251bfec37cddd47b8068ad9c1932`, peels to that merge. Its message is
`Verified MacMST state after first successful isolated DPDV open-close with zero selector calls.`
The tag was pushed and verified before research/selector0-one-byte-readiness was
created from it. The pre-open tag object
`f01208571d395ded9857a2c663f5276e12220c49` still peels to
`1fc8f0241acec829fa732503c13a9ab588e26fb0`; research-baseline-v0.1 and historical
branches are unchanged.

## Evidence Applicability And Hypothesis

The running kernel UUID is still `447D769E-1CB7-3086-A0B4-32226837B587`, on
macOS 26.6.2 (25G83), Apple M5. Retained ABI-02/RPC-03 server evidence therefore
remains the starting point; no fresh kernel call-graph expansion is needed.
An image UUID identifies the build, not the executed firmware route or every live
code page. The M2F success does not close the earlier routing uncertainty.

The local hypothesis to test is that length one changes the RPC allocation/copy
length but does not add a deadline or recover lost reply-completeness information.
The discriminating checks are the retained read/send/wait bodies and a synthetic
one-byte short-reply counterexample: a zero-filled host reply with insufficient
firmware bytes can overwrite a nonzero caller sentinel even if outer status is
zero. A complete-output-size or timeout guarantee in the actual one-byte path
would disprove or narrow this hypothesis. No hardware fault injection is permitted.