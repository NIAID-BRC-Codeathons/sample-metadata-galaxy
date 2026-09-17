```loom-session
id: 01a0aaf9-52aa-74f0-a900-ce73d4a3b388
started_at: 2026-09-16T16:07:41.928Z
ended_at: 2026-09-16T16:08:56.187Z
notebook: notebook.md
orphaned_active_steps: 0
```

```loom-session
id: 01a0aafa-dc1f-7dae-a1a9-25a3e1836374
started_at: 2026-09-16T16:09:22.595Z
ended_at: 2026-09-16T16:09:44.862Z
notebook: notebook.md
orphaned_active_steps: 0
```

```loom-session
id: 01a0ab1c-44ca-7544-89eb-6cfee4334886
started_at: 2026-09-16T16:45:52.116Z
ended_at: 2026-09-16T16:52:55.127Z
notebook: notebook.md
orphaned_active_steps: 0
```

```loom-session
id: 01a0ab22-c544-74e6-8123-b6bb3ba80575
started_at: 2026-09-16T16:52:58.172Z
ended_at: 2026-09-16T16:53:08.055Z
notebook: notebook.md
orphaned_active_steps: 0
```

## 2026-09-16 — PerSpecTM paper: experimental design + FASTQ metadata schema

Source: `pnas.202409747.pdf` — Romano, Bagnall et al., *PNAS* 2024;121(45):e2409747121.
Goal: understand the design well enough to reproduce it, and determine what
metadata each FASTQ needs.

### Data locations

- GEO **GSE251671** — 1,059 samples, platform GPL27892, *P. aeruginosa* UCBPP-PA14 (taxid 208963)
- SRA **PRJNA1055047** / SRP479194 — 1,310 runs, NovaSeq 6000
- Code: `github.com/broadinstitute/psa_rnaseq_manuscript_rproject`
- Reference assembly: NC_008463.1 (paper's methods say "NC_0088463.1", a typo — 8 digits, no such accession)

### Experimental design

384-well plates, 60 µL/well, ~1×10⁸ CFU/mL in LB, 37 °C static, humidity chamber.
Three arms, all biological triplicate, DMSO 0.5% + water 0.5% vehicle controls on every plate:

| Arm | Strains | Perturbation | Time |
| --- | --- | --- | --- |
| Antimicrobial reference set | PA14 WT | 37 compounds @ 0.5×/2×/4× MIC (high-inoculum MIC) | 90 min std; 30/60/90/120 time trial |
| Hypersusceptible | 7 promoter-replacement hypomorphs + `oprL`-hypo | on-target + 2 off-target @ 2× strain MIC | 90 min |
| Genetic depletion | 19 CRISPRi strains + C26 no-guide control | arabinose 0 / 0.125 / 0.5 % | 360 min |

Library: RNAtag-seq (barcode ligation → pool → riboPOOL rRNA depletion →
template-switch RT → P5/P7 PCR), NovaSeq SP 100.

Analysis: BWA → CDS counts → drop samples >80% zero genes / genes zero in ≥50%
samples → DESeq2 VST → quantile-norm + moderated z-score **within batch** →
replicate collapse by Spearman-weighted average, clip ±10 → Pearson correlation
vs reference → r̄max per target category → rpredict → PPV from LOOCV ROC tables.
DESeq2 runs separately only to flag "transcriptionally weak" samples
(no gene with −log₁₀ padj > 20).

**Batch composition is a design parameter, not just bookkeeping.** Batch =
plate × strain × timepoint; z-scores are computed across all samples in it.
The authors' rarefaction analysis requires each batch to contain at minimum a
DNA-synthesis inhibitor, a protein-synthesis inhibitor, a cell-wall *or*
membrane inhibitor, and negative controls.

### Metadata required per FASTQ

Six tiers: (1) file/sequencing, (2) perturbation, (3) strain/organism,
(4) batch structure, (5) compound annotation joined on `pert_id`,
(6) pipeline-derived fields left blank at intake. Full 35-column schema in
`products/sample_metadata_TEMPLATE.csv`; rationale in `products/README.md`.

### Products generated

| File | Contents |
| --- | --- |
| `products/GSE251671_fastq_manifest.csv` | 1,059 rows × 43 cols — GSM/SRR/SRX/BioSample, run stats, perturbation + batch metadata, joined compound annotation |
| `products/sample_metadata_TEMPLATE.csv` | 35-col intake sheet, 6 worked rows spanning all arms |
| `products/compound_metadata_TEMPLATE.csv` | Per-`pert_id` MOA/target annotation sheet |
| `products/validate_metadata.py` | Pre-flight validator, 10 error + 4 warning classes |
| `products/README.md` | Provenance, design constants, the three findings below |

Manifest totals: 1,059 samples / 352 conditions / 35 batches / 196.6 GB.
Categories: antimicrobial_reference_set 724, weak_signal_removed 141,
CRISPRi_not_in_reference_set 99, CRISPRi_reference_set 71, internal_test_compounds 24.
210 samples flagged `weak_signal=TRUE`.

### Findings

**1. `pert_idose` formatting is load-bearing.** `condition_id`/`comb_id` are
string-pasted from it via `sprintf("%.5f")`. `4.5uM` vs `4.50000uM` raises no
error anywhere in the R pipeline — it silently splits a 3-replicate condition
in two and the weighted replicate collapse then averages the wrong samples.
Most likely way to corrupt a reanalysis. → validator E3.

**2. The `condition_id` block suffix cannot be derived.** Normally `:A`, but
the published reference set has 10 vehicle conditions ending `:B` (a second
replicate block, same plate/vehicle/timepoint). Verified the 8 `MOC_1430` `:B`
conditions exist in the authors' reference-set metadata yet have **no matching
rows** in the manuscript table or GEO, and no other column distinguishes them.
So block must be captured explicitly at intake — added as a first-class `block`
column rather than inferred. → validator E5, with W3/W4 catching the collapse
failure mode.

**3. Library layout contradicts the paper.** Paper and GEO both say paired-end;
SRA runinfo is 1,028 PAIRED / 282 SINGLE runs = 918 / 141 at sample level, read
lengths 90/89/49/48/41 nt. No GSM mixes layouts internally. Also 239 GSMs map to
>1 SRR (233×2, 6×4) and need per-GSM concatenation before alignment — consistent
with the authors' `raw_file*_combined` naming. → validator E8.

### Verification

- Validator syntax-checked; `sample_metadata_TEMPLATE.csv` → exit 0, no errors.
- Fault injection (6 classes: dose drift, duplicate `sample_id`, bad `pert_type`,
  paired-end missing R2, reused FASTQ path, lowercase block) → all 6 caught, exit 1.
- Run against the authors' real 814-row metadata table: only E10 fires, on the 4
  genuinely unannotated `pert_id`s (`ara`, `pa0918`, `pa69180`, `brd5750`) — correct,
  since test-compound MOA is the prediction target. Remaining warnings are real
  design features (single-strain `oprL` batch, 270-min hypomorph plates without negcons).
- `condition_id` formula checked against the authors' own values: 240/250 exact in the
  reference set (10 diffs = the `:B` blocks, finding 2), 24/24 exact for CRISPRi.
- Manifest cross-checked against the manuscript table: 748/814 titles matched;
  66 unmatched are `pa69180` and CRISPRi `ara` rows absent from GEO.
- All 1,059 GSMs in SRA runinfo resolve to GEO samples (0 orphans).

No FASTQ downloaded; no expression value recomputed. Reproducing the pipeline
itself is separate work.

```loom-session
id: 01a0abae-00c0-790a-8124-e95d212135b0
started_at: 2026-09-16T19:25:03.126Z
ended_at: 2026-09-16T21:23:08.262Z
notebook: notebook.md
orphaned_active_steps: 0
```

```loom-session
id: 01a0ac29-28a3-714c-98b5-2e31a381001e
started_at: 2026-09-16T21:39:34.293Z
ended_at: 2026-09-16T21:43:21.578Z
notebook: notebook.md
orphaned_active_steps: 0
```
