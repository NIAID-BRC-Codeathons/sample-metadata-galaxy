# Livny / Romano 2024 — Colistin RNA-seq Reanalysis

**Analysis date:** 2026-09-17
**Analyst:** fils (usegalaxy.org)
**Source paper:** Romano et al. 2024, *PNAS* 121:e2409747121 (`pnas.202409747.pdf`)
**Data:** GEO GSE251671 / BioProject PRJNA1055047 / SRA study SRP479194
**Galaxy history:** `LivnyReRun` (`bbd44e69cb8906b5ed1ed8fe3cdf7959`)

## Background

Romano et al. profiled *Pseudomonas aeruginosa* UCBPP-PA14 against a panel of
antimicrobials using RNAtag-seq, and predicted mechanism-of-action by comparing
batch moderated z-score profiles (PerSpecTM) across the compound set.

This reanalysis takes a single arm of that experiment — **colistin 3 µM vs water
vehicle at 90 min in wild-type PA14, n=3** — and asks a narrower question with a
different statistical frame: which genes are differentially expressed by a
per-gene negative-binomial test (DESeq2)?

This is a deliberate methodological deviation. The paper's z-scores are computed
across the whole panel and emphasize perturbation-specific signal against a
background of all compounds; a two-condition DESeq2 contrast does not. The paper
did use DESeq2 as an intermediate step, so the tooling is not foreign to the
original analysis, but the results are not expected to be numerically identical
to anything published.

## Data selection

All 9 runs come from a single batch, **MOC_1430**, avoiding cross-batch
confounding. Sample title schema is
`batch:compound:dose:time:strain:plate:replicate`.

**Water is the control, not DMSO** — colistin is water-dissolved, so water is
the matched vehicle. (The batch also contains DMSO controls, used by the paper
for the DMSO-dissolved compounds.)

| Condition | Replicate | GEO | SRA run(s) |
| --- | --- | --- | --- |
| colistin 3 µM | r1 | GSM7985063 | SRR27299960 |
| colistin 3 µM | r2 | GSM7985064 | SRR27299894 |
| colistin 3 µM | r3 | GSM7985065 | SRR27299892 |
| water (vehicle) | r1 | GSM7985264 | SRR27300164 + SRR27300165 |
| water (vehicle) | r2 | GSM7985265 | SRR27300163 + SRR27300195 |
| water (vehicle) | r3 | GSM7985266 | SRR27300161 + SRR27300162 |

Water GSMs have two sequencing runs each (technical replicates) and are
concatenated per mate before the workflow. Colistin GSMs have one run each.
18 FASTQ files, ~6.4 GB, Illumina NovaSeq 6000, 90 bp paired-end.

ENA URL pattern — **corrected 2026-09-17** (the `<last3>` form below was wrong
and caused the step 4 failure; see "Step 4 failure" in the execution log):
`ftp.sra.ebi.ac.uk/vol1/fastq/<first6>/0<last2>/<RUN>/<RUN>_1.fastq.gz`

For 11-character SRR accessions ENA subdivides by `0` + the **last two** digits,
not the last three, and the top directory is the first six characters of the
accession (so `SRR27300164` sits under `SRR273/064/`, not `SRR272/164/`).
URLs below were read from the ENA filereport API rather than constructed.

| Run | ENA path | R1 bytes | R2 bytes |
| --- | --- | --- | --- |
| SRR27299960 | `SRR272/060/SRR27299960/` | 398,808,026 | 469,731,868 |
| SRR27299894 | `SRR272/094/SRR27299894/` | 264,806,843 | 307,609,646 |
| SRR27299892 | `SRR272/092/SRR27299892/` | 485,971,385 | 572,314,656 |
| SRR27300164 | `SRR273/064/SRR27300164/` | 375,040,018 | 455,277,888 |
| SRR27300165 | `SRR273/065/SRR27300165/` | 275,668,848 | 333,655,626 |
| SRR27300163 | `SRR273/063/SRR27300163/` | 341,818,271 | 407,666,585 |
| SRR27300195 | `SRR273/095/SRR27300195/` | 329,523,908 | 392,902,301 |
| SRR27300161 | `SRR273/061/SRR27300161/` | 232,204,602 | 275,779,635 |
| SRR27300162 | `SRR273/062/SRR27300162/` | 231,365,540 | 275,377,294 |

Total ~6.4 GB, consistent with the estimate above.

## Reference determination

GEO `!Sample_data_processing` states:

```
Assembly: NC_0088463.1 (UCBPP-PA14)
BWA to align reads to reference
```

`NC_0088463.1` has one digit too many and returns no NCBI record. It resolves to
**NC_008463.1** — "Pseudomonas aeruginosa UCBPP-PA14, complete sequence",
6,537,648 bp — i.e. assembly **`GCF_000014625.1_ASM1462v1`**. This is the
paper's reference and the one this reanalysis uses.

Verified via NCBI E-utilities: the 8-digit form returns
`phrasesnotfound: ["NC_0088463.1"]`; the 7-digit form returns the PA14 genome.

## Findings that shaped the plan

Investigated before execution by reading the published workflow's exported JSON,
including both subworkflows.

**1. The paper's reference is not a Galaxy built-in.** The workflow's
"Reference genome" slot is a restricted list of 6,258 built-in indexes; the only
*P. aeruginosa* entries are `GCF_045689255.1` (a newer PA14 assembly) and
`GCF_000006765.1` (PAO1). `GCF_000014625.1` is absent. The STAR tool itself
supports `refGenomeSource: history`, so the restriction is workflow wiring, not
a tool limitation — hence the workflow copy in step 1.

**2. `genomeSAindexNbases` must drop 14 → 10.** STAR's default suits a
mammalian genome. For 6.5 Mb, `log2(6537648)/2 - 1 ≈ 10`. Leaving it at 14 makes
STAR fail or silently build a corrupt index.

**3. The workflow hardcodes `exon` as GTF feature type — this would silently
destroy the analysis.** featureCounts (sub-step 17/21), STAR's
`sjdbGTFfeatureExon` (17/18), and deg_annotate (18/13) all pin `exon`, and none
is exposed as a workflow input. The PA14 RefSeq GTF has only **80 exon records**
(tRNA/rRNA) against 6,041 genes. Counting would return near-zero for every
protein-coding gene and DESeq2 would produce confident-looking garbage from ~1%
of the annotation.

Fix: re-emit each `gene` record as an `exon` record. Standard bacterial-GTF
adaptation; makes the stock workflow usable without touching its tool states.

**4. Gene IDs can be made to match the paper exactly.** The GTF carries
`old_locus_tag` (`PA14_RS00005` → `PA14_00010`), and `PA14_00010` is the ID
style in the paper's own supplementary count matrix
(`GSE251671_moc1430_..._counts_manuscript.csv`). Emitting `gene_id` as the old
tag gives **5,640 / 5,679 = 99.3%** overlap with the published counts, enabling
direct gene-level comparison. RefSeq tag kept as `refseq_locus_tag`, symbols as
`gene_name`.

This makes the paper's reference strictly *better* than the newer built-in,
whose `R0792_*` tags would make that comparison impossible.

**5. Aligner stays STAR, deviating from the paper's BWA.** Matching BWA would
mean rebuilding the read-processing subworkflow rather than rewiring one input.
STAR in end-to-end mode on an unspliced bacterial genome is near-equivalent to
BWA-MEM for counting purposes. Flagged as a deviation; revisit if step 9's
assignment rates look wrong.

## Plan A: Colistin Differential Expression Reanalysis (GSE251671, 90 min) [galaxy]

Based on the published workflow
[End to End Differential Expression RNA-seq](https://usegalaxy.org/workflows/run?id=7f8eb3a584e8080b)
(owner `marius`, v3; 19 steps + 2 subworkflows: `read processing`,
`differential expression`), run as a **modified copy** per finding 1.

### Steps

- [x] 1. **Copy and rewire the workflow** {#plan-a-step-1} — change STAR reference from built-in parameter to history FASTA input; set `genomeSAindexNbases` 14 → 10
  - Routing: galaxy
  - Tool: Galaxy workflow API (copy `7f8eb3a584e8080b`, edit subworkflow STAR step)
  - Verification: copy's input template shows a data slot for reference FASTA and no built-in genome parameter; `genomeSAindexNbases` reads 10 in saved tool state
  - **Done.** Workflow `37014d3793f60e89`, "End to End Differential Expression RNA-seq (history reference) - LivnyReRun", 19 steps. Input template slot 1 is now `label: "Reference genome FASTA", input_type: data, src: hda, accepted_formats: [fasta]` — a data slot, no built-in genome parameter. Downloaded the workflow JSON and inspected STAR sub-step 17/17 directly: `refGenomeSource.geneSource = "history"`, `genomeSAindexNbases = "10"`, `sjdbGTFfeatureExon = "exon"` (the last confirming why the GTF preprocessing in step 3 was required).

- [x] 2. **Upload the paper's reference** {#plan-a-step-2} — `GCF_000014625.1_ASM1462v1_genomic.fna.gz` fetched server-side from NCBI FTP
  - Routing: galaxy
  - Tool: galaxy_upload_file_from_url
  - Verification: dataset `ok`, datatype `fasta`, single sequence `NC_008463.1` of 6,537,648 bp
  - **Done.** hid 2, `PA14_GCF_000014625.1_genomic.fasta` (`f9cad7b01a472135b7becff14f4444f5`), state `ok`, datatype `fasta`, 6,619,435 bytes, `metadata_sequences: 1`, header reads `>NC_008463.1 Pseudomonas aeruginosa UCBPP-PA14, complete sequence`. Note hid 1 is a redundant `fasta.gz` copy of the same fetch; **hid 2 is the one to wire into slot 1**.

- [x] 3. **Upload the adapted GTF** {#plan-a-step-3} — gene-as-exon GTF with paper-style `PA14_*` IDs, derived from `GCF_000014625.1`
  - Routing: galaxy
  - Tool: galaxy_upload_local_file
  - Verification: dataset `ok`, datatype `gtf`, 6,041 lines, all `exon` on `NC_008463.1`; preview shows `gene_id "PA14_00010"` with `gene_name`
  - **Done.** hid 21, `PA14_GCF_000014625.1_gene-as-exon.gtf` (`f9cad7b01a472135726f49c6e7bc8df1`), state `ok`, datatype `gtf`, **6,041 data lines**, 9 columns, 1,106,101 bytes. Galaxy-parsed attribute set is exactly `gene_id, transcript_id, gene_name, gene_biotype, refseq_locus_tag`. First record: `NC_008463.1 RefSeq exon 483 2027 . + . gene_id "PA14_00010"; transcript_id "PA14_00010"; gene_name "dnaA"; gene_biotype "protein_coding"; refseq_locus_tag "PA14_RS00005";` — the paper-style ID and the gene→exon recast both confirmed on-server.

- [!] 4. **Fetch 18 FASTQ from ENA** {#plan-a-step-4} — paired `.fastq.gz` for the 9 runs
  - Routing: galaxy
  - Tool: galaxy_upload_file_from_url
  - Verification: 18 datasets `ok`, datatype `fastqsanger.gz`, sizes match ENA byte counts
  - **Failed — all 18 datasets in `error`** (hids 3–20). Cause: constructed URLs used the wrong ENA directory rule. Galaxy's `misc_info` on hid 3 reads `Unable to fetch https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR272/960/SRR27299960/SRR27299960_1.fastq.gz — HTTP Error 404: Not Found`. Every dataset is 0 bytes with `extension: data` (Galaxy fell back from the requested `fastqsanger.gz` because nothing was downloaded). **Nothing was silently half-fetched** — this is a clean failure, not corrupt data.
  - Correct paths retrieved from the ENA filereport API and recorded in "Data selection" above. Retry tracked as step 4b.

- [x] 4b. **Re-fetch 18 FASTQ with corrected ENA URLs** {#plan-a-step-4b} — replaces the failed step 4
  - Routing: galaxy
  - Tool: galaxy_upload_file_from_url, `file_type=fastqsanger.gz`
  - Verification: 18 datasets `ok`, datatype `fastqsanger.gz`, `file_size` matches the ENA `fastq_bytes` column in the Data-selection table exactly; purge the 18 errored hids 3–20 first so the history has one unambiguous copy of each run
  - **Done.** Pre-flight: all 18 URLs HTTP 200 with `Content-Length` matching the table 18/18. Purge of hids 3–20 confirmed (18 `purged=True`, hids 1/2/21 untouched). Fetches landed as hids 22–39.
  - **Verified 2026-09-17:** all 18 datasets `state=ok`, `extension=fastqsanger.gz`, and `file_size` equals the ENA `fastq_bytes` column **exactly, 18/18** (byte-for-byte, no rounding). History now holds 21 live items: hids 1/2 (reference), 21 (GTF), 22–39 (reads). Peek on hid 39 shows well-formed FASTQ with `/2` mate suffixes and Illumina NovaSeq read headers (`A00761:HJ7YGDMXX190316`), confirming the payload is real sequence rather than an error page.

- [x] 5. **Merge water technical replicates** {#plan-a-step-5} — concatenate 2 runs per water GSM, R1 and R2 separately (6 jobs)
  - Routing: galaxy
  - Tool: tp_cat (`9.5+galaxy3`)
  - Verification: each merged read count equals sum of its two inputs; R1 and R2 match within each sample
  - **Done & verified 2026-09-17.** 6 `tp_cat/9.5+galaxy3` jobs, all `state=ok`, `exit_code=0`, landing as hids 40–45, every one `fastqsanger.gz`. Output size equals the exact arithmetic sum of its two ENA inputs in all 6 cases (see table in the execution log) — gzip member concatenation is byte-additive, so this is a strict check, not an approximation. Peeks confirm the first read of each merged R1 carries a `/1` suffix and each merged R2 the matching `/2`, from the same run and cluster coordinate, so mate order is preserved across the join.

- [x] 6. **Build the sample-sheet collection** {#plan-a-step-6} — `sample_sheet:paired`, 6 pairs, `Condition` + `Replicate` columns
  - Routing: galaxy
  - Tool: POST /api/dataset_collections (`column_definitions` + `rows`; confirmed supported on this 26.1 server)
  - Verification: 6 elements each with forward+reverse; `Condition` reads 3 colistin / 3 water
  - **Done & verified 2026-09-17.** hid 46, `Livny colistin vs water sample sheet` (`ebeeec9b393e08a6`), `collection_type=sample_sheet:paired`, `element_count=6`, `populated_state=ok`. Column definitions copied verbatim from the workflow's own step-0 `tool_state` so they match what the workflow expects: `Condition` (string, required), `Replicate` (int), `Batch 1–3` (optional). Read back per element: 3 × `colistin` and 3 × `water`, replicates 1/2/3 in each arm, each element a `paired` sub-collection whose forward/reverse sizes match the intended hids (colistin from 22–27 directly, water from the merged 40–45).

- [ ] 7. **Invoke the modified workflow** {#plan-a-step-7} — one invocation, all slots filled per parameter table
  - Routing: galaxy
  - Tool: galaxy_invoke_workflow
  - Verification: invocation accepted, recorded via galaxy_invocation_record, polled to terminal state

- [ ] 8. **Verify counting actually worked** {#plan-a-step-8} — guard against findings 2 and 3 failing silently
  - Routing: galaxy
  - Tool: inspect featureCounts summary + MultiQC
  - Verification: STAR uniquely-mapped >70%; featureCounts `Assigned` >50% per sample spread across ~6,000 genes, not ~80. Near-zero ⇒ GTF or index fix failed; stop before interpreting anything

- [ ] 9. **Confirm strandedness** {#plan-a-step-9} — RNAtag-seq direction is asserted, not measured
  - Routing: galaxy
  - Tool: featurecounts on one BAM at `-s 0/1/2`
  - Verification: chosen setting has highest assignment rate; record all three percentages

- [ ] 10. **Cross-check against the paper's published counts** {#plan-a-step-10} — the payoff from finding 4
  - Routing: local
  - Tool: join count matrix to `GSE251671_moc1430_..._counts_manuscript.csv` on gene_id
  - Verification: ≥5,600 genes join; per-sample Spearman vs the paper's counts for the same 6 libraries — expect ρ > 0.95. Divergence means a pipeline problem, not a biological finding

- [ ] 11. **Inspect DE results** {#plan-a-step-11} — annotated table, significant genes, PCA, volcano, heatmaps
  - Routing: galaxy
  - Tool: inspect workflow outputs
  - Verification: ~6,041-row table with baseMean/log2FC/padj; PCA separates colistin from water; count genes at padj<0.05 & |log2FC|>1

- [ ] 12. **Biological sanity check** {#plan-a-step-12} — confirm the known colistin response
  - Routing: galaxy
  - Tool: inspect significant-gene table
  - Verification: LPS-modification / membrane-stress genes (arnBCADTEF, pmrAB, phoPQ, parRS) among induced genes

- [ ] 13. **Write up** {#plan-a-step-13} — results here plus a Galaxy Page bound to LivnyReRun
  - Routing: galaxy
  - Tool: notebook_push_to_galaxy
  - Verification: page readable back from Galaxy with DE summary and embedded plots

### Parameters

Workflow input slots (after the step 1 rewire):

| Slot | Input | Default | Value | Description |
| --- | --- | --- | --- | --- |
| 0 | Sample sheet of sequencing reads | — | 6-pair `sample_sheet:paired` from step 6 | Condition + Replicate |
| 1 | Reference genome **(now a history FASTA)** | — | `GCF_000014625.1_ASM1462v1_genomic.fna` | the paper's NC_008463.1 |
| 2 | GTF File of annotation | — | gene-as-exon PA14 GTF from step 3 | must match slot 1 |
| 3 | DESeq2 Design Formula | — | `~ Condition` | single factor |
| 4 | Reference level | first level | `water` | vehicle is denominator |
| 5 | Forward adapter | (blank) | (blank) | fastp overlap auto-detect |
| 6 | Reverse adapter | (blank) | (blank) | fastp overlap auto-detect |
| 7 | Strandedness | — | `stranded - reverse` | RNAtag-seq; **verified in step 9** |
| 8 | Adjusted p-value threshold | 0.05 | 0.05 | BH-adjusted |
| 9 | log2 fold change threshold | 1.0 | 1.0 | ≥2-fold |
| 10 | Generate additional QC reports | — | `true` | worth it for a reanalysis |
| 11 | Use featureCounts for count tables | — | `true` | over STAR GeneCounts |
| 12 | Compute Cufflinks FPKM | — | `false` | not needed for DE |
| 13 | Compute StringTie FPKM | — | `false` | not needed for DE |
| 14 | GTF to exclude from FPKM norm | — | (omit) | Cufflinks-only |

Changed inside the workflow copy (step 1):

| Sub-step | Tool | Parameter | From | To |
| --- | --- | --- | --- | --- |
| 17/18 | STAR | `refGenomeSource.geneSource` | `indexed` | `history` |
| 17/18 | STAR | `genomeSAindexNbases` | 14 | **10** (6.5 Mb genome) |
| 17 | subworkflow | input 4 "Reference genome" | parameter (text) | data input (FASTA) |

Fixed inside the workflow, not exposed (recorded for completeness):

| Sub-step | Tool | Parameter | Value | Note |
| --- | --- | --- | --- | --- |
| 17/12 | fastp 0.24.0+galaxy3 | qualified_quality_phred | 30 | stricter than fastp default 15 |
| 17/12 | fastp | length_required | 15 | 90 bp reads, fine |
| 17/18 | STAR 2.7.11a | alignEndsType | Local | ENCODE preset |
| 17/18 | STAR | sjdbGTFfeatureExon | exon | **reason for the GTF preprocessing** |
| 17/21 | featureCounts 2.0.8 | gff_feature_type | exon | same |
| 17/21 | featureCounts | gff_feature_attribute | gene_id | now paper-style `PA14_*` |
| 17/21 | featureCounts | paired_end_status | PE_fragments | count fragments |
| 17/21 | featureCounts | mapping_quality | 0 | no MAPQ filter (cannot override) |
| 18/10 | DESeq2 | fit_type / outlier handling | parametric / on | appropriate at n=3 |
| 18/13 | deg_annotate | gff_attributes | gene_biotype, gene_name | why GTF carries both |

## Execution log

### 2026-09-17 — session 2: status audit of `LivnyReRun`

Connected to history `LivnyReRun` (`bbd44e69cb8906b5ed1ed8fe3cdf7959`), 21 items,
history state `error`. Audit result: **steps 1–3 complete and verified, step 4
failed outright, steps 5–13 not started.**

| hids | Contents | State |
| --- | --- | --- |
| 1–2 | PA14 reference FASTA (gz + plain) | `ok` |
| 3–20 | 18 FASTQ fetches | **all `error`, 0 bytes** |
| 21 | gene-as-exon GTF | `ok` |

**Step 4 failure — root cause.** The ENA URL pattern recorded in the original
Data-selection section was wrong. It assumed the run accession's **last three**
digits form the subdirectory; ENA actually uses `0` + the **last two** digits,
and the parent directory is the first six characters of the accession. So the
fetch asked for `…/SRR272/960/SRR27299960/…` when the file lives at
`…/SRR272/060/SRR27299960/…`. All 18 requests 404'd. The nine water/colistin
runs split across two parents (`SRR272/` and `SRR273/`), which the single-pattern
rule could not express either.

This is a benign failure mode — a 404 leaves an empty errored dataset rather
than a truncated FASTQ — but it is worth noting that Galaxy recorded the
datatype as `data`, not `fastqsanger.gz`, so a later step consuming these by
type would have failed loudly rather than counting zero reads.

**Correction applied:** URLs are no longer constructed. They were read from the
ENA filereport API per accession, together with `fastq_bytes`, and both are now
in the Data-selection table so step 4b can verify sizes rather than just states.

No change to the scientific plan — reference, annotation, and workflow rewire
all survived and were re-verified this session against the live server.

### 2026-09-17 — session 3: step 4b submitted

**Pre-flight URL check (local).** Before touching Galaxy, all 18 corrected URLs
were probed with `curl -sI`. Every one returned **HTTP 200**, and every
`Content-Length` matched the `fastq_bytes` value in the Data-selection table
exactly — 18/18. The directory rule is confirmed correct against the live ENA
server, so the step 4 failure mode cannot recur.

**Purge of the failed fetches.** hids 3–20 were deleted with `purge=True` via
`DELETE /api/histories/{id}/contents/{id}`. Verified afterwards by listing
history contents: 21 items, **18 purged** (hids 3–20, all `purged=True`), and
hids 1, 2, 21 untouched at `purged=False, state=ok`. The history now holds one
unambiguous copy of each run. (Note: the purge endpoint returns 204 with an
empty body; a naive JSON parse of the response reports a false failure.)

**Re-fetch submitted.** 18 `galaxy_upload_file_from_url` calls, all accepted,
landing as **hids 22–39** with `file_type=fastqsanger.gz` requested explicitly.
First status poll: 18 new datasets, 14 `queued` / 4 `running`, extension already
reading `fastqsanger.gz`. Running in the background; sizes still need to be
checked against the table before step 4b can be marked verified.

### 2026-09-17 — session 4: steps 4b–7 closed out, workflow invoked

**Step 4b confirmed.** All 18 fetches reached `ok`; `file_size` matches the ENA
`fastq_bytes` column exactly for every one. Step 4b is now marked verified.

**Step 5 — water technical replicates merged.** The six `tp_cat` jobs had already
been submitted in the previous session but were never recorded or verified. All
six are `state=ok` with `exit_code=0` (hids 40–45). Because gzip members
concatenate byte-additively, the output size is an exact arithmetic check on the
inputs rather than an approximation — and all six match to the byte:

| hid | Sample / mate | Inputs (hid) | Expected sum | Actual | ✓ |
| --- | --- | --- | --- | --- | --- |
| 40 | water_r1 R1 | 28 + 30 | 650,708,866 | 650,708,866 | ✓ |
| 41 | water_r1 R2 | 29 + 31 | 788,933,514 | 788,933,514 | ✓ |
| 42 | water_r2 R1 | 32 + 34 | 671,342,179 | 671,342,179 | ✓ |
| 43 | water_r2 R2 | 33 + 35 | 800,568,886 | 800,568,886 | ✓ |
| 44 | water_r3 R1 | 36 + 38 | 463,570,142 | 463,570,142 | ✓ |
| 45 | water_r3 R2 | 37 + 39 | 551,156,929 | 551,156,929 | ✓ |

Mate pairing survived the join: each merged R1 peek starts at
`@SRR27300164.1 …/1` and its R2 partner at the same run/cluster coordinate with
`/2`, so forward and reverse remain in register.

**Step 6 — sample sheet built.** Rather than guessing the schema, the column
definitions were read out of the workflow's own step-0 `tool_state` and copied
verbatim: `Condition` (string, required), `Replicate` (int), `Batch 1–3`
(optional). Two API details worth recording for the next run:

- `rows` must be a **dict keyed by element name**, not a list of lists. Passing a
  list returns `400 — Input should be a valid dictionary in ('body','rows')`.
- On read-back the per-sample values do **not** come back under a top-level
  `rows` key (that reads `null`, which looks alarming); they are attached to each
  element as `columns`. The metadata is present — just serialized elsewhere.

Result: hid 46, `ebeeec9b393e08a6`, `sample_sheet:paired`, 6 elements,
`populated_state=ok`, 3 × colistin and 3 × water with replicates 1/2/3 in each
arm, colistin drawn straight from hids 22–27 and water from the merges 40–45.

**Step 7 — workflow invoked.** Invocation `7b7d74743b94854b` on workflow
`37014d3793f60e89`. Galaxy echoed back the wiring, which confirms on-server what
the plan intended: slot 1 = `f9cad7b01a472135b7becff14f4444f5` (the plain-FASTA
hid 2, not the `.gz` hid 1), slot 2 = the gene-as-exon GTF, design `~ Condition`,
reference level `water`, `stranded - reverse`, padj 0.05, log2FC 1, featureCounts
on, both FPKM paths off. Adapter slots left blank for fastp overlap auto-detect.

The invocation fans out into six subworkflow invocations (read processing,
unstranded coverage, stranded coverage, the two MultiQC arms, differential
expression). `get_invocations` therefore returns **seven** records for this
history — one top-level plus six children — which is expected and not a sign of a
duplicate submission. Only `7b7d74743b94854b` is tracked.

Running in the background. Step 8 is the gate that matters next: STAR
uniquely-mapped rate and featureCounts `Assigned` spread across ~6,000 genes
rather than ~80. If that check fails, the GTF recast or the STAR index parameter
didn't take, and nothing downstream should be interpreted.

```loom-session
id: 01a0b11a-c31f-78e4-8bc8-49d41de0b2bb
started_at: 2026-09-17T20:41:56.587Z
ended_at: 2026-09-17T21:34:55.266Z
notebook: notebook.md
orphaned_active_steps: 0
```

```loom-session
id: 01a0b14b-65f3-747b-b3b3-a5f8c8ca92f6
started_at: 2026-09-17T21:35:04.005Z
ended_at: 2026-09-17T21:43:49.369Z
notebook: notebook.md
orphaned_active_steps: 0
```

```loom-session
id: 01a0b153-79eb-7093-a50d-0a195a8d99ba
started_at: 2026-09-17T21:43:53.404Z
ended_at: 2026-09-17T22:06:20.464Z
notebook: notebook.md
orphaned_active_steps: 0
```

```loom-session
id: 01a0b168-1132-745d-81e0-fbce8e275f93
started_at: 2026-09-17T22:06:22.862Z
ended_at: 2026-09-17T22:11:59.783Z
notebook: notebook.md
orphaned_active_steps: 0
```

```loom-session
id: 01a0b16d-3e1e-7704-ab35-9d712a819a85
started_at: 2026-09-17T22:12:02.039Z
ended_at: 2026-09-17T22:14:30.546Z
notebook: notebook.md
orphaned_active_steps: 0
```

```loom-session
id: 01a0b16f-8d4b-7071-a2fb-637cadc75ca3
started_at: 2026-09-17T22:14:33.366Z
ended_at: 2026-09-17T22:19:11.606Z
notebook: notebook.md
orphaned_active_steps: 0
```

```loom-invocation
invocation_id: 7b7d74743b94854b
galaxy_server_url: https://usegalaxy.org
notebook_anchor: plan-a-step-7
label: Colistin vs water DESeq2 workflow (PA14, n=3)
submitted_at: 2026-09-17T23:06:53.502Z
status: in_progress
summary: 
total_steps: 19
completed_steps: 0
total_jobs: 0
completed_jobs: 0
failed_jobs: 0
last_polled_at: 2026-09-18T10:59:15.549Z
```

```loom-session
id: 01a0b19b-6d95-7108-9099-76d07a26bbca
started_at: 2026-09-17T23:02:28.823Z
ended_at: 2026-09-18T00:40:45.479Z
notebook: notebook.md
orphaned_active_steps: 0
```

```loom-session
id: 01a0b1f5-6f10-74c4-baf7-b5e648b2631f
started_at: 2026-09-18T00:40:47.454Z
ended_at: 2026-09-18T01:26:28.978Z
notebook: notebook.md
orphaned_active_steps: 0
```

```loom-session
id: 01a0b21f-4da2-7363-8448-d746a7f47a52
started_at: 2026-09-18T01:26:31.419Z
ended_at: 2026-09-18T01:28:22.079Z
notebook: notebook.md
orphaned_active_steps: 0
```

```loom-session
id: 01a0b221-60ef-7722-adb8-d1d189e91548
started_at: 2026-09-18T01:28:47.428Z
ended_at: 2026-09-18T10:59:22.467Z
notebook: notebook.md
orphaned_active_steps: 0
```
