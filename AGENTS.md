# 越南市场量化研究 Agent 协作规范

本文件适用于 `vietnam-quant-research` 仓库及其子目录。项目允许多个 agent 并行工作；所有 agent 必须遵守独立 worktree、独立分支和 PR 合并流程。

## 项目目标与边界

- 本项目是越南股票市场的数据获取、数据治理和量化研究资料库。
- 当前优先建设可审计的日频数据闭环和基础因子研究，不默认购买高价基本面、Tick 或 Level 2 数据。
- 研究结果必须明确数据来源、抓取时间、字段口径、交易成本、样本外区间和不确定性。
- 不把公开访问等同于批量抓取、长期存档、团队共享或再分发许可。

## 强制 Git 工作流

### 1. 开始任务前

先在项目根目录执行：

```powershell
git status --short --branch
git worktree list
git branch -vv
git fetch origin
```

- 不直接在 `main` 分支修改文件。
- 如果 `main` 有未提交改动、与远端分叉，或存在其他 agent 未完成的 worktree，先报告并确认处理方式；不得静默覆盖、重置或删除用户改动。
- 每个任务、每个 agent 使用一个独立 worktree 和独立分支。不要让两个 agent 在同一个目录运行、写文件或切换分支。
- 分支名使用 `codex/<short-task>`；并行 agent 需要额外区分时使用 `codex/<agent-id>/<short-task>`。

### 2. 创建 worktree

优先使用项目约定的 worktree 目录；如果目录位于仓库内，必须先确认它已被 `.gitignore` 忽略。示例：

```powershell
$branch = "codex/<short-task>"
$worktree = "<isolated-worktree-path>"
git worktree add $worktree -b $branch main
Set-Location $worktree
```

worktree 创建后先运行项目已有的基线检查。Python 项目至少确认解释器和依赖可用；若存在测试，先运行测试再开始修改。

### 3. 开发与提交

- 只修改当前任务需要的文件，不顺手重构无关代码或文档。
- 新增或修改代码时遵循测试先行：先写一个能证明目标行为的失败测试，再写最小实现，然后运行全部相关测试。
- 数据采集、清洗和回测代码必须保留来源、请求参数、抓取时间、解析版本和质量状态。
- 原始市场数据、商业数据文件、API key、secret、token、账号信息和本地运行产物不得提交到仓库。
- 正式运行数据放在项目外部的数据根目录；仓库只提交代码、文档和不受许可限制的元数据/质量摘要。
- 提交前至少运行：

```powershell
git diff --check
git status --short
```

- 提交应保持单一目的，提交信息使用清晰的动词开头，例如：

```powershell
git add <files>
git commit -m "feat: add daily source observation prototype"
```

### 4. 推送与创建 PR

在 worktree 中完成验证后：

```powershell
git push -u origin <branch>
gh pr create --base main --head <branch> --title "<short title>" --body "<summary, tests, risks>"
```

PR 描述必须包含：

- 变更目标和范围；
- 主要文件和数据流变化；
- 已运行的测试/质量检查及结果；
- 数据来源、授权边界和未解决风险；
- 是否需要人工复核或外部凭证。

PR 只合并满足以下条件的改动：

- CI/自动检查通过；
- 没有未解决的关键 review 意见；
- `git diff --check` 通过；
- 没有凭证、商业原始数据或意外的大文件；
- 回测/数据变更已说明 point-in-time、复权、停牌、流动性和交易成本处理。

### 5. 合并到 main

只有在 PR 审核和检查满足条件、且当前任务授权合并时执行：

```powershell
gh pr merge <number> --merge --delete-branch
```

如果仓库分支保护、检查失败或权限不足，保留 PR 并报告阻塞原因，不绕过保护规则。

### 6. 合并后的清理

合并确认后，在管理 checkout 中同步 `main`，再删除本地 worktree 和分支：

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git worktree remove <isolated-worktree-path>
git branch -d <branch>
git worktree prune
git status --short --branch
```

- 只删除已经合并且不再需要的旧分支和 worktree。
- worktree 有未提交改动时不得使用强制删除；先检查改动、保存必要内容并取得确认。
- `git reset --hard`、`git clean -fd`、强制删除分支或 worktree 都不是默认清理手段，除非用户明确授权且目标已核实。
- 最终状态应为干净的 `main`，并能在 GitHub 上找到对应的合并 PR。

## 并行 Agent 协作规则

- 一个独立任务对应一个 worktree、一个分支和一个 PR。
- Agent 之间通过提交、PR 和明确的文件边界协作，不通过共享工作目录传递半成品。
- 如果两个任务会修改同一文件或同一接口，优先拆分文件边界；无法拆分时串行处理，由后续 agent 基于已合并的 `main` 开新 worktree。
- Agent 不得切换、删除或重写其他 agent 正在使用的分支和 worktree。
- 不把运行时数据、缓存、notebook 输出或密钥复制到另一个 agent 的 worktree；需要共享时只共享可审计的代码、文档和元数据定义。
- 发现基础分支已变化时，停止继续堆叠冲突，先同步最新 `main` 并重新确认任务边界。

## 越南日频研究的最低验收要求

在进入正式基础因子回测前，至少应完成：

- 覆盖 HOSE、HNX、UPCoM 的目标证券样本，并记录历史有效期、停牌、转板和退市状态；
- `instrument_master`、`price_daily`、`source_observations` 三类数据接口或等价结构已建立；
- VCI/KBS/SSI（可用时）同一时间区间的来源差异已抽样记录；
- `countBack` 日期裁剪、KBS 倒序、价格单位和交易日时区已标准化；
- A32、ADC 等 OHLC 异常已输出具体日期和原始字段，不能简单删除或填充；
- raw price 与 adjusted price 分开保存，复权事件有来源；
- 因子结果包含流动性过滤、涨跌停/停牌不可成交约束、交易成本和样本外区间；
- 每个结论都能追溯到来源观察和数据版本。

