---
name: metadata-construction
description: >
  Default first step for most analyses. Assemble structured sample metadata from
  public records, the data itself, and user input before any analysis can proceed.
  Use for any request involving samples, files, accessions, a study, or a biological
  question that is more than simple information retrieval.
metadata:
  surfaces: [loom]
when_to_use: >
  Fetch this skill first for essentially any analysis request — anything beyond
  answering a factual question or looking up a reference. If the user mentions
  samples, files, FASTQs, a BioProject, SRA, GEO, a history, a workflow, a study,
  an organism, a comparison, or a biological question, start here. For public data,
  track down metadata from NCBI, EBI, GEO, and linked publications before asking
  the user. For the user's own data, interview them for the experimental design.
  Skip only if the user already has a complete, validated sample sheet. Analysis
  must not proceed until metadata has been structured here and validated by
  analysis-readiness.
---

# Metadata Construction

Default first step for most analyses. Most users arrive with data but no structured metadata — that is expected. Build a draft metadata record from whatever the user has.

- **Public data** (accessions, BioProject, GEO, SRA, a publication): track down what you can from public sources before asking the user. The user should not have to provide what is publicly available.
- **User's own data** (local files, Galaxy history, private study): interview the user for the experimental design. They are the authoritative source.

This skill builds metadata; it does not validate it. That is the job of `analysis-readiness`.

## Core principles

- Every extracted value is a claim with provenance (`reported`, `observed`, `inferred`, `conflicting`, `unknown`), not a fact.
- Use all available evidence, including filenames and file characteristics, but label it honestly. Filename-derived values are `inferred`. Do not present inferred values as confirmed.
- Never fabricate a value to fill a gap. Explicit `unknown` or `not_found` is always preferable to a plausible-sounding guess.
- If a source is silent on a field, mark `not_found` — do not invent what the source would have said.
- If a field requires the user's knowledge (e.g. which condition is the control), ask. Do not decide for them.
- Three kinds of unknowns: `not_yet_checked` (go check it), `cannot_determine` (tried, source silent), `needs_user_input` (not answerable from any source — ask the user).
- Flag every unknown, conflict, and unresolved question to the user in the conversation, not just in the notebook.
- Record every source consulted and what it yielded, including failed lookups.

## Workflow

### 1. Elicit what the user knows

Ask what they can tell you: biological question, assay, organism, accessions or DOIs, where the files are, what they know about the experimental design, and any sample sheet or README they already have. Partial answers are fine.

### 2. Locate all relevant data and records

Find everything associated with the study. Cross-reference identifiers in both directions — e.g. BioProject ↔ SRA/GEO/ENA, PubMed/DOI ↔ BioProject/GEO/SRA, BioSample ↔ project and runs, anything in a README or data availability statement. Do not assume the provided files are the complete study.

Practical notes:
- GEO HTML pages are recaptcha-gated in headless fetches. Use NCBI E-utilities, GEO SOFT files, or GEO FTP instead. If a fetch returns "Checking your browser," stop — that body is not parseable metadata.
- Save remote responses to files before parsing. Do not pipe remote HTTP content into Python or R — some agent sandboxes refuse this on purpose.
- One GSM often maps to multiple SRRs (technical replicates, resequencing, split lanes). This is normal — do not treat each SRR as a biological sample.

### 3. Extract from all available sources

Pull from public records (BioSample, SRA, GEO, ArrayExpress, PubMed, supplementary files), from the data itself (Galaxy dataset metadata, FASTQ headers, file names, read counts, collection structure), and from the user. Map every value to a sample. When a public-record sample ID differs from the user's, record the mapping and flag it.

Record `library_layout` per run, not per series — the paper and GEO series-level metadata may say paired when individual runs are mixed. One run with a different layout is not an error in the data; it is a fact to record.

File-derived values are `observed`. Filename-derived values are `inferred`. Neither is `confirmed`.

If a `sample_id` or `condition_id` looks like it was built by concatenating fields (e.g. `project:pert:dose:strain:time:block`), the formatting is load-bearing — a formatting drift (e.g. dose rounding, case change) will not error, it will silently split replicates. Reconstruct the grammar from author code where available, not from examples. If a published ID has a token you cannot derive from other metadata, it is an intake column, not a comment — record it explicitly.

### 4. Reconcile across sources

For each field and sample: if sources agree, record the stronger provenance. If they conflict, record both and mark `conflicting`. If only one source provides a value, use its provenance level. If none, mark `unknown` with the appropriate unknown type.

### 5. Produce two artifacts

**Provenance YAML** — record in the notebook with real values:

```yaml
metadata-construction:
  version: 1
  status: draft
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
  sources_consulted:
    - source: ""
      kind: user | bioproject | sra | geo | arrayexpress | biosample | pubmed | doi | file_inspection | galaxy_metadata | other
      what_it_yielded: ""
  samples:
    - sample_id: ""
      source_record_id: ""
      user_provided_id: ""
      id_mapping_confidence: confirmed | inferred | conflicting
      fields:
        - field: ""
          value: ""
          provenance: reported | observed | inferred | conflicting | unknown
          source: ""
          unknown_type: not_yet_checked | cannot_determine | needs_user_input
          notes: ""
      files:
        - ref: ""
          role: single | forward | reverse | interleaved | other | unknown
          role_provenance: reported | observed | inferred | unknown
          datatype: ""
  unresolved_questions_for_user:
    - question: ""
      field: ""
      why_it_matters: ""
  conflicts:
    - field: ""
      sample_id: ""
      values:
        - value: ""
          source: ""
      notes: ""
```

**Tabular sample metadata** (TSV/CSV) — one row per biological sample, one column per relevant field. Include file references so `galaxy-input-modeling` can map samples to Galaxy datasets. Use `unknown` explicitly for undetermined values — never blank. Every value must trace back to a provenance entry in the YAML. Save as a file in the project directory and record its path in the YAML.

Example:

```
sample_id	file_ref	role	condition	control_status	biological_replicate	assay	organism	reference	layout
S1	galaxy:abc123	forward	treated	neither	R1	RNA-seq	Homo sapiens	hg38	paired
S1	galaxy:def456	reverse	treated	neither	R1	RNA-seq	Homo sapiens	hg38	paired
S2	galaxy:ghi789	forward	control	control	R1	RNA-seq	Homo sapiens	hg38	paired
S2	galaxy:jkl012	reverse	control	control	R1	RNA-seq	Homo sapiens	hg38	paired
S3	galaxy:mno345	single	unknown	unknown	unknown	unknown	unknown	unknown	unknown
```

## Handoff

Pass both artifacts to `analysis-readiness`. Both are drafts for validation — neither is ready for analysis. If the user arrived with a complete, already-structured sample sheet, skip to `analysis-readiness`.
