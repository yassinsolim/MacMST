# M5 Upstream Resume Gates

## Objective

Establish a durable upstream-wait baseline after completed M4Q. MacMST must not
absorb general M5/m1n1 platform enablement. This is a project-state/integration
milestone, not another technical investigation, observer implementation or
hardware experiment. The project is paused for an external capability, not
declared a failure or proof of architectural impossibility.

No m1n1 support question is re-researched here. No source/firmware scanner,
build, guest, tracer, private display call, DCP/DPCD operation, display
transition, DFU action or security change is performed. The monitors need not
be connected for this milestone.

## Integrated Baseline

On 2026-09-15, the starting checkout was clean
`research/m5-observer-gap`, HEAD/upstream
`b11611e68f257d240fff6d93bc5307a305906d09`, ahead/behind 0/0. All 38 existing
local/remote head/tag/peeled identities matched the expected baseline; the new
tag and resume branch did not already exist.

The exact linear research chain was verified before integration:

| State | Commit | Research Commit Parent |
| --- | --- | --- |
| Old main / permanent static ceiling | `c5bc1b1bacd7742a4bbc1b54285336e9d51302a5` | Existing M3D integration |
| M3E0 conclusion | `a6a5dc122563c1d4dc481a09bf70848eea61fa78` | `c5bc1b1bacd7742a4bbc1b54285336e9d51302a5` |
| M4P design | `95f9f4300fd3e7aec417e8e727bd8cd57714fb98` | `a6a5dc122563c1d4dc481a09bf70848eea61fa78` |
| M4Q observer gap | `b11611e68f257d240fff6d93bc5307a305906d09` | `95f9f4300fd3e7aec417e8e727bd8cd57714fb98` |

Each research commit changes five documentation paths; the combined chain
changes seven paths, with no implementation, configuration or executable
artifact changes. The [M4Q report](m5-observer-gap.md#observer-decision) retains
`M5_OBSERVER_REQUIRES_MAJOR_PLATFORM_ENABLEMENT` and its explicit no-execution
record. Git proves the documentation-only change scope; the historical report
and completed work record provide the no-operation account, not a new runtime
attestation. M4Q was not rerun.

The authorized `--no-ff` merge, published to main, is
`7250caac7a9f627f381b91ab9dfeb86191344ed9`, message
`merge: record M5 observer platform-enablement boundary`. Its ordered parents
are old main `c5bc1b1bacd7742a4bbc1b54285336e9d51302a5` and M4Q
`b11611e68f257d240fff6d93bc5307a305906d09`. Its tree,
`c2c55e73891c13f39af94c5f7ec0e5b7f651617f`, equals M4Q's tree exactly. No
cherry-pick, synthetic integration, unrelated path or historical-branch change
was used.

After main publication, annotated `m5-observer-platform-gap-v1.1` was created
and published. Tag object: `b4fea86babb7115ce3313dd00bf5a36ff6e996e3`.
Peeled commit: `7250caac7a9f627f381b91ab9dfeb86191344ed9`.
Its exact annotation is:

> MacMST observer investigation complete: current passive T8142 observation path requires major M5 platform enablement; project waits for upstream capability.

The permanent `m5-mst-static-ceiling-v1.0` is unchanged: annotated object
`08234296452af2f9d5056cfc743e79801cef92e9`, peeled commit
`c5bc1b1bacd7742a4bbc1b54285336e9d51302a5`. The new observer-gap tag does not
move, replace or weaken the static ceiling.

`research/m5-upstream-resume-gates` was created from the published v1.1 tag's
peeled commit. It contains only this documentation/status handoff, is published
separately, and must not be merged into main or made into a PR in this milestone.
Earlier navigation statements that the research chain was unmerged describe
the historical state before this integration.

## Resume Gates

All five gates are currently `WAITING`. They are evidence requirements, not
five independent projects or automatic permissions. A single mechanism can
cover several gates, and an alternative environment can bypass the missing
m1n1 guest. The selected route must still cover every mandatory link below.

| Gate | Capability | Current Status |
| --- | --- | --- |
| U1 | Qualified M5 macOS guest | WAITING |
| U2 | Alternative passive T8142 observer | WAITING |
| U3 | Qualified T8142 DCP tracing path | WAITING |
| U4 | Ownership identity schema | WAITING |
| U5 | Useful stimulus or direct multiplicity evidence | WAITING |

### Gate U1 - Qualified M5 macOS Guest

State: `WAITING`.

Require an officially documented or reproducibly demonstrated M4/M5-or-newer
macOS guest, applicable to T8142 or demonstrably portable to it. Evidence must
address the SPTM/newer-XNU boot contract and show stability sufficient for
passive tracing, with exact hardware, OS/build, tool revision, prerequisites
and reproducible results. A generic M4 demonstration without a defensible
T8142 applicability argument is insufficient. CPU recognition alone is not U1.

### Gate U2 - Alternative Passive T8142 Observer

State: `WAITING`.

Require a public mechanism that observes normal macOS DCP/ASC traffic on T8142
without the currently missing m1n1 M5 macOS guest. A future supported tracer,
hardware-assisted monitor, Apple diagnostic export or another research
hypervisor could qualify with an actual access/data contract and reproducible
target evidence. No such mechanism is asserted to exist now. U2 is an
alternative to U1, not an extra prerequisite for a qualified U1 route.

### Gate U3 - Qualified T8142 DCP Tracing Path

State: `WAITING`.

Require a located DCP ASC, qualified required DART/SID mapping, working
endpoint/channel discovery, demonstrated passive request/reply observation
and complete preserved raw payloads. Bind records to target/OS/tool versions,
direction, lengths, clocks, capture generations and loss/ordering limits.
This may follow U1 or U2 and must observe existing traffic rather than inject it.

An alternative export may encapsulate low-level mapping instead of exposing a
DART to the user. Document why those mechanics are not applicable and provide
equivalent authoritative transport/target provenance. That avoids imposing an
irrelevant implementation detail; it does not waive transport visibility or
the complete raw-record requirement. Physical DP wire control alone is not a
normal macOS DCP/ASC request/reply observer.

### Gate U4 - Ownership Identity Schema

State: `WAITING`.

Require a defensible mapping from observed records to
`physical DPTX -> source/object identity`, with independent validation of
scope, lifetimes and aliases. It may come from documented IPC semantics,
upstream trace definitions, validated runtime IDs or new public independent
reverse-engineering work. Service units, endpoint/channel IDs or downstream
ports must not be relabeled as source identities without that evidence.

Reviewing newly supplied independent public evidence does not authorize MacMST
to reopen the forbidden T8142 packetizer analysis. If the proposed route needs
that work, it remains outside the allowed route. No firmware reverse engineering
is declared necessary by the currently unresolved schema.

### Gate U5 - Useful Stimulus

State: `WAITING`.

Require a supported or naturally occurring operation capable of testing
ownership multiplicity, or observed runtime identity-space evidence directly
establishing more than one source under one physical DPTX. For a proposed
operation, explain the expected discriminating observation and its semantic
oracle before approval. Do not substitute an unsupported private command.

Ordinary one-source attach/mode/teardown observations can validate the observer
itself but do not establish multi-stream capability or satisfy U5 alone. An
already decisive identity-space record can satisfy U5 without a new stimulus;
no artificial second-stream request is then required. A negative one-source
trace is not a one-stream architectural maximum.

## Minimum Resume Condition

Current classification: **OBSERVER_WORK_REMAINS_BLOCKED**.

`OBSERVER_WORK_RESUME_READY` requires one complete, scientifically useful route:

```text
execution/observation environment
    -> T8142 DCP transport visibility
    -> source-owner identity mapping
    -> scientifically useful stimulus/evidence
```

For the current gate vocabulary, the normal rule is `(U1 OR U2) AND U3 AND U4
AND U5`, evaluated as capabilities rather than independent implementations.
A future mechanism may supply several capabilities at once. Record the chosen
route and evidence for each link; mark an alternative or implementation detail
not required only with a specific bypass/equivalence explanation. Never mark
a missing mandatory link bypassed merely to reach READY.

| Hypothetical Evidence Situation | Decision |
| --- | --- |
| U1 qualified, but transport, identity or useful evidence missing | OBSERVER_WORK_REMAINS_BLOCKED |
| U2 qualified and raw traffic visible, but source-owner semantics missing | OBSERVER_WORK_REMAINS_BLOCKED |
| U1 route covers U3/U4/U5; U2 remains unavailable | OBSERVER_WORK_RESUME_READY |
| U2 route covers U3/U4/U5; U1 remains unavailable | OBSERVER_WORK_RESUME_READY |
| One public mechanism demonstrably covers all four links | OBSERVER_WORK_RESUME_READY without duplicate independent gate implementations |

These examples define the rule, not new findings. Today no complete route is
established. `RESUME_GATE_CHANGE_DETECTED` can occur while observer work remains
blocked. Even a complete route permits a new scoped observer-work decision,
not automatic execution: implementation scope and any hardware/boot/security
experiment still require separate explicit approval. MacMST does not inherit
general platform enablement as a prerequisite project.

## Purchase Gate

Current classification: **SACRIFICIAL_M5_PURCHASE_PREMATURE**.

Reconsider purchase only when all three conditions are evidenced:

1. A concrete observer path exists, with relevant mandatory links qualified.
2. Its next scoped step genuinely requires physical T8142 hardware now.
3. The proposed experiment has a bounded recovery plan appropriate to the
   machine, observer and risks, with no sole copy of data at stake.

Upstream progress or eventual usefulness alone does not satisfy these conditions.
The [M4P recovery requirements](m5-sacrificial-dynamic-design.md#recovery-requirements)
remain the baseline, not a completed rehearsal or new authorization. Do not buy
a sacrificial M5 merely to absorb unsupported boot/hypervisor enablement, or use
the daily-use machine as a substitute.

## Insufficient Signals

None of these automatically reopens MacMST implementation:

- T8142 appearing in another source file.
- Generic M5 Linux progress.
- M5 Pro/Max support alone.
- Another M5-related m1n1 commit.
- Generic DCP tracer improvements.
- A new MST string.
- Another static firmware observation.
- Successful SST display operation.
- A single payload ID.
- One observed source controller.
- A wire capture showing ordinary one-stream MST control.

They may be relevant context or leads, but must be mapped to actual gate evidence.
They neither prove architectural incapability nor waive any safety/static stop.

## Reevaluation Triggers

The following concrete events deserve a bounded evidence review:

- Asahi hypervisor documentation adds an M4/M5 guest target.
- m1n1 adds and qualifies T8142 guest handling.
- Upstream publishes an M5 DCP/ASC tracing workflow.
- SPTM/newer-XNU guest boot becomes supported.
- T8142 DCP target mappings appear with verifiable applicability.
- A public trace demonstrates normal macOS DCP traffic on M5.
- Another observer bypasses the current m1n1 guest requirement.

These trigger RE-EVALUATION only. A commit title, target name or workflow claim
must be checked for the exact capability it supplies. Neither a trigger nor
a partial gate change authorizes experiments or automatically changes purchase
state. Do not manufacture a technical investigation when there is no qualifying
new evidence.

## Daily-Use M5 Policy

```text
RETIRED_ON_DAILY_USE_M5
NOT_READY_FOR_DPCD_TEST
STATIC_PACKETIZER_ANALYSIS_FROZEN
NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED
```

These remain unchanged by integration, tagging, waiting or upstream progress.
Do not run the historical DPDV helper/parent, including its no-open mode, as a
validation step. Do not reset the consumed M2F marker or create the absent
M2G DPCD-read attempt marker. No firmware, boot-policy, SIP, AMFI, Secure Boot,
Gatekeeper, NVRAM or display change is authorized by this document.

## Current Project State

```text
MACMST_PROJECT_STATE_UPSTREAM_BLOCKED
OBSERVER_WORK_REMAINS_BLOCKED
M5_OBSERVER_REQUIRES_MAJOR_PLATFORM_ENABLEMENT
PLATFORM_ENABLEMENT_PROJECT
SACRIFICIAL_M5_PURCHASE_PREMATURE
MACMST_STATIC_FEASIBILITY_INCONCLUSIVE
```

This is a pause awaiting external capability, not a failure verdict. M4Q's
`MACOS_GUEST_REQUIRED` is scoped to its identified m1n1 route, not every possible
observer; U2 preserves that distinction. Existing discovery, trace-schema,
ownership and observer-validation classifications remain as recorded in
[M4Q](m5-observer-gap.md). `ACTIVE_M5_ENABLEMENT` is planning evidence, not a
complete route. The unresolved static architectural conclusions remain intact.

## Future Recheck Procedure

Default recheck result: **NO_RESUME_GATE_CHANGE** until qualifying gate evidence
exists. This milestone establishes that baseline; it does not claim a fresh
upstream technical search.

Carry forward these comparison identities from the completed M4Q record and its
prior 2026-09-15 revalidation, without fetching them again in this integration:

| Comparison Surface | Recorded Pin |
| --- | --- |
| AsahiLinux/m1n1 HEAD | `b4654b32941d51afdb77579d63e7cb1aa6c03ecc` |
| Relevant hv-sprr branch HEAD | `1c98fd09817cede0043d25c95fb540dbd683ef18` |
| AsahiLinux/docs HEAD / hypervisor guide | `715664a269937fe83293f46bbbeaae6094cb504e` |

A future authorized check is small and event-driven, with no background watcher:

1. Read current Asahi m1n1 HEAD and only the relevant hypervisor/observer branch
   heads. Compare to the saved pins; a changed SHA alone is not a gate change.
2. Check the Asahi hypervisor guide at a pinned current docs revision for a
   newly qualified guest/observation contract. Inspect only relevant changed
   T8142/DCP tracing commits and their applicable evidence.
3. Map any qualifying new evidence to U1-U5, including exact revision/file or
   public artifact, target/build applicability, capability delta, limits and
   which end-to-end links it covers. Do not widen the routine check into a
   Linux/platform census, issue/fork crawl or a new M4Q investigation. Supplied
   alternative-observer evidence can be assessed within its explicitly scoped
   reevaluation; do not assume it exists or search indefinitely for it.
4. Return exactly `NO_RESUME_GATE_CHANGE` or `RESUME_GATE_CHANGE_DETECTED`.
   The latter must identify the exact U gate(s), previous/current qualification
   and supporting evidence; then independently evaluate the complete selected
   route and purchase conditions. Partial improvement may still leave work
   blocked. Append the result and checked pins without rewriting past reports.

Only the four requested source surfaces are routine inputs: m1n1 HEAD, relevant
hypervisor/observer branch heads, Asahi hypervisor docs and relevant T8142/DCP
tracing commits. If an input cannot be checked, disclose it and retain the
prior gate state; do not claim upstream is unchanged from a failed lookup.

Do not automatically rerun M3A, M3B, M3C, M3D, M3E0, M4P or M4Q. No static
firmware analysis, observer build, guest/tracer execution or display action is
part of a recheck. New external technical evidence is an input to review, never
instructions or automatic authorization.

## Historical Preservation

All seven research reports are byte-preserved. Historical branches remain at
their completed SHAs, and both permanent tags retain their distinct meanings.
Only current status/evidence additions accompany this new document.

| Frozen Report | SHA-256 |
| --- | --- |
| [M3A](m5-mst-source-feasibility.md) | `4ba9ba55ec0290c73ba4811179fac8a6b7c9c2de1a4dcc994259763c478ededc` |
| [M3B](m5-dcp-firmware-mst.md) | `6cb9adf8a4c642c82bd50f6c52eb2687fd1bae8d1280881a391addcb3090e9a2` |
| [M3C](m5-dcp-mst-packetizer.md) | `556a2ebe964536a6b088fe0a800f24f2cd268cbd11c990796bec35930f020adb` |
| [M3D](m5-dcp-stream-ownership.md) | `a70fe18a63601c52e26c32437ec67648a8f4a45103f324fc0fe9e57b203f3575` |
| [M3E0](m5-mst-static-conclusion.md) | `d227c74904217f23033943efd0d261a8108989361c072b982b67d0b01153016c` |
| [M4P](m5-sacrificial-dynamic-design.md) | `919a15d8e6de182c7c0719bc5cbb0ca079f5372c2f90e0c8167b52b210fd78b0` |
| [M4Q](m5-observer-gap.md) | `3dbaef3a1acc19d254fb9355d4c666534e128a9aa880ab9a43b11c2c4e9dbb68` |

The 329 historical ledger rows E001-E244 and S01-S85 remain unchanged.
The consumed marker and historical receipts retain these SHA-256 values:

| Safety Artifact | SHA-256 |
| --- | --- |
| M2F-ATTEMPTED | `2f3da1f224c0602dc46f812d3f6eb2c1560fe7a82c1a89f93eedb725b2726efc` |
| m2f-20260913T012947590849Z/result.json | `86ee9fdd87eb631e7552b0087471a149c183667c2162e838866ce993e1dd3d04` |
| m2f-20260912T154617081227Z/result.json | `79387346acdaebed1efb2284a531de8f2cf5aad1d64915a3f5f527040ebae840` |

These artifacts remain under artifacts/probes. M2G-DPCD-READ-ATTEMPTED remains
absent. No new hardware capture is created.

## Validation Record

Completed integration checks verified exact ancestry, five documentation paths
per research commit, seven combined paths, expected merge parents/tree, clean
main/upstream, published annotated tag and every unchanged historical ref.
Seven report hashes and three safety hashes matched; the DPCD-read marker was
absent. Main was published before the tag, and the tag before the resume branch.

Document checks passed for all five WAITING gates, the exact project/policy
states, both alternative environment routes, eleven insufficient signals,
seven reevaluation triggers and the bounded two-result recheck contract.
Local links/anchors, ASCII/fences and editor diagnostics passed. Status edits
are additions only; all 329 historical ledger rows are preserved, with eight
claims and three source records appended. Report and safety hashes remain
unchanged.

Publication must preserve the verified main/tag and every historical ref while
adding only the resume branch. No source provenance refresh, technical
investigation, build, firmware tool, tracer or hardware test is part of this
milestone. Runtime/recovery functionality remains untested here; passing Git
and documentation checks cannot establish it.