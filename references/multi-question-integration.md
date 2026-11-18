# Multi-question Integration

## 1. Treat every interface as an explicit contract

多个子问题章节相邻不代表数值结果自动继承。对每条上游到下游接口，在 `INTERFACE_CONTRACTS.md`（模板见 `templates/INTERFACE_CONTRACTS.md`）中记录：

| 字段 | 内容 |
|---|---|
| `Contract ID` | 稳定编号（如 `IC-Q1-Q2`） |
| `Upstream -> Downstream` | 来源问题与使用方问题 |
| `Relationship Type` | `Independent` / `Sequential inheritance` / `Definition reuse with re-optimization` / `Settlement only` / `Surrogate & Parameter Handoff` |
| `Status` | `LOCKED`、`PROVISIONAL`、`REJECTED` 或 `STALE` |
| `Passed Fields & Units` | 传递的字段、量纲、时间/空间索引、物理意义 |
| `Uncertainty / Error Bound` | 若传递参数估计、预测值或代理模型，写明拟合残差或置信区间 |
| `Excluded Content` | 明确禁止继承的旧决策、固定轨迹、经验参数或旧数字 |
| `Verification Evidence` | 官方条款、代码接口、独立测试或审计记录 |

最常见的错误是把“沿用方法”写成“沿用数值结果”，或忘记传递上游拟合的不确定性。

## 2. Classify inter-question relationships

### Independent

各问题只共享原始数据和统一全局定义，分别重新建模。不得横向比较不同 Scope 的结果。

### Sequential inheritance

下游真正使用上游输出（如最优轨迹、选址方案、聚类标签或预测曲线）作为输入。必须冻结接口字段、版本、单位和 SHA-256 哈希，并在上游变化后立即将下游标为 `STALE`。

### Definition reuse with re-optimization

下游沿用物理定义、约束体系和算法框架，但在新决策变量、新目标或新边界条件下重新优化。不得直接复制上游固定决策或相对改善率。

### Settlement only

下游不改变上游决策变量，只在新价格、新政策阈值或新风险规则下重新评估结算。论文需明确指出没有重新优化。

### Surrogate & Parameter Handoff（高频用于国赛 A / 华为杯）

上游通过实验数据反演物理参数（如阻尼系数、热阻、信道衰落参数、传播率）或构建降阶代理模型供下游优化/仿真使用。下游必须接收**参数点估计 + 误差范围**，并在下游做至少一轮参数误差敏感性传递检验，避免误差放大导致最优方案不可行。

## 3. Maintain a single project state

根目录 `PROJECT_STATE.md`（模板见 `templates/PROJECT_STATE.md`）至少记录：

- 赛制 Profile 与刚性规则（语言、页数上限、官方填报表、匿名要求）；
- 全局锁定决策；
- 每个子问题的题型、正式模型、核心结论与当前状态；
- 当前有效的验收测试或审计证据；
- 是否获准进入总论文与官方结果表；
- 跨问题冲突及裁决结果；
- 当前最大风险。

子目录可保留生成阶段状态，但根状态必须说明它与最终审核状态的关系。发现状态文件、机器摘要和 README 不一致时，不自行选择最有利版本；报告冲突并依据事实源优先级裁决。

## 4. Propagate invalidation

建立简单依赖图：

    official input & official templates
        -> cleaned data
        -> upstream outputs / parameter estimates (q1)
        -> downstream model outputs (q2..qN)
        -> tables, figures & official result*.xlsx
        -> paper sections
        -> abstract / Summary Sheet / Memo & conclusion

跨问题接口会连接多个依赖图。任一节点改变后，所有下游节点先标记为 `STALE`，再重算、重验并刷新所有依赖产物。

重大字段与口径变化包括：

- 名称相同但单位或量纲变化；
- 时空网格分辨率改变或边界增加/减少一个步长；
- 固定外生输入改为联合优化内生变量；
- 毛口径改为净口径（如总产量 vs 净收益、总负荷 vs 净负荷）；
- 个体峰值之和改为系统同时刻峰值；
- 局部到达集合改为全局观察窗口；
- 单一指标权重或主场景/压力情景切换。

## 5. Audit interface semantics, not only numbers

对跨问题接口逐项检查：

- 每个变量的物理来源、去向、符号正负号和单位；
- 压缩或聚合变量是否仍隐含必要非负或守恒约束；
- 同一字段名是否在不同问题中悄悄改变了统计语义；
- 离散状态变量对应时段初还是时段末、节点中心还是网格边界；
- 边界时刻是执行、结算还是仅作终端状态约束；
- 下游能否仅凭上游输出字段独立重建物理守恒方程。

事后输出表面上没有违反约束，不能证明模型可行域已经包含该约束。若语义依赖某个推导量的非负性，应显式建模或给出严格等价证明。

## 6. Compare only compatible metrics

跨问题比较前核对五元组一致性：

- 原始对象集合是否一致；
- 时间窗口或空间域是否一致；
- 决策是固定结算还是重新优化；
- 聚合分母与权重定义是否一致；
- 单位、折算系数与成本/惩罚边界是否一致。

不兼容时只说明机理差异和方向关系，严禁给出虚假优劣排名。论文可以说“采用相同物理定义重新评估”，不能暗示数值可直接继承或对比。

## 7. Write explicit transitions in the paper

相邻问题节首说明：

- 沿用的输入、符号、约束、控制方程或统计口径；
- 新增的决策变量、物理模块、约束或优化目标；
- 明确是“继承上游方案”“基于上游参数估计重新优化”“仅重新结算”还是“独立重建模”；
- 为什么上一问题的某些数字不可直接横向比较。

节末说明本节输出（含精度或误差界）如何成为下游的定义、输入或对照。使用内容化承接（如“沿用前述微分动力学方程及辨识参数 $\hat{\theta}$”），不依赖机械的“在 5.1 节所述”这类位置引用。

## 8. Integrate at the end

最终合龙至少完成：

- 全局统一符号表（物理含义、单位、集合与变量/参数属性）；
- 时空尺度与单位总审计；
- 全文图号、表号与公式编号重排（确保正文引用零断链）；
- 摘要 / Summary Sheet、正文、结论与官方填报表数字 100% 一致；
- 合并相邻章节的重复基本假设与共享约束，保证主线精炼连贯；
- 每问保留最低限度的基线、约束/收敛/泛化和边界证据；
- 统一系统敏感性、误差传递、局限性与未来展望章节；
- 参考文献真实且格式统一（国赛/研赛常用 GB/T 7714，美赛常用 IEEE/APA）；
- 按 `competition-profiles.md` 完成总页数预算检查与全包匿名安全审查。
