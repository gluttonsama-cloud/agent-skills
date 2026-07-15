---
name: daily-report
description: Record completed work from the current agent conversation into a shared local ledger and generate mentor-group daily reports across conversations. Use only when the user explicitly invokes `/daily-report` with `record`, `list`, `edit`, `remove`, `generate`, or `setup`; do not invoke for ordinary status summaries.
---

# Daily Report

Use Python 3.9 or newer. Resolve `scripts/daily_report.py` relative to this
`SKILL.md` and use it for every ledger read or write. Keep the submitted report
in Chinese unless the user requests another language.

## Commands

Interpret the first argument after `/daily-report` as a subcommand:

- `record [date or notes]`: record completed work from the current conversation.
- `list [date]`: show saved items and missing links; default to today.
- `edit <item-id> <change>`: update one saved item.
- `remove <item-id>`: remove one saved item.
- `generate [date]`: render the report; treat the remaining pasted text as
  meeting minutes.
- `setup <name>`: save or replace the report name.

Do not activate implicitly. Do not create automations or reminders.

## Payload safety

Never interpolate user-derived text into a shell command. Use the client's
filesystem-writing tool to create a unique JSON payload in the operating
system's temporary directory, pass only that path to the script, and add
`--consume-payload`. Do this for `record`, `edit`, `setup`, and `generate` when
it includes a meeting plan.

Run the script in this form:

```bash
python3 /absolute/path/to/this-skill/scripts/daily_report.py record \
  --payload /absolute/path/to/temp-payload.json --consume-payload
```

The script emits JSON. Use its fields to form the response; do not expose the
ledger JSON unless asked.

## Record

1. Build a stable conversation key. Prefer a native session or conversation ID
   when the client exposes one. Otherwise combine the client name, working
   directory, conversation title, and first user-request summary. Reuse the same
   key every time this conversation is recorded; ask rather than guess if it
   cannot be made stable.
2. Review the current conversation. Extract only completed outcomes supported
   by the transcript: created or changed artifacts, implemented behavior,
   completed investigation, or a concrete decision. Exclude unfinished
   intentions and tentative plans.
3. Split independent PRs, documents, designs, implementations, or decisions
   into separate items. Keep titles concise enough for `今日完成`.
4. Treat only relevant `http://` or `https://` work-product URLs as shareable
   links. Exclude unrelated references. Keep local paths in `local_artifacts`;
   never present them as submission links.
5. Let explicit notes after `record` refine the extraction without overriding
   transcript facts.
6. Write this payload:

```json
{
  "date": "2026-07-15",
  "thread_id": "cursor|project|conversation",
  "thread_title": "conversation title",
  "thread_cwd": "/absolute/project/path",
  "items": [
    {
      "title": "完成事项",
      "description": "可选事实说明",
      "primary_url": "https://shareable.example/artifact",
      "urls": ["https://shareable.example/artifact"],
      "local_artifacts": ["/absolute/local/path"]
    }
  ]
}
```

Set `primary_url` to `null` when no shareable link exists. The script upserts
one record per date and conversation key, so a repeated `record` refreshes that
conversation instead of duplicating it.

Confirm saved item IDs and titles. Call out missing primary links.

## List, edit, and remove

- Run `list --date <date>` and present item IDs, titles, primary links, and the
  missing-link count.
- Before `edit`, list the target when its values are unknown. Send only the
  requested changes. Supported fields are `title`, `description`,
  `primary_url`, `urls`, `add_urls`, `local_artifacts`, and
  `add_local_artifacts`.
- Run `remove <item-id>` only for the supplied ID and confirm its title.

Accept `YYYY-MM-DD` and `M.D`. Default to the current date in
`Asia/Shanghai`.

## Setup and generate

For `setup`, pass `{"name": "姓名"}`. If `generate` returns
`name_required`, ask for the name, save it, and resume generation.

When meeting minutes follow `generate`:

1. Extract only explicit future actions assigned to the configured person or
   clearly stated as the user's own next step.
2. Preserve deadlines and constraints.
3. Ignore other people's work, background discussion, and uncertain ideas.
4. Deduplicate and compress to one to five bullets. If none are reliable, pass
   an empty list and omit `明日计划`.
5. Send `{"tomorrow_plan": ["行动项"]}` as the generate payload. Never store raw
   meeting minutes.

Render the returned `report` verbatim in a plain-text code block:

```text
姓名 7.15 日报
今日完成：事项一、事项二
- 事项一：https://...
- 事项二：链接待补
明日计划：
- 明确的后续行动
```

Do not add `@所有人` or format instructions. When `missing_links` is non-empty,
label the result as a draft outside the code block and list the item IDs that
need shareable links. Otherwise keep the response minimal.

## Errors

- `name_required`: ask for the name, save it, and continue.
- `no_entries`: report that the selected date has no recorded work.
- `item_not_found`: show the date list or ask for the correct ID.
- Invalid dates, payloads, or URLs: identify the rejected field and never invent
  a replacement.

