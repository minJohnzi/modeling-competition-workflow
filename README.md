# Modeling Competition Workflow (`modeling-competition-workflow`)

面向 **全国大学生数学建模竞赛（CUMCM / 国赛）**、**中国研究生数学建模竞赛（华为杯 / NPMCM）**、**美国大学生数学建模竞赛（MCM / ICM）** 以及 **华数杯 / 数维杯 / APMCM（亚太赛）** 的全流程可复现数学建模竞赛 Skill。

覆盖四大核心题型：**机理仿真（ODE/PDE/几何物理）**、**运筹优化与调度**、**统计学习与预测诊断**、**多属性评价与决策**。

## 目录结构

```text
modeling-competition-workflow/
├── SKILL.md                         # Skill 主入口、路由与不可妥协不变量
├── agents/
│   └── openai.yaml                  # Agent 界面元数据
├── references/
│   ├── workflow-and-governance.md   # 7 阶段治理流、锁定决策、并行 Worker 写入隔离
│   ├── competition-profiles.md      # 国赛 / 华为杯 / 美赛 / 邀请赛赛制硬约束
│   ├── modeling-and-validation.md   # 指标五元组与四大题型专属验证矩阵
│   ├── evidence-and-reproducibility.md # 目录规范、SHA-256 哈希、JSON/CSV/日志标准
│   ├── multi-question-integration.md   # 跨问题接口契约、误差传递与合龙审计
│   ├── paper-and-visualization.md   # 论文结构、算法伪代码、双格式图表规范
│   └── failure-patterns.md          # 19 类高频失效模式诊断与恢复顺序
├── templates/
│   ├── PROJECT_STATE.md             # 项目全局状态模板
│   ├── INTERFACE_CONTRACTS.md       # 跨问题接口契约模板
│   ├── ARTIFACT_REGISTRY.md         # 正式产物状态登记模板
│   └── result_summary.example.json  # 严格 JSON 机器摘要模板
└── scripts/
    └── audit_competition_project.py # 只读结构、哈希、CSV、DPI 与匿名性审计脚本
```

## 让 Agent 或在本地按需下载使用

### 1. 安装到全局 Codex / Agent Skill 目录

Windows (PowerShell):

```powershell
git clone https://github.com/minJohnzi/modeling-competition-workflow.git "$HOME\.codex\skills\modeling-competition-workflow"
```

macOS / Linux (Bash/Zsh):

```bash
git clone https://github.com/minJohnzi/modeling-competition-workflow.git ~/.codex/skills/modeling-competition-workflow
```

### 2. 直接克隆到单个竞赛项目的 `.agents/skills/` 目录

```bash
git clone https://github.com/minJohnzi/modeling-competition-workflow.git .agents/skills/modeling-competition-workflow
```

### 3. 在对话中让 Agent 直接下载并启用

可以直接向 Agent 发送类似指令：

> 请从 `https://github.com/minJohnzi/modeling-competition-workflow` 克隆 `modeling-competition-workflow` skill 到当前项目的 `.agents/skills/modeling-competition-workflow`（或全局 `~/.codex/skills/`），读取 `SKILL.md` 后按其流程开展建模与验证。

## 审计脚本快速验证

运行自带正反测试用例验证环境可用性：

```bash
python scripts/audit_competition_project.py --self-test
```

对具体竞赛项目执行只读审计：

```bash
python scripts/audit_competition_project.py --root <project-root>
```
