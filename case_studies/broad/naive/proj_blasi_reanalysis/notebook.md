# Bläsi lab reanalysis — *P. aeruginosa* PA14 colistin response

Project started 2026-09-17.

## Source publication

Cianciulli Sesso A, Lilić B, Amman F, Wolfinger MT, Sonnleitner E, Bläsi U (2021).
**Gene Expression Profiling of *Pseudomonas aeruginosa* Upon Exposure to Colistin and
Tobramycin.** *Front. Microbiol.* 12:626715. doi:10.3389/fmicb.2021.626715

Local copy: `fmicb-12-626715.pdf`; extracted text: `paper.txt`

### Experimental design (as published)

- Strain: clinical isolate **PA14**, grown aerobically in synthetic cystic fibrosis
  sputum medium (SCFM) at 37 °C.
- At OD600 = 1.7, cultures treated with **colistin 8 µg/ml**, **tobramycin 64 µg/ml**,
  or water (control). Harvested ~2 h later at OD600 ≈ 2.
- Two biological replicates per condition.
- RNA-seq: Trizol extraction, DNase I, Ribo-Zero rRNA depletion, **NEBNext Ultra
  Directional RNA Library Prep** (→ reverse-stranded), 100 bp **single-end**,
  Illumina HiSeq 2000.
- Ribo-seq performed in parallel on the same cultures (separate accession).

### Published analysis pipeline

| Step | Published tool | Notes |
| --- | --- | --- |
| QC | FastQC | "obviated further pre-processing" |
| Adapter removal | cutadapt | |
| Alignment | **Segemehl**, default params | vs PA14 genome NC_008463.1 |
| rRNA/tRNA | reads discarded | excluded from all follow-up |
| Counting | BEDTools | against RefSeq annotation of **NC_002516.2 (PAO1)** — note the genome/annotation mismatch as written |
| DE testing | **DESeq** (v1, Anders & Huber 2010) | |
| Significance | \|FC\| > 2 **and** adjusted p < 0.05 | plus ≥100 RNA-seq reads min expression |

### Published headline results (colistin, RNA-seq)

- **2056 genes** differentially abundant in RNA-seq after colistin exposure
  (1124 in Ribo-seq).
- 1546 genes de-regulated by colistin **only** at the transcriptional level;
  614 only at the translational level; 173 with opposite direction between layers.
- Biology: *arn* operon activation, anti-oxidative stress response, de-regulation of
  the **MexT** and **AlgU** regulons; induction of *mexCD-oprJ* and *mexJK*.
- Spearman ρ (RNA-seq vs Ribo-seq BaseMean) = 0.81 for colistin.

## Data availability (verified 2026-09-17)

RNA-seq raw reads: **ENA PRJEB41029** (study ERP124752) — public, 6 runs, single-end.
Ribo-seq raw reads: ENA PRJEB41027 (not used in this reanalysis).

| Run | Sample | Condition | Reads | Bases | FASTQ size |
| --- | --- | --- | --- | --- | --- |
| ERR4777164 | SAMEA7501830 | colistin R1 | 69,967,314 | 7.00 Gb | 2.76 GB |
| ERR4777165 | SAMEA7501831 | colistin R2 | 68,314,750 | 6.83 Gb | 3.01 GB |
| ERR4777166 | SAMEA7501832 | tobramycin R1 | 67,013,799 | 6.70 Gb | 3.38 GB |
| ERR4777167 | SAMEA7501833 | tobramycin R2 | 69,978,622 | 7.00 Gb | 3.47 GB |
| ERR4777168 | SAMEA7501834 | WT control R1 | 56,739,213 | 5.67 Gb | 4.11 GB |
| ERR4777169 | SAMEA7501835 | WT control R2 | 54,750,350 | 5.48 Gb | 4.01 GB |

FASTQ URLs follow the pattern
`ftp.sra.ebi.ac.uk/vol1/fastq/ERR477/00N/ERR47771NN/ERR47771NN.fastq.gz`.

## Reference genome

Paper mapped to PA14 **NC_008463.1** = assembly **GCF_000014625.1** (ASM1462v1,
*P. aeruginosa* UCBPP-PA14, 6.54 Mb, single chromosome). Both FASTA and GTF verified
reachable at NCBI (HTTP 200, 2026-09-17):

- Genome: `https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/014/625/GCF_000014625.1_ASM1462v1/GCF_000014625.1_ASM1462v1_genomic.fna.gz`
- Annotation: `https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/014/625/GCF_000014625.1_ASM1462v1/GCF_000014625.1_ASM1462v1_genomic.gtf.gz`

We use the PA14 annotation rather than the paper's PAO1 (NC_002516.2) annotation,
since PA14 gene coordinates are what the reads actually map to.

## Galaxy environment

Connected to <https://usegalaxy.org> as `fils` (quota 268.4 GB, 4.3 GB used).
Tool availability confirmed 2026-09-17: Bowtie2, featureCounts, DESeq2, deg_annotate,
volcanoplot, MultiQC all present.

## Planned deviations from the published methods

| Aspect | Paper | This reanalysis | Rationale |
| --- | --- | --- | --- |
| Aligner | Segemehl | **Bowtie2** (`--very-sensitive`, end-to-end) | Segemehl is not in the Galaxy tool panel. Bowtie2 is an unspliced aligner, appropriate for bacteria; STAR-based IWC RNA-seq workflows are designed for eukaryotic splicing and are the wrong fit here. |
| Trimming | cutadapt | **fastp** | Modern equivalent; also produces the QC report, replacing the separate FastQC step. |
| Counting | BEDTools + PAO1 annotation | **featureCounts** + PA14 annotation | featureCounts is the standard, strand-aware counter; PA14 annotation matches the mapping reference. |
| DE testing | DESeq (v1) | **DESeq2** | DESeq v1 is deprecated/unavailable. DESeq2 shrinkage changes LFC estimates, so gene counts will not match the paper exactly. |
| Scope | colistin + tobramycin | **colistin vs control only** | Per user request. Tobramycin runs remain available if scope expands. |

```loom-session
id: 01a0afc3-adcd-7357-9747-d59679b56fdd
started_at: 2026-09-17T14:27:12.306Z
ended_at: 2026-09-17T15:05:27.044Z
notebook: notebook.md
orphaned_active_steps: 0
```

## Failure diagnosis — PerSpecTM pilot run (2026-09-17)

**Scope note:** the failed run is in history `PerSpecTM GSE251671 — Plan A pilot
(NC_008463.1)` (id `bbd44e69cb8906b590d78771d1442073`). This is a *different*
dataset from the Bläsi reanalysis scoped above — GEO GSE251671, 9 paired-end
samples (ciprofloxacin 0.78 µM / 1.56 µM / water, 3 replicates each), not ENA
PRJEB41029. It shares the PA14 NC_008463.1 reference and the same GTF file.

### Symptom

Two workflow invocations reported `failed`:

| Invocation | Workflow | Reported failure |
| --- | --- | --- |
| `00f8cac7170ede09` | RNA-seq PE (outer) | `dataset_failed` at step 19 |
| `77b6457ef84607c7` | DESeq2 (inner) | `dataset_failed` at step 20 |

History dataset states: 494 ok, **31 error**, 32 paused, 4 running, 2 new.
The paused datasets are not independent failures — they are downstream jobs
blocked on the errored ones.

### Root cause — spaces in the GTF source column break STAR's exon parser

The reported DESeq2 error is a **symptom, not the cause**. DESeq2 actually ran
to completion (`R 4.3.3, DESeq2 1.40.2`) and emitted a normalized-counts table —
but with only **240 rows**. PA14 has **6,041 genes**. The counts going into
DESeq2 were almost entirely missing.

Tracing upstream to STAR (`rna_star/2.7.11a+galaxy1`, `--quantMode GeneCounts`,
`--sjdbGTFfeatureExon exon`), the `ReadsPerGene.out.tab` for every sample
contains only 239 genes. Alignment itself was **fine** — 82.09% uniquely mapped,
0 splices (correct for bacteria). The loss is entirely at the counting stage.

The GTF `PA14_NC008463_cds2exon.gtf` (hid 2) is structurally valid: 30,012
lines, all 9 tab-separated fields, 6,046 `exon` lines covering 6,041 distinct
`gene_id`s. But column 2 (source) contains **`Protein Homology` — with a space**:

```
NC_008463.1	Protein Homology	exon	483	2024	.	+	0	gene_id "PA14_RS00005"; ...
```

STAR's GTF reader tokenizes on **whitespace**, not tabs. The embedded space
shifts every field right by one, so STAR reads field 3 as `exon` only on lines
whose source has no space. Confirmed by simulating the tokenizer:

| Source value (col 2) | exon lines | Visible to STAR? |
| --- | --- | --- |
| `Protein Homology` | 5,807 | **no** (space) |
| `GeneMarkS-2+` | 159 | yes |
| `tRNAscan-SE` | 63 | yes |
| `cmsearch` | 17 | yes |

159 + 63 + 17 = **239** — exactly the gene count STAR produced. The 5,807
Protein-Homology genes (96% of the genome, essentially all well-characterised
protein-coding genes including *dnaA*) were silently invisible.

### Consequence — the surviving counts are biological noise

Read fate for sample `GSM7985294_cip_0p78uM_r1` (reverse-stranded column):

| Category | Reads |
| --- | --- |
| Unmapped | 472,313 |
| Multimapping | 88,007 |
| **N_noFeature** | **2,021,236** |
| Ambiguous | 12,506 |
| Assigned to genes | 535,218 |

Of the 535,218 assigned reads, the biotype breakdown is:

| Biotype | Reads | Share |
| --- | --- | --- |
| RNase_P_RNA | 209,997 | 39.2% |
| tmRNA | 199,688 | 37.3% |
| protein_coding | 51,994 | **9.7%** |
| tRNA | 51,167 | 9.6% |
| ncRNA | 18,059 | 3.4% |
| rRNA | 2,356 | 0.4% |
| SRP_RNA | 1,957 | 0.4% |

Only ~10% of counted reads are protein-coding; the table is dominated by two
structural RNAs. **Any DE result from this run is meaningless** and must be
discarded, not filtered or patched.

### Verified fix

Rewrite column 2 only, replacing spaces with underscores, leaving tabs and the
attribute column untouched:

```bash
awk -F'\t' 'BEGIN{OFS="\t"} /^#/{print; next} {gsub(/ /,"_",$2); print}' \
  PA14_NC008463_cds2exon.gtf > PA14_NC008463_cds2exon_fixed.gtf
```

Verified locally (`diag/PA14_NC008463_cds2exon_fixed.gtf`):

| Check | Before | After |
| --- | --- | --- |
| exon lines visible to a whitespace tokenizer | 239 | **6,046** |
| distinct `gene_id` on those lines | 239 | **6,041** |
| total lines | 30,012 | 30,012 (unchanged) |
| tab-fields per record | 9 | 9 (unchanged) |

`Protein Homology` → `Protein_Homology`. The source column is descriptive
provenance metadata only; renaming it has no effect on counting.

### Secondary errors (independent of the GTF bug)

1. **bigWig conversion — 27 datasets** (`Both Strands Coverage` ×9,
   `uniquely mapped stranded coverage` ×18).
   Error: `Parameter 'input1': Unspecified genome build, click the pencil icon
   in the history item to set the genome build`. The reference FASTA (hid 1)
   and all derived datasets have `dbkey = "?"`. Cosmetic/visualisation only —
   does not affect counts or DE. Fix by setting a custom build for
   NC_008463.1, or by dropping the coverage-track branch.

2. **Convert GTF to BED12 (hid 515)** — `no exons defined for group , feature
   gene (perhaps try -ignoreGroupsWithoutExons)`. Same whitespace bug seen
   through a different parser; resolved by the same GTF fix. This blocked the
   RSeQC branch (Read Distribution ×9, Gene Body Coverage ×18 → paused).

### Not the cause (ruled out)

- **Alignment** — 82.09% unique, 2.81% multi, 0 splices. Healthy.
- **fastp trimming** — all 9 samples `ok`.
- **Sample sheet** — 9 rows, correct `Condition` / `Replicate`, `water`
  reference level resolves correctly.
- **DESeq2 parameters** — design `~ Condition`, ref `water`. Correct; it was
  simply handed a 240-gene table.
- **The GTF's cds2exon derivation** — arithmetic is right (24,040 stock NCBI
  lines + 5,966 synthesised exon lines = 30,006). The exon lines were added
  correctly; they inherited the spaced source value from their parent CDS lines.

## Fix applied and re-run submitted (2026-09-17)

### GTF repair

Applied the column-2 whitespace fix to `PA14_NC008463_cds2exon.gtf` and uploaded
the result as **hid 600 `PA14_NC008463_cds2exon_FIXED.gtf`** (state `ok`,
SHA-256 `7ff7ec99b7e8400c3a3af9a5c2aba02dd5bd98aac8a20aaa3f118e6df9bfc226`).

Before accepting the fix I checked **all eight** whitespace-parsed columns, not
just the one known to be broken — column 2 was the sole offender (23,169 lines);
columns 1 and 3–8 were already space-free, so no other field could shift.

Verification of the repaired file:

| Check | Result |
| --- | --- |
| Columns 1,3,4,5,6,7,8,9 byte-identical to original | yes (md5 `b706526d2702e464e98aca46ce21d4b8` both) |
| Only col-2 value changed | `Protein Homology` → `Protein_Homology`; `RefSeq`, `GeneMarkS-2+`, `tRNAscan-SE`, `cmsearch` untouched |
| exon lines visible to a whitespace tokenizer | 239 → **6,046** |
| distinct `gene_id` on those lines | 239 → **6,041** |
| CDS genes lacking an exon | **0** (5,961 / 5,961 covered) |
| exon lines with empty `transcript_id` | 0 |
| Line count / tab-fields / CRLF | 30,012 / 9 / none — unchanged |
| Galaxy-side parse (hid 600) | 30,006 data lines, 9 columns, 6 comments; peek shows `Protein_Homology` |

*dnaA* (`PA14_RS00005`), invisible before, now parses correctly.

### Re-run

Re-invoked `End to End DE RNA-seq — custom NC_008463.1 (PerSpecTM)`
(`a83a2219c9c795ca`) into the same history. Parameters were recovered verbatim
from the failed invocation `00f8cac7170ede09` so that **the GTF is the only
variable changed**:

| Input | Value |
| --- | --- |
| Sample sheet (hdca) | `952b57960c160968` — unchanged |
| **GTF File of annotation** | **hid 600 (FIXED)** — was hid 2 |
| Genome FASTA | hid 1 — unchanged |
| DESeq2 design formula | `~ Condition` |
| Reference level | `water` |
| Strandedness | `stranded - reverse` |
| Adjusted p-value threshold | 0.05 |
| log2 FC threshold | 1 |
| Additional QC reports | true |
| featureCounts / Cufflinks / StringTie FPKM | false / false / false |

Note: the pipeline uses STAR `--quantMode GeneCounts` for counting
(featureCounts disabled), which is exactly the path the GTF bug corrupted.

**Acceptance criteria for the re-run** — the fix is confirmed only if:

1. STAR `ReadsPerGene.out.tab` has **~6,041 gene rows**, not 240.
2. `N_noFeature` drops far below the previous 2,021,236 (~78% of reads).
3. protein_coding share of assigned reads rises from 9.7% to the ~85–95%
   expected for rRNA-depleted bacterial RNA-seq, and RNase_P_RNA + tmRNA
   fall well below their previous combined 76.5%.
4. DESeq2 normalized-counts table has ~6,041 rows, not 240.

The bigWig `dbkey = "?"` errors (27 datasets) are expected to recur — they are
cosmetic, affect only coverage tracks, and were deliberately left unaddressed.

## Re-run outcome — GTF fix CONFIRMED, second unrelated bug found (2026-09-17)

Invocation `ced524078161ba14` reached state `failed`, but this is **not a repeat
of the first failure**. The GTF fix worked completely; a separate, independent
bug in the DESeq2 step is what stopped the run.

### Acceptance criteria — all four met

Measured on `GSM7985294_cip_0p78uM_r1` (STAR `ReadsPerGene`, hid 685) and the
DESeq2 normalized-counts output (hid 1117):

| # | Criterion | Before | After | Verdict |
| --- | --- | --- | --- | --- |
| 1 | STAR gene rows | 240 | **6,041** | pass |
| 2 | `N_noFeature` (reverse-strand col) | 2,021,236 | **379,596** | pass (−81%) |
| 3 | protein_coding share of assigned reads | 9.7% | **~97%** | pass |
| 4 | DESeq2 normalized-counts rows | 240 | **6,041** | pass |

Read fate now (reverse-stranded column, same sample):

| Category | Before | After |
| --- | --- | --- |
| N_unmapped | 472,313 | 472,313 (unchanged — alignment was never the problem) |
| N_multimapping | 88,007 | 88,007 (unchanged) |
| N_noFeature | 2,021,236 | **379,596** |
| N_ambiguous | 12,506 | 275,739 (rose as expected — overlapping genes are now visible) |
| Assigned to genes | 535,218 | **~1,918,000** |

*dnaA* (`PA14_RS00005`), previously absent, now carries 1,848 reads and is the
first row of the counts table. Counts file size 3,896 → 98,008 bytes.

**The GTF whitespace diagnosis is confirmed correct and the fix is effective.**

### Remaining failure — DESeq2 `target_level` is null with 3 condition levels

This is a **different bug**, present in the first run too but masked by the GTF
problem. It is a *workflow configuration* issue, not a data issue.

Evidence that DESeq2 substantively succeeded before failing:

| Output | hid | State | Actual content |
| --- | --- | --- | --- |
| Normalized counts | 1117 | error | **957,942 bytes, 6,042 lines × 10 cols — valid and complete** |
| Plots PDF | 1116 | error | **1,027,201 bytes, valid PDF 1.4, 3 pages** |
| Results table | 1115 | error | **0 bytes — empty** |

Exit code 1, but `DESeq2 version 1.40.2` ran, applied the reference level
correctly (water columns sorted first in the normalized output), and wrote two
of three outputs. Only the contrast/results table is missing.

Root cause is in the job's `select_data` parameters:

```
"design_formula_mode": {
  "mode": "custom",
  "design_formula": "~ Condition",
  "reference_level": "water",
  "target_level": null        <-- not set
}
```

The `Condition` factor has **three** levels — `water`, `cip_0p78uM`,
`cip_1p56uM` (3 samples each). With a reference level but no target level,
DESeq2 has no defined pairwise contrast to extract, so the results table comes
out empty and the tool exits non-zero. The workflow exposes `Reference level`
as an input but has **no `Target level` input**, so this cannot be fixed by
changing invocation parameters alone.

This is also why the original single-dose Bläsi design (2 levels — treated vs
control) would not have hit it: with exactly two levels the contrast is
unambiguous.

**Options to resolve (needs a decision):**

1. Run DESeq2 standalone, twice, on the existing good counts collection
   (hid 912) — `cip_0p78uM vs water` and `cip_1p56uM vs water`. Fastest; reuses
   all completed upstream work; gives both dose contrasts.
2. Add a `Target level` input to the workflow and re-invoke. Cleaner for reuse,
   but re-runs ~40 min of alignment that already succeeded.
3. Subset to two conditions and re-invoke. Discards one dose arm; not advised.

Option 1 is recommended — the counts are verified good, so there is no reason to
repeat alignment.

### RESOLVED — Option 1 executed, both contrasts succeeded (2026-09-17)

Ran the DESeq2 tool directly (`deseq2/2.11.40.8+galaxy2`) against the verified
counts collection (hid 912, 9/9 elements `ok`, 96–99 KB each) and sample sheet
hid 620, with `target_level` **explicitly set** — the parameter the workflow
never wired up. Everything else matched the workflow invocation: custom design
`~ Condition`, reference `water`, header off, count data, alpha_ma 0.05.

| Contrast | Job | Result table | Norm. counts | State |
| --- | --- | --- | --- | --- |
| `cip_0p78uM` vs `water` | `bbd44e69cb8906b524f29cd573a9116b` | hid **1124** (708,875 B, 6,041 × 7) | hid 1126 | `ok` |
| `cip_1p56uM` vs `water` | `bbd44e69cb8906b577517279d2b87171` | hid **1127** (708,754 B, 6,041 × 7) | hid 1129 | `ok` |

Results tables went from **0 bytes → 6,041 data rows × 7 columns**. Confirms the
`target_level`-null diagnosis: the tool exposes the parameter, only the workflow
omitted it.

Local copies: `diag/deseq2_cip0p78_vs_water.tab`,
`diag/deseq2_cip1p56_vs_water.tab`.

#### DE summary

4,836 of 6,041 genes retained a non-NA adjusted p-value (the rest dropped by
independent filtering, as expected).

| Contrast | padj<0.05 | padj<0.05 & \|log2FC\|>1 | up | down |
| --- | --- | --- | --- | --- |
| cip 0.78 µM vs water | 1,054 | **409** | 266 | 143 |
| cip 1.56 µM vs water | 1,308 | **546** | 297 | 249 |

(Using the Bläsi paper's own significance rule — \|FC\|>2 and adjusted p<0.05.)

#### Biological validation — SOS regulon (positive control)

Ciprofloxacin inhibits DNA gyrase and **must** induce the SOS response. It does,
coherently and with a dose-response:

| Gene | locus_tag | cip 0.78 µM | cip 1.56 µM |
| --- | --- | --- | --- |
| recA | PA14_RS07040 | +3.46 (p=8.9e-126) | +4.02 (p=1.7e-174) |
| lexA | PA14_RS10205 | +4.20 (p=4.2e-153) | +4.56 (p=2.9e-186) |
| sulA | PA14_RS10200 | +4.30 (p=1.5e-141) | +4.60 (p=1.6e-146) |
| recN | PA14_RS25755 | +4.18 (p=7.3e-138) | +4.29 (p=2.4e-140) |
| recX | PA14_RS07045 | +3.54 (p=1.4e-85) | +3.61 (p=4.0e-82) |
| imuA | PA14_RS22665 | +4.83 (p=4.6e-28) | +5.03 (p=8.2e-29) |
| dinB | PA14_RS21300 | +1.05 (p=7.5e-07) | +1.45 (p=1.9e-10) |

All 7 up, all significant, **every one larger at the higher dose**. Independent
support: Pearson r = **0.980** between the two contrasts' log2FC (on genes
significant at 0.78 µM), and mean \|log2FC\| rises 1.936 → 2.032. Strong prophage
induction is also present (top hits are phage tail proteins in the RS03190–RS03330
cluster, log2FC +5 to +7), which is the textbook downstream consequence of SOS
activation in *P. aeruginosa*.

This is a coherent, canonical ciprofloxacin response — further confirmation that
the fixed GTF produced biologically sound counts.

**Caution on locus tags:** the fixed GTF's `gene` attribute holds the *old*
`PA14_xxxxx` tags while the counts are keyed on the new `PA14_RSxxxxx` tags. My
first symbol lookup returned the wrong loci (e.g. `PA14_RS30935` is *tnpA*, not
*recA*). Always resolve symbols via the CDS record's `locus_tag` attribute, as
done above.

#### Still outstanding

- `Convert GTF to BED12` (hid 1040) and its dependents (Gene Body Coverage ×10,
  MultiQC hid 1111–1112) remain paused/failed. QC-only; DE results unaffected.
- The 27 bigWig `dbkey="?"` errors remain. Cosmetic.
- **Scope question still unanswered** — this is GSE251671 (ciprofloxacin), not
  Bläsi PRJEB41029 (colistin/tobramycin). The DE results above are sound *as
  ciprofloxacin data*; they do not address the Bläsi reanalysis this notebook
  was opened for.

### Also still failing (unchanged, previously documented as expected)

- **bigWig `dbkey = "?"` — 27 datasets.** Recurred exactly as predicted.
  Cosmetic; coverage tracks only.
- **Convert GTF to BED12 (hid 1040)** — still `no exons defined for group ,
  feature gene`. **This did NOT resolve with the GTF fix**, contrary to the
  earlier prediction in the diagnosis section. The tool groups by `gene` and
  wants transcript-level grouping; it is a distinct parser expectation, not the
  whitespace bug. Blocks the RSeQC branch (Gene Body Coverage ×10 → paused) and
  MultiQC (hid 1111 → paused). Non-blocking for DE results.

```loom-invocation
invocation_id: ced524078161ba14
galaxy_server_url: https://usegalaxy.org
notebook_anchor: gtf-whitespace-fix-rerun
label: PerSpecTM RNA-seq DE re-run with whitespace-fixed PA14 GTF (hid 600)
submitted_at: 2026-09-17T15:26:06.764Z
status: in_progress
summary: 
total_steps: 20
completed_steps: 0
total_jobs: 0
completed_jobs: 0
failed_jobs: 0
last_polled_at: 2026-09-17T17:59:05.829Z
```

```loom-session
id: 01a0afe6-c04a-776c-9af2-b8192336c135
started_at: 2026-09-17T15:05:30.782Z
ended_at: 2026-09-17T17:59:10.466Z
notebook: notebook.md
orphaned_active_steps: 0
```
