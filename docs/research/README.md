# MacMST Phase 0 / Milestone 1

## Scope

Establish a reproducible, read-only baseline of this M5 host, its macOS display
services, and the attached USB-C dock. Do not attempt to enable MST. Neither
source MST hardware nor its absence is established.

## Results And Navigation

Milestone 1's internal-only captures remain below as history. Milestone 2A now
has a controlled ZMUIPNG hub connected/disconnected/reconnected cycle and an
External DCPEXT0 path. The updated probe reports actual graph neighbors and
conservative candidate pairs. ABI-02 now resolves CF cleanup, authenticated
caller bindings and the concrete DPDV/selector-0 host path. It reaches a DCP
register RPC. RPC-03 establishes host zero-fill and AFK reply handling but finds
no local reply deadline and a no-op abort hook. Complete-reply/firmware semantics
and actual process authorization remain unestablished.
**NOT_READY_FOR_DPCD_TEST** remains the result.

The `research/dcp-rpc-safety` branch builds on the published RPC-03 report rather
than repeating the host ABI work. G5/R4/R5 add fresh target/signing provenance,
direct notification/recovery callers, pre-send admission waits and concrete
endpoint cleanup. The [explicit matrix](dcp-dpcd-rpc-03.md#readiness-gates) requires
every gate to be PASS. This completed milestone is now integrated by merge
`2ffc77d9d532502495fca5d88291d42eed61e45b`; its branch and baseline tag are retained.

The subsequent `research/public-dp-native` branch is enumeration-only. P1 observes
an active external display but a null public CG service and no published
IOFramebuffer/I2C interface, including the alternate registry search:
**PUBLIC_IOFRAMEBUFFER_PATH_UNAVAILABLE**. It makes no public or private
transaction, and every private RPC-safety gate remains unchanged.

- [Evidence ledger](evidence-ledger.md): canonical claims, captures, exact sources.
- [M5 display stack](m5-display-stack.md): DCP/DCPEXT and current service paths.
- [AUX access](aux-access.md): IODPDeviceReadDPCD candidate, alternatives, safety gates.
- [DisplayPort/MST](displayport-mst.md): source-backed constants and decoder limits.
- [Dock observations](dock-observations.md): unobserved versus user-reported topology.
- [Open questions](open-questions.md): all 14 questions and the Milestone 2 experiment.
- [ADR 0001](../adr/0001-language-and-architecture.md): language and architecture choice.
- [External differential](external-dock-diff.md): C1/D1/C2 repeatability and G2 graph.
- [IODP API investigation](iodpdevice-api.md): A1 static evidence and remaining gates.
- [ABI-02 read contract](iodpdevice-abi-02.md): G3/A2, resolved lifecycle/dispatch,
  per-argument confidence, exact caller bindings, preflight and one-byte proposal.
- [RPC-03 safety contract](dcp-dpcd-rpc-03.md): G4/R3, request/reply layouts,
  short replies, no-deadline waits, failure/cancellation and all 13 readiness gates.
- [DPDV authorization](dpdv-authorization.md): class-local versus outer policy
  gates, on-disk probe identity and the unresolved actual-access classification.
- [Public DP-native investigation](public-dp-native.md): installed SDK ABI,
  pinned implementation comparisons, P1 mapping/capabilities, validation and limits.

The user reports two physical monitors connected to one USB-C dock showing the
same image. This is an input to investigate, not proof of the dock's transport,
chipset, MST support, or the number of source streams.

## Initial Inspection

Observed at 2026-09-12T00:14:24Z (local date 2026-09-11):

- Repository initially contains only the Copilot instructions, read-only researcher
  definition, and VS Code setup audit. No application, tests, or build files exist.
- Git branch `main` has no commits; `.github/` and `docs/` are untracked. No local
  AGENTS.md, CLAUDE.md, or scoped instruction files were found. Preserve existing
  configuration documentation and do not push.
- Host reports Apple M5, arm64, macOS 26.6.2 (25G83).
- Xcode 26.6 (17F113) is selected at `/Applications/Xcode.app/Contents/Developer`;
  active macOS SDK is 26.5, older than the running OS.
- Apple Clang 21.0.0 (clang-2100.1.1.101), Swift 6.3.3, Swift Package Manager
  6.3.3, CMake 4.4.1, Ninja, make, Homebrew, Python 3, Git, and ripgrep are present.
  Objective-C++ interoperability will be verified by compilation, not assumed.
- No dependency installation is planned. No system configuration changes are
  authorized. The existing chat's permission state is still Allow All; do not
  treat that as permission to execute anything outside this task's safety scope.

## Execution Plan

1. Capture targeted system_profiler and IORegistry observations, keeping only
   relevant fields and redacting serial numbers, UUIDs, addresses, and unrelated
   devices before writing artifacts. Record commands, UTC time, OS, schema, and
   failures. Preserve raw numeric values and their provenance.
2. Inspect primary Linux DisplayPort definitions, Asahi/m1n1 DCP implementations,
   Apple public interfaces, and reproducible IOAVService projects. Pin important
   sources to revisions. Separate source evidence from this M5's observations.
3. Write a language/architecture ADR. Evaluate C, C++, Objective-C++, Swift, and
   mixed stacks against available SDKs, resource lifetime, binary parsing, testing,
   portability, and private-interface experiments. Keep protocol code separate.
4. Build the smallest `macmst probe` using public read-only host, display-list,
   and IORegistry APIs. Report unknowns explicitly; never infer physical monitor
   count, USB-C routing, or MST capability from unrelated USB devices.
5. Add a small hardware-independent DPCD capability decoder using source-backed
   register definitions and synthetic tests. Do not implement a fake AUX transport,
   invoke IOAVService private calls, or send DDC/AUX/MST transactions.
6. Run strict builds, deterministic tests, sanitizer checks where supported, and
   a separately identified read-only hardware probe. Reconcile the evidence ledger,
   prioritize unanswered questions, and propose one bounded Milestone 2 experiment.

Local hypothesis: public display-list and registry reads can establish the number
of macOS logical displays and named DCP services without establishing MST source
capability. Discriminating check: compare an independently captured profiler/
registry baseline with the new probe; disagreement or permission failure must be
reported rather than replaced with guessed data.

## Evidence Labels

- `VERIFIED_ON_M5`: directly observed on this physical host, with reproduction.
- `PRIMARY_SOURCE`: demonstrated by cited code/documentation; its chip/version
  scope is part of the claim, not an implicit statement about M5.
- `INFERRED`: reasoned interpretation, with assumptions identified.
- `HYPOTHESIS`: experimentally testable explanation, not a conclusion.
- `UNKNOWN`: no adequate evidence or no experiment performed.

The evidence ledger will be the source of truth. A zero-result registry query is
not evidence that a hardware feature is absent. A DPCD MST-capability bit belongs
to the addressed receiver/branch, not automatically to the Mac's source engine.

## Testing Strategy

- Application type: local diagnostic CLI; no server, database, browser, Docker,
  credentials, or network service is needed to run it.
- Canonical tests: CTest after CMake configuration. No legacy test assets exist.
- Journeys: enumerate host/displays; report unavailable observations explicitly;
  serialize sanitized evidence; reject invalid CLI arguments; decode synthetic
  DPCD blocks without hardware.
- Unit tests use synthetic byte arrays and privacy fixtures. Hardware tests are
  opt-in and separately labeled. No physical I/O transport is mocked as available.
- Require strict compiler warnings, malformed/truncated input tests, preservation
  of raw protocol bytes, and proof that privacy filters remove unique identifiers.
- Build and unit tests must work without the dock. Hardware success means only
  the named read-only observations succeeded, never that MST can be enabled.
- Capture failures and verification gaps explicitly. No sudo, security weakening,
  firmware changes, persistent system settings, or state-changing hardware calls.

## Verification Run

On the M5/toolchain above:

- `cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build`:
  passed with strict warnings as errors. GNU shorthand conditional warnings were
  fixed without disabling diagnostics.
- `ctest --test-dir build -L unit --output-on-failure`: six CTest entries pass,
  including 42 synthetic DPCD checks, registry privacy, five capture/privacy
  unittest methods, and exact CLI argument/exit-code tests.
- `cmake -S . -B build -DMACMST_ENABLE_HARDWARE_TESTS=ON` and
  `ctest --test-dir build -L hardware --output-on-failure`: one explicitly opt-in
  public read-only hardware test passes. Empty successful IOService queries are
  handled separately from invalidation errors.
- `cmake -S . -B build-sanitized -G Ninja -DCMAKE_BUILD_TYPE=Debug -DMACMST_ENABLE_SANITIZERS=ON -DMACMST_ENABLE_HARDWARE_TESTS=OFF`,
  build, and `ctest --test-dir build-sanitized -L unit --output-on-failure`:
  all six deterministic entries pass under AddressSanitizer/UndefinedBehaviorSanitizer.
- `python3 tools/capture_baseline.py --probe build/macmst`: B03 saved 32 read-only
  command observations plus SDK/driver metadata, with no failures.

These checks establish software behavior and the named host observations, not
working DDC, native AUX, DPCD access, MST sideband communication, or source MST.
No code from another display project was executed; no firmware was extracted.

## Milestone 2A Verification

- `cmake --build build`: strict warnings-as-errors build passes.
- `ctest --test-dir build -L unit --output-on-failure`: seven entries pass,
  preserving the 42 synthetic DPCD checks and adding External pairing/ambiguity/
  incomplete-observation tests plus ten static parser/byte/branch tests.
- `ctest --test-dir build -L hardware --output-on-failure`: one separate opt-in
  public read-only hardware test passes, including graph and unverified-status checks.
- `cmake --build build-sanitized` and
  `ctest --test-dir build-sanitized -L unit --output-on-failure`: all seven
  deterministic entries pass under AddressSanitizer/UndefinedBehaviorSanitizer.
- Existing capture tool ran for C1, owner-disconnected D1, and owner-reconnected
  C2 with the unchanged Milestone 1 binary. The external display and External
  device/service/AV objects followed the transition; Embedded objects remained.
- G2 adds explicit graph and interface-flag evidence: 33 read-only commands,
  zero failures. A1 records 97 IODP names and static library/caller evidence.
- Failed debugger attachment was not bypassed. Cached dyld_info inspection worked
  without attachment; raw bytes/LLVM expose and document symbolication limitations.

No private IODP/IOAV function, IOServiceOpen, IOConnect transaction, DPCD write,
MST sideband message, forced HPD, link-training change, or firmware operation was
executed. Physical cable transitions were performed by the owner as requested,
not by software. No local commits or pushes were made in this milestone.

## M2A-ABI-02 Verification

- `cmake --build build`: strict build passed, already up to date; native probe
  and decoder code were not changed for ABI-02.
- `ctest --test-dir build -L unit --output-on-failure`: all seven entries passed,
  including 24 static-parser tests and the existing 42 DPCD synthetic checks.
- `ctest --test-dir build -L hardware --output-on-failure`: the one opt-in public
  read-only probe test passed. No DPDV open, private object or DPCD read was tested.
- `cmake --build build-sanitized` and
  `ctest --test-dir build-sanitized -L unit --output-on-failure`: all seven entries
  passed. Native targets use ASan/UBSan; Python tests still use the normal interpreter.
- `python3 tools/inspect_iodp.py --baseline artifacts/probes/20260912T021152Z --server`:
  A2 completed with 97 symbol names, 25 IOKit blocks, six PS190 blocks, four CF
  lifecycle records, exact bindings for the three required caller methods,
  59 selected host-kernel function blocks, and six resolved dispatch rows.
  Other unresolved/aliased call bindings remain explicitly marked in the report.
- G3's probe binary and eight core/capture source hashes are unchanged. A2's
  three tool-source digests match the current sources. All 118 artifact hashes
  across B03, C1/D1/C2, G2, A1, G3 and A2 verified successfully.
- Local document links/fences, ledger E001-E052/source S01-S17 uniqueness,
  changed-file whitespace and editor diagnostics passed. Git remains on main
  without a HEAD, with 32 untracked files; no staging, commit, branch or push.

The [ABI-02 report](iodpdevice-abi-02.md) resolves client lifetime and host
dispatch but records **NOT_READY_FOR_DPCD_TEST**. Remaining lower-RPC reply,
wait and native read-only semantics must be established before the separately
approved first experiment: exactly one byte at 0x000. No transport scaffold,
new cable cycle, updater execution, security change, or firmware write occurred.

## M2A-RPC-03 Verification

This is the original pre-publication verification record. The milestone branch's
separate 37-test run, G5/R4/R5 provenance and 161-artifact verification are recorded
in [RPC-03 validation](dcp-dpcd-rpc-03.md#validation).

| Command / Check | Result |
| --- | --- |
| `cmake --build build` | PASS, strict build already up to date. Native source and probe unchanged. |
| `ctest --test-dir build -L unit --output-on-failure` | PASS, 7/7 entries; existing 42 DPCD synthetic checks preserved. |
| `ctest --test-dir build -L hardware --output-on-failure` | PASS, 1/1 public read-only probe entry; no private hardware test. |
| `cmake --build build-sanitized` | PASS, existing sanitizer build up to date. |
| `ctest --test-dir build-sanitized -L unit --output-on-failure` | PASS, 7/7 entries. ASan/UBSan cover native targets; Python uses its ordinary interpreter. |
| `python3 -m unittest discover -s tests -p 'test_iodp_static.py' -v` | PASS, 33 deterministic tests. |
| Final static capture | PASS, R3; full exact selection command is in the RPC report. No inspected code executed. |
| Artifact/provenance checks | PASS, 139 artifacts across B03/C1/D1/C2/G2/A1/G3/A2/G4/R3, 14 reference files, 3 current tool sources. Three source blob IDs independently match GitHub. |
| Unchanged probe/core checks | PASS, G4 probe binary and all 8 recorded core/capture source hashes still match. |
| Documentation/diagnostics | PASS, 13 root/research documents' local links/anchors/fences, E001-E069/S01-S21 uniqueness, changed-file whitespace and editor diagnostics. |

R3 is `artifacts/probes/iodp-static-20260912T045748Z/`, with 26 IOKit function
blocks, six PS190 blocks, 206 selected host-kernel functions and the same running
kernel UUID as ABI-02. The new parser uses declared function boundaries, preserves
duplicate names by address, supports exact string/address captures, and records
undecoded instructions explicitly. Three allocation/growth instructions remain
undecoded; no claim depends on pretending otherwise. Source captures remain ignored.

The full then-current 32-file project was read before completing that investigation;
two research reports were added. At that pre-publication point, Git was still on
main without a HEAD, with 34 untracked project files. No files had yet been staged,
committed, pushed or reverted in that investigation.
No model/global VS Code configuration, firmware or security setting was changed.

The result is [RPC-03's gated safety assessment](dcp-dpcd-rpc-03.md#readiness-gates)
and [authorization category E](dpdv-authorization.md#authorization-categories):
**NOT_READY_FOR_DPCD_TEST**. There is no private transport or runnable experimental
DPCD-read command. The proposed first operation remains exactly one byte at 0x000,
only after resolving the blockers and receiving separate explicit approval.