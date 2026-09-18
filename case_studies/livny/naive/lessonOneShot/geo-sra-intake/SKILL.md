---
name: geo-sra-intake
description: >
  Pull GEO/SRA sample and run metadata without a browser, join GSM→SRX→SRR,
  and record per-run layout. Use when fetching GSE/GSM/PRJNA/SRP records,
  building a FASTQ manifest, or GEO HTML returns recaptcha. Triggers: GSE*,
  GSM*, PRJNA*, SRP*, SRR*, "GEO series", "SRA run table", NCBI recaptcha,
  mixed paired/single, one sample many runs, eutils, GEO SOFT.
---

# GEO / SRA intake without a browser

GEO accession pages in a headless fetch return recaptcha interstitial HTML,
not sample records. That is not a transient failure — do not retry the same
URL. Switch protocol.

## What to call instead

| Need | Source |
| --- | --- |
| Find a GSE in GEO DataSets | NCBI E-utilities `esearch` on db=`gds` |
| Series summary + sample id list | `esummary` / `esearch` db=`gds` with the GDS id (`200251671` for GSE251671) |
| Per-sample characteristics | GEO **SOFT** (`GSE*_family.soft.gz`) or each GSM's `acc.cgi?acc=GSM…&form=text` |
| Run-level FASTQ facts | SRA run info (`PRJNA*` / `SRP*`), or a local SRA mirror / BRC `get_sra_study_runs` |
| Author processed tables | The GitHub/Zenodo linked from Data Availability, not GEO |

E-utilities example pattern (save to disk, then parse — never pipe to an interpreter):

```bash
mkdir -p geo
curl -sL --max-time 60 \
  "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&term=GSE251671[ACCN]&retmode=json" \
  -o geo/esearch.json
curl -sL --max-time 60 \
  "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gds&id=200251671&retmode=json" \
  -o geo/gse_summary.json
```

GSM text (still NCBI, but the `form=text` SOFT-like dump, not the HTML portal):

```bash
curl -sL --max-time 60 \
  "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM7985666&form=text" \
  -o geo/gsm_example.txt
```

If a fetch returns "Checking your browser" / recaptcha, stop. That body is not
parseable metadata.

## Join keys

Build the manifest at **GSM grain**, then explode to SRR:

- GSM title / characteristics → perturbation fields (`pert_id`, dose, time, strain).
- GSM → SRX → SRR via BioSample / SRA links in SOFT (`!Sample_relation = SRA: …`).
-  One GSM to many SRRs is normal (tech reps, resequencing, split lanes).
  If the author pipeline expects `raw_file1_combined`, concatenate those SRRs
  *per GSM* before alignment; do not treat each SRR as a biological sample.

Lowercase join keys. Author R often does `tolower(sample_id)` before matching
count-matrix columns. A case mismatch looks like missing files.

## Do not trust series-level library layout

`library_strategy = RNA-Seq` on the series does not mean every run is paired.

In PRJNA1055047 the paper and every GSM said paired-end; the SRA mirror
reported a mix (sample-level: 918 PAIRED / 141 SINGLE). Consequences:

- Record `library_layout` from the **run**, not from the paper.
- A paired-end sample with an empty R2 path is an error; a genuine SINGLE
  run with an empty R2 path is not.
- Alignment and count scripts must branch per run, or you will silently
  drop or double-count reads.

Also record `instrument_model`, `mbases` / `bytes`, and release date. They
are cheap now and expensive to reconstruct after a partial download.

## Sandbox / agent constraints

- **Do not pipe remote content into Python or R.** Write the HTTP body to a
  file, then `json.load(open(...))`. Agent harnesses may hard-fail
  `curl … | python` with `pipe remote content to an interpreter`.
- Cap `curl --max-time`. NCBI hangs rather than errors.
- Prefer a local SRA mirror or BRC analytics tools for "how many runs / what
  layout" summaries; they are faster than paging ENA and are not recaptcha
  gated. Then fetch SOFT for the characteristic fields the mirror does not
  carry (`pert_idose`, strain, plate).

## Manifest columns worth having on day one

Accession grain: `geo_accession`, `biosample`, `srx`, `srr` (possibly multiple),
`library_layout`, `instrument`, `mbases`.

Biology grain: whatever the author pipeline joins on — typically `sample_id`,
`pert_id`, `pert_idose`, `pert_itime`, `strain_id`, `project_id`,
`project_plate_id_384well`, `replicate_id`, `category`.

If a published `sample_id` is a concatenation of those fields, do not
approximate it. See [composite-sample-ids](../composite-sample-ids/SKILL.md).
