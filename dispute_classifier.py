"""Transparent, multi-label dispute classification for ArabiCCR judgments."""

from __future__ import annotations

import re
from collections.abc import Iterable


DISPUTE_LABELS = {
    "supply_sale": "توريد وبيع",
    "construction": "مقاولات وإنشاءات",
    "financial_claims": "مطالبات مالية وديون",
    "companies_partnerships": "شركات وشراكات",
    "damages": "تعويض عن أضرار",
    "commercial_lease": "إيجار تجاري",
    "commercial_papers": "أوراق تجارية",
    "transport_shipping": "نقل وشحن",
    "commercial_agency": "وكالات وامتياز تجاري",
    "intellectual_property": "ملكية فكرية",
    "bankruptcy": "إفلاس وتصفية",
    "other": "نزاع تجاري آخر",
}


_PATTERNS = {
    "supply_sale": (
        r"\bتوريد\b", r"\bالمور[ّ]?د\b", r"\bالموردة\b",
        r"\bعقد بيع\b", r"\bبيع (?:بضاعة|بضائع|منتجات|سلع)\b",
        r"\bثمن (?:البضاعة|البضائع|المبيع)\b",
    ),
    "construction": (
        r"\bمقاول(?:ة|ات)?\b", r"\bالمقاول\b", r"\bمستخلصات?\b",
        r"\bمشروع (?:إنشائي|انشائي)\b", r"\bأعمال (?:إنشائية|انشائية|بناء)\b",
    ),
    "financial_claims": (
        r"\bمطالب(?:ة|ات) مالي(?:ة|ه)\b", r"\bمستحقات? مالي(?:ة|ه)\b",
        r"\bالمبلغ المستحق\b", r"\bسداد (?:المبلغ|الدين|المستحقات)\b",
        r"\bمديوني(?:ة|ه)\b", r"\bدين مستحق\b", r"\bالمطالبة بمبلغ\b",
    ),
    "companies_partnerships": (
        r"\bعقد شراكة\b", r"\bالشريك(?:ة|ين|ان|اء)?\b", r"\bالشركاء\b",
        r"\bحصص (?:الشركة|الشركاء)\b", r"\bتصفية (?:الشركة|الشراكة)\b",
        r"\bمساهم(?:ة|ين|ون)?\b", r"\bجمعية الشركاء\b",
    ),
    "damages": (
        r"\bالتعويض عن (?:ال)?أضرار\b", r"\bتعويض(?:اً|ا)? عن الضرر\b",
        r"\bطلب التعويض\b", r"\bالحكم بالتعويض\b", r"\bجبر الضرر\b",
    ),
    "commercial_lease": (
        r"\bعقد (?:ال)?إيجار\b", r"\bالأجرة المستحقة\b",
        r"\bالمؤجر\b", r"\bالمستأجر\b", r"\bإيجار تجاري\b",
    ),
    "commercial_papers": (
        r"\bشيك\b", r"\bشيكات\b", r"\bكمبيال(?:ة|ات)\b",
        r"\bسند لأمر\b", r"\bالأوراق التجارية\b",
    ),
    "transport_shipping": (
        r"\bعقد (?:ال)?نقل\b", r"\bأجرة النقل\b", r"\bشحن (?:البضائع|البضاعة)\b",
        r"\bالنقل (?:البحري|البري|الجوي|التجاري)\b", r"\bناقل بحري\b",
    ),
    "commercial_agency": (
        r"\bوكالة تجارية\b", r"\bالوكيل التجاري\b", r"\bعقد وكالة\b",
        r"\bامتياز تجاري\b", r"\bعقد (?:ال)?امتياز\b",
    ),
    "intellectual_property": (
        r"\bملكية فكرية\b", r"\bعلامة تجارية\b", r"\bحقوق المؤلف\b",
        r"\bبراءة اختراع\b", r"\bاسم تجاري\b",
    ),
    "bankruptcy": (
        r"\bنظام الإفلاس\b", r"\bإجراء الإفلاس\b", r"\bأمين الإفلاس\b",
        r"\bإعادة التنظيم المالي\b", r"\bالتصفية الإدارية\b",
    ),
}

_COMPILED_PATTERNS = {
    category: tuple(re.compile(pattern) for pattern in patterns)
    for category, patterns in _PATTERNS.items()
}


def classify_dispute(*texts: object) -> list[str]:
    """Return all supported dispute types evidenced by the supplied text."""
    joined = " ".join(str(text) for text in texts if text is not None)
    joined = re.sub(r"\s+", " ", joined.replace("⏎", " "))
    found = [
        category
        for category, patterns in _COMPILED_PATTERNS.items()
        if any(pattern.search(joined) for pattern in patterns)
    ]
    return found or ["other"]


def labels_for(categories: Iterable[str]) -> list[str]:
    return [DISPUTE_LABELS[item] for item in categories if item in DISPUTE_LABELS]
