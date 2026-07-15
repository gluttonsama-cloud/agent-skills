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

如果安装后没有立即显示 Skill，请重启 Codex 或 Cursor。随后在 Agent 对话中完成初始化并验证：

```text
/daily-report setup 你的姓名
/daily-report list
```

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
