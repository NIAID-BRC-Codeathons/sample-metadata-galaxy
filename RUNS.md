# Runs

These are Loom / Galaxy analysis runs, now organized under `case_studies/`.

## case_studies/broad/naive/

PDF: **Perturbation-specific transcriptional mapping for unbiased target elucidation of antibiotics** (`project1v2/pnas.202409747.pdf`)

Naive agent runs (no skills) for the Romano, Bagnall et al. *PNAS* 2024 PerSpecTM RNA-seq study (*P. aeruginosa* PA14; GEO GSE251671 / SRA PRJNA1055047).

- `project1v2/` — the canonical run: metadata reconstruction + Galaxy execution attempt (smoke run failed on DESeq2 + GTF issues).
- `project1-metadata-only/` — earlier session, metadata construction only. This is where the confident errors (water dosage, single/paired mislabeling) were identified.
