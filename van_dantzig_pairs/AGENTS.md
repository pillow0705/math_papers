# Repository guide for research agents

This repository studies constructive van Dantzig pairs: independent real U,V with E exp(t(U+iV))=1 for every real t. It develops Fourier/Hankel criteria, polynomial realization, explicit families, and recovery of known classes.

## Start here

1. Read `2.1_AI_paper.md` (five-page PDF: `2_AI_paper.pdf`). It collects result contracts, reusable methods, and research leads.
2. Look up the cited IDs in `theorem_graph/theorems.json`. Use `7_theorem_graph.pdf` for the dependency overview.
3. Read the referenced statement and proof in `latex/paper.tex`. The complete human-readable version is `1_paper.pdf`.
4. For a short overview, use `4_guide_zh.pdf` or `3_guide_en.pdf`. Their content corresponds module by module.
5. Check `6_review_zh.pdf` and `5_review_en.pdf` for the status of the user-supplied 6 Astra review.

## Authority and mathematics

- `latex/paper.tex` is the authoritative manuscript. Preserve its source and style for companion-only updates.
- `latex/AI_paper.tex` is the AI typesetting source; `latex/guide_zh.tex` and `latex/guide_en.tex` are the guide sources. `theorem_graph/theorems.json` is the source for the graph formats.
- State all hypotheses and parameter quantifiers when reusing a result. The existence criteria quantify over all points or matrix sizes. T3.1 supplies sufficiently large b followed by sufficiently large tau.
- T2.5 requires a polynomial or the stated entire-function integrability condition. Use the full symmetric moment sequence for C2.4.
- KPS Theorem 4.1 is an external premise for D_P. Classical inputs and candidate-original contributions are distinguished in the registry. The historical comparison with Lukacs 1968 remains outstanding.
- The registry retains two unapplied editorial notes from the previous audit. Do not interpret their presence as edits to the original manuscript.
- There is no separate public-insights section. Put reusable observations and clearly labelled research directions in the AI edition.

## Files and build

All final PDFs are at the repository root. All current LaTeX/BibTeX sources are in `latex/`. Theorem registries and any diagram source are in `theorem_graph/`; review provenance and scope are recorded in `6_review_zh.pdf` and `5_review_en.pdf`. Reusable insights and research leads remain in the AI edition.

Compile entry files directly with Tectonic, e.g. `tectonic --outdir . latex/paper.tex` from the repository root. Keep the Chinese and English guides aligned. Preserve theorem IDs, mathematical assumptions, external-dependency status, and review provenance. Source line numbers and PDF page mappings must be refreshed if mathematical text or pagination changes.
