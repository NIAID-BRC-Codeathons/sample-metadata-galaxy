# Case Study: Blasi — A Naive-User Scenario

A second case study using a published study we do not know the authors of, closer to what a naive user experiences when arriving with a paper and no privileged ground truth.

**Paper:** Cianciulli Sesso et al., "Gene Expression Profiling of *Pseudomonas aeruginosa* Upon Exposure to Colistin and Tobramycin," *Front. Microbiol.* 2021. doi: [10.3389/fmicb.2021.626715](https://doi.org/10.3389/fmicb.2021.626715)

Same organism (*P. aeruginosa* PA14) and treatment context (antibiotic exposure) as the Livny case study, but a different lab, different assay, and no ground truth.

## Structure

Each paper gets two bundles — a **naive** run (no skills) and a **with-skills** run — so we can compare:

- `naive/` — agent runs without the skills. This is the baseline.
- `with-skills/` — agent runs with the skills enabled. (Not yet run for this paper.)

## What's in `naive/`

- `proj_blasi_reanalysis/` — the agent reanalyzed the colistin vs. water arm of the study using DESeq2 in Galaxy, including a custom PA14 reference and CDS-to-exon GTF fix (same bacterial GTF issue found in the Livny case study).
