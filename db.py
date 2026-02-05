from __future__ import annotations

from typing import Dict, List

import sheets

_data: Dict[int, Dict] = {}


def init() -> None:
    pass


def _default_state() -> Dict:
    return {
        "paid": False,
        "pending": False,
        "stage": 0,
        "question": 0,
        "answers": [],
    }


def ensure_user(chat_id: int) -> None:
    if chat_id not in _data:
        _data[chat_id] = _default_state()


def reset_state(chat_id: int) -> None:
    _data[chat_id] = _default_state()


def get_state(chat_id: int) -> Dict:
    ensure_user(chat_id)
    return _data[chat_id]


def set_paid(chat_id: int, value: bool) -> None:
    ensure_user(chat_id)
    _data[chat_id]["paid"] = value


def set_pending(chat_id: int, value: bool) -> None:
    ensure_user(chat_id)
    _data[chat_id]["pending"] = value


def set_stage(chat_id: int, stage_index: int) -> None:
    ensure_user(chat_id)
    _data[chat_id]["stage"] = stage_index
    _data[chat_id]["question"] = 0
    _data[chat_id]["answers"] = []


def set_question(chat_id: int, question_index: int) -> None:
    ensure_user(chat_id)
    _data[chat_id]["question"] = question_index


def save_answer(chat_id: int, answer_index: int) -> None:
    ensure_user(chat_id)
    _data[chat_id]["answers"].append(answer_index)


def advance_question(chat_id: int) -> int | None:
    ensure_user(chat_id)
    state = _data[chat_id]
    total_questions = sheets.get_question_count(state["stage"])
    next_question = state["question"] + 1
    if next_question >= total_questions:
        return None
    state["question"] = next_question
    return next_question
