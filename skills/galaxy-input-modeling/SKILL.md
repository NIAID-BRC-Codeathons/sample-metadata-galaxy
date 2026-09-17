---
name: galaxy-input-modeling
description: >
  Convert validated sample metadata into the correct Galaxy dataset or collection
  structure required by a specific tool or workflow — paired, list, nested, sample
  sheet, or single dataset. Use after analysis-readiness has declared the study
  ready, before invoking the analysis.
metadata:
  surfaces: [loom]
when_to_use: >
  Fetch this skill when the analysis is ready (analysis-readiness has declared ready
  or ready_with_warnings) and the next step is to run a Galaxy tool or workflow that
  needs structured inputs. Use before invoking any analysis that requires datasets,
  collections, or sample sheets. Never use this skill to paper over missing or
  unvalidated metadata — if the readiness record is missing or blocked, go back to
  metadata-construction or analysis-readiness first.
---

# Galaxy Input Modeling

Convert validated sample metadata into the Galaxy input structure required by a specific tool or workflow. Shield the researcher from Galaxy collection mechanics without hiding consequential decisions or uncertainty.

## Preconditions

Require from `analysis-readiness`:
1. The validated tabular sample metadata (primary input — what gets converted to Galaxy data structures).
2. The readiness record YAML (context on warnings, provenance, and constraints).

Specifically: status `ready` or `ready_with_warnings`, unambiguous sample-to-file mappings, confirmed file roles where pairing matters, explicit groups/controls/contrasts/replicates as required, and a known target Galaxy tool/workflow input contract. If any are absent, return to `analysis-readiness`.

## Core principles

- Inspect the actual target tool or workflow inputs; do not select a collection type from memory.
- Filename resemblance or equal read counts can suggest pairing, but are not proof. Use them as hypotheses, flag as `inferred`, and verify before committing to a paired structure.
- Do not encode unknown controls, groups, or replicate relationships as if they were confirmed. If only inferred, label them as such and flag to the user.
- Preserve stable sample identifiers through every collection level and sample-sheet row.
- Prefer Galaxy-native collection tools for reproducible, workflow-extractable construction.
- Verify collection contents and shape, not merely successful job completion.
- Never invent Galaxy dataset, collection, history, tool, workflow, job, or invocation IDs.
- If the live tool/workflow input contract cannot be inspected, say so and stop. Do not construct from memory.
- If a sample-sheet schema cannot be confirmed from the consumer definition, do not generate one from a generic template.
- If construction or verification reveals an unexpected shape, missing element, or mismatch, report it — do not silently correct it.
- Flag every unknown, mismatch, and unresolved issue to the user in the conversation, not just in the notebook.

## Workflow

### 1. Inspect the consumer contract

For every target input, determine from the live Galaxy tool/workflow definition: accepted source (dataset, collection, parameter, multiple data), accepted collection types, required datatype, whether mapping occurs over elements, whether multiple inputs must align by identifier, whether metadata is passed structurally or as a sample sheet, and the exact sample-sheet schema if applicable. If the live definition cannot be inspected, stop.

### 2. Choose the minimum faithful Galaxy representation

Let the inspected consumer contract decide. Examples (not exhaustive):

| Biological/input model | Typical Galaxy representation |
|---|---|
| One file used once | dataset |
| Many independent single-file samples | list |
| One sample with confirmed forward/reverse files | paired |
| Many samples, each with confirmed forward/reverse files | list:paired |
| Multiple files/runs per sample | nested collection when accepted; otherwise merge or use a sample sheet |
| Rich factors, covariates, batches, controls, or contrasts | tabular sample sheet when supported |
| Several inputs requiring element-wise correspondence | collections with identical stable identifiers and verified alignment |

A Galaxy collection shape controls execution mapping; it is not a general-purpose metadata database. Do not create deeper nesting merely because metadata are hierarchical.

### 3. Construct

Prefer in order: reuse a verified existing collection; use Galaxy-native collection-building or operation tools; transform an existing collection using native tools (build, zip, nest, relabel, sort, harmonize, Apply Rules); construct a validated tabular sample sheet using an appropriate Galaxy tool; use direct collection APIs only when no native operation can express the construction and the user accepts the reproducibility limitation. When available, fetch and follow the `galaxy-transform-collection` skill for concrete collection operations.

For sample sheets: obtain the exact schema from the tool/workflow, generate one row per semantic unit, preserve sample IDs, use controlled vocabulary, represent missing values as the schema requires (not invented), and encode controls/contrasts only from confirmed metadata.

### 4. Verify before analysis

For collections, inspect recursively and verify: `collection_type` matches the consumer requirement, element count matches expected at every level, identifiers are unique and map back to sample IDs, each sample contains the expected files and roles, no dataset is missing/duplicated/failed/substituted, datatypes and genome builds are accepted, and aligned collections have matching identifiers and ordering.

For sample sheets, verify: exact required columns and accepted values, row count and uniqueness, sample/file references against the readiness record, groups/controls/batches/subjects/covariates/contrasts, delimiter/quoting/null representation, and successful parsing by the target consumer when a non-destructive validation path exists.

Do not invoke the downstream analysis until verification passes.

## Output record

```yaml
galaxy-input-model:
  version: 1
  readiness_record_status: ready | ready_with_warnings
  consumer:
    kind: tool | workflow
    name: ""
    id: ""
    input_name: ""
    contract_verified_from: ""
  decision:
    representation: dataset | list | paired | list:paired | nested | tabular_sample_sheet | multiple_data
    semantic_unit: file | sample | subject | contrast | other
    rationale: ""
    alternatives_rejected: []
  identifier_mapping:
    - sample_id: ""
      galaxy_identifier_or_row: ""
  construction:
    method: reuse | galaxy_native_tool | apply_rules | sample_sheet_tool | direct_api
    source_ids: []
    tool_ids: []
    output_id: ""
  verification:
    expected_shape: ""
    observed_shape: ""
    expected_elements: 0
    observed_elements: 0
    checks:
      - check: ""
        result: pass | fail
        evidence: ""
  status: verified | failed | blocked
  warnings: []
```

## Failure handling

Stop and return to `analysis-readiness` when: a file has no unambiguous sample or mate role even after investigation, the control/reference group is only inferred and the user has not confirmed it, replicates cannot be distinguished, sample-sheet fields require absent metadata, the requested contrast is unsupported, construction reveals missing/extra/duplicate/mismatched files, or the target input contract cannot be verified. Preserve evidence, report `failed` or `blocked`, and do not invoke the analysis.
