"""Classify Arabic court judgment outcomes."""

from __future__ import annotations

import re
from typing import Any


def normalize_arabic_text(value: Any) -> str:
    """Normalize Arabic text before classification."""

    if value is None:
        return ""

    if isinstance(value, (list, tuple)):
        value = " ".join(
            str(item)
            for item in value
            if item is not None
        )

    text = str(value).strip()

    # Remove Arabic diacritics and tatweel.
    text = re.sub(
        r"[\u064B-\u065F\u0670\u0640]",
        "",
        text,
    )

    # Normalize common Arabic letter variations.
    text = re.sub(r"[أإآ]", "ا", text)
    text = text.replace("ى", "ي")

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text)

    return text


def classify_outcome(verdict: Any) -> str:
    """
    Classify a judgment outcome.

    Possible categories:
        - accepted
        - rejected
        - inadmissible
        - settlement
        - no_jurisdiction
        - other
    """

    text = normalize_arabic_text(verdict)

    if not text:
        return "other"

    # Settlement.
    if any(
        phrase in text
        for phrase in (
            "اثبات الصلح",
            "تصالح الطرفان",
            "اتفاق الطرفين علي الصلح",
            "اتفاق الطرفين على الصلح",
            "الصلح المبرم",
            "اثبات اتفاق الصلح",
        )
    ):
        return "settlement"

    # Lack of jurisdiction.
    if any(
        phrase in text
        for phrase in (
            "عدم الاختصاص",
            "بعدم اختصاص",
            "غير مختصه",
            "غير مختصة",
            "غير مختص",
        )
    ):
        return "no_jurisdiction"

    # Inadmissibility.
    if any(
        phrase in text
        for phrase in (
            "عدم قبول الدعوي",
            "عدم قبول الدعوى",
            "بعدم قبول الدعوي",
            "بعدم قبول الدعوى",
            "عدم قبول الطلب",
            "بعدم قبول الطلب",
        )
    ):
        return "inadmissible"

    # Accepted / granted.
    accepted_patterns = (
        "الزام المدعي عليه",
        "الزام المدعي عليها",
        "الزام المدعى عليه",
        "الزام المدعى عليها",
        "الزمت المحكمه",
        "الزمت المحكمة",
        "الزمت الدائره",
        "الزمت الدائرة",
        "استحقاق المدعي",
        "الحكم للمدعي",
        "الحكم للمدعية",
        "ثبوت استحقاق المدعي",
        "ثبوت استحقاق المدعية",
        "اجابة طلب المدعي",
        "اجابة طلب المدعية",
        "قبول الدعوي",
        "قبول الدعوى",
        "قبول الطلب",
    )

    # Rejected / denied.
    rejected_patterns = (
        "رفض الدعوي",
        "رفض الدعوى",
        "برفض الدعوي",
        "برفض الدعوى",
        "رد الدعوي",
        "رد الدعوى",
        "رفض الطلب",
        "برفض الطلب",
        "عدم ثبوت استحقاق المدعي",
        "عدم ثبوت استحقاق المدعية",
    )

    has_accepted = any(
        phrase in text
        for phrase in accepted_patterns
    )

    has_rejected = any(
        phrase in text
        for phrase in rejected_patterns
    )

    # If the judgment grants the claim/request,
    # classify it as accepted.
    if has_accepted:
        return "accepted"

    # If the judgment explicitly rejects the claim/request,
    # classify it as rejected.
    if has_rejected:
        return "rejected"

    return "other"


if __name__ == "__main__":
    test_verdicts = [
        (
            "إثبات الصلح المبرم بين الطرفين "
            "وإلزامهما بما ورد فيه."
        ),
        (
            "حكمت المحكمة بعدم اختصاصها "
            "بنظر الدعوى."
        ),
        (
            "حكمت الدائرة بعدم قبول الدعوى."
        ),
        (
            "حكمت المحكمة برفض الدعوى."
        ),
        (
            "إلزام المدعى عليها بسداد مبلغ "
            "100,000 ريال."
        ),
        (
            "حكمت المحكمة بقبول الطلب."
        ),
        "",
        None,
    ]

    print("Testing outcome classifier...")
    print("=" * 60)

    for verdict in test_verdicts:
        category = classify_outcome(verdict)

        print(f"Verdict: {verdict}")
        print(f"Category: {category}")
        print("-" * 60)
