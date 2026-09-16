# Human-Only M5 Observer Platform Handoff

## Goal And Boundary

For a **human developer**, obtain a passive T8142 normal macOS-to-DCP capture
producer emitting [observer schema v1](dcp-observer-schema-v1.md). The eventual
MacMST goal remains multiple independent external displays on the base M5
MacBook Pro through ordinary USB-C/DisplayPort MST hubs/docks, without
DisplayLink or special Thunderbolt multi-DP hardware. This handoff concerns
instrumentation, not proof that the final display goal is achievable.

The sibling `/Users/ysoli/Projects/m1n1-MacMST` contains upstream-tracked
instructions prohibiting AI/LLM work. Respect those instructions. This is not
an assignment to another AI agent. Do not remove, rename, bypass or copy around
the policy; no AI-generated m1n1 patch or new implementation derivation is
provided here. A human must read upstream instructions and decide whether they
are willing and authorized to perform the work.

M5P1 touches only independent MacMST source and synthetic files. Its only
sibling access was verifying status, HEAD and remotes: clean detached checkout,
with official upstream fetching and upstream pushing disabled. No platform
source was read, edited, built or copied for this milestone.

## Already-Known Pins

These are recorded M4Q/M5P0 facts, not freshly researched platform results:

| Item | Recorded Identity |
| --- | --- |
| Official AsahiLinux/m1n1 main | `b4654b32941d51afdb77579d63e7cb1aa6c03ecc` |
| Official hv-sprr | `1c98fd09817cede0043d25c95fb540dbd683ef18` |
| AsahiLinux/docs | `715664a269937fe83293f46bbbeaae6094cb504e` |
| Target | Mac17,2 / J704AP / T8142; macOS 26.6.2 build 25G83 |
| MacMST M4Q | `b11611e68f257d240fff6d93bc5307a305906d09` |
| MacMST partial M5P0 | `3f2240de0d33126c8f264dcfa0e04e3e61397391` |

Refer to the frozen [M4Q report](m5-observer-gap.md) and the historical M5P0
sections in [the self-enablement report](m5-observer-self-enable.md). They are
leads with explicit limits, not patch instructions or boot-success evidence.

## Known Unresolved Items

- Pristine pinned hv-sprr build was not performed in M5P0.
- B1 was not re-evaluated in M5P0; no new SPTM-aware guest result exists here.
- The T8142 selector audit remains incomplete.
- The essential-device audit remains incomplete.
- Guest image/trust/security/execution preconditions remain incomplete.
- A live passive DCP capture producer remains unimplemented by MacMST.

M4Q reported a CPU-start selection mismatch and partial upstream groundwork;
this document does not derive or supply a fix. M5P1's synthetic producer and
passing parser/evidence tests are not substitutes for a real producer or
platform build. No Apple binary or real Apple trace is supplied.

## Manual Checklist

1. Read all applicable upstream repository instructions.
2. Decide whether you are willing and authorized to perform the work under
   those instructions; resolve policy questions with maintainers, not an agent.
3. Build pristine pinned hv-sprr before modifying source; retain compiler,
   configuration, command, warnings, full log and artifact hashes.
4. Inspect T8142 selectors against already-established authoritative target data.
5. Inspect guest prerequisites, separating image loading, monitor/trust state,
   guest execution and target-specific fixups.
6. Implement only justified T8142 changes, one logical change per commit.
7. Build after each change and preserve failure logs as well as successful ones.
8. Implement a producer for the frozen observer schema, preserving raw records
   before decoding and explicitly recording loss, truncation and generations.
9. Run producer unit tests without target hardware where possible, including
   unknown opcodes/services, complete replies and buffer-loss reporting.
10. Return exact upstream base/patch SHAs, build logs, producer version and
    synthetic unit-test results to MacMST for provenance review.

This is a compile/offline checklist only. It contains no boot, installation,
DFU, live-debugger, security-change or DCP command recipe. No human target test
is authorized by M5P1 either. Any future hardware work requires a separately
reviewed procedure, appropriate hardware and explicit approval.

## Result Package

A human-authored result directory may contain result.json, build.log,
unit-tests.log and other bounded nonsecret supporting files. The JSON requires:

| Field | Contract |
| --- | --- |
| handoff_version | Integer 1 |
| upstream_base_sha | Exact lowercase 40-character upstream commit |
| patch_commits | Ordered list of exact, unique patch commit SHAs; empty for a pristine-only result |
| build_command | Recorded command string, never executed by the importer |
| build_result | PASS, FAIL or NOT_RUN |
| artifact_hashes | Artifact name -> lowercase SHA-256; absent artifacts remain unverified claims |
| producer_version | Exact producer version, or explicit UNKNOWN if not implemented |
| unit_tests | Object with status PASS/FAIL/NOT_RUN and nonnegative count |
| execution_status | NO_HARDWARE or HARDWARE, explicitly reported, never inferred |
| files | Relative supporting file path -> SHA-256, validated against supplied bytes |
| build_log | Required path present in files |
| unit_test_log | Required hash-inventoried path when unit_tests.status is not NOT_RUN |

Do not include secrets, personal machine identifiers, Apple binaries, credentials
or recovery keys. Preserve exact commands and failures as facts rather than
editing logs to suggest success. Return any proposed live-operation history
explicitly; its existence would require separate review, not retrospective
authorization by this document.

## Import And Provenance Review

```sh
python3 tools/dcp_trace_analyze.py human-result/result.json --platform-result --json
```

The validator reads only these offline files. It checks required fields, SHA
syntax, path confinement and supporting log hashes, never executes a command,
fetches a repository, loads a binary or opens a device. A successful result is
EXTERNAL_PROVENANCE_FORMAT_VALID, not automatic technical acceptance.

A human reviewer must then verify upstream ancestry and patch identity in an
authorized human-managed repository, compare commands/configuration with logs,
verify available artifact hashes, check producer-schema compatibility and test
results, and corroborate the reported no-hardware/hardware status. Hashes alone
do not establish author authenticity, semantic truth or actual execution.
Until that review, claims remain external/unverified; record exact accepted
facts and limitations in new MacMST ledger rows without rewriting history.

Real capture bundles follow the separate observer schema bundle contract.
Raw records, topology and source info must match their hashes; ownership claims
need explicit independent semantic provenance. A producer build result alone
does not prove source membership, multi-stream support or bounded recovery.

## Unchanged Gates

`M5_OBSERVER_CODE_NOT_READY_FOR_TARGET_TEST` and
`SACRIFICIAL_M5_STILL_PREMATURE` remain unchanged by M5P1 or a merely well-formed
handoff. `USB_C_HUB_CONNECTION_NOT_REQUIRED`: keep the hub and displays unplugged.
Preserve `RETIRED_ON_DAILY_USE_M5`, `NOT_READY_FOR_DPCD_TEST`,
`STATIC_PACKETIZER_ANALYSIS_FROZEN` and
`NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED`. This document
provides no AI platform patch and no permission to bypass upstream policy.