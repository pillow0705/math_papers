# Hodge Classes on Abelian Sixfolds

| Material | PDF | Source |
|---|---|---|
| Original paper | [PDF](1_paper.pdf) | [LaTeX](latex/paper.tex) |
| AI edition and insights | [PDF](2_AI_paper.pdf) | [LaTeX](latex/AI_paper.tex) |
| Chinese reading guide | [PDF](4_guide_zh.pdf) | [LaTeX](latex/guide_zh.tex) |
| English reading guide | [PDF](3_guide_en.pdf) | [LaTeX](latex/guide_en.tex) |
| Theorem dependency graph | [PDF](7_theorem_graph.pdf) | [Renderer](theorem_graph/render_graph.py) |

[Searchable AI edition](2.1_AI_paper.md)

- [Theorem registry](theorem_graph/theorems.json): IDs, hypotheses, conclusions, dependencies, proof locations, and external status.
- [Chinese review](6_review_zh.pdf) · [English review](5_review_en.pdf).
- [Agent entry point](AGENTS.md).
- Public insights and research leads are included in the AI edition.

[Chinese external review](6_review_zh.pdf) · [English external review](5_review_en.pdf). The author has confirmed that these are the 6 Astra review of the current manuscript and its English translation. The full 21-case conclusion is conditional on the precisely stated external inputs; see the AI edition, registry, and AGENTS.md.

## Build

Compile a retained LaTeX entry directly with Tectonic, for example `tectonic --outdir . latex/paper.tex`. Chinese typesetting requires the fonts specified in the corresponding source. The graph renderer also requires Python 3 and ReportLab (`python3 -m pip install reportlab`). PDF outputs belong in the repository root.
