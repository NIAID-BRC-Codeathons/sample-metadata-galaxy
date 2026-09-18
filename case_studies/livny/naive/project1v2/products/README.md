# PerSpecTM metadata products

Intake artifacts for reproducing Romano, Bagnall et al., *PNAS* 2024;121(45):e2409747121,
"Perturbation-specific transcriptional mapping for unbiased target elucidation of antibiotics."

Sources: GEO **GSE251671** (SOFT family file, 1,059 GSMs), SRA **PRJNA1055047**
(runinfo, 1,310 runs), and the authors' R project
`broadinstitute/psa_rnaseq_manuscript_rproject`.

## Files

| File | What it is |
| --- | --- |
| `GSE251671_fastq_manifest.csv` | 1,059 rows, one per GEO sample: SRR/SRX/BioSample accessions, run-level stats, full perturbation + batch metadata, joined compound annotation |
| `sample_metadata_TEMPLATE.csv` | Empty-but-for-examples intake sheet, 35 columns in pipeline order, 6 worked rows covering every experimental arm |
| `compound_metadata_TEMPLATE.csv` | Per-`pert_id` annotation sheet (the MOA/target labels the prediction depends on) |
| `validate_metadata.py` | Pre-flight validator; 10 error classes, 4 warning classes |

## Validator

```bash
python3 validate_metadata.py sample_metadata.csv compound_metadata.csv
```

Exit 0 = no errors (warnings permitted). Exit 1 = errors.

Errors E1-E10 block the pipeline. Warnings W1-W4 flag designs that will
run but produce degraded or meaningless z-scores.

## Three findings worth carrying forward

**1. `pert_idose` formatting is load-bearing (E3).**
`condition_id` and `comb_id` are string-pasted from `pert_idose` using
`sprintf("%.5f")`. Writing `4.5uM` instead of `4.50000uM` does not error
anywhere in the R pipeline — it silently splits one 3-replicate condition
into two, and the Spearman-weighted replicate collapse then averages the
wrong things. This is the single most likely way to corrupt a reanalysis.

**2. The `condition_id` block suffix is not derivable (E5).**
Conditions end in `:A` normally, but the published reference set contains
10 vehicle-control conditions ending in `:B` — a second replicate block of
the same vehicle, same plate, same timepoint. Verified: the 8 `MOC_1430`
`:B` blocks appear in the authors' reference-set metadata but have **no
corresponding rows** in either the manuscript metadata table or GEO, and
nothing in the remaining columns distinguishes them. Block must therefore
be recorded explicitly at intake; it is a first-class `block` column here,
not something to infer. Two blocks wrongly sharing a letter collapse into
one condition (caught as W3/W4).

**3. Library layout is mixed, contradicting the paper (E8).**
The paper and GEO both state paired-end. SRA runinfo for PRJNA1055047 is
1,028 PAIRED / 282 SINGLE runs, i.e. 918 PAIRED / 141 SINGLE at the sample
level, with read lengths of 90, 89, 49, 48, and 41 nt. No GSM mixes layouts
internally. Record actual layout per run rather than assuming.

Also note 239 GSMs map to more than one SRR (233 × 2 runs, 6 × 4). Those
must be concatenated per-GSM before alignment — the authors' `raw_file*_combined`
column names reflect this ("combined").

## Design constants

- Strain: *P. aeruginosa* UCBPP-PA14, taxid 208963, assembly NC_008463.1
- Batch (`comb_id`) = 384-well plate × strain × timepoint; z-scores computed within batch
- Condition (`condition_id`) = `project_id:pert_id:pert_idose:strain_id:pert_itime:block`; replicates collapse within condition
- Biological triplicate; vehicle controls (DMSO 0.5%, water 0.5%) on every plate
- Timepoints: 90 min standard for compounds (30/60/120 in the time trial); 360 min for CRISPRi
- Dosing: 2-4× MIC measured at **high inoculum** (1×10⁸ CFU/mL), not standard-inoculum MIC
- Minimum batch composition for valid z-scoring: DNA-synthesis inhibitor +
  protein-synthesis inhibitor + (cell-wall or membrane inhibitor) + negative controls

## Manifest composition

1,059 samples / 352 conditions / 35 batches / 196.6 GB.

| Category | n |
| --- | --- |
| antimicrobial_reference_set | 724 |
| weak_signal_removed_from_antimicrobial_reference_set | 141 |
| CRISPRi_not_in_reference_set | 99 |
| CRISPRi_reference_set | 71 |
| internal_test_compounds | 24 |

Strains: PA14 (736), 7 promoter-replacement hypomorphs (21 each), `oprL`-hypo (6),
20 CRISPRi strains (8-9 each). 210 of 1,059 samples carry `weak_signal=TRUE`.

`pert_mechanism` is empty for 242 samples — arabinose (CRISPRi inducer, not a
drug) and the blinded test compounds pa0918/pa69180/brd5750. That is correct,
not missing data: the test compounds' MOA is the thing being predicted.

## Scope note

These are metadata/intake artifacts, validated against the published record.
No FASTQ has been downloaded and no expression value recomputed. Reproducing
the analysis itself (BWA → counts → VST → z-score → correlation) is separate
work not covered here.
