from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


MANUAL_TERMS = {
    "Limgrave": "Замогилье",
    "Liurnia": "Лиурния",
    "Caelid": "Кэлид",
    "Altus": "Альтус",
    "Leyndell": "Лейнделл",
    "Roundtable Hold": "Крепость Круглого стола",
    "Lands Between": "Междуземье",
    "Site of Grace": "место благодати",
    "grace": "благодать",
    "runes": "руны",
    "rune": "руна",
    "DLC": "DLC",
    "NG+": "NG+",
}

SECTION_TERMS = {
    "Tutorial": "Обучение",
    "First steps in Limgrave": "Первые шаги в Замогилье",
    "West Limgrave": "Западное Замогилье",
    "North Limgrave": "Северное Замогилье",
    "Weeping Peninsula": "Плачущий полуостров",
    "Castle Morne": "Замок Морн",
    "Stormveil Castle": "Замок Грозовой Завесы",
    "Fringefolk Hero's Grave": "Могила героя окраин",
    "South Liurnia": "Южная Лиурния",
    "West Liurnia": "Западная Лиурния",
    "Central Liurnia": "Центральная Лиурния",
    "Academy of Raya Lucaria": "Академия Райи Лукарии",
    "East Liurnia": "Восточная Лиурния",
    "Caria Manor": "Поместье Кария",
    "Ruin-Strewn Precipice": "Усыпанный руинами обрыв",
    "Ainsel River": "Река Ансель",
    "Siofra River": "Река Сиофра",
    "Sellia": "Селлия",
    "Redmane Castle": "Замок Рыжей Гривы",
    "Nokron": "Нокрон",
    "Carian Study Hall": "Карианский читальный зал",
    "Deeproot Depths": "Низовье Глубокого Корня",
    "Nokstella": "Нокстелла",
    "Lake of Rot": "Озеро гнили",
    "Moonlight Altar": "Алтарь лунного света",
    "West Altus": "Западный Альтус",
    "The Shaded Castle": "Сумрачный замок",
    "Central Altus": "Центральный Альтус",
    "East Altus": "Восточный Альтус",
    "Mt. Gelmir": "Вулкан Гельмир",
    "Volcano Manor": "Вулканово поместье",
    "Capital Outskirts": "Окраины столицы",
    "Leyndell, Royal Capital": "Лейнделл, столица королевства",
    "Subterranean Shunning-Grounds": "Подземелье отчуждения",
    "Forbidden Lands": "Запретные земли",
    "West Mountaintops": "Западные Вершины великанов",
    "Castle Sol": "Замок Сол",
    "East Mountaintops": "Восточные Вершины великанов",
    "Greyoll's Dragonbarrow": "Драконий курган Грейолл",
    "Consecrated Snowfield": "Священное заснеженное поле",
    "Mohgwyn Palace": "Дворец Могвинов",
    "Miquella's Haligtree": "Святое Древо Микеллы",
    "Elphael, Brace of the Haligtree": "Эльфаэль, опора Святого Древа",
    "Crumbling Farum Azula": "Разрушающийся Фарум-Азула",
    "Leyndell, Ashen Capital": "Лейнделл, столица пепла",
    "Endings": "Концовки",
    "New Game Plus Preparation": "Подготовка к Новой игре+",
}


def load_route(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"window\.ROUTE_DATA\s*=\s*(.*);\s*$", text, flags=re.S)
    if not match:
        raise ValueError("route-data.js does not contain window.ROUTE_DATA")
    return json.loads(match.group(1))


def write_route(path: Path, data: dict[str, Any]) -> None:
    path.write_text("window.ROUTE_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


def page_title_from_markdown(path: Path) -> str:
    name = re.sub(r"__\d+\.md$", "", path.name)
    return name.replace("_", ":")


def build_wiki_glossary(wiki_pages: Path, terms: set[str]) -> dict[str, str]:
    glossary = dict(MANUAL_TERMS)
    normalized_terms = {normalize(term): term for term in terms if term and len(term) > 2}
    candidates: dict[str, str] = {}

    for path in wiki_pages.glob("*.md"):
        title = page_title_from_markdown(path)
        try:
            sample = path.read_text(encoding="utf-8", errors="ignore")[:2400]
        except OSError:
            continue

        # The markdown often contains a short parenthetical original title:
        # "(англ. Ranni's Rise)" or, when console displays mojibake, still "... Ranni's Rise".
        for match in re.finditer(r"\(([^\)]{0,40}?)([A-Z][A-Za-z0-9][A-Za-z0-9 '\-:!,\[\]&.]+)\)", sample):
            english = match.group(2).strip(" .")
            if 2 < len(english) < 80:
                candidates.setdefault(normalize(english), title)

    for normalized, original in normalized_terms.items():
        if normalized in candidates:
            glossary[original] = candidates[normalized]

    return glossary


def normalize(value: str) -> str:
    value = re.sub(r"\s+x\d+$", "", value.strip(), flags=re.I)
    return re.sub(r"\s+", " ", value).casefold()


def collect_link_terms_from_html(path: Path) -> set[str]:
    html = path.read_text(encoding="utf-8", errors="replace")
    terms = set()
    for match in re.finditer(r"<a\b[^>]*>(.*?)</a>", html, flags=re.I | re.S):
        text = strip_html(match.group(1))
        text = re.sub(r"\s+x\d+$", "", text)
        if text and re.search(r"[A-Za-z]", text):
            terms.add(text)
    return terms


def strip_html(fragment: str) -> str:
    fragment = re.sub(r"<[^>]+>", "", fragment)
    fragment = fragment.replace("&nbsp;", " ")
    return urllib.parse.unquote(re.sub(r"\s+", " ", html_unescape(fragment)).strip())


def html_unescape(value: str) -> str:
    import html

    return html.unescape(value)


def protect_terms(text: str, glossary: dict[str, str]) -> tuple[str, dict[str, str]]:
    replacements: dict[str, str] = {}
    protected = text
    terms = sorted(glossary, key=len, reverse=True)
    index = 0
    for term in terms:
        if not term or term not in protected:
            continue
        token = f"ZXQ{index:04d}"
        pattern = re.compile(rf"(?<![A-Za-z]){re.escape(term)}(?![A-Za-z])")
        protected, count = pattern.subn(token, protected)
        if count:
            replacements[token] = glossary[term]
            index += 1
    return protected, replacements


def restore_terms(text: str, replacements: dict[str, str]) -> str:
    restored = text
    for token, value in replacements.items():
        restored = re.sub(rf"\b{re.escape(token)}\b", value, restored, flags=re.I)
    return restored


def translate_google(texts: list[str], delay: float, cache_path: Path) -> list[str]:
    if cache_path.exists():
        cache: dict[str, str] = json.loads(cache_path.read_text(encoding="utf-8"))
    else:
        cache = {}

    out: list[str] = []
    for i, text in enumerate(texts, start=1):
        if not text:
            out.append(text)
            continue
        if text in cache:
            out.append(cache[text])
            continue
        query = urllib.parse.urlencode({"client": "gtx", "sl": "en", "tl": "ru", "dt": "t", "q": text})
        url = f"https://translate.googleapis.com/translate_a/single?{query}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        translated = "".join(part[0] for part in data[0] if part and part[0])
        cache[text] = translated
        if i % 25 == 0:
            cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
        out.append(translated)
        if i % 100 == 0:
            print(f"translated {i}/{len(texts)}", flush=True)
        if delay:
            time.sleep(delay)
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def polish(text: str) -> str:
    replacements = {
        "Необязательный:": "Опционально:",
        "Необязательно:": "Опционально:",
        "Пропустить:": "Пропускаемое:",
        "Пропускаемый:": "Пропускаемое:",
        "Примечание:": "Заметка:",
        "Поговорите с": "Поговори с",
        "Возьмите": "Возьми",
        "Подберите": "Подбери",
        "Активируйте": "Активируй",
        "Убейте": "Убей",
        "Победите": "Победи",
        "Купите": "Купи",
        "Вернитесь": "Вернись",
        "Отправляйтесь": "Отправляйся",
        "Продолжайте": "Продолжай",
    }
    polished = text
    for src, dst in replacements.items():
        polished = polished.replace(src, dst)
    return polished


def main() -> None:
    parser = argparse.ArgumentParser(description="Translate imported route data to Russian with wiki-aware terminology.")
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--wiki-pages", type=Path, required=True)
    parser.add_argument("--delay", type=float, default=0.04)
    parser.add_argument("--cache", type=Path)
    args = parser.parse_args()

    route = load_route(args.route)
    glossary = build_wiki_glossary(args.wiki_pages, collect_link_terms_from_html(args.html))

    jobs: list[tuple[dict[str, Any], str, dict[str, str]]] = []
    for section in route["sections"]:
        section["title"] = SECTION_TERMS.get(section["title"], section["title"])
        section["region"] = SECTION_TERMS.get(section.get("region", ""), section.get("region", ""))
        for step in section["steps"]:
            protected, replacements = protect_terms(step["text"], glossary)
            jobs.append((step, protected, replacements))

    cache_path = args.cache or args.route.with_suffix(".translation-cache.json")
    translated = translate_google([job[1] for job in jobs], args.delay, cache_path)
    for (step, _protected, replacements), text in zip(jobs, translated):
        step["text"] = polish(restore_terms(text, replacements))

    route.setdefault("source", {})["translated"] = "ru"
    route["source"]["translationGlossarySize"] = len(glossary)
    route["source"]["translationNote"] = "Machine translated to Russian with local wiki title protection."
    write_route(args.route, route)
    print(f"translated {len(jobs)} steps with {len(glossary)} protected terms")


if __name__ == "__main__":
    main()
