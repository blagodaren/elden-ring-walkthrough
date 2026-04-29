from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTE_DATA = ROOT / "data" / "route-data.js"

TRANSLATIONS = [
    "Выбери любой класс. Если сомневаешься, хорошими стартовыми вариантами будут Бродяга или Самурай: у них удобные характеристики для большинства билдов.",
    "Из стартовых реликвий самые ценные — Руна Междуземья (уникальная) и Прах клыкастых бесов (нужен для одной загадки). Новичкам также поможет Золотое семечко в первых двух разделах. Мечевидные ключи лучше не брать: маршрут построен так, что они не понадобятся.",
    "Начни прохождение и посмотри вступительный ролик.",
    "Опционально: если играешь онлайн, можно добавить до пяти групповых паролей с учётом регистра. Знаки призыва, сообщения и пятна крови участников группы будут подсвечиваться, фантомы игроков станут золотыми, а за победу участника группы над Носителем осколка или становление Элден-лордом ты получишь суммируемый бонус 5% к рунам. Пароль группы сайта: ERSHEET.",
    "Жест «Кольцо» выдаётся автоматически, если у тебя был предзаказ игры.",
    "Жест «Кольцо Микеллы» так же выдаётся за предзаказ DLC.",
    "Подбери Ссохшийся палец Погасшего у мёртвой служанки.",
    "Выйди из часовни и погибни в бою с Привитым отпрыском.",
    "После возрождения в пещере спрыгни в отверстие и активируй место благодати «Пещера знаний».",
    "В самой пещере нет предметов. Пройди обучение и убей Солдата Годрика, чтобы получить 400 рун.",
    "Перед тем как спрыгнуть вниз, подбери жест «Сила!».",
    "За дверью активируй место благодати «Плавучее кладбище».",
    "Подбери Отсекатель пальцев и Скрюченный палец Погасшего с тела в углу.",
    "Поднимись на лифте и выйди в Замогилье.",
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
    section = data["sections"][0]
    section["title"] = "Обучение"
    section["region"] = "Часовня ожидания"
    section["level"] = "1"

    if len(section["steps"]) != len(TRANSLATIONS):
        raise RuntimeError(f"Expected {len(TRANSLATIONS)} tutorial steps, found {len(section['steps'])}")

    for step, text in zip(section["steps"], TRANSLATIONS):
        step["text"] = text
        step["translatedBy"] = "gpt-section-v1"

    data.setdefault("source", {})["sectionTranslation"] = "tutorial:gpt-section-v1"
    save_route(data)
    print("Updated tutorial section with GPT translation")


if __name__ == "__main__":
    main()
