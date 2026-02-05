from __future__ import annotations

from typing import Dict, List, Optional


STAGES: List[Dict] = [
    {
        "title": "Введение в курс",
        "videos": [
            {
                "title": "Как будет проходить обучение",
                "url": "https://youtu.be/5qap5aO4i9A",
            },
            {
                "title": "Организация подготовки",
                "url": "https://youtu.be/2Vv-BfVoq4g",
            },
        ],
        "questions": [
            {
                "text": "Сколько этапов в курсе?",
                "options": ["2", "3", "4", "5"],
            },
            {
                "text": "Как лучше смотреть уроки?",
                "options": [
                    "В записи",
                    "В прямом эфире",
                    "В Telegram",
                    "На сайте",
                ],
            },
        ],
    },
    {
        "title": "Базовые темы",
        "videos": [
            {
                "title": "Основные понятия",
                "url": "https://youtu.be/9bZkp7q19f0",
            },
            {
                "title": "Типичные ошибки абитуриентов",
                "url": "https://youtu.be/3JZ_D3ELwOQ",
            },
        ],
        "questions": [
            {
                "text": "Что нужно сделать в первую очередь?",
                "options": [
                    "Изучить программу",
                    "Сдать экзамен",
                    "Найти репетитора",
                    "Не знаю",
                ],
            }
        ],
    },
]


def get_stage_count() -> int:
    return len(STAGES)


def get_stage(index: int) -> Optional[Dict]:
    if 0 <= index < len(STAGES):
        return STAGES[index]
    return None


def get_question_count(stage_index: int) -> int:
    stage = get_stage(stage_index)
    if not stage:
        return 0
    return len(stage["questions"])


def get_question(stage_index: int, question_index: int) -> Optional[Dict]:
    stage = get_stage(stage_index)
    if not stage:
        return None
    if 0 <= question_index < len(stage["questions"]):
        return stage["questions"][question_index]
    return None
