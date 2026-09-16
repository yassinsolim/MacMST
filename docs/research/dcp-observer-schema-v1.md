# DCP Observer Record Contract v1

## Status And Scope

Frozen by M5P1 for independent offline transport records, synthetic production,
replay and evidence evaluation. No real Apple trace has been captured, and no
live producer is implemented in MacMST. This is not an Apple ABI or an emulation
of DCP behavior. It is a loss-accounted evidence interchange format.

The M5P0 proposal used version 1 before capture metadata was finalized. Proposed
records missing the required fields below are rejected, not silently upgraded
or repaired. The historical M5P0 description remains unchanged as a proposal.
Future incompatible changes require another schema version. No real capture
compatibility is displaced by this finalization.

The normative executable validator is
[tools/dcp_trace_schema.py](../../tools/dcp_trace_schema.py). Validation never
creates an ownership assertion from an endpoint, channel, service, downstream
port, payload ID, two records or nearby timestamps. Raw bytes are authoritative;
decoded fields are optional supplemental data and cannot replace raw bytes.

## Serialization

One UTF-8 JSON object per line. A final complete object may omit its newline.
Blank lines, malformed JSON/UTF-8, duplicate keys at any depth, non-finite
numbers and non-JSON values are invalid. Object keys are strings. Objects and
arrays have bounded depth/node count. Unknown fields, including nested fields,
survive JSON-value round-trip; original whitespace/number spellings are not
preserved. No undeclared default is inserted into the stored record.

Canonical output sorts keys, uses ASCII JSON escapes and compact separators.
`raw_payload` hex text is retained exactly as a value, including its case. Byte
hashes decode that hex; changing supplemental decoding does not change raw-byte
identity. Whole-record provenance reviews bind canonical JSONL as described
below, so annotation/metadata changes invalidate the review too.

## Required Fields

| Field | Type And Rule |
| --- | --- |
| schema_version | Integer exactly 1; booleans are not integers |
| capture_id | Nonempty string, at most 256 characters; constant throughout one records file |
| capture_generation | Nonempty string identifying a contiguous recording epoch; no reopening a closed generation |
| boot_generation | Nonempty boot identity within capture_generation; a boot change requires a new capture generation |
| lifetime_generation | Nonempty producer-declared object/ID namespace lifetime; participates in correlation, not source-count inference |
| sequence | Unsigned 64-bit recording sequence, strictly increasing per capture_generation; starts at zero for full coverage |
| timestamp_ns | Unsigned 64-bit monotonic timestamp, nondecreasing within capture_generation |
| timestamp_units | Exactly ns |
| clock | Exactly monotonic; no assumption of wall-clock equivalence or cross-generation clock continuity |
| kind | request, reply, event or loss |
| direction | host_to_dcp or dcp_to_host; none is reserved for loss records |
| asc | Nonempty producer-supplied transport identifier, not an automatic physical-DPTX identity |
| endpoint | Null or unsigned 8-bit integer |
| channel | Null or unsigned 32-bit integer |
| service | Null or nonempty string, at most 256 characters; unknown service remains null or an explicitly unknown name |
| opcode | Null, unsigned 64-bit integer or nonempty bounded string; unknown opcodes are permitted |
| request_id | Null, unsigned 64-bit integer or nonempty bounded string; integer and string IDs remain distinct |
| payload_length | Retained byte count, at most 1 MiB |
| declared_payload_length | Original byte count, unsigned 64-bit and at least payload_length |
| raw_payload | Exactly twice payload_length hexadecimal characters without separators; empty body is an empty string |
| record_complete | Boolean; describes the record, not completeness of the entire capture or firmware lifecycle |
| truncated | Boolean exactly matching declared_payload_length greater than payload_length |
| loss_state | Required loss object below |
| producer | Required producer object below; constant throughout one capture file |

All unspecified nonempty identifier strings above are bounded to 256 characters.
Sequence wrap is not repaired into an increasing number. A producer reports
wrap/loss explicitly and either continues its recording counter or starts a new
capture generation. Missing initial/intermediate sequence positions are warnings,
not silently filled records. Duplicate or regressing sequences are invalid.

`producer` requires name, version, commit and synthetic. Name/version are
bounded strings. Commit is a lowercase 40-character Git SHA or UNKNOWN;
synthetic is a boolean. UNKNOWN is useful for artificial/test producers, not
sufficient producer revision provenance for a real-evidence review. A false
synthetic flag is a claim, not authenticity. Reserved `extensions.synthetic`
marking cannot coexist with `producer.synthetic` false.

## Optional Fields

| Field | Contract |
| --- | --- |
| record_index | Optional M5P0 alias; if supplied it must exactly equal sequence |
| decoded_fields | JSON object of supplemental interpretation; ignored by automatic ownership evaluation |
| extensions | JSON object of forward-compatible data; arbitrary JSON values retained without interpretation |
| correlation | Explicit producer-supplied scope/evidence object below |
| annotations | Externally supplied ownership assertions below; never synthesized from transport metadata |

Other fields are retained and reported as UNKNOWN_EXTENSION_FIELD warnings.
Known-container extension fields are also preserved; the presence of an
extension never expands the evidence it proves. No field is assumed to contain
an object pointer, source identity, independent timing or virtual channel unless
that meaning has explicit provenance.

## Completeness And Loss

`loss_state` requires status, dropped_records and detail. Status is none,
dropped, wrapped, truncated or unknown. Dropped_records is null or unsigned
64-bit; none requires zero, dropped requires a positive count. Detail is null
or a nonempty string up to 1024 characters. A wrap without a known lost count
uses null, not a fabricated count.

A longer declared payload requires truncated=true, record_complete=false and
loss status truncated or unknown. Truncated status requires a longer declared
length. Incomplete records cannot report loss status none. Explicit loss records
cannot report no loss. A complete loss-marker record can describe a transport
gap even though its own empty body is intact.

The importer distinguishes retained bytes, reported dropped records, unknown
loss counts and inferred sequence gaps; those counts may overlap and are not
summed as an invented total loss. `record_coverage_complete` is only the absence
of recorded gap/loss indicators, not proof of complete producer observation.
Evidence evaluation conservatively excludes a generation containing any loss,
gap or incomplete record from positive gates. This may underclaim valid evidence;
it never assumes a missing interval was harmless.

## Validation Model

Each parsed record has a ValidationResult containing the unchanged record and
structured Issue values: code, message, field and severity. Aggregate states:

- VALID: schema/stream checks found no error or warning.
- VALID_WITH_WARNINGS: usable syntax with explicit loss, extension fields or
  other qualified limitations. This is not automatically useful evidence.
- INVALID: no analysis decision or partial output stream is published.

Representative codes include MALFORMED_JSON, DUPLICATE_JSON_KEY,
UNSUPPORTED_SCHEMA, MISSING_FIELD, INVALID_DIRECTION, INVALID_ENDPOINT,
IMPOSSIBLE_LENGTH, PAYLOAD_LENGTH_MISMATCH, TRUNCATED_RECORD,
DUPLICATE_SEQUENCE, SEQUENCE_REGRESSION, TIMESTAMP_REGRESSION,
CAPTURE_GENERATION_MISMATCH, AMBIGUOUS_CORRELATION, MALFORMED_ANNOTATION,
UNKNOWN_EXTENSION_FIELD and SYNTHETIC_ORIGIN_MISMATCH. Resource-limit errors
are explicit, not partial gate decisions. An invalid annotation is not stripped
to make its record acceptable.

Limits: 1 MiB payload; 2 MiB plus 64 KiB serialized record; 256 MiB records
file; 100,000 records; JSON depth 64 and 100,000 nodes per record. The reader
accepts only regular nonsymlink files, not pipes, devices, sockets or live
streams. `--records` validates/spools the whole input before publishing output.
Warnings and machine-readable diagnostics are available in summary mode.

## Explicit Correlation

The [correlation module](../../tools/dcp_trace_correlation.py) is separate from
file parsing. Optional `correlation` requires scope and evidence strings, with
an exchange kind and nonnull endpoint, channel and request_id. Evidence is a
producer-supplied rationale, not independent verification by this tool.

Pair only within matching capture_id, capture_generation, boot_generation,
lifetime_generation, ASC, endpoint, channel, service, declared scope and typed
request ID, with matching declared contract rationale and opposite directions.
Timestamp proximity never forms a pair. ID reuse is permitted after an explicit
exchange, but duplicate in-flight IDs and conflicting directions/contracts are
ambiguous. Gaps/loss invalidate pending requests in the affected generation.

Results are CORRELATION_EXPLICIT, CORRELATION_AMBIGUOUS or
CORRELATION_UNAVAILABLE. A request without its reply and a reply without its
request remain unavailable. Generation/lifetime resets cannot accidentally
complete an earlier request. Pairing is a transport fact, not source ownership.

## Ownership Assertions

`annotations` can retain physical_dptx, source_identity, timing_identity,
payload_identity, confidence and evidence. Missing identity values remain
UNKNOWN in the normalized view; the raw record is not edited. Confidence is
exactly VERIFIED, STRONG, INFERRED, HYPOTHESIS or UNKNOWN. Supplied identity
claims require explicit confidence and a nonempty list of evidence strings.
Evidence text is bounded to 64 entries of 1024 characters each.

For a gate-eligible assertion, also supply claim_id, assertion, capture_id,
capture_generation, boot_generation, lifetime_generation, start_ns, end_ns,
independent and provenance. Bind generation fields to the containing record.
The half-open interval must have positive duration and contain the record's
monotonic timestamp. Pair-based gates additionally require simultaneous=true
and a shared non-UNKNOWN coexistence_id backed by the explicit provenance.

`provenance` requires origin (synthetic/observed/UNKNOWN), mapping_basis
(explicit_contract/independent_measurement/heuristic/UNKNOWN), method,
independently_validated and references. References are a nonempty list of at
most 64 objects containing capture_id, capture_generation, sequence and the
lowercase SHA-256 of the referenced raw bytes. A claim must reference its own
record, and all references must resolve with matching hashes in the same
capture/boot generation. Missing, cross-generation or partial references do not
qualify. A duplicate claim ID invalidates those claims. Two facts sharing a raw
reference cannot by themselves establish two independent contexts.

Only STRONG/VERIFIED claims with explicit independence and justified mapping
provenance are gate candidates. INFERRED/HYPOTHESIS values stay unqualified.
An annotation on a request/reply needs complete explicit correlation. Decoded
fields, service units, port numbers and transport IDs never supply missing facts.

| Gate | Explicit Assertion And Additional Requirement |
| --- | --- |
| A | source_context: two distinct source_identity values, same physical owner and overlapping explicitly coexistent intervals |
| B | timing_generator: two distinct timing_identity values, independently justified as generators/contexts, same owner and coexistence |
| C | source_payload_binding: distinct sources and distinct payload_identity values simultaneously bound to the same owner |
| D | source_api_space: explicit same-owner contract with more than one distinct non-UNKNOWN source_space member; no simultaneous-output claim is implied |
| E | wire_vc: distinct vc_identity and timing_identity values, same owner/coexistence, independent_measurement mapping and observation_plane=dp_main_link |

The optional observation_plane is host_dcp_transport, dp_main_link, dp_aux or
UNKNOWN. AUX/ordinary one-stream MST control does not qualify for E. Different
physical owners, including EXT0/EXT1, are never combined. Sequential recreation
or payload changes on one source do not qualify as simultaneous sources.

Evaluation is bounded to 2048 annotated claims and 100,000 pair comparisons per
gate; exhausting a budget raises EVIDENCE_RESOURCE_LIMIT, not a negative
architectural conclusion. No automatic source detector is implemented.

## Synthetic Versus Real

Artificial data is marked by producer.synthetic and the reserved synthetic
extension. All supplied fixtures and producer scenarios are artificial.
Qualifying artificial assertions yield SYNTHETIC_GATE_TEST_PASS only; the
project gate remains NOT_ESTABLISHED, real_evidence_passes remains zero, and
hardware_authorized is false.

Observed-labeled records without a separately supplied human provenance review
can only produce REAL_PROVENANCE_REVIEW_REQUIRED for an otherwise complete
candidate. A real review must explicitly approve claim IDs, name the reviewer
and review basis, bind capture_id and the SHA-256 of canonical whole JSONL,
and require exact producer revisions. Synthetic inputs cannot receive it.
The review has review_version=1, capture_id, records_sha256, reviewer, basis
and approved_claim_ids. It must be explicitly selected and hash-inventoried
within a validated bundle for the CLI.

REAL_EVIDENCE_GATE_PASS is conditional on those externally reviewed facts;
hashes do not authenticate a reviewer, prove semantic truth or establish that
the supplied capture is really hardware-derived. Independent human provenance
review remains mandatory. No real review, real capture or real-evidence pass
is included in M5P1. No tool changes the platform target-test or purchase gate
from capture-analysis results alone.

## Capture Bundles

```text
capture/
  manifest.json
  records.jsonl
  source-info.json
  hashes.json
  analysis/
```

The [bundle validator](../../tools/dcp_trace_bundle.py) validates and consumes
the same hashed bytes, not a second unbound read. `hashes.json` has
algorithm=sha256 and files mapping relative paths to lowercase SHA-256 digests.
It must cover manifest.json, records.jsonl and source-info.json, plus any
explicitly used review file. It cannot hash itself or analysis outputs as
input evidence. Paths cannot be absolute, traverse parents or contain symlinks.
Hashes establish integrity, not authenticity. Analysis output is optional and
not silently written back into input captures.

`manifest.json` requires bundle_version=1, schema_version=1, capture_id,
synthetic, machine, producer, capture_start, capture_end,
observer_configuration, stimulus_description, topology, known_loss and
tool_commits. Machine contains model, soc, os_version and os_build; no serial,
personal UUID, credential or recovery key is required. Start/end are timezone-
qualified ISO timestamps with end at or after start. Monotonic record clocks
remain separate from these wall-clock labels. Tool commits are exact Git SHAs
or explicit UNKNOWN. Unknown metadata is preserved, not treated as verified.

`known_loss` records reported_dropped_records, sequence_gaps,
incomplete_records and loss_count_unknown, each matching the actual import
summary. `source-info.json` requires kind (synthetic/observed), producer and
description. Capture ID, producer object and synthetic status must agree across
manifest, source-info and records. Metadata files are limited to 1 MiB each,
64 hashed inputs and 272 MiB combined input. Unhashed/unreviewed evidence does
not become a real gate pass merely because a bundle exists.

## Neutral Topology

Topology version 1 contains nodes and directed edges. Each node has a unique
id and kind: mac, physical_output, hub, dock or sink. There is one Mac root;
every node is reachable with one parent except the root, and cycles are invalid.
Allowed directions are Mac -> physical output -> hub/dock/sink, with optional
cascaded hubs/docks -> sinks. Maximum 128 nodes and 127 edges.

Optional node fields include label, connection_type, reported vendor_id and
product_id, port_index, sink_logical_identity and mst_branch_identity. Numeric
IDs/indices are bounded unsigned 16-bit values; unavailable values may be null.
Edges contain source, target and connection_type. No dock manufacturer or
display brand is hard-coded. A described two-sink topology is metadata, not
proof of two independent source contexts or observed MST support.

## Offline Workflow

```sh
python3 tools/dcp_trace_synthetic.py request_reply --output synthetic.jsonl
python3 tools/dcp_trace_import.py synthetic.jsonl --json
python3 tools/dcp_trace_replay.py synthetic.jsonl --json
python3 tools/dcp_trace_replay.py synthetic.jsonl --endpoint 42 --jsonl
python3 tools/dcp_trace_synthetic.py two_sources --bundle synthetic-capture
python3 tools/dcp_trace_analyze.py synthetic-capture --json
```

Synthetic creation refuses to overwrite existing files/directories. Replay
preserves validated input order, full generation metadata and loss markers,
with no delay by default. Endpoint/channel/service/opcode filters use typed
exact matches; all input is validated/correlated before filtering. Whole-input
diagnostics are retained, and omitted records are counted. Reimporting filtered
JSONL exposes any resulting sequence gaps; it cannot add evidence.
Loss/truncation attached to a normal request, reply or event is also always
retained, even when its endpoint/channel/service/opcode does not match a filter.

Optional --realtime host pacing is disabled by default, accepts a positive
--speed and caps each delay at one second. Tests replace pacing with a mock;
M5P1 does not run delayed replay. Human summaries and JSON/JSONL outputs are
available with --help on all CLIs. Exit 0 means valid or valid-with-warnings;
invalid input returns 2. No command connects to a live device or network.

The [golden corpus manifest](../../tests/fixtures/dcp_trace/manifest.json) binds
31 small artificial fixtures in valid/warning/invalid/evidence categories to
hashes and fixed expected validation/correlation/gate results. The 1 MiB maximum
body is generated in tests, not stored as a large fixture. Regeneration creates
a new directory only; fixture changes require reviewing the manifest and diff.