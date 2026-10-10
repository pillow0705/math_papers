# 定理依赖图：格式与解释

`7_theorem_graph.pdf` 是 `theorems.json` 的可视化视图。PDF 展示核心路线、21 行结论合同和全部编号陈述索引；完整陈述、定位与引用信息在 JSON 中。图中省略的边不意味着独立性。

## JSON v1.0.0

- `nodes`：定理、引理、命题、推论、辅助例子／备注、21 行结论合同与外部输入。
- `edges`：人工整理的核心充分逻辑路线，`source -> target` 表示前者是后者的依赖；不主张列尽全部隐含经典前提。
- `reference_edges`：程序提取的原稿 `ref/eqref/autoref`，可能含前向指引、例子和替代路线，不能等同于逻辑边。
- `source_sha256`：生成数据所用原稿的哈希。
- `external_status`：核验日期、官方来源、撤回断言清单及 CM 断言的审查边界。

## 节点关键字段

| 字段 | 含义 |
|---|---|
| `id` | 优先使用原 LaTeX 标签；否则 `result:<number>`；S/N 表示整行；`EXT:` 表示外部输入 |
| `number`, `row`, `kind` | 原编号、所属分类、陈述类型 |
| `assumptions_and_conclusion_latex` | 完整原文陈述，假设与结论一起保留；用 LaTeX 编码避免数学转写损失 |
| `assumptions`, `conclusion` | 外部输入及类别合同的可读条件、结论 |
| `source` | 源文件、1 起算行号、证明起止位置、LaTeX 标签及两版 PDF 的物理页码 |
| `logical_dependencies` | 当前整理的直接依赖；与逻辑边一致 |
| `dependency_coverage` | `curated_core`／`curated_case_main_theorem`／`curated_case_contract`／`references_indexed_only`／`external_contract` |
| `curated_transitive_external_inputs` | 沿已整理逻辑边得到的外部依赖闭包 |
| `curated_transitive_conditional_inputs` | 其中 Weil8、CM、KS、Aux 的子集；空集并不认证尚未整理的节点无外部依赖 |
| `powers_scope` | `all_powers`、`sixfold_only_as_stated` 或 `sixfold_full_row_and_residual_all_powers` |

外部 `status` 的取值为 `withdrawn_assertion_assumed`、`unverified_preprint_assertion_assumed`、`cited_external_theorem_not_reproved`、`cited_external_theorems_not_reproved`、`standard_results_not_formalized_here`。这些标签描述资料包的使用方式，不认证外部数学结论。

## 查询示例

```python
import json
from pathlib import Path
g = json.loads(Path('theorem_graph/theorems.json').read_text())
nodes = {n['id']: n for n in g['nodes']}
print(nodes['p:N3KS']['source'])
print(nodes['N2']['curated_transitive_conditional_inputs'])
print(nodes['S11']['powers_scope'])
```

图只列某条充分证明路线，不宣称依赖最小化。整行节点可能同时列出主定理与其关键工具；这类冗余有助于路线浏览。因不同分层可使用不同充分路线，不可用整行闭包代替每个具体分层的最小依赖分析。
