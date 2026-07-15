# Agent Skills

Private, installable Agent Skills for the team. Personal runtime data is never
stored in this repository.

## Available skills

- `daily-report`: record completed work across conversations and generate the
  mentor-group daily report format.

## Install for Cursor

The repository owner must first add each teammate under **Settings →
Collaborators**. After the teammate accepts the invitation, configure GitHub
SSH and install the skill globally:

```bash
npx skills add git@github.com:gluttonsama-cloud/agent-skills.git \
  --skill daily-report --agent cursor --global --yes
```

If GitHub CLI authentication is already configured for HTTPS, this form also
works:

```bash
npx skills add https://github.com/gluttonsama-cloud/agent-skills \
  --skill daily-report --agent cursor --global --yes
```

Restart Cursor if the skill does not appear immediately. Verify it in Agent
chat:

```text
/daily-report setup Your Name
/daily-report list
```

Update an installed copy after new versions are merged:

```bash
npx skills update daily-report --global --yes
```

## Contributing

The initial repository bootstrap is committed directly to `main`. For later
changes, create a branch and open a pull request so skill instructions and
scripts can be reviewed together before teammates update their installed copy.

## Privacy

The skill writes each person's profile and ledger to their own machine. Never
commit `profile.json`, `ledger.json`, `ledger.lock`, meeting minutes, or generated
daily reports to this repository.

The ledger location can be overridden with `DAILY_REPORT_HOME`. Without an
override, the skill uses the operating system's normal application-data folder.
An existing `~/Documents/Codex/.daily-report` ledger is reused automatically for
backward compatibility.

## Development

Requires Python 3.9 or newer. Run the test suite with:

```bash
python3 tests/test_daily_report.py -v
```
