from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


TAGS = [
    {"id": "all", "label": "Все"},
    {"id": "main", "label": "Сюжет"},
    {"id": "loot", "label": "Лут"},
    {"id": "npc", "label": "NPC"},
    {"id": "boss", "label": "Боссы"},
    {"id": "missable", "label": "Пропускаемое"},
    {"id": "optional", "label": "Опционально"},
    {"id": "achievement", "label": "Достижения"},
]


def clean_text(fragment: str) -> str:
    fragment = re.sub(r"<input\b[^>]*>", "", fragment, flags=re.I)
    fragment = re.sub(r"<script\b[^>]*>.*?</script>", "", fragment, flags=re.I | re.S)
    fragment = re.sub(r"<style\b[^>]*>.*?</style>", "", fragment, flags=re.I | re.S)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    fragment = html.unescape(fragment)
    fragment = fragment.replace("\xa0", " ")
    fragment = re.sub(r"\s+", " ", fragment)
    return fragment.strip()


def section_title_from_h3(line: str) -> tuple[str, str]:
    section_id = re.search(r'<h3\s+id="([^"]+)"', line, flags=re.I)
    title = clean_text(line)
    title = re.sub(r"^Toggle\s+", "", title)
    title = re.sub(r"DONE$", "", title).strip()
    title = re.sub(r"\d+\s*/\s*\d+$", "", title).strip()
    return section_id.group(1) if section_id else slugify(title), title


def split_level(title: str) -> tuple[str, str]:
    match = re.search(r"\((Levels? [^)]+)\)", title)
    if not match:
        return title.strip(), ""
    clean = (title[: match.start()] + title[match.end() :]).strip()
    level = match.group(1).replace("Levels ", "").replace("Level ", "")
    return clean, level


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9а-яё]+", "-", value, flags=re.I)
    return value.strip("-") or "section"


def infer_tags(text: str) -> list[str]:
    lower = text.lower()
    tags: set[str] = set()

    if "missable" in lower:
        tags.add("missable")
    if lower.startswith("optional:") or " optional:" in lower:
        tags.add("optional")
    if "🏆" in text:
        tags.add("achievement")
    if re.search(r"\b(talk|meet|exhaust|dialogue|quest|varre|melina|ranni|alexander|fia|gideon|millicent|tanith)\b", lower):
        tags.add("npc")
    if re.search(r"\b(defeat|kill|boss|invader|dragon|erdtree avatar|night's cavalry|deathbird)\b", lower):
        tags.add("boss")
    if re.search(r"\b(pick up|grab|loot|obtain|purchase|buy|receive|chest|corpse|cookbook|talisman|smithing stone|golden rune|sacred tear|golden seed)\b", lower):
        tags.add("loot")

    if "optional" not in tags:
        tags.add("main")
    return sorted(tags, key=["main", "loot", "npc", "boss", "missable", "optional", "achievement"].index)


def parse_walkthrough(path: Path) -> dict:
    sections: list[dict] = []
    current: dict | None = None

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if line.startswith("<h3 "):
            section_id, title = section_title_from_h3(line)
            title, level = split_level(title)
            current = {
                "id": section_id,
                "title": title,
                "level": level,
                "region": title,
                "steps": [],
            }
            sections.append(current)
            continue

        if current is None or "<label" not in line or "<input" not in line:
            continue

        id_match = re.search(r'<input\s+type="checkbox"\s+id="([^"]+)"', line, flags=re.I)
        label_match = re.search(r"<label\b[^>]*>(.*?)</label>", line, flags=re.I | re.S)
        if not label_match:
            continue

        text = clean_text(label_match.group(1))
        if not text:
            continue

        current["steps"].append(
            {
                "sourceId": id_match.group(1) if id_match else f"{current['id']}-{len(current['steps']) + 1}",
                "text": text,
                "tags": infer_tags(text),
            }
        )

    sections = [section for section in sections if section["steps"]]
    return {
        "source": {
            "name": "Walkthrough.html",
            "path": str(path),
            "importedFrom": "https://eldenring.redmaw.dev/sheets/walkthrough",
        },
        "tags": TAGS,
        "sections": sections,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a saved Redmaw walkthrough HTML file.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    data = parse_walkthrough(args.input)
    payload = "window.ROUTE_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    args.output.write_text(payload, encoding="utf-8")

    step_count = sum(len(section["steps"]) for section in data["sections"])
    print(f"Imported {len(data['sections'])} sections and {step_count} steps")


if __name__ == "__main__":
    main()
