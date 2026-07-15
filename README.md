# Agent Skills

供团队安装使用的 Agent Skills。个人运行数据不会存储在本仓库中。

## 可用 Skill

- `daily-report`：跨对话记录已完成的工作，并按导师群规范生成日报。

## 安装

无需 GitHub 账号或仓库邀请。根据使用的 Agent 选择安装命令。

### Codex

```bash
npx skills add https://github.com/gluttonsama-cloud/agent-skills \
  --skill daily-report --agent codex --global --yes
```

### Cursor

```bash
npx skills add https://github.com/gluttonsama-cloud/agent-skills \
  --skill daily-report --agent cursor --global --yes
```

如果安装后没有立即显示 Skill，请重启 Codex 或 Cursor。

## 使用方法

- Cursor 使用 `/daily-report`。
- Codex 使用 `$daily-report`，也可以从 Skill 列表中选择“日报助手”。

下面以 Cursor 的 `/daily-report` 为例；在 Codex 中把命令开头替换成 `$daily-report` 即可。

### 1. 设置姓名

首次使用先保存日报姓名：

```text
/daily-report setup 张三
```

姓名只保存在本机，之后生成日报时会自动使用。

### 2. 记录当前对话的完成事项

在一个工作对话结束后执行：

```text
/daily-report record
```

也可以补充说明或成果链接：

```text
/daily-report record 已完成方案整理，文档：https://example.com/document
```

Skill 只收录当前对话中已经完成的成果。相同日期、相同对话再次执行时会更新原记录，不会重复添加。

### 3. 查看和维护记录

查看今天或指定日期的事项：

```text
/daily-report list
/daily-report list 7.15
```

根据 `list` 返回的事项 ID 修改标题、说明或链接：

```text
/daily-report edit dri-xxxxxxxxxxxx 补充链接 https://example.com/result
```

删除误收录事项：

```text
/daily-report remove dri-xxxxxxxxxxxx
```

### 4. 生成日报

聚合当天所有对话中已经记录的成果：

```text
/daily-report generate
/daily-report generate 7.15
```

需要生成“明日计划”时，可以在命令后直接粘贴会议纪要：

```text
/daily-report generate 7.15
会议纪要：
- 张三明天继续细化网关计划，并完成 URL Scheme 实现。
- 李四负责测试环境部署。
```

Skill 只提取明确属于当前用户的后续行动，不会保存原始会议纪要。生成结果可以直接复制到导师群：

```text
张三 7.15 日报
今日完成：整理网关下一步计划、完成 URL Scheme 方案
- 整理网关下一步计划：https://example.com/plan
- 完成 URL Scheme 方案：链接待补
明日计划：
- 继续细化网关计划，并完成 URL Scheme 实现
```

没有可分享链接时仍会生成草稿，并标记“链接待补”。本地文件路径不会被当作提交链接。

## 更新

仓库合并新版本后，可以执行以下命令更新已安装的 Skill：

```bash
npx skills update daily-report --global --yes
```

## 参与维护

仓库初始化版本已直接提交到 `main`。后续修改请新建分支并提交 Pull Request，确保 Skill 指令和脚本经过评审后，再通知团队成员更新本地版本。

## 隐私说明

Skill 会将每个人的配置和日报台账保存在各自电脑上。请勿将 `profile.json`、`ledger.json`、`ledger.lock`、会议纪要或生成的日报提交到本仓库。

可以通过 `DAILY_REPORT_HOME` 环境变量指定台账目录。未指定时，Skill 使用操作系统的标准应用数据目录。为了向后兼容，如果本机已有 `~/Documents/Codex/.daily-report`，Skill 会自动继续使用该目录。

## 开发与测试

需要 Python 3.9 或更高版本。运行测试：

```bash
python3 tests/test_daily_report.py -v
```
