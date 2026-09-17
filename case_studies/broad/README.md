# Case Study: Broad — Reproducing a Known Quantity

## What we tried to do

Assess the agent's ability to reconstruct sample metadata from public resources for a published study where the ground truth is known. The paper came from a team member, so we could check the agent's output against the real answer.

**Paper:** Romano et al., "Perturbation-specific transcriptional mapping for unbiased target elucidation of antibiotics," PNAS 2024. [PMC11551328](https://pmc.ncbi.nlm.nih.gov/articles/PMC11551328/) · DOI: [10.1073/pnas.2409747121](https://doi.org/10.1073/pnas.2409747121)

**Data:** GEO accession [GSE251671](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE251671), linked BioProject PRJNA291292.

## What we found

The agent was **mostly able** to reconstruct sample metadata from public resources (GEO, SRA, BioSample, the publication). It located the study, pulled sample attributes, and assembled a structured metadata record without much prompting.

However, it was **subtly and confidently wrong** in a few places — making assumptions that were not flagged to the user:

1. **Negative control dosage misread.** The agent recorded a dosage of ~0.05 for the negative control, which was just water. This was a misread of the paper and does not make sense — water is not dosed. The agent presented this as fact without flagging it as uncertain.

2. **Single vs. paired mislabeling not flagged.** The agent labeled many samples as "single" (single-end reads) when they were actually paired. This was an upstream error — the samples are mislabeled as single in SRA — but the agent should have flagged the inconsistency because the allegedly single samples each had two files with the same number of spots, which is strong evidence of paired-end data. The agent propagated the SRA label without questioning it against the data.

## Takeaway

The agent can do most of the work of assembling metadata from public sources, but it currently makes confident errors that a careful human analyst would catch. The two failure modes above — misreading the paper and propagating upstream labels without checking against the data — are exactly the kinds of gaps that the `analysis-readiness` skill is designed to catch.

## Artifacts

- `project1/` — the full agent session: notebook, activity log, GEO data pulls, reconstructed metadata, and the original paper PDF.
- `pnas.202409747.pdf` — the published paper.
