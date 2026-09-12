# DPDV Authorization (M2A-RPC-03)

## Milestone Branch Revalidation

This update is on `research/dcp-rpc-safety`, based on the unchanged published
commit `2512e2f34ec5fc2b2f03102ecfb44951dad3c517`. The class-local ABI is reused,
not re-derived. New **R5** at `artifacts/probes/iodp-static-20260912T100306Z/`
refreshes the current kernel policy bytes and adds a privacy-filtered signing
record tied to the exact on-disk probe binary.

| R5 Observation | Value / Limit |
| --- | --- |
| Report SHA-256 | `3eb1ce95df7815e9e719e12baa9d9e14c6ea34f0aad5a0560723949925cd2e2f` |
| Probe SHA-256 | `3968fe8e43d04013e1e91110e3a206890b65a5d48b86327e4109f435dac1ddda`, equal to G5's probe hash. |
| Identifier / format / signature | macmst / Mach-O thin (arm64) / adhoc. |
| TeamIdentifier / CDHash | not set / `403268a38c514bd76acff186dc0a028b8942d40a`. |
| Entitlement display | codesign exit 0; `NO_DATA_REPORTED`, zero keys reported. |
| Empty entitlement-output SHA-256 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. |
| App Sandbox entitlement | null (not reported), **not** an observed runtime sandbox state. |
| Authorization field | `UNRESOLVED_NOT_TESTED`, deliberately independent of signing result. |

The collector omits the absolute executable path, signing authority details and
entitlement contents. It rejects duplicate identity fields, malformed plist or
hash fields, oversized inputs, and a binary changed during inspection. It only
invokes codesign's display operation, never signs or executes the probe.

The R5 kernel UUID and original/decoded collection hashes equal R3. All 191
same-named function records shared with R3 have identical instruction hashes,
including the outer open and sandbox routines below. Their current gate logic
can therefore be reused with stronger fresh provenance, not promoted to an
actual authorization test.

| Current Block | Byte SHA-256 |
| --- | --- |
| Outer open, 0xfffffe000c037b80 | `29f2834dda56b7192bcfe36c9fd0becd2e0589f6810fe621ca89d96eef368e7c` |
| _hook_iokit_check_open | `ab894d7006407714198f28253b0857b0bf3ae77ac72833022724010a5e2bcd4c` |
| _hook_iokit_check_open_service | `83fd549db7127f3c0b4e34cc3157b7b67f0d26dd43940986adbabf18ebb35ee7` |
| _sb_evaluate_internal | `753a3dd6437a7e92c82fdf59e37581ac6b86b7fc59aea7ce9b80adcfb78c63e3` |

The unresolved inputs are precise: which registered mandatory/system policies
apply, the eventual task/credential sandbox state, the client entitlement value
after permitted construction, and the resolved per-user-client selector filter.
They are not all observable from static codesign output or from the provider's
published dictionary. No class-local root-only or platform-only requirement was
found, but category A is still unjustified. Category **E: policy-dependent /
statically unresolved** remains the result, with high confidence in the existence
of these gates and no claimed successful access.

Reproduce the static refresh on the recorded build:

```sh
python3 tools/inspect_iodp.py \
  --baseline artifacts/probes/20260912T093139Z --server \
  --reference-root artifacts/sources/rpc03 --signing-probe build/macmst \
  --kernel-image com.apple.security.sandbox \
  --kernel-symbol _hook_iokit_check_open \
  --kernel-symbol _hook_iokit_check_open_service \
  --kernel-symbol _sb_evaluate_internal \
  --kernel-symbol __ZN12IOUserClient10clientDiedEv \
  --kernel-string 'IOUC %s missing entitlement in process %s
' \
  --kernel-address 0xfffffe000c0dc69c \
  --kernel-address 0xfffffe000c0dc918
```

No DPDV open, runtime sandbox-policy probe, privilege change, entitlement grant
or platform-signing change was performed. Conditional power work found in the
[endpoint-close follow-up](dcp-dpcd-rpc-03.md#request-ownership-and-endpoint-close)
does not imply that the selected user-client start reruns provider setup; it does
mean teardown must remain part of the future experiment's safety assessment.

## Result

**E: authorization for the eventual normal process cannot be fully determined
statically from the recovered evidence.** No DPDV user client was opened.
Root is not established as necessary or sufficient, and no specific private
entitlement/platform-signing requirement was proved for this concrete client.
Do not translate those negative scoped findings into permission to invoke it.

The class-local creation path is strongly understood. The remaining authorization
boundary is the outer kernel open/filter policy and its runtime inputs, including
system policy that can apply to a process without an App Sandbox label.
This is a blocking gate in [dcp-dpcd-rpc-03.md](dcp-dpcd-rpc-03.md), independent
of the separate unbounded-wait/cancellation blockers.

## Provenance And Process Identity

- G4: `artifacts/probes/20260912T042950Z/`, fresh public External target.
- R3: `artifacts/probes/iodp-static-20260912T045748Z/`, exact current kernel,
  IOAV/DP, AppleFirmwareKit and sandbox function/dispatch evidence.
- Kernel UUID `447D769E-1CB7-3086-A0B4-32226837B587` matches the running build.
  Sandbox UUID `D4780E99-68D4-3902-8072-5151727ABD4C`.
- Pinned source: apple-oss-distributions/xnu
  `f6217f891ac0bb64f3d375211650a4c1ff8ca1ea` (xnu-12377.1.9),
  [IOUserClient.cpp](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/iokit/Kernel/IOUserClient.cpp)
  and IOService.cpp. This source revision is not claimed to be the exact running
  OS source; the identified current instruction paths corroborate relevant logic.

`VERIFIED_ON_M5`: read-only code-signing inspection of the existing probe:

```sh
codesign --display --verbose=4 --entitlements - build/macmst
```

Exit 0; Identifier `macmst`, arm64, flags `0x20002` (ad-hoc, linker-signed),
Signature `adhoc`, TeamIdentifier not set, no displayed entitlements,
CDHash `403268a38c514bd76acff186dc0a028b8942d40a`. Nothing was signed or changed.
This establishes on-disk identity, not the future process's sandbox label,
dynamic mandatory policy, or successful private-interface access.

## Actual Target Class

`VERIFIED_ON_M5`: the currently observed External / Unit 0 DP device publishes
`IOUserClientClass = DCPDPDeviceProxyUserClient`. The provider's selected properties
do not include IOUserClientEntitlements. **Absence on the provider is not proof
of absence on a client that has never been created.** A query for existing client
instances returned exit 0 with zero stdout/stderr bytes; no client was created
to inspect its properties. This does not enumerate unpublished kernel objects.

`PRIMARY_SOURCE`: the exact proxy vtable inherits
IOService::newUserClient(task*,void*,unsigned,OSDictionary*,IOUserClient**).
The class property selects the client, which inherits the base IOUserClient
initWithTask overloads and has the concrete DCPDP client start. The latter casts
its provider and installs the IODPDeviceUserClient/IOAVUserClient dispatch/gate.
The observed type argument is DPDV `0x44504456`; this inherited path does not
use a DPDV-specific type switch as an access-control check.

In the examined class-local methods no clientHasPrivilege, UID-0 check, private
entitlement string check, audit-token identity requirement, Apple platform-binary
check, or SIP/AMFI configuration check was found. Installed DP personality
metadata advertises its IOClass and AFKEndpointInterface provider; it is not an
authorization declaration. Other users of the same family or PS190's Apple
signing do not prove what the independently built probe may do.

## Outer Open Gates

The stripped current routine at **`0xfffffe000c037b80`**, bounded by
LC_FUNCTION_STARTS, references the exact string
`IOUC %s missing entitlement in process %s\n` at `0xfffffe00070e611c`.
Its argument flow, task checks, client construction, property checks and error
paths match the role of XNU's `is_io_service_open_extended`.
That source-level identity is **INFERRED**, not an exported symbol in this image.

| Gate | Current Evidence | Consequence |
| --- | --- | --- |
| Service and owning task | Type check; non-null owning task must equal current task before construction. | A foreign task/invalid handle is not a permitted workaround. |
| Service-stage MACF | Direct call at 0xfffffe000c037c6c to 0xfffffe000c0dc69c, before newUserClient. | Service policy can reject before the class's start method runs. |
| newUserClient | Indirect slot +1952 at 0xfffffe000c037cb8; same concrete proxy factory as ABI-02. | A correct DPDV argument does not bypass outer checks. |
| Client properties | Copy-property and class/boolean checks at 0xfffffe000c0381f0 onward. | Class-local absence of checks is insufficient. |
| Required entitlement | Current `_IOTaskHasEntitlement` call at 0xfffffe000c0382d0. | When a requirement is present, signing/entitlements matter independently of UID. |
| Client-stage MACF | Call at 0xfffffe000c03844c to 0xfffffe000c0dc918. | Policy can reject after client construction. |
| Filter resolver | Callback dispatch at 0xfffffe000c0385f8, with task/client/type and output policy. | A resolved external-method policy can further constrain selectors. |
| Failure cleanup | clientClose, terminate-defer update and release before returning failed connection status. | Rejected construction is not proof that no bookkeeping occurred. |

The two unnamed MACF dispatchers iterate registered policy operations and combine
errors. The exact current code and call-site roles are retained. A source name
for a stripped helper is not fabricated in the report; the source-named
callExternalMethod request was explicitly rejected by the collector when absent.

`PRIMARY_SOURCE` in pinned XNU: IOUserClient2022 requires an
IOUserClientEntitlements property with an allowed type. Boolean false permits
that entitlement gate; a string requires the named task entitlement. The legacy
IOUserClient path lacks the blanket 2022 property-presence requirement, but
still honors a supplied entitlement and still passes MACF/filter gates. R3's
current property/class/entitlement branches corroborate this distinction.
The examined concrete chain is the legacy IOUserClient family; that does not
exempt it from the remaining gates.

## Sandbox, Platform And System Policy

`PRIMARY_SOURCE`: current sandbox functions are:

| Function | Address | Observed Operation |
| --- | --- | --- |
| _hook_iokit_check_open | `0xfffffe000b22c830` | Gets the credential's sandbox label and evaluates operation 66 with the object. |
| _hook_iokit_check_open_service | `0xfffffe000b234020` | Evaluates operation 67 with the service and connect type. |
| _sb_evaluate_internal | `0xfffffe000b241130` | Derives credentials, handles transient/system policy and optional per-process policy; has rootless-modifier paths. |

The evaluator considers system/transient policy as well as an App Sandbox label.
Consequently the existing binary's lack of `com.apple.security.app-sandbox`
does not establish an unconditional allow. Global policy selection, current
credential labels, resolved filter policy and any required entitlement value
have not all been determined for a future private-open process.

No static finding establishes that disabling SIP/AMFI, using root, changing
sandbox profiles, adding an unsigned entitlement, or impersonating a platform
binary is needed or appropriate. None was attempted or proposed as a prerequisite.
Rootless-modifier code is evidence that policy exists, not a command to weaken it.
This analysis also does not prove the absence of every AMFI/platform-signing
condition in the complete mandatory-policy chain.

## Authorization Categories

| Category | Assessment | Confidence |
| --- | --- | --- |
| A. Normal user process can open | Not proved. Class construction has no recovered root-only condition, but outer policies remain. | UNKNOWN for actual access |
| B. Root-only | No such class-local requirement was found; root sufficiency is not established. | UNKNOWN as an end-to-end requirement |
| C. Private entitlement required | Generic entitlement enforcement exists; no required private string was recovered for this never-created concrete client. | HIGH for mechanism, UNKNOWN for required value |
| D. Apple platform signing required | No direct class-local check found; PS190 being Apple-signed is not evidence that all callers must be. | UNKNOWN for full policy |
| E. Cannot determine fully statically | Selected result: dynamic/system/filter conditions remain unresolved. | HIGH that an authorization proof is incomplete |

## Open/Start Effects And Future Gate

The selected CF/client chain performs allocation, reference ownership, attachment,
gate setup and dispatch installation. No explicit DP retraining, HPD, DPCD write,
lane/rate, MST or display-route command appears in the examined client init/start
methods. An IOServiceOpen is not equivalent to the generic EPIC service `open`
message found in m1n1, and it does not rerun the existing provider's start.

The same-service optional AV creation is nullable and gated by an absent support
flag in the observation. Recheck that fact before relying on the path; never
substitute the AV sibling or use lazy getters that open other objects.
Potential read-time endpoint power assertions are documented separately in the
RPC report; they must not be described as harmless merely because the API is
named ReadDPCD.

Before any later approved experiment, the exact process identity and applicable
requirements must be known and satisfiable without weakening system security.
Failure of a future authorized open must be logged and stopped, never retried
automatically as root or with changed entitlements. This milestone did not make
that open attempt and does not authorize one.