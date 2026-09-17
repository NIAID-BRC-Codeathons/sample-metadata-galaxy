---
name: reproduce-published-omics
description: >
  Recreate a published omics analysis from the paper, GEO/SRA, and author
  code — not from methods prose alone. Use when the user wants to reproduce
  RNA-seq / perturbation / expression-profiling results, asks what metadata
  each FASTQ needs, or points at a paper plus a GEO/SRA accession. Triggers:
  "recreate these analysis", "reproduce the paper", "what metadata do I need
  for each FASTQ", GSE*/PRJNA*/SRP* plus a methods PDF, PerSpecTM / CMAP-style
  screens, "author pipeline", "intake template".
---

# Reproduce a published omics analysis

The paper is a claim. The pipeline is the contract. GEO/SRA are the inventory.
Treat mismatches among those three as the actual work, not as noise.

## Order of evidence

Do not design a metadata sheet from the Materials and Methods section and then
go looking for files. Work in this order:

1. **Paper** — experimental arms, time points, doses, strain list, data
   availability accessions (GSE, PRJNA, GitHub).
2. **Author code** — the scripts that actually join counts to metadata. Column
   names, ID construction, batch keys, and filters live here.
3. **GEO SOFT / series matrix** — per-sample characteristics as deposited.
4. **SRA run table** — layout, instrument, one-GSM-to-many-SRR, bytes.
5. **Author supplementary tables** — the collapsed condition/batch tables the
   figures were made from. These are the ground truth for ID formulae.

If any of 2–5 is missing, say so. Do not invent a schema to fill the gap.

## What the paper will lie about (quietly)

These showed up in GSE251671 / PRJNA1055047 / Romano et al. PNAS 2024 and will
show up again:

- **Library layout.** Paper and GEO both said paired-end; SRA was mixed
  PAIRED/SINGLE. Record layout *per run*, never as a series-level constant.
- **Sample count.** GEO GSMs, manuscript tables, and figure n's routinely
  disagree (here: 1,059 GSMs vs 814 manuscript rows vs 270 collapsed
  conditions). Name which universe you are in.
- **One GSM, several SRRs.** Tech-rep concatenation is often already done in
  the author's `raw_file*_combined` column and *not* done in SRA. If you
  re-download, concatenate per GSM before alignment.
- **ID suffixes that look decorative.** A trailing `:A` / `:B` was a second
  replicate *block* on the same plate. It was not recoverable from GEO or the
  manuscript table. If a published ID has a token you cannot derive, it is an
  intake column, not a comment.

See [geo-sra-intake](../geo-sra-intake/SKILL.md) for how to pull NCBI without
the recaptcha wall, and [composite-sample-ids](../composite-sample-ids/SKILL.md)
for load-bearing concatenated IDs.

## Metadata is the analysis

For perturbation screens (moderated z-score, CMAP, PerSpecTM, and relatives)
the computational method is a function of **who shares a batch**, not of the
FASTQ header.

- A batch is typically plate × strain × time (or whatever the author script
  groups on). Write that grouping down before you write a sample sheet.
- Z-score / quantile-norm batches have a **minimum composition** (here: one
  DNA-synthesis inhibitor, one protein-synthesis inhibitor, a cell-wall *or*
  membrane inhibitor, plus negcons). A sheet that is schema-valid can still
  be analytically empty. Validate composition, not just columns.
- Different arms normalize differently. CRISPRi batches in this paper
  normalize across strains, not across MOAs. Do not apply the reference-set
  composition rule to every arm.
- Compound annotation (`pert_target`, `pert_mechanism`, class) is not
  optional decoration — it *is* the label set the predictor uses. Query
  compounds being predicted will (correctly) lack it; do not error them the
  same way as a missing reference compound.

## Do not circularly validate

If you generate `condition_id` with a formula, then check that the same
formula reproduces `condition_id`, you have tested nothing.

Check the formula against **the authors' published IDs**. The misses are the
finding (here: 240/250 exact; the 10 misses were `:B` vehicle blocks that
existed only in the reference-set table).

Then fault-inject a copy of the template (dose rounding, duplicate
`sample_id`, `pert_type="control"`, missing R2, reused FASTQ, bad block
letter) and confirm each class is caught. A validator that has never failed
on purpose is not a validator.

## Deliverables that actually help

Write these before downloading a single FASTQ:

- A **FASTQ manifest** keyed by GSM/SRR with perturbation + batch columns
  joined in.
- An **intake template** with the author's column order and a few worked
  rows covering every arm (WT treatment, vehicle, hypomorph, CRISPRi,
  blinded query).
- A **compound annotation** sheet keyed by `pert_id`.
- A **validator** with error classes for silent-split bugs (dose format,
  constructed IDs, layout vs files) and warnings for batch composition.

State the scope honestly: metadata-validated is not pipeline-reproduced.
Reproduction starts when one real batch runs `FASTQ → counts → VST → z-score`
against this manifest and the author's IDs reappear.

## NCBI and sandbox notes

- GEO HTML is recaptcha-gated. Use E-utilities, GEO FTP, or SOFT. See
  [geo-sra-intake](../geo-sra-intake/SKILL.md).
- Do not pipe a remote HTTP body into Python/R. Save to a file, then parse
  the file. Some agent sandboxes will refuse `curl | python` on purpose.
