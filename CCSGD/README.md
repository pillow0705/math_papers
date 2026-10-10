# Complex-Corrected SGD for Noisy Observations

| Material | PDF | Source |
|---|---|---|
| Original paper | [PDF](1_paper.pdf) | [LaTeX](latex/paper.tex) |
| AI edition and insights | [PDF](2_AI_paper.pdf) | [LaTeX](latex/AI_paper.tex) |
| Chinese reading guide | [PDF](4_guide_zh.pdf) | [LaTeX](latex/guide_zh.tex) |
| English reading guide | [PDF](3_guide_en.pdf) | [LaTeX](latex/guide_en.tex) |
| Theorem dependency graph | [PDF](7_theorem_graph.pdf) | [LaTeX](latex/theorem_graph.tex) |

[Searchable AI edition](2.1_AI_paper.md)

- [Theorem registry](theorem_graph/theorem_graph.json): IDs, hypotheses, conclusions, dependencies, proof locations, and external status.
- [Chinese review](6_review_zh.pdf) · [English review](5_review_en.pdf).
- [Agent entry point](AGENTS.md).
- Public insights and research leads are included in the AI edition.

The supplied 6 Astra review concerns `main(6).pdf`; the author has confirmed its correspondence to the current manuscript. The two `latex/figure_*.pdf` files are required by the original manuscript source.

## Build

Compile a retained LaTeX entry directly with Tectonic, for example `tectonic --outdir . latex/paper.tex`. Chinese typesetting requires the fonts specified in the corresponding source. PDF outputs belong in the repository root.


## Experiment source

[Source and run instructions](experiments/README.md): regression simulation, neural-network comparison, and the five-seed runner.
