"""Classify the final outcome of Arabic court judgments."""

from __future__ import annotations

import re
from typing import Any


def normalize_arabic_text(value: Any) -> str:
    """Convert a judgment value into normalized Arabic text."""
    if value is None:
        return ""

    if isinstance(value, (list, tuple)):
        value = " ".join(str(item) for item in value if item)

    text = str(value).strip()

    # Remove Arabic diacritics and tatweel
    text = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", text)

    # Normalize common Arabic letter variations
    text = re.sub(r"[أإآ]", "ا", text)
    text = text.replace("ى", "ي")

    # Normalize spaces
    text = re.sub(r"\s+", " ", text)

    return text


def classify_outcome(verdict: Any) -> str:
    """
    Classify a judgment outcome into one of:
    accepted, rejected, inadmissible, settlement,
    no_jurisdiction, or other.
    """
    text = normalize_arabic_text(verdict)

    if not text:
        return "other"

    # Settlement must be checked before accepted,
    # because settlement judgments may also include "إلزام".
    if any(
        phrase in text
        for phrase in (
            "اثبات الصلح",
            "تصالح الطرفان",
            "اتفاق الطرفين علي الصلح",
            "الصلح المبرم",
        )
    ):
        return "settlement"

    if any(
        phrase in text
        for phrase in (
            "عدم الاختصاص",
            "بعدم اختصاص",
            "غير مختصه",
            "غير مختصة",
        )
    ):
        return "no_jurisdiction"

    if any(
        phrase in text
        for phrase in (
            "عدم قبول الدعوي",
            "بعدم قبول الدعوي",
            "عدم قبول الطلب",
        )
    ):
        return "inadmissible"

    accepted_patterns = (
        "الزام المدعي عليه",
        "الزام المدعي عليها",
        "الزمت المحكمه",
        "الزمت الدائره",
        "استحقاق المدعي",
        "الحكم للمدعي",
    )

    rejected_patterns = (
        "رفض الدعوي",
        "برفض الدعوي",
        "رد الدعوي",
        "رفض الطلب",
        "برفض الطلب",
    )

    has_accepted = any(
        phrase in text
        for phrase in accepted_patterns
    )

    has_rejected = any(
        phrase in text
        for phrase in rejected_patterns
    )

    # Some judgments grant part of the claim
    # and reject the remaining requests.
    if has_accepted:
        return "accepted"

    if has_rejected:
        return "rejected"

    return "other"


if __name__ == "__main__":
    test_verdicts = [
        "إثبات الصلح المبرم بين الطرفين وإلزامهما بما ورد فيه.",
        "حكمت المحكمة بعدم اختصاصها بنظر الدعوى.",
        "حكمت الدائرة بعدم قبول الدعوى.",
        "حكمت المحكمة برفض الدعوى.",
        "إلزام المدعى عليها بسداد مبلغ 100,000 ريال.",
        "",
    ]

    for verdict in test_verdicts:
        print(verdict)
        print("=>", classify_outcome(verdict))
        print("-" * 50)
