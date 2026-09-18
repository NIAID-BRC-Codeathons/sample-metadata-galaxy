---
name: composite-sample-ids
description: >
  Handle load-bearing concatenated sample/condition IDs (dose strings,
  sprintf rounding, plate-block suffixes) so replicates do not silently
  split. Use when a pipeline builds sample_id / condition_id / comb_id from
  other columns, when z-score or replicate-collapse keys look like
  pasted fields, or when metadata validation is being written. Triggers:
  pert_idose, condition_id, comb_id, "5 decimals", moderated z-score,
  replicate collapse, CMAP/L1000/PerSpecTM sample sheets, "silent split".
---

# Composite sample IDs are load-bearing

When a pipeline pastes `project_id:pert_id:pert_idose:strain_id:pert_itime:block`
and groups on that string, the string **is** the experimental design. Formatting
drift does not throw; it creates extra conditions with n=1.

## Reconstruct the grammar from code, not from examples

Read the author script that assigns `condition_id` / `sample_id` / `comb_id`.
Typical pieces:

| Token | Source | Trap |
| --- | --- | --- |
| `pert_id` | short key (`ami`, not `Amikacin`) | display name ≠ join key |
| `pert_idose` | `sprintf("%.5f", dose) + unit` | `4.5uM` ≠ `4.50000uM` |
| `pert_itime` | `f"{int(time)}{unit}"` with no space | `90 min` ≠ `90min` |
| `strain_id` | `PA14` vs `bamA-hypo` vs `CRISPRi-gyrB` | aliases (`lptD_kd` vs `PA14_lptD_c165`) |
| `block` | `A` / `B` | looks constant; is not |
| case | `tolower()` before join | `MOC_1430` vs `moc_1430` |

If you cannot find the sprintf, dump unique published IDs and infer. Then
**prove** the inference against the authors' table (exact string match counts).
A 96% match is a bug in the grammar, not rounding noise. The 4% are the lesson.

## Fields you cannot derive later

Anything in the published ID that does not follow from other GEO
characteristics must become an explicit intake column.

Worked example from Romano et al.: vehicle controls on some plates were run
as two replicate blocks. Conditions ended in `:A` or `:B`. GEO, the manuscript
sample table, and every other column were identical across those blocks. The
`:B` rows existed only in the authors' reference-set metadata. Inferring
`block="A"` always was wrong, and merging blocks would average six biological
samples as if they were three.

If you catch yourself writing "suffix is always `A`", stop and grep the
published IDs for other suffixes.

## Validator rules that catch silent splits

Errors (fail the sheet):

- **E-dose-format** — `pert_idose` is not the canonical `%.5f` + unit form of
  `pert_dose` + `pert_dose_unit`. Message must say this will split replicates.
- **E-constructed-id** — `sample_id` / `condition_id` / `comb_id` ≠ formula
  applied to the row, using the explicit `block`.
- **E-duplicate-sample-id**
- **E-pert-type** — controlled vocabulary (`negcon`/`poscon`/`test`), not
  synonyms like `control`.
- **E-layout-files** — PAIRED requires R1 and R2; a FASTQ path used twice.
- **E-block** — single uppercase letter, required, not inferred.

Warnings (schema-ok, analysis-empty):

- Batch missing negcons.
- Batch missing required MOA diversity — **but only for arms that z-score
  across compounds**. Genetic-depletion / CRISPRi batches that normalize
  across strains will false-positive this rule. Gate warnings on `category`
  / arm, or the validator trains people to ignore it.
- Replicate count ≠ 3 (or whatever the design says). A count of 6 is often
  two unlabeled blocks, not extra replicates.

## Do not circularly test the formula

Generating `condition_id` with your formula and then asserting the formula
holds is tautological. Required tests, in order:

1. **Author table** — formula vs published `condition_id`. Report exact-match
   fraction and print the misses. The misses rewrite the formula.
2. **Fault injection** — copy the template, mutate one field per class
   (dose `4.5uM`, duplicate id, `pert_type=control`, missing R2, reused
   FASTQ, `block=b`), assert each class fires and exit is non-zero.
3. **Illustrative template** — a 6-row sheet covering every arm will trip
   batch-composition warnings. That is expected; do not "fix" W2 by
   weakening it until the toy sheet is silent. Either mark those warnings
   as design-incomplete, or keep a separate full-batch fixture.

## Intake practice

- Store `pert_dose` as a number and `pert_idose` as the canonical string;
  never re-derive the string ad hoc in a second script.
- Store `block` even when every current row is `A`.
- Keep `vehicle` (`dmso`/`water`) — it is not recoverable from `pert_id`
  for mixed-vehicle plates.
- Query compounds with unknown MOA should be allowed to lack
  `pert_mechanism`; reference compounds must not.
- Lowercase `sample_id` / `project_id` at the boundary the author code does,
  and keep a `original_cid` copy of the count-matrix column names so a
  mismatch is printable.

Related: [reproduce-published-omics](../reproduce-published-omics/SKILL.md)
for the surrounding reproduction workflow.
