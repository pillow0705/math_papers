# Agent entry point

本仓库研究复六维阿贝尔簇的有理 Hodge 类，按 S1–S11、N1–N10 共 21 行组织。请简明回答，数学表述准确；未经用户明确要求，不调用子代理。

## 阅读顺序

1. 先读 `2.1_AI_paper.md` 的方法提炼，或 `2_AI_paper.pdf` 的前四页，了解可复用机制、假设与边界；完整证明正文紧随其后。
2. 用 `4_guide_zh.pdf` 或对应英文版了解分类及阅读路径。
3. 在 `theorem_graph/theorems.json` 中按 `id` 或 `row` 定位结果。原 LaTeX 标签是稳定 ID；无标签编号陈述使用 `result:<number>`。S/N ID 表示整行的结论范围。
4. 查 `source.start_line`、`proof_start_line`、`end_line`、`original_pdf_page` 或 `ai_pdf_page`，返回具体证明。
5. 查 `6_review_zh.pdf` 或 `5_review_en.pdf` 了解审查范围；作者已确认评审者为 6 Astra，且评审与当前稿件对应。

## 数学使用约定

- 区分群论／不变量计算、循环代数性、六维结论、全幂结论。这四者不是同一断言。
- `A^n` 的维数是 `6n`，不是 `6^n`。N2、N3 的剩余模型全幂结果不自动覆盖其完整行的所有幂。
- `edges` 仅收录整理过的充分证明路线，方向是“依赖 -> 使用者”；`reference_edges` 是原文显式引用，不能自动当作逻辑依赖。`references_indexed_only` 表示尚未逐项整理其完整依赖，并不表示独立于外部结果。
- 完整行依赖与分层依赖不同。某行使用外部输入，不意味着该行每个具体实例都使用它。
- 四个新外部输入必须按 JSON 的准确强度使用：Weil8、CM、指定完整 KS、Aux。Aux 是独立四槽张量假设。不要以普通 KS 代替它，不要把抽象 Hodge 同构直接称为代数对应。
- 三个撤回稿件对应的断言标为 `withdrawn_assertion_assumed`。CM 标为 `unverified_preprint_assertion_assumed`。外部状态以 2026-10-11 的核验为时间戳；需要更新时查询官方记录并注明来源。
- “在指定外部假设下未发现重大 gap”是用户提供报告的有限审查判断，不是对稿件、外部定理或 Lean 代码的认证。
- 没有文献比较前，不把 takeaways 称为已确认独有的新技术。有限脚本核验不证明代数循环存在。

## Files and build

All final PDFs are at the repository root. All current LaTeX/BibTeX sources are in `latex/`. Theorem registries and any diagram source are in `theorem_graph/`; review provenance and scope are recorded in `6_review_zh.pdf` and `5_review_en.pdf`. Reusable insights and research leads remain in the AI edition.

Compile entry files directly with Tectonic, e.g. `tectonic --outdir . latex/paper.tex` from the repository root. Keep the Chinese and English guides aligned. Preserve theorem IDs, mathematical assumptions, external-dependency status, and review provenance. Source line numbers and PDF page mappings must be refreshed if mathematical text or pagination changes.
