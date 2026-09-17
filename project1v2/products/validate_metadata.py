#!/usr/bin/env python3
"""Validate a PerSpecTM sample-metadata sheet before running the pipeline.

Reproduces the intake contract of Romano/Bagnall et al. PNAS 2024 (GSE251671)
and the R project broadinstitute/psa_rnaseq_manuscript_rproject.

Usage:
    python3 validate_metadata.py sample_metadata.csv [compound_metadata.csv]

Exit code 0 = clean (warnings allowed), 1 = errors found.

Checks, in order of how badly they break the pipeline:
  E1  required columns present
  E2  sample_id unique and non-empty
  E3  pert_idose matches sprintf("%.5f", pert_dose) + pert_dose_unit
      -> this is the silent replicate-splitter
  E4  pert_itime matches pert_time + pert_time_unit
  E5  condition_id matches
      project_id:pert_id:pert_idose:strain_id:pert_itime:<BLOCK>
      where <BLOCK> is a single uppercase letter. Block is normally 'A';
      the authors use 'B' for a second vehicle-control block run on the
      same plate at the same timepoint (10 such conditions in the
      published reference set, all negcon). Two blocks of the same
      vehicle must NOT collapse into one condition.
  E6  comb_id matches project_plate_id_384well:strain_id:pert_itime
  E7  pert_type in {poscon, negcon, test}
  E8  paired-end rows have both R1 and R2; single-end have only R1
  E9  R1/R2 never equal; no FASTQ path reused across samples
  E10 every pert_id resolves in the compound annotation (if supplied)
  W1  batch (comb_id) lacks negative controls
  W2  batch lacks the minimum MOA diversity z-scoring needs
      (DNA synthesis + Protein synthesis + [Cell wall | Membrane Integrity]).
      Skipped for CRISPRi batches, which normalize across strains/doses
      rather than across mechanisms.
  W3  condition has replicate count != 3
  W4  replicate_id duplicated within a condition -- usually means two
      replicate blocks were given the same block letter and will be
      wrongly collapsed; give the second block 'B'
"""

import csv
import re
import sys
import collections

REQUIRED = [
    "sample_id", "raw_file1_combined", "single_or_paired_end",
    "organism", "strain_id",
    "pert_id", "pert_dose", "pert_dose_unit", "pert_idose",
    "pert_time", "pert_time_unit", "pert_itime", "pert_type",
    "category", "project_id", "project_plate_id_384well", "replicate_id",
    "block", "comb_id", "condition_id",
]

VALID_PERT_TYPE = {"poscon", "negcon", "test"}

# The three mechanism buckets a batch needs for z-scores to mean anything.
NEED_MECH = ["DNA synthesis", "Protein synthesis"]
NEED_EITHER = ["Cell wall synthesis", "Membrane Integrity"]

errors = []
warnings = []


def err(code, row, msg):
    errors.append(f"[{code}] row {row}: {msg}")


def warn(code, ctx, msg):
    warnings.append(f"[{code}] {ctx}: {msg}")


def fmt_dose(dose, unit):
    try:
        return f"{float(dose):.5f}{unit}"
    except (TypeError, ValueError):
        return None


def main(path, comp_path=None):
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        print("FATAL: no data rows")
        return 1

    cols = set(rows[0].keys())
    for c in REQUIRED:
        if c not in cols:
            errors.append(f"[E1] missing required column: {c}")
    if errors:
        report()
        return 1

    compounds = {}
    if comp_path:
        with open(comp_path, newline="") as fh:
            compounds = {r["pert_id"]: r for r in csv.DictReader(fh)}

    seen_ids = set()
    seen_fastq = {}

    for i, r in enumerate(rows, start=2):
        sid = (r["sample_id"] or "").strip()

        if not sid:
            err("E2", i, "empty sample_id")
        elif sid in seen_ids:
            err("E2", i, f"duplicate sample_id: {sid}")
        seen_ids.add(sid)

        # E3 -- the load-bearing one
        want = fmt_dose(r["pert_dose"], r["pert_dose_unit"])
        if want is None:
            err("E3", i, f"pert_dose not numeric: {r['pert_dose']!r}")
        elif r["pert_idose"].strip() != want:
            err("E3", i,
                f"pert_idose {r['pert_idose']!r} != expected {want!r} "
                f"(replicates will silently split)")

        # E4
        want_t = f"{r['pert_time']}{r['pert_time_unit']}"
        if r["pert_itime"].strip() != want_t:
            err("E4", i, f"pert_itime {r['pert_itime']!r} != expected {want_t!r}")

        # E5 -- prefix must match exactly; suffix must equal the declared
        # block. Block is NOT derivable from the other columns (the
        # published MOC_1430 ':B' vehicle blocks have no distinguishing
        # field), so it must be recorded explicitly at intake.
        block = (r.get("block") or "A").strip() or "A"
        if not re.fullmatch(r"[A-Z]", block):
            err("E5", i, f"block {block!r} must be a single uppercase letter")
            block = "A"
        prefix = ":".join([r["project_id"], r["pert_id"], r["pert_idose"],
                           r["strain_id"], r["pert_itime"]])
        want_c = f"{prefix}:{block}"
        if r["condition_id"].strip() != want_c:
            err("E5", i,
                f"condition_id {r['condition_id']!r} != expected {want_c!r}")

        # E6
        want_b = ":".join([r["project_plate_id_384well"], r["strain_id"],
                           r["pert_itime"]])
        if r["comb_id"].strip() != want_b:
            err("E6", i, f"comb_id {r['comb_id']!r} != expected {want_b!r}")

        # E7
        if r["pert_type"] not in VALID_PERT_TYPE:
            err("E7", i, f"pert_type {r['pert_type']!r} not in {sorted(VALID_PERT_TYPE)}")

        # E8
        layout = r["single_or_paired_end"].strip().lower()
        r1 = (r["raw_file1_combined"] or "").strip()
        r2 = (r.get("raw_file2_combined") or "").strip()
        if not r1:
            err("E8", i, "raw_file1_combined empty")
        if layout.startswith("paired") and not r2:
            err("E8", i, "paired-end but raw_file2_combined empty")
        if layout.startswith("single") and r2:
            err("E8", i, "single-end but raw_file2_combined populated")

        # E9
        if r1 and r2 and r1 == r2:
            err("E9", i, "R1 and R2 are the same file")
        for f in (r1, r2):
            if f:
                if f in seen_fastq:
                    err("E9", i, f"FASTQ {f} already used by {seen_fastq[f]}")
                seen_fastq[f] = sid

        # E10
        if compounds and r["pert_id"] not in compounds:
            err("E10", i, f"pert_id {r['pert_id']!r} absent from compound annotation")

    # ---- batch-level warnings ----
    by_batch = collections.defaultdict(list)
    for r in rows:
        by_batch[r["comb_id"]].append(r)

    # CRISPRi batches z-score across strains/arabinose doses, so the
    # chemical-MOA-diversity rule does not apply to them.
    def is_crispri(rs):
        return (any("crispri" in x["category"].lower() for x in rs)
                or all(x["pert_id"] == "ara" for x in rs))

    for batch, rs in sorted(by_batch.items()):
        if not any(x["pert_type"] == "negcon" for x in rs):
            warn("W1", batch, "no negcon samples in batch")

        if compounds and not is_crispri(rs):
            mechs = {compounds.get(x["pert_id"], {}).get("pert_mechanism", "")
                     for x in rs}
            missing = [m for m in NEED_MECH if m not in mechs]
            if not any(m in mechs for m in NEED_EITHER):
                missing.append("Cell wall synthesis or Membrane Integrity")
            if missing:
                warn("W2", batch,
                     "insufficient MOA diversity for z-scoring; missing: "
                     + ", ".join(missing))

    # ---- condition-level warnings ----
    by_cond = collections.defaultdict(list)
    for r in rows:
        by_cond[r["condition_id"]].append(r)

    for cond, rs in sorted(by_cond.items()):
        if len(rs) != 3:
            extra = (" -- if these are two replicate blocks on one plate,"
                     " set block='B' on the second set") if len(rs) > 3 else ""
            warn("W3", cond, f"{len(rs)} replicates (expected 3){extra}")
        reps = [x["replicate_id"] for x in rs]
        dup = [k for k, v in collections.Counter(reps).items() if v > 1]
        if dup:
            warn("W4", cond, f"duplicate replicate_id: {dup}")

    print(f"Parsed {len(rows)} samples / {len(by_cond)} conditions / "
          f"{len(by_batch)} batches")
    report()
    return 1 if errors else 0


def report():
    if errors:
        print(f"\n{len(errors)} ERROR(S):")
        for e in errors:
            print("  " + e)
    if warnings:
        print(f"\n{len(warnings)} WARNING(S):")
        for w in warnings:
            print("  " + w)
    if not errors and not warnings:
        print("\nClean.")
    elif not errors:
        print("\nNo errors.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
