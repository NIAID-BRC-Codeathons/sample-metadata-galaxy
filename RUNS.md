# Runs

These are Loom / Galaxy analysis runs, now organized under `case_studies/`.

## case_studies/livny/naive/

PDF: **Perturbation-specific transcriptional mapping for unbiased target elucidation of antibiotics** (`project1v2/pnas.202409747.pdf`)

Naive agent runs (no skills) for the Romano, Bagnall et al. *PNAS* 2024 PerSpecTM RNA-seq study (*P. aeruginosa* PA14; GEO GSE251671 / SRA PRJNA1055047).

- `project1v2/` — the canonical run: metadata reconstruction + Galaxy execution attempt (smoke run failed on DESeq2 + GTF issues).
- `project1-metadata-only/` — earlier session, metadata construction only. This is where the confident errors (water dosage, single/paired mislabeling) were identified.
- `livny/` — reanalysis of a single arm (colistin vs water) using DESeq2.

## case_studies/blasi/naive/

Naive agent run for the Cianciulli Sesso et al. *Front. Microbiol.* 2021 study (*P. aeruginosa* PA14 colistin/tobramycin response).

- `proj_blasi_reanalysis/` — DESeq2 reanalysis of the colistin vs. water arm in Galaxy, including custom PA14 reference and CDS-to-exon GTF fix.
