# M5P0: T8142 Observer Platform Bootstrap

## Objective

The owner explicitly authorized a separate M5 Observer Platform Enablement
track on 2026-09-16. The previous project-wide upstream-wait decision no longer
prohibits this development track. Hardware execution and further T8142 DCP
packetizer reverse engineering remain prohibited. Historical reports and the
upstream-wait handoff are preserved, not rewritten as though the old decision
had never existed.

**Partial milestone: the independent offline consumer is implemented; platform
development is blocked before its pristine build.** No platform patch, capture
producer or qualified target-test path was produced.

MacMST started clean at resume-gates commit
`6edeb43700f0172f4a0bd5e4cbf9a13476deda5b`. Main/origin-main remain
`7250caac7a9f627f381b91ab9dfeb86191344ed9`; M4Q remains
`b11611e68f257d240fff6d93bc5307a305906d09`; observer-gap tag object
`b4fea86babb7115ce3313dd00bf5a36ff6e996e3` still peels to main. All 41 original
published branch/tag identities and consumed/absent safety guards were verified.
The new coordination branch is `research/m5-observer-self-enable`, based on the
completed resume-gates branch. Its only implementation is the offline consumer
and synthetic tests explicitly requested in Part 13, not platform code.

The separate sibling clone is `/Users/ysoli/Projects/m1n1-MacMST`, outside
MacMST's Git history. While reading its build instructions, the tracked
[upstream agent policy](https://github.com/AsahiLinux/m1n1/blob/1c98fd09817cede0043d25c95fb540dbd683ef18/AGENTS.md)
was found to prohibit AI/LLM work and direct agents to stop. Its Git blob is
`44d5b4f7118289132c1f7b1a2ea9447d4f66b3b3`; it links to
[Asahi's policy](https://asahilinux.org/slop/). Work in that repository was
stopped before a build or source edit. This records a repository-workflow
blocker, not a compiler failure or an interpretation of its software license.
A human platform-development handoff or resolution with the maintainers is
needed before that portion can proceed. No attempt was made to remove, alter
or bypass the policy.

## Upstream Pins

Fresh official remote queries in M5P0 returned:

| Source | Revision |
| --- | --- |
| AsahiLinux/m1n1 main | `b4654b32941d51afdb77579d63e7cb1aa6c03ecc` |
| AsahiLinux/m1n1 hv-sprr | `1c98fd09817cede0043d25c95fb540dbd683ef18` |
| AsahiLinux/docs HEAD | `715664a269937fe83293f46bbbeaae6094cb504e` |

The official m1n1 repository was cloned and checked out detached at the exact
hv-sprr pin. Fetch remote `upstream` is
`https://github.com/AsahiLinux/m1n1.git`; its push URL is deliberately
`DISABLED_DO_NOT_PUSH`. No user-owned fork is configured. No upstream push,
fork creation, platform development commit or `macmst/t8142-observer` branch
was made: branch/patch work remains gated on the unperformed pristine build.
The current docs identity was recorded, not used to repeat a technical search.

## hv-sprr Architecture

The local `main...hv-sprr` diff metadata confirms the previously recorded
14-file branch delta. Architectural traversal, per-file dependency
classification, guarded-state/genter/gexit/sysreg/exception inspection and B1
re-evaluation were not performed after the policy blocker was found.

The [M4Q branch assessment](m5-observer-gap.md#development-branches-and-discussion)
remains historical evidence, not a fresh M5P0 architectural analysis or boot
receipt. No new B1 classification is asserted. In particular, neither partial
SPRR/GXF code nor its existence is promoted here to an SPTM-aware working guest.
The requested platform dependency graph remains an explicit uncompleted item.

## T8142 Selector Audit

No selector patch or comprehensive current-selector audit was performed. The
[M4Q CPU-start finding](m5-observer-gap.md#m5-hypervisor-blockers) is retained
as a lead for a human platform worker, not automatically fixed in the clone.
No addresses were guessed, no nearby SoC lists were mechanically extended,
and no runtime failure was patched by analogy.

CPU start, AIC, UART, essential mappings, DART/SID and ASC/DCP discovery still
need the requested source audit on the development branch once the blocker is
resolved. They are not all classified as broken merely because this work is
incomplete. No claim of `GENERIC_DISCOVERY_ALREADY_SUFFICIENT` is made for the
complete target path.

## Guest Preconditions

The target remains Mac17,2 / J704AP / T8142, macOS 26.6.2 build 25G83. No Apple
binary was obtained, redistributed, loaded or executed in M5P0. These distinct
preconditions remain unqualified in this milestone:

| Layer | M5P0 Status |
| --- | --- |
| Image loading/format | No fresh guest-loader audit or 25G83 input validation performed |
| Trust/security-monitor state | No new SPTM/TXM contract or initialization qualification |
| Guest execution | Not attempted; no boot, debugger attachment or exception-transition test |
| Target-specific fixups | None implemented; no unknown fixups inferred from M4 or another SoC |

These are incomplete source/design/build prerequisites, not all runtime-only
unknowns. A future hardware test must not be used to conceal an unreviewed
loader or security-monitor architecture. No boot-policy change is supplied as
a routine prerequisite or workaround.

## Observer Capture Schema

**Proposed offline schema version 1. No live producer exists for it yet.** The
format is independent of m1n1 and MacMST ownership interpretation. Each line is
one UTF-8 JSON object; the final complete line may omit its newline. Blank lines,
duplicate object keys, non-finite numbers, malformed JSON and unsupported
schema versions are rejected. Unknown fields at every object level are retained
as JSON values, not interpreted as capabilities.

| Required Field | Meaning / Validation |
| --- | --- |
| schema_version | Integer 1; booleans are not integers for schema validation |
| capture_generation | Nonempty capture/boot-generation identifier, at most 256 characters |
| record_index | Unsigned 64-bit monotonic index per generation; a producer starts at zero; gaps including a missing prefix are reported |
| timestamp_ns | Unsigned 64-bit host monotonic timestamp in nanoseconds, nondecreasing per generation, not wall-clock time |
| kind | request, reply, event or loss |
| direction | host_to_dcp, dcp_to_host, or none only for loss records |
| asc | Nonempty observer-supplied transport identifier; not a physical-DPTX assertion |
| endpoint / channel | Nullable unsigned 8-bit endpoint / unsigned 32-bit channel |
| service | Nullable nonempty service name, at most 256 characters |
| opcode / request_id | Nullable unsigned 64-bit integer or nonempty string, at most 256 characters; integer and string IDs remain distinct |
| payload_length | Retained payload length in bytes, at most 1 MiB |
| raw_payload | Exactly twice payload_length hexadecimal characters, no whitespace/separators; empty payload is an empty string |
| loss_state | Object with status, dropped_records and detail as defined below |

Capture envelopes and otherwise undecoded bytes may be retained in extension
fields. A future producer must preserve full request/reply data before any
semantic decoder; this independent importer does not add that hook to m1n1.
The offline size limit is an explicit acceptance limit, not a claim about the
largest DCP message. It never silently clips input to fit.

`loss_state.status` is none, dropped, wrapped, truncated or unknown.
`dropped_records` is a nullable unsigned 64-bit count: none requires zero and
dropped requires a positive value. `detail` is null or a nonempty string of at
most 256 characters. An explicit loss record cannot claim status none. Unknown
drop counts remain unknown, not guessed from a ring wrap.

Optional `declared_payload_length` records the original length and must be at
least the retained length. A larger value requires truncated or unknown loss;
truncated status requires a strictly larger declared length. Thus a valid
partial-record report is distinguishable from an unmarked length mismatch,
which is rejected. No incomplete record is called lossless.

Optional `correlation` contains nonempty `scope` and `evidence` strings, each
at most 256 characters. It is permitted only on request/reply records with
nonnull request_id, endpoint and channel. The scope denotes a producer-declared
request-ID/lifetime namespace; evidence records its rationale. The importer
does not independently verify that rationale. Equal numeric IDs alone are not
enough to pair requests and replies.

An illustrative synthetic request, not a hardware capture:

```json
{"schema_version":1,"capture_generation":"synthetic","record_index":0,"timestamp_ns":1000,"kind":"request","direction":"host_to_dcp","asc":"synthetic-asc","endpoint":42,"channel":7,"service":"synthetic-service","opcode":"unknown-operation","request_id":23,"payload_length":2,"raw_payload":"00ff","loss_state":{"status":"none","dropped_records":0,"detail":null},"correlation":{"scope":"synthetic-channel-lifetime","evidence":"Synthetic test contract only"}}
```

Optional `annotations` supports physical_dptx, source_identity, timing_identity,
payload_identity, confidence and evidence. Missing values are exposed as
`UNKNOWN` by the annotation accessor. Supplied identities/confidence are strings;
a claimed identity requires explicit non-UNKNOWN confidence and a nonempty
list of evidence strings. These are externally supplied annotations, never
automatic proof or a decoder heuristic. Extension annotation fields survive
round-trip validation too.

## MacMST Offline Consumer

[tools/dcp_trace_import.py](../../tools/dcp_trace_import.py) uses only the Python
standard library and opens a regular offline input file. It has no m1n1 import,
device-discovery code, subprocess launcher, network connection, private API or
live DCP transport. The separate source implementation does not depend on
upstream decoder code.

The CLI emits a deterministic summary by default. `--records` instead emits
all validated records, including extension fields and undecoded raw bytes.
Records are validated/spooled first, so malformed later input does not publish
a partial record stream. This preserves JSON values, not the original file's
whitespace or textual number representation. Raw-payload hex contents are not
decoded into ownership claims. Captures may contain sensitive data; no automatic
upload or privacy-redaction claim is made.

```sh
python3 tools/dcp_trace_import.py capture.jsonl
python3 tools/dcp_trace_import.py capture.jsonl --records
```

The example filename denotes a future supplied offline capture. No live capture
was collected or imported in M5P0. Tests create only synthetic temporary files.

Resource limits are 1 MiB retained payload per record, 2 MiB plus 64 KiB per
JSONL line, 256 MiB input and 100,000 records. Oversized/malformed records,
regressing indexes and regressing timestamps are rejected rather than silently
accepted as complete. A gap or explicit loss invalidates pending correlations
in that generation. Pairing requires matching generation, ASC, endpoint,
channel, service, declared scope and typed request ID, with opposite directions.
Duplicate in-flight IDs or same-direction responses are marked ambiguous;
IDs may be reused after a completed unambiguous exchange.

Summary channels/services/opcodes are counts, not source/controller counts.
`record_coverage_complete` describes only the recorded index/loss information,
not whether a producer observed every event or a whole firmware lifecycle.
Unmatched replies, pending requests, ambiguous IDs, inferred index gaps and
reported drop counts are separate. The importer always reports ownership as
`UNKNOWN` and `ownership_inferred` as false, even when annotations are supplied.

[Synthetic tests](../../tests/test_dcp_trace_import.py) cover request/reply,
unknown opcode/fields, empty payload, maximum/oversized payload, malformed and
truncated input, duplicate keys, non-finite values, explicit drop/wrap state,
generation/context separation, ambiguous/reused IDs, annotation limits and CLI
all-or-error record publication. All 21 tests pass. CTest registration is
`dcp_trace_import`, labeled unit/offline; it never runs the hardware probe.

## Patch Queue

| Repository / Change | Commit / State | Classification |
| --- | --- | --- |
| MacMST offline consumer, tests and CTest registration | `5dfad2d6113d6b9a1138f57502750c6897e8bd16`, tools: add offline DCP trace import validation | MACMST_ONLY |
| MacMST coordination/schema/blocker record | Separate documentation commit on research/m5-observer-self-enable | MACMST_ONLY |
| T8142 guest selector fix | Not implemented or committed | No patch to classify |
| Lossless upstream transport producer | Not implemented or committed | No patch to classify |

There is no platform patch series and no upstream-generic submission claim.
The platform clone is pristine, detached at the hv-sprr pin with upstream pushing
disabled. Its development branch is intentionally not created before a
successful pristine baseline build. No official Asahi repository is pushed.
MacMST changes are committed locally, without a merge or PR; no publication is
needed to represent this incomplete platform milestone as successful.

## Build Matrix

| Target | Command / Configuration | Result |
| --- | --- | --- |
| Pristine pinned hv-sprr | None: stopped at repository agent-policy check | NOT RUN; neither HV_SPRR_BASELINE_BUILDS nor a compiler failure is claimed |
| Patched macmst/t8142-observer | No branch or patches produced | NOT RUN |
| MacMST C++/Objective-C++ build | CMake/Ninja Debug; hardware tests OFF; DPDV experiment OFF; existing strict warnings including -Werror | PASS, 16 build actions; produced native binaries not executed |
| Independent Python importer/tests | Python 3.14.6, -X dev -W error unittest and py_compile | PASS, 21 synthetic tests and byte compilation |
| Offline CTest entry | ctest -R '^dcp_trace_import$' | PASS, 1/1; Python tests only |

Build host compiler: AppleClang 21.0.0.21000101, arm64 macOS, CMake 4.4.1.
No m1n1 compiler invocation or dependency installation occurred. Available
host tool locations are not an established m1n1 build toolchain. No baseline
artifact hashes or warning counts are invented for a build that did not run.

Executed MacMST validation commands:

```sh
python3 -X dev -W error -m unittest discover -s tests -p test_dcp_trace_import.py -v
python3 -m py_compile tools/dcp_trace_import.py tests/test_dcp_trace_import.py
cmake -S . -B build-m5p0-offline -G Ninja -DCMAKE_BUILD_TYPE=Debug -DMACMST_ENABLE_HARDWARE_TESTS=OFF -DMACMST_ENABLE_DPDV_OPEN_EXPERIMENT=OFF
cmake --build build-m5p0-offline
ctest --test-dir build-m5p0-offline -R '^dcp_trace_import$' --output-on-failure
```

No compiler warnings were emitted by that MacMST build. Recorded SHA-256:

| Artifact | SHA-256 |
| --- | --- |
| Offline importer source | `f0b9538bae5dc89db4a83c9205074c60b127b593d34436da51306d10b4d7a8ba` |
| Synthetic tests source | `05858901e8aa7320227e26b2c94c5e342665fd1b5a4a78490323be2078e943e2` |
| Unexecuted build-m5p0-offline/macmst | `2604f1f92cfb4b29943a7240e9abe82bf87c3be55802fc2deb94d85104296520` |
| build-m5p0-offline/libmacmst_displayport.a | `e08f6a3ef901a77d1d0e8c9b0df5c55d73a5531fe8e9da93e4aacfb0f9eabdd8` |

These prove only host build/output identity, not target functionality. The
existing firmware-scanner tests, hardware tests and private helper modes were
not run. No resulting native binary or boot payload was executed.

## Runtime-Only Unknowns

Once a reviewed and built platform implementation exists, runtime evidence
would be needed for actual T8142 guest stability through normal DCP startup,
correct passive request/reply observation with real buffer lifetimes, capture
loss/latency under real traffic and recoverability after observer failure.
None is tested here. Such evidence could come from separately authorized
hardware testing or qualified independent target results.

The repository-policy blocker, missing baseline build, unperformed B1/selector
audit, absent producer and unresolved source-owner contract are not classified
as runtime-only gaps. They require workflow, code or evidence work first.
Owning hardware would not by itself resolve them.

## Hardware Readiness Gate

**M5_OBSERVER_CODE_NOT_READY_FOR_TARGET_TEST**.

The pristine and patched hv-sprr builds are absent; platform compile/static
blockers have not been reviewed; no producer or producer losslessness tests
exist; and no bounded test procedure for a completed patch set can be supplied.
The 21 importer tests do not substitute for those gates. M4P's documented
recovery prerequisites remain references, not a recovery rehearsal or execution
approval. No B1 success or boot-success claim is made.

## Purchase Decision

**SACRIFICIAL_M5_STILL_PREMATURE**.

The next meaningful task is resolving the platform workflow blocker and
completing code/build qualification, not executing a finished patch set on
T8142. No purchase is justified by the independent parser alone. The current
daily-use M5 must not be substituted for sacrificial hardware.

## Safety Policy

Preserve `MACMST_STATIC_FEASIBILITY_INCONCLUSIVE`,
`STATIC_PACKETIZER_ANALYSIS_FROZEN`,
`NO_FURTHER_T8142_PACKETIZER_REVERSE_ENGINEERING_AUTHORIZED`,
`RETIRED_ON_DAILY_USE_M5` and `NOT_READY_FOR_DPCD_TEST`.
The owner's strategy change authorizes a separate compile/offline development
track; it does not reopen packetizer research or permit live target operations.

No m1n1, hypervisor, tracer, boot payload, live debugger, DCP/AUX/DPCD command,
display transition, partition change, 1TR/DFU entry, boot-policy command or
security reduction was performed. The USB-C hub and two monitors are not needed
for this offline work. Historical MacMST reports, branches/tags, the consumed
M2F marker/receipts and absent M2G DPCD-read marker remain unchanged.