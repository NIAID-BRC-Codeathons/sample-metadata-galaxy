---
name: analysis-readiness
description: >
  Validate assembled sample metadata against the data and the intended analysis
  before any tool or workflow runs. Detect incomplete, inaccurate, unverified, or
  missing metadata, study-design gaps, file-layout mismatches, and data-suitability
  problems. Use after metadata-construction, or when the user has a sample sheet
  that needs checking.
metadata:
  surfaces: [loom]
when_to_use: >
  Fetch this skill after metadata-construction has produced a draft metadata record,
  or when the user already has a structured sample sheet. Use before running any
  analysis, workflow, or tool — the analysis must not proceed until this skill has
  declared the study ready or ready with warnings. If metadata-construction has not
  been run yet, send the user there first. The scope is open-ended: anything that
  could undermine validity, interpretation, or input construction counts as a gap.
---

# Analysis Readiness

Validate assembled metadata against the data and the intended analysis before any tool or workflow runs.

## Preconditions

Expects two artifacts from `metadata-construction`:
1. The provenance YAML record (every value traced to a source).
2. The tabular sample metadata (one row per sample, the practical form for Galaxy input construction).

If neither exists, send the user to `metadata-construction`. If the user has a complete sample sheet, treat it as a draft — every value is a claim to validate.

## Core principles

- Treat all metadata as claims to validate, not facts to trust.
- Use all available evidence, including filenames, but label it honestly: filename-derived values are `inferred`, not `confirmed`. Flag inferred values to the user so they know the confidence level.
- Separate `reported`, `observed`, `inferred`, and `confirmed` values.
- Never guess to fill a gap. Explicit `unknown` or `not_found` is always preferable to a plausible fabrication.
- When a check is inconclusive, say so — do not round toward a convenient answer.
- When a decision requires biological or experimental judgement (which condition is the control, whether replicates are biological, whether a batch effect is acceptable), say so and stop. Do not decide for the user.
- Three kinds of unknowns: `not_yet_checked` (go check it), `cannot_determine` (tried, evidence insufficient), `needs_human_judgement` (not resolvable from data — ask the user and stop).
- Flag every unknown, conflict, and unresolved issue to the user in the conversation, not just in the notebook.

## Scope

This skill looks for **anything** that could make the analysis invalid, uninterpretable, or incorrectly constructed — not a fixed checklist. The examples below are common cases, not an exhaustive list. If something looks wrong, unsupported, inconsistent, fabricated, or irrelevant, flag it even if it is not named here:

- metadata fields that are missing, empty, placeholder, or defaulted;
- values that conflict with observed data or with each other;
- references, identifiers, URLs, or accessions that do not resolve or point to the wrong thing;
- values that look plausible but are likely hallucinated or copied from an unrelated study;
- files, datasets, or collections that are the wrong type, organism, build, or assay;
- study-design assumptions (controls, replicates, pairing, batches, confounders) that are unstated or unsupported;
- sample-to-file mappings that are ambiguous, duplicated, or missing;
- study data that are incomplete because linked records were not followed;
- anything else that a careful analyst would question before running the analysis.

## Workflow

### 1. State the intended analysis

Capture in plain language: biological question, assay, experimental unit, conditions or groups to compare, control or reference level, primary contrast, design structure (paired, repeated-measures, blocked, batch), covariates, and candidate Galaxy tool or workflow if already selected. If the user cannot define the comparison, that is a blocking design gap — do not choose one for them.

### 2. Review the assembled metadata

Review both artifacts: the provenance YAML (honest provenance, visible conflicts) and the tabular (internally consistent, every value traces back to provenance, suitable for the intended analysis). Confirm one row per biological sample with separate file records where a sample has multiple files.

### 3. Validate internal consistency

Check anything that could be wrong — the items below are a floor, not a ceiling:

- sample IDs are non-empty and unique;
- every input file maps to exactly one sample and role;
- no expected sample or file is missing or duplicated;
- group labels, controls, and contrasts are explicit and refer to observed groups;
- biological and technical replicates are not conflated;
- repeated or paired observations have subject/block identifiers;
- file labels, extensions, datatypes, and observed content agree;
- reference build, organism, assay, and annotation are compatible;
- sample count and replication are suitable for the requested inference;
- any URLs, accessions, or external references resolve and point to the intended resource;
- no value appears fabricated, templated, or copied from an unrelated study.

### 4. Test claims against the data

Use the least expensive reliable check appropriate for each claim — e.g. inspect Galaxy dataset metadata, FASTQ headers, read counts, tabular headers, reference identifiers, or resolve URLs and accessions. A similar number of records in two files is supporting evidence for pairing, not proof by itself. Two files labeled "single" may be suspected mates — use that as a hypothesis, but flag it as `inferred` and do not treat it as confirmed until verified.

### 5. Classify every issue

Severity: `blocking` (could invalidate the run or interpretation), `warning` (can proceed but limitations must be visible), `informational`. For each issue state: the claim or missing fact, why it matters, evidence inspected, what would resolve it, its unknown type (`not_yet_checked`, `cannot_determine`, `needs_human_judgement`), and whether the user or a data check can resolve it.

### 6. Produce the readiness record

```yaml
analysis-readiness:
  version: 1
  status: ready | blocked | ready_with_warnings
  tabular_file: "sample-metadata.tsv"
  intended_analysis:
    question: ""
    assay: ""
    method_or_workflow: ""
    experimental_unit: ""
    primary_contrast: ""
    design_factors: []
  data_provenance:
    identifiers_checked:
      - identifier: ""
        type: bioproject | sra | geo | arrayexpress | biosample | pubmed | doi | other
        resolved_to: ""
        linked_records_found: []
        status: resolved | unresolved | partial | not_checked
    completeness:
      provided_subset_of_larger_study: false
      missing_records: []
      notes: ""
  samples:
    - sample_id: ""
      condition: ""
      control_status: unknown
      biological_replicate: ""
      technical_replicate: ""
      subject_id: ""
      batch: ""
      files:
        - ref: ""
          role: single | forward | reverse | interleaved | other | unknown
          datatype: ""
      claims:
        - field: ""
          value: ""
          provenance: reported | observed | inferred | confirmed
          evidence: ""
  requested_input_contract:
    consumer: "tool or workflow name/id"
    inputs:
      - input_name: ""
        required_shape: dataset | list | paired | list:paired | nested | tabular_sample_sheet | unknown
        datatype: ""
        semantic_unit: file | sample | subject | contrast | other
  issues:
    - severity: blocking | warning | informational
      field: ""
      message: ""
      unknown_type: not_yet_checked | cannot_determine | needs_human_judgement
      evidence: ""
      resolution: ""
  checks:
    - check: ""
      result: pass | fail | inconclusive
      evidence: ""
  confirmed_by_user: []
```

`status: ready` only when there are no blocking issues and evidence is sufficient. `ready_with_warnings` only when warnings do not undermine validity. Otherwise `blocked`.

## Handoff

When `ready` or `ready_with_warnings`, hand the validated tabular and the readiness YAML to `galaxy-input-modeling`. If `blocked`, stop and request what is needed to unblock. If the gap is that metadata were never assembled, send the user to `metadata-construction`.
