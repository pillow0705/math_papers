# Math papers

| Research area | Repository | Original paper | AI edition | Chinese guide | English guide | Theorem graph |
|---|---|---|---|---|---|---|
| Stochastic optimization | [CCSGD](CCSGD/README.md) | [PDF](CCSGD/1_paper.pdf) | [PDF](CCSGD/2_AI_paper.pdf) | [PDF](CCSGD/4_guide_zh.pdf) | [PDF](CCSGD/3_guide_en.pdf) | [PDF](CCSGD/7_theorem_graph.pdf) |
| Probability | [van Dantzig pairs](van_dantzig_pairs/README.md) | [PDF](van_dantzig_pairs/1_paper.pdf) | [PDF](van_dantzig_pairs/2_AI_paper.pdf) | [PDF](van_dantzig_pairs/4_guide_zh.pdf) | [PDF](van_dantzig_pairs/3_guide_en.pdf) | [PDF](van_dantzig_pairs/7_theorem_graph.pdf) |
| Algebraic geometry | [Hodge classes on abelian sixfolds](hodge_sixfolds/README.md) | [PDF](hodge_sixfolds/1_paper.pdf) | [PDF](hodge_sixfolds/2_AI_paper.pdf) | [PDF](hodge_sixfolds/4_guide_zh.pdf) | [PDF](hodge_sixfolds/3_guide_en.pdf) | [PDF](hodge_sixfolds/7_theorem_graph.pdf) |

Each repository keeps its seven numbered reading PDFs at the repository root. LaTeX/BibTeX sources are in `latex/`. CCSGD's two manuscript figures are also in `latex/`, and its current experiment code is in `experiments/`. Reusable insights are included in the AI editions.

PDF numbering is for browsing; LaTeX filenames identify the corresponding source:

| PDF | LaTeX source |
|---|---|
| `1_paper.pdf` | `latex/paper.tex` |
| `2_AI_paper.pdf` | `latex/AI_paper.tex` |
| `3_guide_en.pdf` | `latex/guide_en.tex` |
| `4_guide_zh.pdf` | `latex/guide_zh.tex` |
| `5_review_en.pdf`, `6_review_zh.pdf` | PDF-only review records; review sources were intentionally removed. |
| `7_theorem_graph.pdf` | `latex/theorem_graph.tex`; Hodge instead uses `theorem_graph/render_graph.py` and the JSON registry. |

Each AI edition also has a directly readable `2.1_AI_paper.md` entry.

Each repository includes `6_review_zh.pdf` and `5_review_en.pdf`; provenance and scope are recorded within the PDFs. No additional review files are retained.


The author has confirmed that all three reviews are by 6 Astra and correspond to the current manuscripts. Review PDFs retain their received wording; the subsequent author confirmation supersedes earlier identity/version uncertainty in those records.
