# M2F: First Isolated DPDV Open/Close

**Outcome: EXPERIMENT_NOT_RUN.** The fresh dry-run preflight observed zero active
external displays and LinkRate=0 / No Link. The coordinator stopped before the
real helper was spawned. No DPDV open, close or selector was attempted. The
implementation is committed, but the helper's live selection path is not validated.

## Authorization And Boundaries

This milestone is explicitly authorized to attempt exactly one
`IOServiceOpen(service, mach_task_self(), 0x44504456, &connection)` against the
fresh External DCPDPDeviceProxy, followed immediately by `IOServiceClose` only
on successful open with a nonzero connection. There is no retry, intentional
dwell, selector, IODP constructor, DPCD, AUX, IOI2C request or MST operation.

This is an authorized risk-bearing experiment, not a retrospective static safety
proof. The selected provider may take the unresolved IOUserServer/DriverKit route.
A userspace watchdog bounds parent observation, not kernel-call cancellation;
SIGKILL and successful reaping do not certify firmware/kernel quiescence. Prior
NOT_READY_FOR_ISOLATED_DPDV_OPEN_CHECK and USER_SERVER_RUNTIME_STATE_UNRESOLVED
remain historical findings. The global gate stays **NOT_READY_FOR_DPCD_TEST**.

The user's mandatory preflight stop condition took precedence over the otherwise
explicit one-shot authorization. No retry, display wake/reconfiguration or further
runtime capture was performed after that stop. The forensic tag remains before
any private display operation executed by this project.

## Integration And Forensic Tag

M2E.1 was checked against its clean audited three-commit history ending at
`823b2748bb69ea134bbf75052d489ad0448d967a`, then merged with `--no-ff` as
`1fc8f0241acec829fa732503c13a9ab588e26fb0` and pushed to main. Parents are
`ce28518eb301592ed6dd3d2b75d152b1a8e54970` and the M2E.1 HEAD; the merge tree
equals M2E.1 exactly.

Before real-operation code was added, annotated tag `pre-dpdv-open-v0.2` was
created and pushed. Tag object: `f01208571d395ded9857a2c663f5276e12220c49`.
Peeled commit: `1fc8f0241acec829fa732503c13a9ab588e26fb0`.
Message: `Verified MacMST state before first private DPDV IOServiceOpen experiment.`
Main, tag object/target, all historical branches and `research-baseline-v0.1`
were verified remotely. This tag must never move. Implementation and any execution
are confined to `experiment/dpdv-open-check` based on that commit.

## Initial Public Preflight

G10, artifacts/probes/20260912T152130Z, ran before real-helper implementation:
40 public read-only commands, zero failures. Report SHA-256:
`379893719ef0c159a840aca4988a037f7354e742a9f646584fc51c7e3a50fa96`.

- Apple M5, Mac17,2, arm64, macOS 26.6.2 (25G83).
- One active external logical display, 1920x1080 at 60 Hz, not in a mirror set.
- One External Unit 0 DCPDPDeviceProxy and matching supported DCPDPServiceProxy
  under RTBuddy(DCPEXT0); no Embedded fallback.
- One active USB-C DisplayPort path, HPD raw 2 / High, two lanes, raw LinkRate 4 /
  Apple HBR3 description, SinkCount 1, Tunneled=false.
- Public result remains PUBLIC_IOFRAMEBUFFER_PATH_UNAVAILABLE.

The relevant semantic state matches G9. Registry IDs from G10 are comparison
evidence only, not selection authority. A new BEFORE capture and independent
helper enumeration are required immediately before the real attempt.

## Implementation

The normal `macmst` executable remains a public-only probe. A separate opt-in
`macmst_dpdv_open_check` parent bridge reuses M2C's spawn/drain/watchdog/reap loop;
`macmst_dpdv_open_helper` is the only binary containing the open/close operations.
[The Python coordinator](../../tools/dpdv_open_check.py) performs public preflight,
audit, receipt checks and BEFORE/AFTER capture. These are not operations inside
the normal probe process.

`MACMST_ENABLE_DPDV_OPEN_EXPERIMENT` defaults OFF. The helper links IOKit and
CoreFoundation only for registry selection, class/property reads, reference
cleanup and the authorized open/close; no CoreGraphics, Foundation, IODP dynamic
resolution, IOConnect machinery or transport library is linked into it.

The helper enumerates exact classes independently. It requires one External
Unit 0 supported device and service, matching DCPEXT0 processor prefixes, one
active HPD-High/two-lane/HBR3/non-tunneled/single-sink path, and compares the three
fresh IDs with the parent. It receives no handles, Mach ports or connection.
The operation is outside all enumeration loops. Failure/ambiguity exits before
open. `--no-open` performs the same selection, then reports without opening.

There is one source and compiled callsite for IOServiceOpen and one for
IOServiceClose. A successful nonzero connection is closed immediately after
reading the monotonic completion timestamp; no message is emitted and no deliberate
wait occurs between open and close. Open failure never calls close. Success with
a null connection is an internal error. A failed close is not retried. All registry
and CF references unwind before the final result is sent. Raw connection values
are never serialized.

## Protocol And Watchdog

The fixed little-endian frame is 64 bytes: magic M2FO, version 1, phase, flags,
reserved byte; raw precheck/open/close return bit patterns and reason; transient
device/service/transport IDs; open and close elapsed microseconds. Flags distinguish
open attempted, open result available, open succeeded, nonzero connection,
close attempted and close result available. Unknown results are not represented
as successful zero in parent JSON.

Dry run/precheck failure uses one frame. A real attempt emits an OPEN_ATTEMPTED
intent frame immediately before the sole call, then a terminal frame after
cleanup: OPEN_FAILED, CLOSE_SUCCEEDED, CLOSE_FAILED or INTERNAL_ERROR. A lone
intent frame after abnormal death is not proof the call returned or even began;
it is retained as intent, with no fabricated status. Two-frame IDs must agree
and match parent comparison values. Missing/truncated/malformed/oversized data,
inconsistent flags, unexpected mode or bad process exit cannot become success.

The inherited parent policy uses CLOEXEC file actions, empty signal mask/reset
dispositions, /dev/null stdin, only LC_ALL=C, bounded stdout/stderr, nonblocking
drains and waitpid. M2F uses a 30-second post-spawn observation deadline, one
SIGKILL attempt on failure, and a five-second bounded reap grace. Reap failure
does not signal a potentially reused PID. Spawn, OS scheduling and kernel work
are not proved to obey a hard wall-clock bound. The coordinator does not kill
the parent with an outer timeout.

Before real spawn, the parent creates/fsyncs an O_EXCL/O_NOFOLLOW mode-0600 marker
at artifacts/probes/M2F-ATTEMPTED. The coordinator uses this fixed path and refuses
any subsequent run once it exists. It is never deleted or reset. Reserving an
attempt can prevent future runs even if precheck/spawn subsequently fails; safety
takes priority over recovering the opportunity. There is no automatic startup,
reboot resume, retry or privilege escalation. An unreaped timeout requires stopping
all private work and recommending reboot before any later separately authorized work.

## Pre-Execution Gates

Before the sole real attempt, all of the following must pass:

1. Strict and sanitizer builds; unit, parser, original 13-scenario mock and new
   eight-scenario M2F-framing regressions; public-only hardware probe.
2. Helper import/source/disassembly audit: one open, one close, no IOConnect,
   IODP functions, dynamic lookup, intentional dwell or operation retry loop.
3. The parent/probe have no private-operation imports; marker-refusal test spawns
   no helper. Tests never run a real private open.
4. Dry-run helper/parent agreement, normal exit and reaping, no operation flags.
5. Implementation committed and clean, exact forensic tag and experiment branch,
   dry-run commit/source/binary hashes matching the real attempt.
6. Fresh public BEFORE state equals the initial preflight semantics; its IDs
   agree with the dry-run receipt. The helper independently checks again.

The existing mock cases remain intact. Eight additional cases use only the mock
executable: M2F dry-run, successful pair, denial, close failure, progress hang,
post-result hang, malformed frame and comparison-ID mismatch. No real helper is
registered as a hardware test. The expanded suite checks 28 mock children total:
27 explicit reaps and one intentional auto-reaped ECHILD ownership case.

## Outcome Rules

The coordinator records a privacy-filtered BEFORE capture, prepared receipt and
source/binary hashes before invoking the parent once. After any returned result,
it attempts the same public AFTER capture while the parent environment remains
functional. Semantic comparison excludes transient registry/display IDs and
includes external count/mode/refresh, processor path, endpoints, HPD, lanes/rate,
Active, tunneling and sink count. A missing AFTER result is explicitly unavailable.

Normal fast denial plus unchanged public state is DPDV_OPEN_DENIED_CLEANLY.
Successful open/close plus unchanged public state is
DPDV_OPEN_CLOSE_SUCCEEDED_NO_PUBLIC_STATE_CHANGE. Close error, changed display
state, timeout/unreaped helper or crash selects the corresponding safety-stop
outcome. Unexpected incomplete evidence is recorded as inconclusive rather than
inventing a crash or a successful unchanged-state result. No outcome causes a retry.

Only a successful pair with unchanged public state establishes
DPDV_OPEN_CLOSE_RUNTIME_VALIDATED. It does not reveal userServer, prove a native
route, show absence of internal work, establish general safety or permit selector 0.
The next milestone, if warranted by the actual result, must separately reassess
selector-read reply completeness, unbounded waits and cancellation limitations.
**NOT_READY_FOR_DPCD_TEST remains unchanged.**

## Runtime Record

The implementation was strictly compiled and audited, and the full strict and
sanitizer suites passed before a dry-run coordinator invocation:

```sh
python3 tools/dpdv_open_check.py --no-open --preflight artifacts/probes/20260912T152130Z
```

That command did not reach the helper. Its fresh capture at
artifacts/probes/m2f-20260912T154617081227Z/before completed 40 public commands
with zero command failures, but semantic preflight rejected it at 15:46:18 UTC:
`Expected one active external logical display`.

| Field | Initial G10 / 15:21:30 UTC | Dry-Run BEFORE / 15:46:18 UTC |
| --- | --- | --- |
| Active external logical displays | 1 | 0 |
| External display present / mode | Present, 1920x1080 at 60 Hz | Still listed, same mode, active=false |
| Internal display active | true | false |
| External device/service | One supported External Unit 0 pair | Pair still present with supported properties |
| Processor correlation | RTBuddy(DCPEXT0) | Same processor path |
| DP Active / HPD | true / raw 2 High | true / raw 2 High |
| Lane count | 2 | 2 |
| Link rate | raw 4 / 8.1 Gbps (HBR3) | raw 0 / No Link |
| Tunneling / sink count | false / 1 | false / 1 |
| Public-path result | PUBLIC_IOFRAMEBUFFER_PATH_UNAVAILABLE | PUBLIC_PATH_UNRESOLVED |
| Public probe errors | none | none |

This is a material change before any private operation. The failure is not an
IOServiceOpen denial or an experiment-induced display-state change. The cause of
inactive displays/link state is not established; no wake, cable change or other
restoration was attempted to bypass the gate. Stale candidate activity annotations
do not override the freshly measured active-display count and raw link rate.

### Exact Attempt Record

| Requested Runtime Fact | Observed Result |
| --- | --- |
| Real helper spawned | No, count 0 |
| Dry-run parent/helper target agreement | Not tested: stopped before child spawn |
| IOServiceOpen attempted | No, count 0 |
| Raw open result / elapsed time | Unavailable, no call |
| Connection returned | No connection created |
| Selector calls | 0 |
| IOServiceClose attempted / raw result | No / unavailable |
| Helper exit / watchdog / reaping | Not applicable; helper never started |
| Prepared real-operation receipt | Absent |
| Durable M2F attempt marker | Absent; no real spawn was reserved |
| AFTER capture | Not taken; no experiment occurred and the stop was honored |
| AFTER comparison | AFTER_STATE_UNAVAILABLE, not a claimed unchanged state |
| Primary outcome | EXPERIMENT_NOT_RUN |
| DPDV runtime gate | DPDV_OPEN_CHECK_PREFLIGHT_FAILED |
| Global gate | NOT_READY_FOR_DPCD_TEST |

The first coordinator version exited before writing a structured failure receipt.
A recording-only fix now persists preflight stops before any spawn. It was tested
offline, and an explicitly labeled offline receipt was generated from the retained
capture without replaying the command. That receipt records
`implementation_committed_at_preflight=false`: the failed command was a development
dry run, not an authorized real execution of uncommitted code. No open-mode command
was run before or after implementation commit
`d7f41b8cea54e57534da7cedcd21c6afdc9e34ed`.

### Evidence Hashes

| Artifact | SHA-256 |
| --- | --- |
| G10 initial public report | `379893719ef0c159a840aca4988a037f7354e742a9f646584fc51c7e3a50fa96` |
| Stopped dry-run BEFORE public report | `9bb2d4aaf062d567d2b0c76c9bbd5c3e6194bbf97658ec0c8b8b20e1d74e723f` |
| Stopped BEFORE manifest | `27c18c5c0ef98c3e0ee5708bf88c260f707aad1ca056129e7983708299ff0e81` |
| Offline stop result.json in the same m2f directory | `79387346acdaebed1efb2284a531de8f2cf5aad1d64915a3f5f527040ebae840` |
| Unchanged public macmst binary | `450832c50446d3a430cbed2bcab7c285cddf5f6b370b2339df2cd0a33aefd89a` |
| Built, unexecuted real helper | `4ffc55f505364467f82cbd5685be3af976be8dc01990081dfaf240b2261535cc` |
| Parent bridge binary | `834c856d7761e944055f5a1f6020a6d3ecd28834d69156430885df3de8e50a4b` |

All raw public captures and the offline receipt remain ignored. Their source
and binary provenance is retained without EDID, serials or private port values.
The recording-only fix did not change native binaries or the retained captures.

## Validation Results

| Pre-Execution Check | Result |
| --- | --- |
| Strict opt-in build | PASS, `cmake --build build` |
| Strict unit/mock/parser/import/audit suite | PASS, 9/9 CTest entries |
| Public-only hardware test | PASS, 1/1 before the later preflight change |
| Sanitizer opt-in build | PASS, existing ASan/UBSan flags |
| Sanitizer unit/mock/parser/import/audit suite | PASS, 9/9 entries |
| Existing static parser/inspector tests | PASS, 60 methods |
| Original M2C mock regression | PASS, all 13 scenarios preserved |
| New M2F-framed mock regression | PASS, eight scenarios using mock executable only |
| Import/source/disassembly audit | PASS, one compiled open and close callsite; zero IOConnect/IODP imports, no dynamic lookup/dwell/operation loop |
| Parent/probe separation | PASS, neither imports IOServiceOpen/Close; probe code and CLI unchanged |
| Marker-refusal test | PASS, existing file unchanged, zero spawns, nonexistent helper path supplied |
| Dry-run helper selection | BLOCKED before spawn by fresh public preflight |
| Final stop-recording fix | PASS, nine focused Python contract tests, no real helper or probe rerun |
| Documentation/provenance | Hashes, links/fences, preserved historical reports and diff whitespace verified |

The two full suites ran the eight contract methods present before the stop;
the final ninth method covers the accurate stop receipt. No post-stop private
operation or repeated public preflight was used as a validation shortcut.
Mock timings were 5.18 seconds strict and 6.94 seconds sanitized for the combined
original/new isolation entry; these are test durations, not real driver bounds.

## What Was Learned

The preflight gate correctly prevented a helper spawn when the required active
display/HBR3 state was absent. Compiled separation, protocol/watchdog behavior
and synthetic failure handling were validated. Runtime DPDV authorization,
accepted class/route, open/close duration, userServer value and hardware effects
were not measured. DPDV_OPEN_CLOSE_RUNTIME_VALIDATED is **not established**.

No selector 0 or DPCD decision is made here. The next separately authorized work
must first re-establish the normal active-display/HBR3 public state, then complete
a committed-code `--no-open` selection check. This stopped milestone must not
resume automatically or retry the open under the earlier authorization.