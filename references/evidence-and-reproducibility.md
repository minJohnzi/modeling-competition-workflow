# Evidence and Reproducibility

## 1. Respect the repository before imposing a layout

先读取仓库规则和已有结构。若项目没有约定，可采用标准化的多问题结构（`qN/` 与 `QN/` 大小写保持一致即可）：

    project/
    ├── q1/                  # 或 Q1/
    │   ├── data/            # 本题专用清洗/衍生数据（只读指向根目录 data/）
    │   ├── src/             # 求解、验证、可视化脚本
    │   ├── tests/           # 独立不变量与约束验证测试
    │   ├── outputs/         # result_summary.json, table_*.csv, figNN_*.png/.pdf, run_log.md
    │   ├── paper/           # 持续写作草稿（单文件或五阶段草稿）
    │   ├── README.md        # 运行入口、依赖、种子、输入与核心数字
    │   └── notes.md         # 待验证假设、口径记录与局限备忘
    ├── data/                # 官方原始只读数据（建议根目录集中存放）
    ├── shared/              # 跨问题公共模块（数据加载、可复制自 templates/paper_style.py 的绘图样式、官方填表工具）
    ├── paper/               # 最终整合总论文（LaTeX/Word/Markdown 章节与官方结果表）
    ├── PROJECT_STATE.md     # 复制自 templates/PROJECT_STATE.md
    ├── INTERFACE_CONTRACTS.md # 复制自 templates/INTERFACE_CONTRACTS.md
    └── ARTIFACT_REGISTRY.md # 复制自 templates/ARTIFACT_REGISTRY.md

子问题是独立研究任务时分目录；共享代码只放真正跨问题稳定复用的内容。不要为了统一而擅自移动已有仓库的文件。

## 2. Keep raw inputs immutable

- 原始数据只读；
- 清洗或派生数据写入单独位置（如 `qN/data/processed/`）；
- 记录源文件、工作表、字段映射、清洗规则和样本行数变化；
- 对正式输入计算真实 **SHA-256 哈希**，并在运行前后核对；
- 不把参考资料、网友答案或草稿中间表当作官方输入。

输入缺失或字段语义不明时，停止形成正式结论。允许建立带清晰标签的假设情景，但不能伪装成官方数据。

## 3. Centralize configuration

集中管理（建议 `src/config.py` 或 `config.yaml`）：

- 相对路径、时空范围与网格/步长参数；
- 随机种子（含多种子评估列表）；
- 数值容差与收敛阈值；
- 物理/经济/业务模型参数与单位标注；
- 敏感性参数扫描网格；
- 求解器时间上限和 MIP gap；
- 正式策略或模型名称；
- 图片格式（`.png` 必选，可选 `.pdf`/`.svg`）和分辨率（$\ge 300$ dpi）；
- 升级与停止阈值。

代码使用相对项目目录的路径，严禁硬编码包含本机用户名的绝对路径（如 `C:\Users\...` 或 `/Users/...`）。配置快照进入 `result_summary.json` 或 `run_log.md`。

## 4. Produce a minimum formal artifact set

每次正式运行至少输出：

- `result_summary.json`：严格 JSON 的关键参数、真实输入哈希、结果与状态；
- `table_*.csv`：可独立复算的干净数值表（无 `NaN`/`inf`/合并单元格）；
- `figNN_meaning.png`：300–400 dpi 论文级图片（推荐基于 `templates/paper_style.py` 绘制；若使用 LaTeX 排版，强烈建议同时输出同名 `figNN_meaning.pdf` 或 `.svg` 矢量图）；
- `run_log.md`：命令、环境、时间、参数、哈希、测试和结论；
- 官方填报表（如赛题要求 `result1.xlsx`、`Result.csv`）：由脚本从正式输出自动生成与校验；
- 与当前结果同步的 `paper/` 草稿。

不要只保存图片；图片不是机器事实源。不要只保存巨型明细表；还需摘要和解释。

## 5. Design result_summary.json as an interface

标准模板见 `templates/result_summary.example.json`，建议包含：

- `schema_version` 与 `question`；
- `archetype`（`mechanistic_simulation` / `operations_research` / `statistical_ml` / `evaluation_decision`）；
- `generated_at` 与 `status`（`PROVISIONAL` / `SUPPORTED` / `STALE` / `INVALID`）；
- `configuration` 与 `random_seed`；
- `input_hashes`（必须为真实 64 位十六进制 SHA-256 字符串）；
- `data_audit`（记录原始行数、清洗后行数、缺失/异常处置）；
- `scope_contract`（明确对象集合、时空范围、分母、聚合与单位）；
- `baselines` 与 `recommended_solution`；
- `primary_metrics`；
- `constraint_or_conservation_audit`（独立校验结果）；
- `validation`（收敛性/下界 gap/滚动回测/排名翻转率等题型验证结果）；
- `sensitivity`；
- `runtime_seconds`；
- `limitations`。

JSON 必须拒绝 `NaN`、`Infinity` 和手工注释（Python 中使用 `json.dumps(..., allow_nan=False)`）。数值单位体现在字段名或配套元数据中。

## 6. Make tables answer audit questions

为以下证据保留独立表（按题型按需生成）：

- 数据质量与清洗统计；
- 简单基线、竞争方法与主模型同口径比较；
- 硬约束、守恒残差或收敛性审计；
- 逐组、逐区域或跨类别影响分解；
- 参数敏感性、临界区间与权重扰动测试；
- 解质量、多种子稳定性或误差传递界；
- 正式结果填报映射与新旧版本差异。

表头写清单位和 Scope。改善行同时区分绝对值与百分比，避免把百分比填入绝对量列。

## 7. Record a trustworthy run log

运行日志应包含：

- 从项目根目录或题目录执行的实际命令；
- Python、求解器（如 Gurobi/HiGHS/SciPy/PyTorch）和核心依赖版本；
- 真实输入 SHA-256 哈希；
- 核心参数和随机种子；
- 真实单调时钟（`time.perf_counter()`）测得的运行时长；
- 测试命令与通过数；
- 主要结果与约束/验证状态；
- 降级、超时、重试和未执行实验；
- 结论适用边界。

若真实起止时间没有保留，只报告可靠的耗时，不用文件写入时间伪造模型运行时间。

## 8. Test results independently

优先测试可观察不变量，而不是测试文本措辞：

- 原始主键集合与输出集合一致；
- 时间/空间边界与连续性；
- 守恒残差、步长加密收敛性与量纲一致性；
- 硬约束与资源占用由独立逻辑从原始决策变量重算；
- 时序/分组切分无未来信息或分组数据泄漏；
- 评价权重扰动后的排名相关性与稳定性；
- 真实输入 SHA-256 哈希一致；
- 正式结果、官方填报表（`result*.xlsx`）、摘要 JSON 与论文数字一致；
- 正式图片格式、命名和 DPI 达标；
- 失效旧产物未混入当前输出。

若测试直接调用主求解器内部同一个评分或检查函数，不能称为独立验证。对关键约束必须使用不同代码路径重算。

## 9. Manage artifact state

使用 `templates/ARTIFACT_REGISTRY.md` 统一登记状态：

| 状态 | 含义 |
|---|---|
| `PROVISIONAL` | 已运行，但仍有接口、审核或验证未完成 |
| `SUPPORTED` / `VALID` | 当前证据支持进入正式论文与官方结果表 |
| `STALE` | 上游输入、口径或参数变化后已过期，等待重跑 |
| `INVALID` | 已知错误，严禁进入论文 |
| `ARCHIVED` | 仅保存历史对照 |

状态登记表必须保持标准列结构（`问题 | 产物 | 当前状态 | 验证证据 | 说明`），以便自动化审计脚本对齐校验。不要仅靠文件修改时间判断新旧。

## 10. Prevent stale conclusions

修改数据处理、模型、参数、字段或统计口径后：

1. 找出受影响的机器结果、官方填报表、CSV、图、README、论文和摘要；
2. 先标记为 `STALE`；
3. 重新运行并生成新产物，或明确移除/归档过期证据；
4. 交叉核对数字与官方表；
5. 更新 `ARTIFACT_REGISTRY.md` 和 `PROJECT_STATE.md`。

避免手工只改论文或 Excel 数字而不重跑代码，也避免新输出生成后保留同名旧图或旧版本策略标签。

## 11. Use the bundled structural audit

从 Skill 目录或指定绝对路径运行只读审计脚本：

```bash
python <skill-dir>/scripts/audit_competition_project.py --root <project-root>
```

常用选项：

- `--questions auto`（自动发现 `q1`–`q9` 或 `Q1`–`Q9`，也可逗号指定）
- `--paper-mode auto`（`auto` 自动兼容五阶段草稿或单文件章节草稿；可选 `stages` / `single`）
- `--min-dpi 300`（最低 PNG 物理 DPI 门槛）
- `--strict-warnings`（存在 `WARNING` 时也返回非零退出码）
- `--json`（输出结构化 JSON 审计报告）
- `--self-test`（运行内置正反测试用例验证脚本自身健壮性）

该脚本检查目录、严格 JSON、真实 SHA-256 输入哈希、CSV `NaN/inf` 健康度、PNG DPI（同时放行配套 `.pdf`/`.svg` 矢量图）、日志要素、表头感知的状态冲突、绝对路径与匿名性词汇泄漏。**它不判断公式推导是否正确、模型选择是否合理或论文论证是否充分**；脚本通过只意味着工程与结构性门槛通过。

## 12. Final reproducibility & anonymity checklist

- 在干净环境中能从 `README.md` 命令一键复跑；
- 路径全部相对、原始输入只读、随机种子固定；
- `result_summary.json` 为严格 JSON 且 `input_hashes` 与实际数据 SHA-256 匹配；
- 关键 CSV、PNG/PDF 图和官方 `result*.xlsx` 能从当前代码重生；
- 所有核心约束/守恒/收敛/泛化/稳定性有独立验证；
- 正式数字在摘要、`result_summary.json`、CSV、官方表、图和论文中完全一致；
- 符合赛制匿名规范（无本机用户路径、校名、队名或导师信息泄漏）；
- 交付附件包已剔除 `.venv/`、`__pycache__/`、临时文件与历史无效产物。
