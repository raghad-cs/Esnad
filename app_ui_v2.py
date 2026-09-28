"""Esnad MVP: Arabic search interface for commercial judgments."""

from __future__ import annotations

from collections import Counter

import streamlit as st

from search_engine import LegalSearchEngine


st.set_page_config(
    page_title="إسناد | بحث الأحكام التجارية",
    page_icon="⚖️",
    layout="centered",
)


st.markdown(
    """
    <style>
    @import url(
        'https://fonts.googleapis.com/css2?'
        'family=Amiri:wght@400;700&'
        'family=Tajawal:wght@400;500;700&display=swap'
    );

    html,
    body,
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"] {
        background: #0d1323;
        color: #eee9dd;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 920px;
        padding-top: 3.3rem;
        padding-bottom: 4rem;
    }

    html,
    body,
    div[data-testid="stMarkdownContainer"],
    div[data-testid="stCaptionContainer"],
    input,
    button {
        font-family: 'Tajawal', sans-serif;
    }

    .hero {
        direction: rtl;
        text-align: center;
        padding: 2.6rem 0 1.2rem;
    }

    .hero h1 {
        font-family: 'Amiri', serif !important;
        font-size: 5rem;
        font-weight: 400;
        line-height: 1.2;
        color: #f1eee5;
        margin: 0;
    }

    .hero p {
        color: #a8a79f;
        font-size: 1rem;
        margin: 0.2rem auto;
    }

    .eyebrow {
        color: #caa766;
        font-size: 0.8rem;
        letter-spacing: 0.05em;
    }

    .section-title {
        direction: rtl;
        text-align: right;
        color: #eee9dd;
        font-family: 'Amiri', serif !important;
        font-size: 2rem;
        font-weight: 400;
        margin: 2.3rem 0 0.3rem;
    }

    .section-hint {
        direction: rtl;
        text-align: right;
        color: #aaa9a3;
        margin: 0 0 1rem;
    }

    .divider {
        border: 0;
        border-top: 1px solid #293044;
        margin: 1.8rem 0;
    }

    .disclaimer {
        direction: rtl;
        color: #a8a79f;
        font-size: 0.85rem;
        text-align: center;
        line-height: 1.8;
        margin-top: 3rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(
        .case-card-marker
    ) {
        border: 1px solid #31384b;
        border-radius: 8px;
        background: #11192b;
        padding: 0.65rem 1rem;
    }

    .case-card-marker {
        height: 0;
        overflow: hidden;
    }

    div[data-testid="stTextInput"] input {
        direction: rtl;
        text-align: right;
        background: #11192b;
        color: #f2ecdf;
        border: 1px solid #424a5c;
        border-radius: 4px;
        outline: none;
        box-shadow: none;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #d8ba7f !important;
        outline: none !important;
        box-shadow: none !important;
    }

    div[data-testid="stTextInput"]
    [data-testid="InputInstructions"] {
        display: none !important;
    }

    div[data-testid="stTextInput"] label {
        direction: rtl;
        color: #c9c6be;
    }

    div[data-testid="stButton"] button {
        background: #151c2e;
        color: #d8ba7f;
        border: 1px solid #5c5141;
        border-radius: 4px;
    }

    div[data-testid="stButton"] button:hover {
        border-color: #d8ba7f;
        color: #f6e3ba;
    }

    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] h3 {
        direction: rtl;
        text-align: right;
        line-height: 1.75;
    }

    div[data-testid="stExpander"] {
        direction: rtl;
        background: #10182a;
        border: 1px solid #323a4b;
        border-radius: 5px;
    }

    div[data-testid="stExpander"] summary {
        direction: rtl;
        justify-content: flex-start;
        gap: 0.6rem;
    }

    div[data-testid="stExpander"] summary p {
        margin: 0;
        white-space: nowrap;
    }

    div[data-testid="stExpander"]
    summary [data-testid="stIconMaterial"] {
        display: none !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] h3 {
        font-size: 1.45rem;
        line-height: 1.65;
        margin: 0.25rem 0;
    }

    .outcome-badge {
        direction: rtl;
        display: inline-block;
        background: rgba(202, 167, 102, 0.12);
        color: #d8ba7f;
        border: 1px solid rgba(202, 167, 102, 0.45);
        border-radius: 20px;
        padding: 0.28rem 0.75rem;
        margin: 0.25rem 0 0.65rem;
        font-size: 0.88rem;
        font-weight: 500;
    }

    .outcome-summary {
        direction: rtl;
        text-align: right;
        color: #c9c6be;
        background: #10182a;
        border-right: 3px solid #caa766;
        border-radius: 5px;
        padding: 0.75rem 1rem;
        margin: 0.8rem 0 1.2rem;
        line-height: 1.8;
    }

    a {
        color: #d8ba7f !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


EXAMPLES = (
    "التعسف في استعمال الحق",
    "مبدأ حسن النية في العقود",
    "الفسخ القضائي للعقد",
    "المطالبة بباقي ثمن سيارة بالتقسيط",
)


OUTCOME_LABELS = {
    "accepted": "إلزام أو قبول",
    "rejected": "رفض الدعوى",
    "inadmissible": "عدم قبول الدعوى",
    "settlement": "صلح",
    "no_jurisdiction": "عدم اختصاص",
    "other": "نتيجة أخرى",
}


@st.cache_resource(show_spinner=False)
def load_engine() -> LegalSearchEngine:
    """Load and cache the unified semantic search engine."""
    return LegalSearchEngine()


def content(value: object) -> str:
    """Display stored fields without inventing missing information."""
    if value is None:
        return ""

    if isinstance(value, (list, tuple)):
        return "\n".join(
            str(part)
            for part in value
            if part
        )

    return str(value).strip()


def show_result(hit: dict, number: int) -> None:
    """Display one judgment result."""

    source = (
        "وزارة العدل"
        if hit.get("source") == "MOJ"
        else "مجموعة ALARB"
    )

    title = content(hit.get("title"))

    if not title:
        title = f"حكم تجاري · نتيجة {number}"

    facts = content(hit.get("facts"))
    summary = content(hit.get("summary"))

    outcome_category = hit.get(
        "outcome_category",
        "other",
    )

    outcome_label = OUTCOME_LABELS.get(
        outcome_category,
        OUTCOME_LABELS["other"],
    )

    with st.container(border=True):
        st.markdown(
            '<span class="case-card-marker"></span>',
            unsafe_allow_html=True,
        )

        st.caption(f"{source}  ·  نتيجة {number}")

        st.markdown(
            (
                '<div class="outcome-badge">'
                f'اتجاه الحكم: {outcome_label}'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        st.subheader(title)

        excerpt = summary or facts

        if excerpt:
            if len(excerpt) > 330:
                excerpt = excerpt[:330] + "…"

            st.write(excerpt)

        with st.expander("تفاصيل الحكم"):
            fields = (
                ("الوقائع", "facts"),
                ("تسبيب المحكمة", "reasoning"),
                ("الحكم", "verdict"),
                ("المواد المذكورة", "applicable_laws"),
            )

            for label, key in fields:
                value = content(hit.get(key))

                if value:
                    st.markdown(f"**{label}**")
                    st.write(value)

            if hit.get("source") == "ALARB":
                case_id = content(hit.get("case_id"))

                if case_id:
                    st.caption(
                        "رقم القضية في مجموعة البيانات، "
                        "وليس رقم الحكم الرسمي:"
                    )
                    st.write(case_id)

                source_url = content(hit.get("source_url"))

                if source_url:
                    st.link_button(
                        "الاطلاع على مجموعة البيانات",
                        source_url,
                    )

            else:
                source_url = content(hit.get("source_url"))

                if source_url:
                    st.link_button(
                        "فتح المصدر",
                        source_url,
                    )
                else:
                    st.caption(
                        "رابط الحكم المباشر غير متوفر "
                        "في البيانات الحالية."
                    )


st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">
            البحث في الأحكام التجارية السعودية
        </div>
        <h1>إسناد</h1>
        <p>ابحث بلغتك عن أحكام قضائية مشابهة</p>
    </div>
    """,
    unsafe_allow_html=True,
)


if "query_text" not in st.session_state:
    st.session_state.query_text = ""


st.text_input(
    "وصف القضية أو موضوع البحث",
    key="query_text",
    placeholder=(
        "مثال: شركة وردت بضاعة "
        "ولم يُسدّد المشتري الثمن"
    ),
)


submitted = st.button(
    "ابحث في الأحكام",
    use_container_width=True,
)


st.caption("جرّب البحث عن:")

example_columns = st.columns(2)

for index, example in enumerate(EXAMPLES):
    column = example_columns[index % 2]

    if column.button(
        example,
        key=f"sample_{index}",
        use_container_width=True,
    ):
        st.session_state.active_query = example


if submitted:
    st.session_state.active_query = (
        st.session_state.query_text.strip()
    )


query = st.session_state.get("active_query", "")


if query:
    try:
        with st.spinner(
            "جاري البحث في الأحكام… "
            "قد يستغرق تحميل النموذج وقتًا عند أول تشغيل"
        ):
            response = load_engine().search(
                query,
                top_k=5,
            )

    except (FileNotFoundError, ValueError) as error:
        st.error(f"تعذر تشغيل البحث: {error}")

    except Exception:
        st.error(
            "تعذر إكمال البحث. تحققي من تثبيت المكتبات "
            "وملفات الفهرسة، ثم حاولي مرة أخرى."
        )

    else:
        results = response.get("results", [])

        st.markdown(
            '<hr class="divider">',
            unsafe_allow_html=True,
        )

        st.markdown(
            (
                '<div class="section-title">'
                'الأحكام الأقرب إلى بحثك'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        st.markdown(
            (
                '<div class="section-hint">'
                'نتائج مرتّبة حسب التشابه الدلالي، '
                'وقد تختلف ظروف كل قضية.'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        st.caption(
            f"الاستفسار: {query}  ·  "
            f"النتائج المعروضة: {len(results)}"
        )

        outcome_counts = Counter(
            hit.get("outcome_category", "other")
            for hit in results
        )

        outcome_summary = "  ·  ".join(
            (
                f"{label}: "
                f"{outcome_counts.get(category, 0)}"
            )
            for category, label in OUTCOME_LABELS.items()
            if outcome_counts.get(category, 0) > 0
        )

        if outcome_summary:
            st.markdown(
                (
                    '<div class="outcome-summary">'
                    f'{outcome_summary}'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

        for number, hit in enumerate(results, start=1):
            show_result(hit, number)

        if not results:
            st.info(
                "لا توجد نتائج في البيانات الحالية. "
                "جرّبي وصفًا آخر للقضية."
            )


st.markdown(
    """
    <div class="disclaimer">
        إسناد أداة للبحث والاطلاع على أحكام منشورة.
        النتائج ليست رأيًا قانونيًا ولا تتنبأ بنتيجة القضية.
    </div>
    """,
    unsafe_allow_html=True,
)
