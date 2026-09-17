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

## 2026-09-17 — Galaxy workflow assessment: End to End Differential Expression RNA-seq

Target workflow: `7f8eb3a584e8080b` on usegalaxy.org (UI "Version: 4", API
`version: 3`), owner `marius`, published. fastp → STAR → counts → DESeq2 →
volcano/heatmaps, with two nested subworkflows (`15cbf3bd320b9df4` processing,
`d5e6089f681628e9` DE). Question asked: can our products satisfy its 15 inputs?

### Compatibility findings

**A. All FASTQs are retrievable.** All 1,310 SRRs referenced by the manifest
resolve on ENA (`PRJNA1055047`), 0 missing, 0 extra. File counts agree with
layout for every GSM: 1,028 PAIRED×2 files, 282 SINGLE×1. Zero disagreements
between ENA `library_layout` and the manifest.

**B. The workflow is paired-end only.** Input 0 is a `sample_sheet:paired`
collection. The 141 SINGLE samples (all `weak_signal_removed`, 41 nt) cannot
enter it. Usable pool: **918 samples / 171 GB**. Confirms notebook finding 3.

**C. Galaxy's built-in PA14 is the wrong genome for this reproduction.** The
STAR index list (6,258 genomes) offers `Pseudomonas aeruginosa PA14
(GCF_045689255.1)` — a 2024 Georgia Tech re-sequencing on contig
`NZ_CP136842.1`, 6,051 genes, locus tags `R0792_RS*`. The paper used
`NC_008463.1` (`GCF_000014625.1`, UCBPP-PA14, MGH 2006), 6,041 genes, tags
`PA14_RS*`. Intersection of gene_id sets: **0**. Using the built-in would make
every result untranslatable to the published tables. → decision: custom index.

**D. Custom reference requires patching, not configuring.** Input 1 "Reference
genome" is a *text* parameter selecting a prebuilt index; the STAR step
hardwires `refGenomeSource.geneSource: "indexed"`. The STAR tool does support
`geneSource: "history"` (`genomeFastaFiles` + `genomeSAindexNbases`), so the
plan owns a modified copy of the workflow.

**E. Bacterial GTFs hit a silent-zero-counts bug.** The workflow hardwires
`sjdbGTFfeatureExon: "exon"` (STAR) and `gff_feature_type: "exon"`
(featureCounts). The NC_008463.1 GTF carries only **80 `exon` lines** — all
tRNA/rRNA/ncRNA. All **5,891 protein-coding genes are annotated as `CDS`**
(5,961 genes have ≥1 CDS line; only 80 have ≥1 exon line). Run unmodified, the
pipeline would succeed, green, with near-zero counts for every protein-coding
gene. → mitigation: rewrite CDS→exon in the GTF, which keeps both hardwired
parameters valid.

**F. Two STAR defaults are wrong for a 6.5 Mb genome.** `genomeSAindexNbases`
must be `min(14, log2(6537648)/2 − 1)` = **10**; the default 14 targets ~3 Gb.
`alignIntronMax` is inherited as 1,000,000 — bacteria have no introns, so it
invites spurious spliced alignments. Set to 1.

**G. Strandedness is measurable, not guessable.** RNAtag-seq (paper ref. 65) is
typically reverse-stranded but the methods never state it. STAR's hardwired
`quantMode: GeneCounts` emits unstranded/forward/reverse columns side by side,
so the smoke run determines it empirically.

**H. Vehicle-matched control.** cip/gent/carb/col are all water-vehicle in batch
`MOC_1779_2`; dmso is a separate vehicle arm (87 dmso / 63 water / 24 blank).
Control is therefore `water`, not `dmso`.

**I. Batch columns must stay out of the DESeq2 formula.** Batch = plate × strain
× timepoint is constant within the chosen batch, so including those terms would
make the model matrix rank-deficient. Recorded in the sheet for provenance only.

Selected batch: `MOC_1779_2` / PA14 / 90 min — 174 samples, 17.8 GB, and it
satisfies the authors' rarefaction minimum (DNA-synthesis + protein-synthesis +
cell-wall + membrane inhibitors + both vehicle controls present).

## Plan A: PerSpecTM RNA-seq Pilot on Custom NC_008463.1 [hybrid]

Reproduce the PerSpecTM processing pipeline for one batch of GSE251671
(`MOC_1779_2` / PA14 / 90 min) using a modified copy of the "End to End
Differential Expression RNA-seq" workflow, indexed against the paper's own
reference (NC_008463.1 / GCF_000014625.1) so gene IDs stay comparable to the
published `PA14_RS*` tables.

Two-stage: a 9-sample smoke run to validate the reference, the CDS→exon fix and
measure strandedness; then a 27-sample vehicle-matched pilot spanning four MOAs.

### Steps

- [x] 1. **Build custom reference inputs** {#plan-a-step-1} — fetch NC_008463.1 FASTA + GTF, rewrite CDS→exon
  - Routing: local
  - Tool: curl + awk
  - Detail: emit `PA14_NC008463.gtf` where every `CDS` line is re-emitted as `exon` with `gene_id`/`transcript_id` preserved; retain the original 80 RNA exons
  - Verification: assert exon-bearing gene count rises 80 → ~5,971 and that `gene_id` prefix is `PA14_RS`; confirm single seqid `NC_008463.1` matches the FASTA header
- [x] 2. **Stage reference into Galaxy** {#plan-a-step-2} — server-side URL fetch for FASTA, upload transformed GTF
  - Routing: galaxy
  - Tool: `galaxy_upload_file_from_url` (FASTA), `galaxy_upload_local_file` (GTF)
  - Verification: both datasets reach state `ok`; FASTA datatype `fasta.gz`, GTF datatype `gtf`; GTF line count matches local file
- [x] 3. **Clone and patch the workflow** {#plan-a-step-3} — custom-genome STAR + bacterial alignment params
  - Routing: galaxy
  - Tool: workflow import/update API
  - Detail: in subworkflow step 18 set `refGenomeSource.geneSource=history`, wire new FASTA input, `genomeSAindexNbases=10`, `alignIntronMax=1`, `alignMatesGapMax=1000`; replace the "Reference genome" text input with a data input
  - Verification: re-fetch patched workflow, assert `geneSource == "history"` and the three numeric params hold expected values; confirm input slot count changed as intended
- [x] 4. **Resolve FASTQ URLs + stage smoke cohort** {#plan-a-step-4} — first-SRR-only for the 3 water controls (scope change, see results)
  - Routing: galaxy
  - Tool: ENA filereport join (local) → `galaxy_upload_file_from_url`
  - Verification: each GSM yields exactly one R1 and one R2; every staged file byte-exact against ENA `fastq_bytes`
- [!] 5. **Build sample sheet + smoke run (9 samples)** {#plan-a-step-5} — cip 0.78/1.56 µM vs water, n=3 each
  - FAILED 2026-09-17: DESeq2 target_level (finding O) + GTF/STAR gene loss blocker (finding P). See "Step 5 smoke run FAILED: diagnosis".
  - Routing: galaxy
  - Tool: sample_sheet:paired collection + patched workflow
  - Verification: invocation reaches terminal state, all jobs `ok`; STAR log shows >70% uniquely mapped; counts table is non-trivial for `PA14_RS*` genes
- [ ] 6. **Determine strandedness empirically** {#plan-a-step-6} — from STAR ReadsPerGene columns
  - Routing: local
  - Tool: column-sum comparison on `ReadsPerGene.out.tab`
  - Verification: one of col3 (forward) / col4 (reverse) carries >75% of assigned reads; record the winner as the `Strandedness` value for step 7
- [ ] 7. **Pilot run (27 samples, 4 MOAs + control)** {#plan-a-step-7} — cip, gent, carb, col vs water
  - Routing: galaxy
  - Tool: patched workflow, `~ Condition`, reference level `water`
  - Verification: all jobs `ok`; PCA separates MOA groups; DE gene counts per contrast are non-zero and cip shows the expected SOS/DNA-damage signature

### Parameters

Workflow inputs (all 15):

| # | Parameter | Default | Value | Description |
| --- | --- | --- | --- | --- |
| 0 | Sample sheet of sequencing reads | — | built in step 5 | `sample_sheet:paired` collection |
| 1 | Reference genome | (indexed picker) | replaced by data input | patched to custom FASTA (step 3) |
| 2 | GTF File of annotation | — | `PA14_NC008463_cds2exon.gtf` | from step 1 |
| 3 | DESeq2 Design Formula | — | `~ Condition` | single batch → no batch term |
| 4 | Reference level | (blank) | `water` | vehicle-matched negative control |
| 5 | Forward adapter | (blank) | (blank) | fastp overlap auto-detection |
| 6 | Reverse adapter | (blank) | (blank) | fastp overlap auto-detection |
| 7 | Strandedness | — | `stranded - reverse` (step 6 confirms) | RNAtag-seq typically reverse; vocabulary is constrained — see step 3 results |
| 8 | Adjusted p-value threshold | 0.05 | 0.05 | |
| 9 | log2 fold change threshold | 1.0 | 1.0 | |
| 10 | Generate additional QC reports | false | true | needed to validate a novel reference |
| 11 | Use featureCounts | false | false (smoke) / true (pilot) | smoke needs STAR's ReadsPerGene for step 6 |
| 12 | Compute Cufflinks FPKM | false | false | slow, not needed |
| 13 | Compute StringTie FPKM | false | false | not needed |
| 14 | FPKM-exclusion GTF | (optional) | (omitted) | Cufflinks disabled |

STAR parameters patched in step 3:

| Parameter | Default / inherited | Value | Description |
| --- | --- | --- | --- |
| `refGenomeSource.geneSource` | `indexed` | `history` | paper's NC_008463.1 |
| `genomeFastaFiles` | n/a | new data input | `GCF_000014625.1` FASTA |
| `genomeSAindexNbases` | 14 | 10 | `log2(6537648)/2−1`; 14 targets ~3 Gb |
| `alignIntronMax` | 1000000 | 1 | bacteria have no introns |
| `alignMatesGapMax` | 1000000 | 1000 | realistic fragment size |

STAR inherited unchanged: `twopassMode=None`, `sPaired=paired_collection`,
`sjdbGTFfeatureExon=exon`, `sjdbOverhang=100`, `quantMode=GeneCounts`,
seed group (`seedSearchStartLmax=50`, `seedSearchStartLmaxOverLread=1.0`,
`seedSearchLmax=0`, `seedMultimapNmax=10000`, `seedPerReadNmax=1000`,
`seedPerWindowNmax=50`, `seedNoneLociPerWindow=10`), align group
(`alignIntronMin=20`, `alignSJoverhangMin=8`, `alignSJDBoverhangMin=1`,
`alignSJstitchMismatchNmax=0,-1,0,0`, `alignSplicedMateMapLmin=0`,
`alignSplicedMateMapLminOverLmate=0.66`, `alignWindowsPerReadNmax=10000`,
`alignTranscriptsPerWindowNmax=100`, `alignTranscriptsPerReadNmax=10000`,
`alignEndsType=Local`, `peOverlapNbasesMin=0`, `peOverlapMMp=0.01`), filter
group (`basic_filters=exclude_unmapped`, `outFilterType=true`,
`outFilterMultimapScoreRange=1`, `outFilterMultimapNmax=20`,
`outFilterMismatchNmax=999`, `outFilterMismatchNoverLmax=0.3`,
`outFilterMismatchNoverReadLmax=0.04`, `outFilterScoreMin=0`,
`outFilterScoreMinOverLread=0.66`, `outFilterMatchNmin=0`,
`outFilterMatchNminOverLread=0.66`, `outSAMmultNmax=-1`, `outSAMtlen=1`),
output group (`outSAMattributes=NH,HI,AS,nM`, `HI_offset=1`,
`outSAMprimaryFlag=OneBestScore`, `outSAMmapqUnique=255`,
`outWigType=bedGraph`, `outWigStrand=true`), perf group
(`outBAMsortingBinsN=50`, `winAnchorMultimapNmax=50`), `chimOutType` off.
Noted-but-left: `sjdbOverhang` ideally 89 (read length − 1) and
`alignIntronMin` is inert once `alignIntronMax=1`; both harmless on a
spliceless genome.

featureCounts (pilot only): `gff_feature_type=exon` (valid because of the
step-1 rewrite), `gff_feature_attribute=gene_id`, `anno_select=history`,
`summarization_level=false`, `paired_end_status=PE_fragments`,
`exclude_chimerics=true`, `only_both_ends=false`, `checkFragLength=false`,
`mapping_quality=0`, `primary=false`, `ignore_dup=false`, `splitonly` off,
`multifeat` off, `min_overlap=1`, `frac_overlap=0`, `frac_overlap_feature=0`,
`read_extension_5p=0`, `read_extension_3p=0`, `largest_overlap=false`,
`long_reads=false`, `by_read_group=false`, `read_reduction` off, `R=false`,
`format=tabdel_short`, `include_feature_length_file=false`.

Step 1 GTF transform:

| Parameter | Default | Value | Description |
| --- | --- | --- | --- |
| Source FASTA | — | `GCF_000014625.1_ASM1462v1_genomic.fna.gz` | NC_008463.1, 6,537,648 bp |
| Source GTF | — | `GCF_000014625.1_ASM1462v1_genomic.gtf.gz` | 6,041 genes |
| Rewrite rule | — | `CDS` → `exon` | adds 5,966 exon lines |
| Preserve existing exons | — | yes | the 80 tRNA/rRNA/ncRNA lines |
| Expected exon-bearing genes | 80 | ~5,971 | pass/fail assertion |

Cohort + sample-sheet encoding:

| Parameter | Value | Description |
| --- | --- | --- |
| Batch | `MOC_1779_2` / PA14 / 90 min | 174 samples available |
| Smoke cohort | cip + water, n=9, 1.44 GB | 3 GSMs need SRR concatenation |
| Pilot cohort | cip, gent, carb, col, water — n=27, 2.91 GB | 4 MOAs + control; 3 need concatenation |
| `Condition` (smoke) | `water`, `cip_0p78uM`, `cip_1p56uM` | sanitized, drift-proof (see below) |
| `Condition` (pilot) | + `gent_6p25uM`, `gent_12p5uM`, `carb_6400uM`, `carb_12800uM`, `col_12p5uM`, `col_25uM` | 9 levels × 3 reps |
| `Replicate` | 1, 2, 3 | schema declares `int` — must strip the `r` prefix |
| `Batch 1/2/3` | plate, strain, timepoint | provenance only; excluded from formula (finding I) |

`Condition` is a sanitized R-safe label (decimal point → `p`, trailing zeros
dropped) rather than raw `pert_idose`, which directly mitigates notebook
finding 1: `%.5f` drift can silently split a 3-replicate condition. Mapping
back to `pert_idose` stays in the manifest.

### Step 1 results (2026-09-17) — reference built and verified

Artifacts in `reference/`:

| File | Size | md5 |
| --- | --- | --- |
| `GCF_000014625.1_ASM1462v1_genomic.fna.gz` | 1.8M | `e85e904d10348b4521a88b17747824f1` |
| `GCF_000014625.1_ASM1462v1_genomic.gtf.gz` (source) | 656K | `b5783a2ab6617e4fe89ef291442d6d68` |
| `PA14_NC008463_cds2exon.gtf` (transformed) | 13M | `b9be57f22cd58ea907d997594903c8b6` |

Transform (additive — CDS lines retained alongside the new exon lines, so the
file stays valid for CDS-reading tools; featureCounts reads only `exon`, so no
double-counting):

```
awk 'BEGIN{FS=OFS="\t"} /^#/{print; next} {print} $3=="CDS"{ $3="exon"; print }'
```

Verification — all assertions pass:

- **exon-bearing genes: 80 → 6,041 of 6,041.** Exceeds the ~5,971 estimate in
  the plan: the estimate assumed protein_coding (5,891) + 80 RNA genes, but the
  CDS set actually spans 5,961 genes (it includes the 70 pseudogenes). CDS∩exon
  was empty and 0 genes had neither, so the two disjoint sets sum to complete
  coverage. No gene is left uncountable.
- 30,006 feature lines parsed, **0 malformed**; all 9-column; all coordinates
  within 1..6,537,648; all strands valid.
- Feature census after transform: gene 6,041 / exon 6,046 / CDS 5,966 /
  start_codon 5,934 / stop_codon 5,939 / transcript 80. Line delta +5,966 = the
  CDS count, as expected.
- Single seqid `NC_008463.1`, matching the FASTA header; FASTA is 1 record of
  exactly 6,537,648 bp, matching the NCBI assembly report.
- All 6,046 exon lines carry `gene_id` (100% `PA14_RS*` — the paper's
  namespace) and non-empty `transcript_id`; new exon coords mirror source CDS
  exactly (spot-checked `PA14_RS00005`, `PA14_RS12345`).
- `gene_biotype` on 6,041/6,041 gene lines → DESeq2 annotation step will work.
  `gene` symbol on only 1,880/6,041 — an upstream RefSeq limitation, inherited
  by both candidate assemblies, not introduced here.

Note: the file is not coordinate-sorted (RefSeq groups features by gene). STAR
and featureCounts both accept unsorted GTF, so no re-sort applied.

### Step 2 results (2026-09-17) — reference staged in Galaxy

History: **`PerSpecTM GSE251671 — Plan A pilot (NC_008463.1)`**
`bbd44e69cb8906b590d78771d1442073` on usegalaxy.org.

| hid | Dataset | Galaxy id | ext | state |
| --- | --- | --- | --- | --- |
| 1 | `PA14_NC008463.fasta.gz` | `f9cad7b01a472135cb067a4bbc2ff3d4` | `fasta.gz` | ok |
| 2 | `PA14_NC008463_cds2exon.gtf` | `f9cad7b01a47213550f83ae306f2228e` | `gtf` | ok |

FASTA fetched server-side by URL from NCBI (no local round-trip); GTF uploaded
via TUS since it is a locally-derived artifact.

Verification — integrity confirmed by checksum, not just dataset state:

- **SHA-256 match, both files.** FASTA `1d17779c…9ab621`, GTF `6f123b93…d688f47`,
  each identical to the local artifact. Byte sizes also match exactly
  (1,868,144 and 13,117,444).
- Galaxy parsed the GTF as 9 columns / 30,006 data lines / 6 comment lines =
  30,012 total, matching the local file exactly. Attribute keys detected include
  `gene_id`, `gene_biotype`, `transcript_id`, `exon_number`.
- FASTA registered as 1 sequence; peek shows the `NC_008463.1` header.
- Caveat noted and dismissed: the FASTA's `misc_info` carries a truncated
  `Exception ignored in: <_io.BufferedWriter …>` trace from Galaxy's URL-fetch
  cleanup. The SHA-256 match proves the payload is complete; the warning is
  cosmetic.

### Step 3 results (2026-09-17) — workflow cloned and patched

Patched copy: **`End to End DE RNA-seq — custom NC_008463.1 (PerSpecTM)`**
id `a83a2219c9c795ca` (source `7f8eb3a584e8080b` v3, downloaded, edited as JSON,
re-imported via `POST /api/workflows`).

Edits applied to the processing subworkflow (`15cbf3bd320b9df4` copy):

1. New `data_input` step 27 "Genome FASTA" added to the subworkflow.
2. STAR step 18 `refGenomeSource` rewritten from
   `{geneSource: indexed, __current_case__: 0}` to
   `{geneSource: history, __current_case__: 1}` with
   `genomeFastaFiles` connected, `genomeSAindexNbases: "10"`,
   `GTFselect: with-gtf`, `sjdbGTFfeatureExon: exon`,
   `quantMode: GeneCounts`, `diploidconditional: No`.
3. `alignIntronMax: 1000000 → 1`, `alignMatesGapMax: 1000000 → 1000`.
4. Connection `refGenomeSource|GTFconditional|genomeDir` removed;
   `refGenomeSource|genomeFastaFiles` added.
5. Parent-level `data_input` step 19 "Genome FASTA" added and wired into the
   subworkflow.

Verification — re-fetched from the server, 15 assertions, all PASS:

- `geneSource=history`, `__current_case__=1`, `genomeSAindexNbases="10"`,
  `genomeFastaFiles` is a ConnectedValue.
- `GTFselect=with-gtf`, `sjdbGTFfeatureExon=exon`, `quantMode=GeneCounts`,
  `sjdbGTFfile` is a ConnectedValue.
- `alignIntronMax="1"`, `alignMatesGapMax="1000"`.
- `genomeDir` connection gone; FASTA source resolves to a `data_input`
  labelled "Genome FASTA".
- Run-form template reports **16 slots**, new slot 15 "Genome FASTA"
  (`data`/`hda`, required).

Two discoveries from the resolved run-form template:

- **Finding J — `Strandedness` is a constrained vocabulary**, not free text.
  Allowed: `stranded - forward`, `stranded - reverse`, `unstranded`. The plan's
  planned value `reverse` would have been rejected at invoke time. Parameter
  table updated to `stranded - reverse`.
- **Finding K — slot 1 "Reference genome" survives and is still required.**
  Deliberately not removed: it also feeds a `compose_text_param` step whose
  output drives Cufflinks' cached-index selector. Post-patch tracing confirms
  STAR no longer consumes it, and its only remaining consumer (step 24
  Cufflinks) is gated `when: Compute Cufflinks FPKM`, which is `false` in this
  plan. A placeholder string is therefore inert. Removing the input outright
  would have broken that step's wiring for future Cufflinks-enabled runs.

```loom-session
id: 01a0ae3a-79f2-73a8-9e3b-7b1c65abc52a
started_at: 2026-09-17T07:17:43.356Z
ended_at: 2026-09-17T07:49:03.938Z
notebook: notebook.md
orphaned_active_steps: 0
```

### Step 4 results (2026-09-17) — smoke cohort staged (9 samples, 18 files)

Scope change agreed in session: **skip per-GSM SRR concatenation for the smoke
run.** Instead of merging multi-run GSMs, take only the *first* SRR of each.

**Finding L — dropping multi-SRR samples outright would have deleted the entire
control group.** In batch `MOC_1779_2` all six negative controls are 2-SRR
(`water` r1/r2/r3 = GSM7985465/66/67, `dmso` r1/r2/r3 = GSM7985330/31/32), and
there is no single-run `water` sample anywhere in GSE251671 (0 of 1,059 rows).
A strict "single-SRR only" filter therefore yields a cip-only cohort with no
vehicle arm. Resolved by option (b): keep the water controls, use first SRR only.

Depth cost is acceptable — the truncated controls (2.05/3.05/2.51 M reads) sit
*inside* the cip range (1.96–4.82 M), so the controls are not the shallowest
samples and no depth confound is introduced against the treated arm. Full
concatenation is still required for the step-7 pilot, where the water arm
carries the DE contrast.

**Finding M — ENA FASTQ directory shards are `0`+last-two-digits, not
last-three.** First upload attempt built URLs as `SRR272/793/SRR27299793/…`
(last 3 digits) and all 18 datasets failed `HTTP Error 404`. The correct shard
for a 11-char accession is the last two digits zero-padded to three:
`SRR272/093/SRR27299793/…`. Fix: stop constructing URLs and read `fastq_ftp`
verbatim from the ENA filereport. The 18 failed datasets (hids 3–20) were
purged; the good copies are hids 21–38.

Staged into history `bbd44e69cb8906b590d78771d1442073`, 1.80 GB total:

| GSM | Condition | Rep | SRR used | SRR dropped | Reads | hid R1/R2 |
| --- | --- | --- | --- | --- | --- | --- |
| GSM7985294 | cip_0p78uM | 1 | SRR27299793 | — | 3,271,195 | 21 / 22 |
| GSM7985295 | cip_0p78uM | 2 | SRR27299792 | — | 3,945,990 | 23 / 24 |
| GSM7985296 | cip_0p78uM | 3 | SRR27299791 | — | 3,297,839 | 25 / 26 |
| GSM7985297 | cip_1p56uM | 1 | SRR27299790 | — | 4,821,174 | 27 / 28 |
| GSM7985298 | cip_1p56uM | 2 | SRR27299789 | — | 2,798,265 | 29 / 30 |
| GSM7985299 | cip_1p56uM | 3 | SRR27299788 | — | 1,959,530 | 31 / 32 |
| GSM7985465 | water | 1 | SRR27299763 | SRR27299974 | 2,050,087 | 33 / 34 |
| GSM7985466 | water | 2 | SRR27299761 | SRR27299762 | 3,051,934 | 35 / 36 |
| GSM7985467 | water | 3 | SRR27299682 | SRR27299760 | 2,507,861 | 37 / 38 |

Verification — all pass:

- **18/18 datasets in state `ok`**, datatype `fastqsanger.gz`, none in `error`.
- **18/18 byte-exact against ENA `fastq_bytes`.** Every staged file's
  `file_size` equals the ENA-reported byte count for that run and mate, e.g.
  hid 21 = 95,678,011 and hid 28 = 172,660,805. Total 1.80 GB.
- **Pairing correct**: each GSM contributes exactly one `_R1` and one `_R2`,
  confirmed by name and by the `_1`/`_2` suffix assertion on the source URLs.
- All 9 runs are `PAIRED` / 90 nt in the ENA filereport — no layout surprises
  (notebook finding 3 does not bite this cohort).
- The same cosmetic `Exception ignored in: <_io.BufferedWriter …>` note seen in
  step 2 appears in `misc_info` for all 18; byte-exactness proves payloads are
  complete.

Naming convention `GSM_<condition>_r<rep>_R<mate>.fastq.gz` encodes the
sanitized `Condition` level directly, so the step-5 sample sheet can be built
from dataset names without rejoining the manifest.

### Step 5 progress (2026-09-17) — sample sheet built, smoke run submitted

**Sample sheet**: `PerSpecTM smoke cohort (9 samples, cip vs water)`,
hid 75, collection id `952b57960c160968`, type `sample_sheet:paired`.

Schema read from the workflow's step-0 `tool_state` rather than assumed —
`column_definitions` declares `Condition` (string, required), `Replicate`
(int, optional), `Batch 1/2/3` (string, optional). Rows populated as
`[Condition, Replicate, "MOC_1779_2", "PA14", "90min"]`; the batch columns
carry plate/strain/timepoint for provenance only and stay out of the
formula (finding I).

**Finding N — `sample_sheet:paired` collections need a `rows` dict, not
per-element `columns`.** Two API rejections before the right shape emerged:
putting the metadata on each element as `columns` gives
`Missing or null parameter 'rows'`; passing `rows` as a list of lists gives
`Input should be a valid dictionary in ('body','rows')`. Galaxy types it as
`SampleSheetRows = dict[str, SampleSheetRow]` — a **mapping keyed by element
identifier**, sibling to `element_identifiers`, with values as ordered lists
matching `column_definitions`. Also `default_value` must be omitted (not
`null`) for an `int` column, since the validator type-checks it against the
declared type.

Sample-sheet verification — all pass:

- Collection type `sample_sheet:paired`, `element_count` 9.
- All 9 elements well-formed: each has exactly `forward`/`reverse`, the
  forward member's name ends `_R1.fastq.gz` and reverse `_R2.fastq.gz`, both
  in state `ok`, and both names prefix-match their element identifier — so no
  sample got a mate from a different run.
- `Condition` levels balanced 3/3/3 (`cip_0p78uM`, `cip_1p56uM`, `water`);
  `Replicate` is 1/2/3 within each level, stored as int per finding 1's
  drift mitigation.

**Invocation**: `00f8cac7170ede09`, submitted 2026-09-17T14:23:38Z.
Inputs as planned, with two smoke-specific settings: slot 11
`Use featureCounts = false` so STAR's `ReadsPerGene.out.tab` is produced for
the step-6 strandedness call, and slot 10 `Generate additional QC reports =
true` to validate the novel reference. Slot 4 reference level `water`; slot 7
`stranded - reverse` as a provisional value pending step 6. Slot 1
"Reference genome" passed the inert placeholder `unused-placeholder` per
finding K (Cufflinks disabled, STAR no longer consumes it). Slot 14 omitted
(optional, Cufflinks off). Slot 15 "Genome FASTA" wired to hid 1, slot 2 GTF
to hid 2.

Status tracked in the `loom-invocation` block above; verification of outputs
happens when it reaches a terminal state.

```loom-invocation
invocation_id: 00f8cac7170ede09
galaxy_server_url: https://usegalaxy.org
notebook_anchor: plan-a-step-5
label: "Smoke run: 9-sample cip vs water RNA-seq on custom NC_008463.1"
submitted_at: 2026-09-17T14:23:38.159Z
status: failed
summary: "DESeq2 failed: 3-level Condition needs target_level (finding O). Blocker: GTF lost 5802/6041 genes in STAR (finding P)."
total_steps: 20
completed_steps: 0
total_jobs: 0
completed_jobs: 0
failed_jobs: 3
last_polled_at: 2026-09-17T15:23:19.343Z
```

```loom-session
id: 01a0afab-931c-7a42-94be-788f544efba6
started_at: 2026-09-17T14:00:52.588Z
ended_at: 2026-09-17T15:04:46.050Z
notebook: notebook.md
orphaned_active_steps: 0
```

```loom-session
id: 01a0afe6-2a14-74f5-b8f1-b9e7484cf00c
started_at: 2026-09-17T15:04:52.322Z
ended_at: 2026-09-17T15:09:26.719Z
notebook: notebook.md
orphaned_active_steps: 0
```

## 2026-09-17 — Step 5 smoke run FAILED: diagnosis

Invocation `00f8cac7170ede09` reached terminal state **failed**. Root cause
identified and a second, more consequential defect found along the way.

### Finding O — the fatal error: DESeq2 needs `target_level` for a 3-level factor

The invocation's only errored jobs are the DESeq2 trio (hids 590 result,
591 plots, 592 normalized counts); the other ~40 paused datasets are
cascade-pauses, not independent failures. The Galaxy API's `misc_info` is
truncated at 255 chars and shows only "No size factor was used", which is a
red herring. Full `tool_stdout` (via `/api/jobs/<id>?full=true`) carries the
real message:

```
9 samples with counts over 239 genes
creating plots
Error: Multiple factor levels detected without explicit target_level specification.
Factor 'Condition' has 3 levels: water, cip_0p78uM, cip_1p56uM
Please either:
  1. Specify target_level to indicate which level to compare against the reference, or
  2. Use many_contrasts mode to compare all levels pairwise
```

DESeq2 actually *succeeded* statistically — stderr shows size-factor
estimation, dispersion fitting and model testing all completed. It died at
the reporting stage, purely because a `~ Condition` design with **three**
levels (`water`, `cip_0p78uM`, `cip_1p56uM`) is ambiguous: `reference_level`
= `water` was supplied but `target_level` was not, so the tool cannot tell
which contrast to emit. The step-5 cohort was deliberately designed with two
cip doses plus vehicle, so this was latent in the plan from the start — a
two-level smoke cohort would not have hit it.

Job params confirm `"target_level": null` and `"how": "sample_sheet_contrasts"`.

Fixes, in order of preference:
1. **`many_contrasts` mode** — emits all pairwise contrasts
   (cip_0p78 vs water, cip_1p56 vs water, cip_1p56 vs cip_0p78). Best fit:
   the dose-response comparison is the scientific point of this cohort.
2. Set `target_level` explicitly — gives one contrast per run; would need two
   runs to cover both doses.
3. Drop to a 2-level cohort — abandons the dose-response readout. Not advised.

Note the sample sheet itself is clean: 9 rows, `Condition` balanced 3/3/3,
`Replicate` 1/2/3 within level, tab-separated, no whitespace damage. The
step-4/5 verification work holds up; this is purely a DESeq2 parameterization gap.

### Finding P — BLOCKER: the GTF silently loses 5,802 of 6,041 genes in STAR

Far more serious than the DESeq2 error, and it would have produced a
scientifically worthless result even if DESeq2 had run.

STAR's `ReadsPerGene.out.tab` carries **239 genes**, identical across all
nine samples. PA14 has ~5,900. Quantifying:

| Metric | Value |
| --- | --- |
| Genes in GTF (`gene` features) | 6,041 |
| Genes with ≥1 `exon` feature | 6,041 |
| Genes in STAR output | **239** |
| Genes lost | **5,802 (96.0%)** |
| Uniquely-mapped reads assigned to genes | **20.9%** |
| `N_noFeature` | 2,021,236 reads |

The loss is not random. The 239 surviving genes are *exactly* the set whose
exon lines come from a non-`Protein Homology` source:

| Exon source | In GTF | Counted by STAR |
| --- | --- | --- |
| Protein Homology | 5,802 | **0** |
| GeneMarkS-2+ | 159 | 159 |
| tRNAscan-SE | 63 | 63 |
| cmsearch | 17 | 17 |

Every single `Protein Homology` gene was dropped; every gene from the other
three sources survived. That partition is perfectly clean, which rules out
anything stochastic.

Hypotheses tested and **eliminated**:
- Alignment failure — no: 82.09% uniquely mapped, 0% too-many-mismatches.
- Genome/GTF seqname mismatch — no: all 30,006 GTF rows are `NC_008463.1`,
  matching the single FASTA record.
- Truncated/short GTF — no: 30,006 data lines, 13 MB, all 9 fields, and the
  `gene`/`CDS`/`exon`/`start_codon`/`stop_codon` structure is identical
  between a surviving gene (PA14_RS00130) and a dropped one (PA14_RS00005).
- Missing `exon` features on dropped genes — no: all 5,802 have one.
- Missing/duplicate `transcript_id` — no: 6,041 unique, zero shared across genes.
- Missing `exon_number` — no: present on all 6,046 exon lines.
- Line length / STAR buffer — no: 2,756 dropped genes have exon lines
  shorter than the longest surviving one (451 chars).
- Malformed attributes — no: quotes balanced, no embedded tabs, no non-ASCII,
  `gene_id` always first, every attr field ends `; `.

The one attribute-level difference that tracks the split: 46 `Protein Homology`
exon lines contain a **semicolon inside a quoted value** (in `product`/`note`
free text), and none of those 46 genes are counted. That accounts for 46 of
5,802, so it is a symptom of the same "rich free-text attributes" pattern
rather than the whole cause — the `Protein Homology` records are the ones
carrying `Ontology_term`, `go_function`, `go_process`, `note` and long
`product` strings (mean attr line 500 chars, max 1,233; other sources ~350).

Working conclusion: STAR's GTF parser is choking on the heavy free-text
attribute payload on `Protein Homology` rows, most likely the embedded
semicolons breaking attribute splitting. **Not yet proven** — the decisive
experiment is to re-run STAR against a stripped GTF and see whether gene
count goes 239 → 6,041.

Prepared for that test: `diag_PA14_minimal.gtf` — every exon line reduced to
`gene_id` + `transcript_id` only, coordinates and strand untouched.
6,046 lines, 6,041 unique genes, 728 KB vs the original 13 MB.

### Implication for the plan

Step 5 cannot simply be re-invoked with a DESeq2 flag change. Finding P means
the counts feeding DESeq2 represent 21% of reads over 4% of genes, so any
differential expression from this run is meaningless regardless of contrast
settings. **Both** defects must be fixed before step 5 is re-run; finding P is
the blocker and needs a cheap single-sample STAR test first.

Also worth noting for step 6: the strandedness question is already answered by
this data. Column sums on `ReadsPerGene.out.tab` are firstStrand 6,507 vs
secondStrand 535,218 — an ~82× asymmetry confirming the provisional
`stranded - reverse` setting is correct.

Diagnostic artifacts kept locally: `diag_ReadsPerGene.tabular`, `diag_PA14.gtf`,
`diag_PA14_minimal.gtf`, `diag_samplesheet.tsv`, `diag_star_log.txt`,
`diag_job.json`, `diag_counts/` (9 count tables).

## 2026-09-17 15:26 — Re-run (invocation `ced524078161ba14`): Finding P FIXED, Finding O still open

Polled after the earlier diagnosis. A **second smoke run was launched at 15:26**
against a corrected GTF (`PA14_NC008463_cds2exon_FIXED.gtf`, hid 600). It was not
recorded in the notebook at submit time, so it had no `loom-invocation` block —
noted here retroactively. It reached terminal state **failed** at 15:48.

### Finding P is RESOLVED — the GTF fix worked

The decisive test proposed in the previous entry has effectively been run, and
the hypothesis is **confirmed**. New STAR output (hid 685) vs the original:

| Metric | Run 1 (original GTF) | Run 2 (FIXED GTF) |
| --- | --- | --- |
| Genes in `ReadsPerGene.out.tab` | 239 | **6,041** |
| Reads on annotated genes | 20.9% | **83.4%** |
| `N_noFeature` (reverse strand) | 2,021,236 | 379,596 |
| DESeq2 input matrix | 239 genes | **6,041 genes** |

All 6,041 GTF genes now quantify, and `PA14_RS00005`/`PA14_RS00010` — the
`Protein Homology` genes that were previously dropped to zero — carry real
counts (2,005 and 1,103). The attribute-payload diagnosis was correct.
83.4% on-gene assignment is a healthy figure for bacterial RNA-seq.

### Finding O is UNCHANGED — same DESeq2 error, same cause

The re-run hit the *identical* failure at the same stage (job
`bbd44e69cb8906b5859472f9bffe75ad`, hid 1115–1117):

```
9 samples with counts over 6041 genes     <- note: 6041, the fix is visible here
creating plots
Error: Multiple factor levels detected without explicit target_level specification.
Factor 'Condition' has 3 levels: water, cip_0p78uM, cip_1p56uM
```

Job params confirm `reference_level = "water"` but **`target_level = null`** —
the contrast parameter was not changed between run 1 and run 2. Only the GTF was
fixed. DESeq2 again completed size factors, dispersions and model fitting, then
died at the reporting stage.

So the two defects were independent, exactly as diagnosed, and one of them has
now been addressed.

### Current state of the history

- 877 datasets `ok`, 80 `error`, 67 `paused`.
- Of the 80 errors, the great majority are **not** new problems:
  - 18 × `upload1` on the source FASTQs (hids 3–20) — these are the pre-existing
    upload-record errors; the staged FASTQs themselves were verified byte-exact
    in step 4 and STAR read them fine in both runs.
  - 54 × `wig_to_bigWig` — coverage-track conversion, cosmetic, not on the
    counts→DESeq2 path.
  - 2 × `gtftobed12` (hids 515, 1040) — feeds RSeQC QC only.
  - 6 × `deseq2` — the two failed runs × 3 outputs each. **These are the real ones.**
- The RNA-seq subworkflow itself (`dc545b3fbd4f6409`) reports **completed**.

### What remains

Only Finding O. The counts are now trustworthy, so the next re-run should
produce usable differential expression. Two options, unchanged from the previous
entry:

1. **`many_contrasts` mode** — all three pairwise contrasts
   (cip_0p78 vs water, cip_1p56 vs water, cip_1p56 vs cip_0p78). Preferred:
   matches the dose-response intent of this cohort.
2. Set `target_level` explicitly — one contrast per invocation, so two runs to
   cover both doses against vehicle.

Re-running the whole 20-step workflow to fix one DESeq2 parameter is wasteful;
the counts collection (hid 912) is already `ok`, so the cheaper path is to run
the DESeq2 tool directly on the existing counts + sample sheet (hid 620) rather
than re-invoking the full pipeline. Recommend confirming that approach before
launching.

```loom-session
id: 01a0afea-b136-7441-8634-d5b2016a4dee
started_at: 2026-09-17T15:09:49.070Z
ended_at: 2026-09-17T17:58:23.663Z
notebook: notebook.md
orphaned_active_steps: 0
```
