# Failure Patterns and Recovery

本参考总结数学建模竞赛中最容易产生“代码能跑通、论文写得很满、但结果经不起推敲或被判违规”的 19 类高频失效模式。

## 1. Reference material overrides the official prompt

**信号：** 往年参考论文或开源代码中的系数、列名、假设或目标定义与当年官方题目附件不一致。

**风险：** 模型解决的是别人往年的旧问题，而非当前官方赛题。

**处理：** 严格按事实源优先级恢复官方主场景；参考资料仅作思路校验；标记并重跑所有受影响结果。

## 2. One boundary step changes physical or time meaning

**信号：** 到达索引、执行时段、结算窗口或空间离散节点数相差 1（如 `0..N-1` vs `0..N`）。

**风险：** 初值（Carry-in）、终端状态（Closure）、累计积分或边界条件出现系统性偏差。

**处理：** 用明确的半开或闭区间定义每个离散索引；绘制索引到物理节点的映射；为首尾边界建立独立单元测试。

## 3. A unit or scaling transformation is applied twice

**信号：** 单位换算（如 km/m、MW/kW、元/万元、度/弧度）、效率或放大系数在数据预处理层与模型公式层重复乘除。

**风险：** 所有结果系统性偏大或偏小几个数量级，但内部守恒残差仍表面成立。

**处理：** 建立单一单位转换表与字段 lineage；规定单位换算只发生在数据入口层；用极简手算样例交叉核对。

## 4. Output feasibility substitutes for an explicit constraint

**信号：** 当前数据集下的输出恰好满足某个非负、容量上限或互斥关系，但目标/约束代码中并未写该约束。

**风险：** 更换压力情景、灵敏度参数或下游重用时立即产生物理不可行解。

**处理：** 显式将约束写入数学模型与求解代码，并同步更新独立约束验证器和测试。

## 5. Compressed variables hide source-to-destination semantics

**信号：** 单个聚合变量同时代表多种流向或状态组合，派生差值被隐式假定为非负。

**风险：** 成本、流量、排放或转移量出现隐蔽的重复计算或漏算。

**处理：** 建立显式来源—去向流矩阵；输出各分量分解表；逐项检查平衡残差。

## 6. A near-zero denominator creates spectacular percentages

**信号：** 基线指标本身极小，主模型降至零附近，于是报告“改善 99.9%”或“降低 100%”。

**风险：** 把局部微弱尾部的消除包装成全局重大突破，极易被评委一眼识破。

**处理：** 同时报告绝对变化量、基线分母值与发生位置；保留原始场景作为事实，用预设非退化压力情景解释机制。

## 7. Sensitivity is flat

**信号：** 多档参数扫描下所有核心指标和决策完全不变。

**可能原因：** 参数未接入计算图、对应约束未激活、扫描步幅过窄或候选集已退化。

**处理：** 先审计代码变量传递，再扩大扰动区间直到跨过临界相变点，或改选真正影响可行域的参数。

## 8. A heuristic failure is called physical infeasibility

**信号：** 某种资源/预算约束下启发式算法未找到可行解，就在论文中断言“系统在理论上无解”。

**风险：** 混淆“当前算法搜索能力不足”与“物理可行域为空”。

**处理：** 严谨表述为“当前启发式算法的可满足边界”；若要断言不可行，必须给出松弛模型不可行证明或矛盾约束链。

## 9. A local exact result is promoted to global optimality

**信号：** 只在局部窗口、降维子集或固定边界下求得最优解，却在摘要和结论中宣称“求得全问题全局最优解”。

**风险：** 结论强度明显越界。

**处理：** 完整说明窗口选择规则、固定条件、gap 与外推边界；正文只称“可行方案”“启发式 incumbent”或“局部精确验证”。

## 10. Entity sets and observation windows are mixed

**信号：** 将“某批到达任务集合的指标”与“固定时间观察窗内的资源指标”使用相同名词并列比较。

**风险：** 样本集合、分母与边界覆盖不匹配，出现无法自洽的均值或利用率。

**处理：** 为对象集合与时空窗口分别命名；在表头和 `scope_contract` 中强制保留五元组定义。

## 11. Status files drift apart

**信号：** `result_summary.json`、`PROJECT_STATE.md`、`ARTIFACT_REGISTRY.md` 和 `README.md` 显示不同的数字或状态。

**风险：** 过期的旧版本数值进入论文或官方结果表。

**处理：** 指定单一机器事实源，修改后按依赖图传播 `STALE` 标记，运行 `audit_competition_project.py` 检查冲突。

## 12. New outputs coexist with stale artifacts

**信号：** 新生成的图、新版本结果表与旧版本文件留在同一个 `outputs/` 目录。

**风险：** 论文插图脚本、LaTeX 编译或附件打包误抓旧文件。

**处理：** `outputs/` 实行白名单管理，旧版产物立即移入 `archive/` 并标为 `ARCHIVED`；定期运行结构审计检查残余文件。

## 13. Documentation or official Excel is hand-edited after generation

**信号：** 手工修改了论文草稿或 `result1.xlsx` 中的小数和数字，却未同步改代码与 `result_summary.json`。

**风险：** 后续重跑代码后修改回退，导致代码无法复现交付数字。

**处理：** 一切数字修改必须回到生成脚本和配置中重跑，禁止手工绕过流水线改表。

## 14. Runtime metadata is fabricated from file timestamps

**信号：** 用文件修改时间戳充当模型运行起止时间，或长流程只记录最后一个微步骤的耗时。

**风险：** 算法复杂度分析与实际耗时自相矛盾。

**处理：** 在主入口使用单调时钟（`time.perf_counter()`）精确测量各阶段耗时；未知历史时间如实标明缺失。

## 15. Visual polish outruns evidence

**信号：** 论文塞满炫酷热力图、3D 图和雷达图，但缺乏简单基线对比、硬约束检验或明确现象解释。

**风险：** 看起来像商业 PPT 展示，而非可审计的科学建模论文。

**处理：** 先确保证据链前 8 项齐备，再控制主图数量；每张主图只服务于一个核心命题。

## 16. Numerical step-size or mesh dependence masquerades as physical oscillation (机理仿真类)

**信号：** ODE/PDE 数值积分曲线出现高频抖动、峰值漂移或异常分叉，未做加密步长验证就直接当作“物理混沌/共振现象”大书特书。

**风险：** 实际上只是显式欧拉/固定步长在刚性区域发散或截断误差累积。

**处理：** 执行三档步长/网格加密收敛性测试（$\Delta t, \Delta t/2, \Delta t/4$），核对守恒残差与刚性求解器稳定性。

## 17. Temporal or group data leakage inflates out-of-sample accuracy (统计预测类)

**信号：** 在全量数据集上先做标准化、缺失均值填补、特征选择或 SMOTE 过采样，再随机划分训练/测试集；或者时序预测使用随机 K-Fold 交叉验证。

**风险：** 测试集统计分布和未来趋势泄漏进训练过程，导致竞赛指标虚高、真实泛化失效。

**处理：** 时序严格按时间窗口切分，分组数据按实体分组切分；所有预处理步骤封装进 Pipeline，仅在训练集上 `.fit()`。

## 18. Unchecked weight sensitivity causes silent rank reversal (评价决策类)

**信号：** 使用单一方法（如仅熵权法或一次主观打分）算出一套排名，未验证数据微小波动或权重微调对排序的影响。

**风险：** 数据分布极差微调或专家评分差 1 档，Top-3 决策对象排序完全翻转，导致管理建议根基不稳。

**处理：** 进行主客观权重对比及 $\pm 10\%$–$30\%$ 权重蒙特卡洛扰动实验，报告 Spearman/Kendall 相关系数和 Top-$K$ 稳健度。

## 19. Official submission spreadsheet drifts or violates anonymity (赛制合规类)

**信号：** 论文正文改了模型，但忘记重新运行官方填表脚本；或代码注释、PDF 元数据、图片路径中留有 `C:\Users\张三`、校名、导师姓名或禁用的队号格式。

**风险：** 官方填表对不上正文数字导致扣分，或因违反匿名纪律直接取消获奖资格。

**处理：** 将官方填表脚本纳入自动化主流水线末端；交付打包前执行关键词扫描、PDF 属性清理和 `audit_competition_project.py` 匿名审计。

## Recovery order

发现重大问题时严格按以下顺序恢复：

1. 冻结当前正式结论；
2. 定位最高优先级事实源；
3. 将受影响产物与下游契约标为 `STALE` 或 `INVALID`；
4. 修正输入、口径、模型或约束；
5. 重跑机器结果与独立验证；
6. 更新表格、图片、官方 `result*.xlsx`、README 与论文；
7. 更新 `ARTIFACT_REGISTRY.md`、`PROJECT_STATE.md` 与 `INTERFACE_CONTRACTS.md`；
8. 记录旧版本为何失效并清理/归档。
