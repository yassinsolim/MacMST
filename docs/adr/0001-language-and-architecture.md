# ADR 0001: Portable C++ Core, Objective-C++ macOS Adapter

Status: accepted for Phase 0 / Milestone 1, 2026-09-11.

## Context And Evidence

The selected Xcode 26.6 toolchain provides Apple Clang 21, Swift 6.3.3, and macOS
SDK 26.5. CMake 4.4.1 and Ninja are already installed. A strict syntax-only
Objective-C++ compilation imported Foundation, IOKit, CoreGraphics, `std::span`,
and `std::optional` successfully. No dependency installation is necessary.

The first executable needs public C APIs for registry enumeration and logical
display queries, structured JSON, deterministic binary decoding, and explicit
resource ownership. Future private calls, if justified and approved, likely use
C ABI declarations; that does not establish that native AUX is available.

| Candidate | Benefits | Costs For This Phase |
| --- | --- | --- |
| C | Direct IOKit/CoreFoundation ABI; portable protocol code. | Manual resource lifetime and cumbersome structured output; more error paths. |
| C++20 | RAII, bounded spans, optional unknown values, portable byte tests, sanitizers. | Requires disciplined small interfaces and explicit CoreFoundation ownership. |
| Objective-C++ | C++ plus Foundation JSON/ARC; direct C framework access. | Apple-specific runtime and language; confine it to the macOS adapter. |
| Swift | Foundation and public framework interoperability; safe collections and SPM. | Private-C/packed-protocol experiments need bridges; generic core portability adds a Swift toolchain dependency. |
| Swift + C/C++ | Can combine the strengths above. | Two language/build boundaries before a UI or Swift-specific need exists. |

## Decision

- Use C++20 for CLI control flow and generic DisplayPort decoding.
- Use one narrow Objective-C++ macOS adapter with public IOKit, CoreGraphics,
  CoreFoundation, and Foundation APIs. ARC manages Objective-C objects; RAII
  wrappers manage IOKit objects. No private API invocation in the initial probe.
- Use CMake/CTest with strict warnings and optional AddressSanitizer and
  UndefinedBehaviorSanitizer. Generic decoder tests do not link Apple frameworks.
- Use a small Python-standard-library capture tool for independent system_profiler
  and plist/IORegistry baselines. Python is already installed; it is not a runtime
  dependency of `macmst probe`. Independently collected artifacts can detect
  disagreements with the CLI, rather than comparing the CLI with itself.
- Keep `src/displayport/dpcd/` free of Apple headers; put host-specific enumeration
  in `src/platform/macos/`, output boundary types in `src/probe/`, and argument
  handling in `src/cli/`. Do not create empty AUX/MST subsystems for appearance.
- Add an `AuxTransport` only when a real transport is justified. Future operations
  must distinguish native read/write from I2C read/write, include address spaces,
  bounded buffers, reply/error details, and explicit unsupported results. There
  is no transport in Milestone 1; capability fields remain `UNKNOWN`.

## Consequences

Protocol tests are hardware-independent and can be built on another C++20 host.
The macOS CLI does not parse command output or shell out. The independent capture
tool filters structured command output before persistence. Neither tool may turn
absence of a registry property into evidence of absent source hardware.

Keep raw numeric registry values and source field names; use Apple's accompanying
description where present instead of guessing private units or enumeration values.
Do not retain EDID serial data, complete registry dumps, or private identifiers.
The active SDK is older than the OS, so private layout/selector assumptions would
need separate verification. No protocol implementation is copied from Linux.