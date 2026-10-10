# Agent instructions

## Purpose and entry points

This repository makes the CCSGD paper easy to locate, understand and reuse. Read in this order:

1. `2.1_AI_paper.md` (or its five-page PDF): contract and twelve takeaways.
2. `theorem_graph/theorem_graph.json`: resolve stable IDs to exact assumptions, conclusions, dependencies and proof locations.
3. `1_paper.pdf` and the corresponding `.tex` section: check the complete argument before applying a result.
4. `4_guide_zh.pdf` or `3_guide_en.pdf` for a human reading route.
5. `6_review_zh.pdf` for the supplied review and its explicit limits.

The original paper is authoritative. The AI edition and graph summarize it; neither replaces proofs nor certifies correctness.

## Mathematical reuse

- Preserve quantifiers and conditioning. Pointwise finite moments do not automatically imply a deterministic uniform variance bound along SGD.
- Keep A-ENV (input exponent), A-AMP (parameter-dependent amplitude control) and A-CLEAN (clean sampling variance) distinct. Derive the corrected-oracle bound; do not assume it under a new name.
- The exact Gaussian identity is classical. Do not claim its invention here or say all prior correction methods are inexact or non-executable.
- Do not identify unbiasedness with zero variance or clean-oracle efficiency. For `n` observations and `m` simulations per observation, variance is `v_obs/n + v_sim/(n*m)`.
- Convex bounds use a step-size-weighted average; PR CLTs use a uniform average. Nonconvex stationarity does not imply convergence to a global optimizer.
- At `alpha = 1`, check the spectral condition and the endpoint PR kernel; do not reuse the interior PR covariance automatically.
- Higher moments are derived from input growth and tails. The CLT trajectory bound is obtained after almost-sure convergence, not assumed to prove it.
- With random response `Y`, hold its observed value fixed during input complexification and verify joint moment conditions. Appendix A.9 is a separate example-specific verification.
- Non-Gaussian statements in Section 7.1 depend on the companion criterion and integrability. Match the exponent to conjugate tails; do not claim arbitrary noise or arbitrary entire scores are covered.
- Entire neural-network inputs do not automatically satisfy a parameter-independent growth exponent or amplitude condition. The network experiment is empirical.

## Source and evidence rules

- Cite stable result IDs together with original labels, e.g. `T-PR / Theorem 4.4 / Appendix A.7`.
- `depends_on` records direct logical result dependencies. `reuse_edges` are conditional proof reuse, not unconditional theorem implications.
- External statuses distinguish tools used without reproving them, internally reproved identities, historical citations, and the external companion manuscript.
- The supplied review was received from the author, not run by this packaging agent. It concerns the filename `main(6).pdf`; the author has confirmed that it matches the current manuscript. Do not convert “no major gap found” into a correctness or publication guarantee.
- Dashed regression reference lines are asymptotic population biases, not finite-time lower bounds. WH means the specified Eq. (5) comparator; SIMEX uses three training trajectories. Preserve the reported later SIMEX/CCSGD ordering.
- Keep public insights inside the AI edition; do not create a duplicate insights section or directory.

## Files and build

All seven numbered reading PDFs are at the repository root; the two manuscript figure PDFs are in `latex/`. All current LaTeX/BibTeX sources are in `latex/`. Theorem registries and any diagram source are in `theorem_graph/`; review provenance and scope are recorded in `6_review_zh.pdf` and `5_review_en.pdf`. Reusable insights and research leads remain in the AI edition.

Compile entry files directly with Tectonic, e.g. `tectonic --outdir . latex/paper.tex` from the repository root. Keep the Chinese and English guides aligned. Preserve theorem IDs, mathematical assumptions, external-dependency status, and review provenance. Source line numbers and PDF page mappings must be refreshed if mathematical text or pagination changes.
