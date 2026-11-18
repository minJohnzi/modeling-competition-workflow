---
name: modeling-competition-workflow
description: Plan, implement, validate, and write reproducible mathematical-modeling competition solutions with auditable data, baselines, sensitivity analysis, multi-question interfaces, official result tables, figures, and paper-ready evidence. Use for CUMCM (全国大学生数学建模竞赛), Huawei Cup / NPMCM (中国研究生数学建模竞赛), MCM/ICM (美国大学生数学建模竞赛), Huashu Cup (华数杯), ShuWeiBei (数维杯), APMCM (亚太赛), and similar end-to-end modeling tasks across mechanistic simulation, operations research/scheduling, statistical/ML prediction, and multi-criteria evaluation/decision problems; do not use for isolated theorem proofs, routine homework, generic data analysis, or copyediting that does not require a modeling evidence chain.
---

# Mathematical Modeling Competition Workflow

把数学建模竞赛任务交付为一条**可复现、可验证、可追溯到官方结果表与论文正文**的证据链，而不是只给算法名称、一次成功运行或一组无法核验的数字。

## First route the request

先完整阅读 [workflow-and-governance.md](references/workflow-and-governance.md)，再按当前任务需要读取最少参考：

- 初始化竞赛项目、锁定语言/页数/匿名与提交格式、填写官方结果表（`result*.xlsx`）或撰写美赛 Summary Sheet / Memo 时，读取 [competition-profiles.md](references/competition-profiles.md)。
- 进行题意建模、四大题型选模（机理仿真 / 运筹优化 / 统计预测 / 评价决策）、基线对比、守恒/收敛/可行域校验或敏感性设计时，读取 [modeling-and-validation.md](references/modeling-and-validation.md)。
- 设计目录结构、集中配置、计算输入哈希、输出 `result_summary.json` / `table_*.csv` / `run_log.md` 或使用 `templates/` 治理模板时，读取 [evidence-and-reproducibility.md](references/evidence-and-reproducibility.md)。
- 题目含多个递进或独立子问题（`q1`–`q6` / `Q1`–`Q6`）、存在误差传递或并行多成员协作时，读取 [multi-question-integration.md](references/multi-question-integration.md)。
- 需要撰写/整合中英文论文、设计算法伪代码、绘制正式图表或执行完稿写作审计时，读取 [paper-and-visualization.md](references/paper-and-visualization.md)。
- 出现零值退化、极端改善、平坦敏感性、步长/网格震荡、数据泄漏、排名翻转、官方表漂移或历史产物混用时，读取 [failure-patterns.md](references/failure-patterns.md)。

不要为了“完整”而一次加载全部参考。

## Establish authority before modeling

按以下优先级建立事实源：

1. 竞赛官方题目、附件数据、官方勘误、指定结果填报表模板（如 `result*.xlsx`）与匿名/排版要求；
2. 用户明确锁定的口径与当前仓库规则；
3. 原始数据及可独立复算的数据字典；
4. 当前有效的机器结果（`result_summary.json`、`table_*.csv`）、接口契约（`INTERFACE_CONTRACTS.md`）与状态登记（`ARTIFACT_REGISTRY.md`）；
5. 参考论文、往年优秀论文、他人代码、经验参数与示例答案。

较低层级只能启发或校验，不能覆盖较高层级。发现冲突时停止传播冲突结论，记录受影响范围并请求裁决。

## Preserve authorization boundaries

- “看看、分析、审计、给建议”只授权只读发现和设计，不授权修改正式代码、数据、结果或论文。
- “实现、生成、完成、直接做”通常授权在明确范围内实施；仍需遵守仓库自己的批准门槛。
- 若没有仓库规则且请求含糊，先交付发现结论和实施契约，再请求批准。
- 题意、数据清洗、统计口径、核心模型、目标函数、硬约束、关键参数范围或结论方向发生实质变化时，暂停并重新确认。

## Non-negotiable modeling invariants

- 原始数据只读；清洗和衍生数据说明来源、规则、样本量变化和生成方法。
- 每个指标写明五元组口径：`(对象集合, 时空范围, 分母, 聚合方式, 单位)`。
- 物理结算量、统计误差指标、启发式候选评分、精确优化目标、综合评价得分和论文结论指标严格区分，不混用口径。
- 每个主模型至少比较一个简单基线和一个合理竞争方法；不能只选择容易击败的基线。
- 核心约束、守恒律或结构边界必须在模型中显式表达，并由独立于主求解器的新代码路径重算验证；事后恰巧可行不能替代可行域约束。
- 有随机性时固定并记录种子；无随机性时明确说明算法为确定性。
- 无全时域或全局最优性证明时，只称可行方案、启发式 incumbent、非支配候选或局部验证结果。
- 涉及上游参数拟合/代理模型向下游传参时，必须传递误差界或残差范围并评估误差放大。
- 每条正式结论必须可追溯到代码、机器摘要、正式表格、图片或已核验公式。
- 结果必须同时报告收益、代价、适用边界和局限。

## Required evidence chain

正式交付至少形成：

1. 题意、赛制要求与数据审计；
2. 主要矛盾、物理/统计机理与真实瓶颈；
3. 模型定义、假设、目标、约束与参数来源；
4. 可复现实现与集中配置；
5. 简单基线、竞争方法与主模型的同口径比较；
6. 题型专属验证（守恒/步长收敛/硬约束独立复算/无泄漏泛化/权重排名稳定性）；
7. 决策导向的敏感性、临界区间与压力情景分析；
8. 解质量、不确定性区间或跨问题误差传递评估；
9. 局限性、失效条件与外部有效性说明；
10. 与机器结果及官方填报表完全一致的论文表述。

缺少任一关键环节时，明确标为待验证，不把“程序运行成功”写成模型结论。

## Scale exactness to the problem

先估算变量规模、网格/时间步长成本、求解时间和精确验证价值。若全量精确求解或高保真仿真不可承受：

- 连续机理题：先建立降维解析近似或代理模型，再在关键区段用精细步长/高阶求解器交叉校验收敛性；
- 离散运筹题：在全时域构造可复现、硬约束可行的启发式或分解算法；用独立规则选取代表性紧张窗口，固定窗外边界与状态，建立覆盖启发式落点的 LP/MIP 强基准，报告 incumbent、下界、gap 与不可外推边界；
- 统计预测/评价题：先用可解释简单基线建立性能下限，再逐步引入非线性模型或组合赋权，用相同无泄漏切分比较收益与复杂度代价。

## Verify before publishing

发布正式结论前检查：

- 输入 SHA-256 哈希、主键、时空边界、单位与符号；
- 样本集合、观察窗口与评价口径是否混用；
- 目标方向、守恒残差/步长收敛/约束覆盖、极值与退化情形；
- 基线是否公平，参数敏感性扫描是否真正扰动决策；
- 小分母、零值和退化场景是否被相对百分比夸大；
- `result_summary.json`、`table_*.csv`、官方 `result*.xlsx`、图片、README、运行日志和论文数字是否一致；
- 匿名要求与附件打包规则是否达标（无本机路径、队号/校名泄漏或缓存垃圾）；
- 上游变更是否已使下游依赖产物标记并重算。

若项目采用标准的 `qN`/`QN` 结构，可运行只读结构审计：

```bash
python scripts/audit_competition_project.py --root <project-root>
```

该脚本只检查目录结构、严格 JSON、输入 SHA-256、CSV 健康度、图片 DPI、匿名与绝对路径泄漏等可机械验证的不变量，不能替代题意、公式、模型或论文论证的人工审阅。

## Close with a decision-ready handoff

交付时先说明结论状态（`SUPPORTED` / `PROVISIONAL` / `STALE`），再列出：

- 已完成的代码、机器摘要、官方结果表、图表和论文产物；
- 实际运行、独立验证与审计命令；
- 通过的约束/收敛/泛化/基线与敏感性证据；
- 未解决问题、适用边界和失效条件；
- 受影响与未触碰的文件范围；
- 需要用户裁决的后续事项。
