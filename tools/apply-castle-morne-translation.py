from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTE_DATA = ROOT / "data" / "route-data.js"

TRANSLATIONS = [
    "После лифта поднимись по лестнице слева и подбери Кузнечный камень [2].",
    "Слева от дерева в юго-западной части области лежит тело с 3 Кузнечными камнями [1].",
    "Подбери 2 Огненные смазки на выступе рядом с горой тел во дворе.",
    "Зайди в комнату, доступную с выступа: в сундуке у входа лежит Клеймор.",
    "Спустись по лестнице и поднимись по стремянке. На бастионе найдёшь Средство от призывающего пальца и Факел со стальной проволокой.",
    "Поднимись по лестнице на бастионе, затем спрыгни вниз и подбери Золотую руну [2], свисающую с края моста.",
    "Справа за мостом есть лестница, ведущая к телу с 2 Кузнечными камнями [2].",
    "Спустись по лестнице слева за мостом и подбери Золотую руну [2] рядом со сражающимися врагами.",
    "Поднимись по деревянной лестнице и поговори с Эдгаром, чтобы получить Жертвенную ветвь, затем передай ему Письмо Ирины.",
    "Вернись вниз, наступи на кирпичные обломки в конце бастиона и перепрыгни через ограду, чтобы открыть место благодати «За замком».",
    "Спрыгни на верх бастиона, затем спрыгни на юго-запад и приземлись на деревянную платформу с Мечевидным ключом.",
    "Войди в комнату ниже и найди тело с Маринованной черепашьей шеей.",
    "Поднимись по лестнице за мостом и открой сундук с Талисманом парного клинка.",
    "Спрыгни на крышу под мостом и подбери 3 Поблёкших золотых подсолнуха рядом с деревом.",
    "Продолжай спускаться, пока не выйдешь на платформу замка, затем спрыгни в дыру на деревянную балку и подбери Кузнечный камень [2].",
    "В комнате внизу лежит тело с Кнутом.",
    "Снаружи комнаты поверни налево и открой место благодати «У тюрьмы бастиона».",
    "Перейди деревянный мост и подбери 8 Метательных кинжалов.",
    "Спустись по лестнице, затем обойди строение сбоку и найди Кузнечный камень мрака [1].",
    "В узком проходе к северу-северо-востоку от лестницы лежит тело с 15 Огненными стрелами.",
    "🏆 Убей бастарда Леонина, чтобы получить Двуручник с гибридным клинком и 3800 рун.",
    "Опционально: знак призыва Эдгара находится перед входом, если ты передал ему Письмо Ирины.",
    "На арене нет предметов, так что просто активируй место благодати «Плачущая могила Морна».",
    "Опционально: вернись к Эдгару и исчерпай его диалог.",
    "Переместись к Мосту жертвоприношения и поговори с Эдгаром рядом с телом Ирины.",
]


def load_route() -> dict:
    text = ROUTE_DATA.read_text(encoding="utf-8")
    match = re.search(r"window\.ROUTE_DATA\s*=\s*(.*);\s*$", text, re.S)
    if not match:
        raise RuntimeError("Could not parse route-data.js")
    return json.loads(match.group(1))


def save_route(data: dict) -> None:
    ROUTE_DATA.write_text("window.ROUTE_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


def main() -> None:
    data = load_route()
    section = data["sections"][6]
    if section["id"] != "castle-morne":
        raise RuntimeError(f"Expected castle-morne section, got {section['id']}")
    if len(section["steps"]) != len(TRANSLATIONS):
        raise RuntimeError(f"Expected {len(TRANSLATIONS)} steps, got {len(section['steps'])}")

    section["title"] = "Замок Морн"
    section["region"] = "Эдгар, Бок, бастард Леонин"
    section["level"] = "35-40"

    for step, text in zip(section["steps"], TRANSLATIONS):
        step["text"] = text
        step["translatedBy"] = "gpt-section-v7"

    data.setdefault("source", {})["sectionTranslation"] = (
        "tutorial:gpt-section-v1;first-steps:gpt-section-v2;"
        "early-liurnia:gpt-section-v3;west-limgrave:gpt-section-v4;"
        "north-limgrave:gpt-section-v5;weeping-peninsula:gpt-section-v6;"
        "castle-morne:gpt-section-v7"
    )
    save_route(data)
    print(f"Updated castle-morne section: {len(section['steps'])} steps")


if __name__ == "__main__":
    main()
