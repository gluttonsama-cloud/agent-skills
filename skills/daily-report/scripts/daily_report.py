#!/usr/bin/env python3
"""Atomic, cross-platform ledger for the daily-report Agent Skill."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
import tempfile
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlparse

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX
    msvcrt = None


SCHEMA_VERSION = 1
TIMEZONE = timezone(timedelta(hours=8), name="Asia/Shanghai")
ID_NAMESPACE = uuid.UUID("7d32ee8d-f307-43e6-a82c-5f6ad2468c82")


def resolve_default_home() -> Path:
    override = os.environ.get("DAILY_REPORT_HOME")
    if override:
        return Path(override).expanduser()

    legacy = Path.home() / "Documents" / "Codex" / ".daily-report"
    if legacy.exists():
        return legacy

    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "daily-report"
        return Path.home() / "AppData" / "Local" / "daily-report"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "daily-report"

    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / "daily-report"
    return Path.home() / ".local" / "share" / "daily-report"


DEFAULT_HOME = resolve_default_home()


class DailyReportError(Exception):
    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


def emit(payload: dict[str, Any], exit_code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return exit_code


def now_shanghai() -> datetime:
    return datetime.now(TIMEZONE)


def normalize_date(value: str | None) -> str:
    if not value:
        return now_shanghai().date().isoformat()
    value = value.strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return date.fromisoformat(value).isoformat()
        match = re.fullmatch(r"(\d{1,2})\.(\d{1,2})", value)
        if match:
            current_year = now_shanghai().year
            return date(current_year, int(match.group(1)), int(match.group(2))).isoformat()
    except ValueError as exc:
        raise DailyReportError("invalid_date", f"Invalid date: {value}") from exc
    raise DailyReportError(
        "invalid_date", f"Invalid date: {value}; use YYYY-MM-DD or M.D"
    )


def normalize_text(value: Any, field: str, *, required: bool = False) -> str:
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise DailyReportError("invalid_payload", f"{field} must be a string")
    result = value.strip()
    if required and not result:
        raise DailyReportError("invalid_payload", f"{field} is required")
    return result


def normalize_title_key(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold()


def is_shareable_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def unique_strings(values: Any, field: str) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise DailyReportError("invalid_payload", f"{field} must be an array")
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = normalize_text(raw, field)
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def unique_urls(values: Any, field: str = "urls") -> list[str]:
    return [value for value in unique_strings(values, field) if is_shareable_url(value)]


def is_pull_request_url(value: Any) -> bool:
    if not is_shareable_url(value):
        return False
    path = urlparse(value.strip()).path.rstrip("/")
    return bool(
        re.search(r"/(?:pull|pulls)/\d+$", path)
        or re.search(r"/-/merge_requests/\d+$", path)
    )


def is_commit_url(value: Any) -> bool:
    if not is_shareable_url(value):
        return False
    path = urlparse(value.strip()).path.rstrip("/")
    return bool(re.search(r"/(?:-/)?commit/[0-9A-Za-z._-]+$", path))


def preferred_primary_url(primary_url: Any, urls: Any) -> str | None:
    candidates: list[str] = []
    if is_shareable_url(primary_url):
        candidates.append(primary_url.strip())
    if isinstance(urls, list):
        for value in urls:
            if is_shareable_url(value):
                normalized = value.strip()
                if normalized not in candidates:
                    candidates.append(normalized)
    pull_request = next((value for value in candidates if is_pull_request_url(value)), None)
    return pull_request or (candidates[0] if candidates else None)


def promote_primary_url(item: dict[str, Any]) -> None:
    primary_url = preferred_primary_url(item.get("primary_url"), item.get("urls", []))
    item["primary_url"] = primary_url
    urls = [
        value
        for value in item.get("urls", [])
        if is_shareable_url(value) and value != primary_url
    ]
    item["urls"] = ([primary_url] if primary_url else []) + urls


def pending_pr_links(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    pending: list[dict[str, str]] = []
    for item in items:
        primary_url = preferred_primary_url(
            item.get("primary_url"), item.get("urls", [])
        )
        if primary_url and is_commit_url(primary_url):
            pending.append(
                {
                    "id": str(item.get("id", "")),
                    "title": str(item.get("title", "")),
                    "current_url": primary_url,
                }
            )
    return pending


def default_ledger() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "entries": []}


def default_profile() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "name": None,
        "timezone": "Asia/Shanghai",
    }


def ensure_home(home: Path) -> None:
    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        home.chmod(0o700)
    except OSError:
        pass


@contextlib.contextmanager
def store_lock(home: Path) -> Iterator[None]:
    ensure_home(home)
    lock_path = home / "ledger.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        try:
            lock_path.chmod(0o600)
        except OSError:
            pass
        lock_file.seek(0)
        if lock_file.read(1) == "":
            lock_file.write("0")
            lock_file.flush()
        lock_file.seek(0)
        if fcntl is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        elif msvcrt is not None:  # pragma: no cover - Windows
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
        else:  # pragma: no cover - unknown platform
            raise DailyReportError(
                "lock_unavailable", "No supported file-locking backend is available"
            )
        try:
            yield
        finally:
            lock_file.seek(0)
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            elif msvcrt is not None:  # pragma: no cover - Windows
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)


def load_store(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DailyReportError("corrupt_store", f"Cannot read {path}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise DailyReportError(
            "unsupported_schema", f"Unsupported schema in {path}"
        )
    return data


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    ensure_home(path.parent)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.chmod(0o600)
        os.replace(temp_path, path)
        path.chmod(0o600)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


def load_payload(path_value: str | None, consume: bool) -> dict[str, Any]:
    if not path_value:
        return {}
    path = Path(path_value).expanduser()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise DailyReportError("invalid_payload", "Payload must be a JSON object")
        return data
    except DailyReportError:
        raise
    except (OSError, json.JSONDecodeError) as exc:
        raise DailyReportError("invalid_payload", f"Cannot read payload: {path}") from exc
    finally:
        if consume:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass


def make_entry_id(day: str, thread_id: str) -> str:
    value = uuid.uuid5(ID_NAMESPACE, f"entry|{day}|{thread_id}").hex[:12]
    return f"dre-{value}"


def make_item_id(entry_id: str, title: str, primary_url: str | None) -> str:
    value = uuid.uuid5(
        ID_NAMESPACE,
        f"item|{entry_id}|{normalize_title_key(title)}|{primary_url or ''}",
    ).hex[:12]
    return f"dri-{value}"


def clean_item(
    raw: Any,
    entry_id: str,
    existing_by_title: dict[str, dict[str, Any]],
    existing_by_url: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise DailyReportError("invalid_payload", "Each item must be an object")
    title = normalize_text(raw.get("title"), "title", required=True)
    description = normalize_text(raw.get("description"), "description")
    urls = unique_urls(raw.get("urls", []))
    local_artifacts = unique_strings(raw.get("local_artifacts", []), "local_artifacts")

    primary_raw = raw.get("primary_url")
    primary_url: str | None = None
    if primary_raw is not None:
        primary_text = normalize_text(primary_raw, "primary_url")
        if is_shareable_url(primary_text):
            primary_url = primary_text
        elif primary_text and primary_text not in local_artifacts:
            local_artifacts.append(primary_text)
    if primary_url is None and urls:
        primary_url = urls[0]
    if primary_url and primary_url not in urls:
        urls.insert(0, primary_url)

    normalized_link = {"primary_url": primary_url, "urls": urls}
    promote_primary_url(normalized_link)
    primary_url = normalized_link["primary_url"]
    urls = normalized_link["urls"]

    existing = None
    supplied_id = raw.get("id")
    if isinstance(supplied_id, str):
        for candidate in existing_by_title.values():
            if candidate.get("id") == supplied_id:
                existing = candidate
                break
    if existing is None and primary_url:
        existing = existing_by_url.get(primary_url)
    if existing is None:
        existing = existing_by_title.get(normalize_title_key(title))
    item_id = (
        existing.get("id")
        if isinstance(existing, dict) and isinstance(existing.get("id"), str)
        else make_item_id(entry_id, title, primary_url)
    )

    return {
        "id": item_id,
        "title": title,
        "description": description,
        "primary_url": primary_url,
        "urls": urls,
        "local_artifacts": local_artifacts,
    }


def command_record(home: Path, args: argparse.Namespace) -> dict[str, Any]:
    payload = load_payload(args.payload, args.consume_payload)
    day = normalize_date(payload.get("date"))
    thread_id = normalize_text(payload.get("thread_id"), "thread_id", required=True)
    thread_title = normalize_text(payload.get("thread_title"), "thread_title")
    thread_cwd = normalize_text(payload.get("thread_cwd"), "thread_cwd")
    raw_items = payload.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise DailyReportError("invalid_payload", "items must be a non-empty array")

    with store_lock(home):
        ledger_path = home / "ledger.json"
        ledger = load_store(ledger_path, default_ledger())
        entries = ledger.get("entries")
        if not isinstance(entries, list):
            raise DailyReportError("corrupt_store", "ledger entries must be an array")
        entry_id = make_entry_id(day, thread_id)
        existing_entry = next(
            (
                entry
                for entry in entries
                if entry.get("date") == day and entry.get("thread_id") == thread_id
            ),
            None,
        )
        existing_items = (
            existing_entry.get("items", []) if isinstance(existing_entry, dict) else []
        )
        existing_by_title = {
            normalize_title_key(item.get("title", "")): item
            for item in existing_items
            if isinstance(item, dict) and isinstance(item.get("title"), str)
        }
        existing_by_url = {
            item["primary_url"]: item
            for item in existing_items
            if isinstance(item, dict) and isinstance(item.get("primary_url"), str)
        }
        items = [
            clean_item(raw, entry_id, existing_by_title, existing_by_url)
            for raw in raw_items
        ]
        captured_at = now_shanghai().isoformat(timespec="seconds")
        entry = {
            "id": entry_id,
            "date": day,
            "thread_id": thread_id,
            "thread_title": thread_title,
            "thread_cwd": thread_cwd,
            "captured_at": captured_at,
            "items": items,
        }
        if existing_entry is None:
            entries.append(entry)
            action = "created"
        else:
            entries[entries.index(existing_entry)] = entry
            action = "updated"
        entries.sort(key=lambda value: (value.get("date", ""), value.get("captured_at", "")))
        atomic_write(ledger_path, ledger)

    missing = [item for item in items if not item.get("primary_url")]
    return {
        "status": "ok",
        "action": action,
        "date": day,
        "entry_id": entry_id,
        "items": items,
        "missing_links": [
            {"id": item["id"], "title": item["title"]} for item in missing
        ],
        "pr_links_pending": pending_pr_links(items),
    }


def flatten_day(ledger: dict[str, Any], day: str) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for entry in ledger.get("entries", []):
        if not isinstance(entry, dict) or entry.get("date") != day:
            continue
        for item in entry.get("items", []):
            if not isinstance(item, dict):
                continue
            merged = dict(item)
            merged["thread_id"] = entry.get("thread_id")
            merged["thread_title"] = entry.get("thread_title")
            merged["captured_at"] = entry.get("captured_at")
            promote_primary_url(merged)
            flattened.append(merged)
    return flattened


def command_list(home: Path, args: argparse.Namespace) -> dict[str, Any]:
    day = normalize_date(args.date)
    with store_lock(home):
        ledger = load_store(home / "ledger.json", default_ledger())
        items = flatten_day(ledger, day)
    missing = [item for item in items if not item.get("primary_url")]
    return {
        "status": "ok",
        "date": day,
        "count": len(items),
        "missing_link_count": len(missing),
        "pr_link_pending_count": len(pending_pr_links(items)),
        "pr_links_pending": pending_pr_links(items),
        "items": items,
    }


def find_item(ledger: dict[str, Any], item_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    for entry in ledger.get("entries", []):
        if not isinstance(entry, dict):
            continue
        for item in entry.get("items", []):
            if isinstance(item, dict) and item.get("id") == item_id:
                return entry, item
    raise DailyReportError("item_not_found", f"Item not found: {item_id}")


def command_edit(home: Path, args: argparse.Namespace) -> dict[str, Any]:
    payload = load_payload(args.payload, args.consume_payload)
    allowed = {
        "title",
        "description",
        "primary_url",
        "urls",
        "add_urls",
        "local_artifacts",
        "add_local_artifacts",
    }
    unknown = set(payload) - allowed
    if unknown:
        raise DailyReportError(
            "invalid_payload", f"Unsupported edit fields: {', '.join(sorted(unknown))}"
        )
    if not payload:
        raise DailyReportError("invalid_payload", "Edit payload is empty")

    with store_lock(home):
        ledger_path = home / "ledger.json"
        ledger = load_store(ledger_path, default_ledger())
        _, item = find_item(ledger, args.item_id)

        if "title" in payload:
            item["title"] = normalize_text(payload["title"], "title", required=True)
        if "description" in payload:
            item["description"] = normalize_text(payload["description"], "description")
        if "urls" in payload:
            item["urls"] = unique_urls(payload["urls"])
        if "add_urls" in payload:
            item["urls"] = unique_urls(
                list(item.get("urls", [])) + unique_urls(payload["add_urls"], "add_urls")
            )
        if "local_artifacts" in payload:
            item["local_artifacts"] = unique_strings(
                payload["local_artifacts"], "local_artifacts"
            )
        if "add_local_artifacts" in payload:
            item["local_artifacts"] = unique_strings(
                list(item.get("local_artifacts", []))
                + unique_strings(payload["add_local_artifacts"], "add_local_artifacts"),
                "local_artifacts",
            )
        if "primary_url" in payload:
            raw_url = payload["primary_url"]
            if raw_url is None or raw_url == "":
                item["primary_url"] = None
            else:
                url = normalize_text(raw_url, "primary_url", required=True)
                if not is_shareable_url(url):
                    raise DailyReportError(
                        "invalid_url", "primary_url must be an http(s) URL"
                    )
                item["primary_url"] = url
                if url not in item.get("urls", []):
                    item.setdefault("urls", []).insert(0, url)
        promote_primary_url(item)

        atomic_write(ledger_path, ledger)
        updated = dict(item)

    return {
        "status": "ok",
        "item": updated,
        "missing_link": not bool(updated.get("primary_url")),
        "pr_link_pending": bool(pending_pr_links([updated])),
    }


def command_remove(home: Path, args: argparse.Namespace) -> dict[str, Any]:
    with store_lock(home):
        ledger_path = home / "ledger.json"
        ledger = load_store(ledger_path, default_ledger())
        entry, item = find_item(ledger, args.item_id)
        entry["items"].remove(item)
        if not entry["items"]:
            ledger["entries"].remove(entry)
        atomic_write(ledger_path, ledger)
    return {"status": "ok", "removed": item}


def command_setup(home: Path, args: argparse.Namespace) -> dict[str, Any]:
    payload = load_payload(args.payload, args.consume_payload)
    name = normalize_text(payload.get("name"), "name", required=True)
    if "\n" in name or "\r" in name or len(name) > 80:
        raise DailyReportError("invalid_name", "name must be one line and at most 80 characters")
    with store_lock(home):
        profile_path = home / "profile.json"
        profile = load_store(profile_path, default_profile())
        profile["name"] = name
        profile["timezone"] = "Asia/Shanghai"
        atomic_write(profile_path, profile)
    return {"status": "ok", "profile": profile}


def clean_tomorrow_plan(values: Any) -> list[str]:
    items = unique_strings(values, "tomorrow_plan")
    result: list[str] = []
    seen: set[str] = set()
    for value in items:
        cleaned = re.sub(r"^\s*[-*•]\s*", "", value).strip()
        key = normalize_title_key(cleaned)
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        primary = item.get("primary_url")
        key = f"url:{primary}" if primary else f"title:{normalize_title_key(item.get('title', ''))}"
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def command_generate(home: Path, args: argparse.Namespace) -> dict[str, Any]:
    payload = load_payload(args.payload, args.consume_payload)
    day = normalize_date(args.date)
    tomorrow_plan = clean_tomorrow_plan(payload.get("tomorrow_plan", []))
    with store_lock(home):
        profile = load_store(home / "profile.json", default_profile())
        name = profile.get("name")
        if not isinstance(name, str) or not name.strip():
            raise DailyReportError(
                "name_required", "Configure a name before generating the report"
            )
        ledger = load_store(home / "ledger.json", default_ledger())
        items = dedupe_items(flatten_day(ledger, day))
    if not items:
        raise DailyReportError("no_entries", f"No recorded work for {day}", date=day)

    parsed_day = date.fromisoformat(day)
    display_date = f"{parsed_day.month}.{parsed_day.day}"
    titles = [item["title"] for item in items]
    lines = [f"{name.strip()} {display_date} 日报", f"今日完成：{'、'.join(titles)}"]
    for item in items:
        link = item.get("primary_url") or "链接待补"
        lines.append(f"- {item['title']}：{link}")
    if tomorrow_plan:
        lines.append("明日计划：")
        lines.extend(f"- {item}" for item in tomorrow_plan)
    missing = [item for item in items if not item.get("primary_url")]
    return {
        "status": "ok",
        "date": day,
        "report": "\n".join(lines),
        "missing_links": [
            {"id": item["id"], "title": item["title"]} for item in missing
        ],
        "pr_links_pending": pending_pr_links(items),
        "tomorrow_plan": tomorrow_plan,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--home",
        default=str(DEFAULT_HOME),
        help="Ledger directory; defaults to the platform application-data directory",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    record = subparsers.add_parser("record")
    record.add_argument("--payload", required=True)
    record.add_argument("--consume-payload", action="store_true")

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--date")

    edit = subparsers.add_parser("edit")
    edit.add_argument("item_id")
    edit.add_argument("--payload", required=True)
    edit.add_argument("--consume-payload", action="store_true")

    remove = subparsers.add_parser("remove")
    remove.add_argument("item_id")

    setup = subparsers.add_parser("setup")
    setup.add_argument("--payload", required=True)
    setup.add_argument("--consume-payload", action="store_true")

    generate = subparsers.add_parser("generate")
    generate.add_argument("--date")
    generate.add_argument("--payload")
    generate.add_argument("--consume-payload", action="store_true")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    home = Path(args.home).expanduser()
    commands = {
        "record": command_record,
        "list": command_list,
        "edit": command_edit,
        "remove": command_remove,
        "setup": command_setup,
        "generate": command_generate,
    }
    try:
        result = commands[args.command](home, args)
        return emit(result)
    except DailyReportError as exc:
        return emit(
            {
                "status": "error",
                "error": exc.code,
                "message": exc.message,
                **exc.details,
            },
            exit_code=2,
        )
    except Exception as exc:  # Keep unexpected failures structured for the skill.
        return emit(
            {
                "status": "error",
                "error": "unexpected_error",
                "message": str(exc),
            },
            exit_code=3,
        )


if __name__ == "__main__":
    sys.exit(main())
