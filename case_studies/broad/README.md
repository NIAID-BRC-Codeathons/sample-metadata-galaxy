# Case Study: Broad — Reproducing a Known Quantity

Assess the agent's ability to reconstruct sample metadata from public resources for a published study where the ground truth is known. The paper came from a team member, so we could check the agent's output against the real answer.

**Paper:** Romano et al., "Perturbation-specific transcriptional mapping for unbiased target elucidation of antibiotics," PNAS 2024. [PMC11551328](https://pmc.ncbi.nlm.nih.gov/articles/PMC11551328/) · DOI: [10.1073/pnas.2409747121](https://doi.org/10.1073/pnas.2409747121)

**Data:** GEO accession [GSE251671](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE251671), linked BioProject PRJNA1055047.

## Structure

Each paper gets two bundles — a **naive** run (no skills) and a **with-skills** run — so we can compare:

- `naive/` — agent runs without the skills. This is the baseline.
- `with-skills/` — agent runs with the skills enabled. (Not yet run for this paper.)

## What's in `naive/`

- `project1v2/` — the canonical run. The agent reconstructed metadata from GEO/SRA/the paper, built intake templates and a validator, then attempted to run the analysis in Galaxy (custom reference, patched workflow, 9-sample smoke test). The smoke run failed on a DESeq2 issue and a GTF/STAR gene-loss bug.
- `project1-metadata-only/` — an earlier, shorter session that stopped at metadata construction. This is the session where we identified the confident errors documented below.

## What we found (naive run)

The agent was **mostly able** to reconstruct sample metadata from public resources. It located the study, pulled sample attributes, and assembled a structured metadata record without much prompting.

However, it was **subtly and confidently wrong** in a few places — making assumptions that were not flagged to the user:

1. **Negative control dosage misread.** The agent recorded a dosage of ~0.05 for the negative control, which was just water. This was a misread of the paper and does not make sense — water is not dosed. The agent presented this as fact without flagging it as uncertain.

2. **Single vs. paired mislabeling not flagged.** The agent labeled many samples as "single" (single-end reads) when they were actually paired. This was an upstream error — the samples are mislabeled as single in SRA — but the agent should have flagged the inconsistency because the allegedly single samples each had two files with the same number of spots, which is strong evidence of paired-end data. The agent propagated the SRA label without questioning it against the data.

The Galaxy run in `project1v2/` uncovered a deeper layer of issues beyond metadata: the workflow itself has bugs for bacterial data (silent zero counts from CDS-only GTFs, wrong genome build, wrong STAR defaults). These are documented in the notebook.

## Context

We explicitly asked the agent to do this assessment. The average user will not — they will just start talking about analyzing data and expect the agent to handle the rest. So two reasonable first goals:

1. **Make the process more honest about what is known vs. not known.** The agent should flag inferred values, conflicts, and unresolved questions to the user rather than presenting them as fact.
2. **Make it happen automatically.** Metadata construction and validation should kick in when a user starts talking about analyzing data in Orbit, without the user having to know these steps exist or ask for them.

The skills in `../../skills/` are a first attempt at both goals. The `with-skills/` bundle will test whether they actually help.
