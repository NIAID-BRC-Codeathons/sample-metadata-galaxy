# Sample Metadata That Survives Analysis in Galaxy

**NIAID-BRCs AI Codeathon 2.0** · September 16–18, 2026 · Argonne National Laboratory

Preserving validated sample metadata through Galaxy analysis and exporting it as a portable, standards-based record that another scientist can independently audit and reproduce.

Project page: https://niaid-brc-codeathons.github.io/projects/sample-metadata-galaxy/

## Problem

When a researcher sits down to analyze data in Galaxy, the sample metadata that should accompany that data is often missing, incomplete, inaccurate, or not structured in a way that maps cleanly to the Galaxy data types the analysis requires. The agent (Loom/Orbit) can help, but in its current state it makes confident errors — misreading papers, propagating upstream label errors, and presenting inferred values as fact without flagging uncertainty to the user.

## Deliverables

### 1. Skills (`skills/`)

Three cooperating skills for the Loom/Orbit skill system that ensure sample metadata is assembled, validated, and correctly mapped to Galaxy data types before any analysis proceeds:

- **`metadata-construction`** — default first step for most analyses. Elicits, extracts, and assembles sample metadata from public records, the data itself, and user input. Produces a provenance YAML and a tabular sample metadata file.
- **`analysis-readiness`** — validates the assembled metadata against the data and the intended analysis. Flags any gap — incomplete, inaccurate, unverified, or missing — before the analysis proceeds. Declares the study ready, ready with warnings, or blocked.
- **`galaxy-input-modeling`** — converts the validated tabular metadata into the correct Galaxy dataset or collection structure required by a specific tool or workflow.

The skills are designed to fire automatically when a user starts talking about analyzing data in Orbit, without the user having to know they exist.

### 2. Case studies (`case_studies/`)

Two papers, each with two bundles — a **naive** run (no skills) and a **with-skills** run — so we can compare agent behavior with and without the skills on the same data:

- **`livny/`** — a known quantity: a PNAS paper from a team member (Romano et al., 2024, [PMC11551328](https://pmc.ncbi.nlm.nih.gov/articles/PMC11551328/), GEO [GSE251671](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE251671)). The naive run found the agent was mostly right but subtly and confidently wrong in two places: it misread a water negative control as dosed, and it propagated SRA's single-end mislabeling without flagging that the allegedly single samples had two files with the same number of spots. The with-skills run is in progress.
- **`blasi/`** — a naive-user scenario: a *Front. Microbiol.* paper (Cianciulli Sesso et al., 2021) we don't know the authors of, same organism and treatment context but a different lab and assay. Closer to what a naive user experiences. The naive run is done; the with-skills run is pending.

### 3. Learning feature (in progress)

A mechanism for the agent to push specific failure modes it encounters around sample metadata back to a shared database, using a similar mechanism to user feedback. These findings could be harvested to:

- improve future versions of the skills,
- improve the Orbit harness itself, or
- inform upstream submission processes (e.g. flagging systematic metadata issues to NCBI/SRA).

## Future directions

- **Migrate skills into the harness.** The skills are a prototype — essentially suggestions the agent follows. If they prove useful, the next step is turning the most important suggestions into rules in the Orbit harness itself, so they are enforced rather than suggested.
- **Formal evaluation.** To know what is working or not, we need a formal eval method and suite — a set of studies with known ground truth, run with and without the skills, scored on metadata accuracy, gap detection, and whether inferred values are honestly labeled.

## Full proposal

A longer write-up is available at <https://gist.github.com/dannon/bc321e5b8d208431a8f41942d566625b>.

## Leads

- Danielle Callan
- Dannon Baker

## Working here

This repository is the team's working space for the codeathon — code, notebooks, data pointers, and notes. Team members get access through the [NIAID-BRC-Codeathons](https://github.com/NIAID-BRC-Codeathons) organization; accept the invitation if you have not already.
