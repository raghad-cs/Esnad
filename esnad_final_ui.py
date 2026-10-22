"""Esnad MVP: Arabic search interface for commercial judgments."""

from __future__ import annotations

from collections import Counter
from html import escape
import hashlib
import os

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
    @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Tajawal:wght@400;500;700&display=swap');

    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background: #0d1323;
        color: #eee9dd;
    }
    [data-testid="stHeader"] {background: transparent;}
    [data-testid="stMainBlockContainer"] {
        max-width: 920px;
        padding-top: 3.3rem;
        padding-bottom: 4rem;
    }
    html, body, div[data-testid="stMarkdownContainer"],
    div[data-testid="stCaptionContainer"], input, button {
        font-family: 'Tajawal', sans-serif;
    }
    .hero {text-align: center; direction: rtl; padding: 2.6rem 0 1.5rem;}
    .hero h1 {
        font-family: 'Amiri', 'Traditional Arabic', serif !important;
        font-weight: 400 !important;
        color: #f1eee5;
        font-size: 5rem;
        line-height: 1.2;
        margin: 0;
    }
    .hero p {color: #a8a79f; font-size: 1rem; margin: .2rem auto;}
    .eyebrow {color: #caa766; font-size: .8rem; letter-spacing: .05em;}
    .search-label {
        direction: rtl;
        text-align: center;
        color: #eee9dd;
        font-size: 1.05rem;
        font-weight: 500;
        margin: .2rem 0 .7rem;
    }
    div[data-testid="stTextInput"] [data-baseweb="input"] {
        min-height: 58px;
        background: #11192b !important;
        border: 1px solid #596178 !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 28px rgba(0, 0, 0, .18) !important;
        overflow: hidden;
    }
    div[data-testid="stTextInput"] [data-baseweb="input"]:focus-within {
        border-color: #d8ba7f !important;
        box-shadow: 0 0 0 2px rgba(216, 186, 127, .12) !important;
    }
    div[data-testid="stTextInput"] input {
        direction: rtl;
        text-align: center;
        background: transparent !important;
        color: #f2ecdf !important;
        font-size: 1rem;
        padding: .9rem 1.2rem;
        border: 0 !important;
        outline: 0 !important;
        box-shadow: none !important;
    }
    div[data-testid="stTextInput"] input::placeholder {color: #8f93a1;}
    [data-testid="InputInstructions"], [data-testid="stInputInstructions"] {display: none !important;}
    div[data-testid="stButton"] button {
        background: #151c2e;
        color: #d8ba7f;
        border: 1px solid #5c5141;
        border-radius: 12px;
        min-height: 42px;
    }
    div[data-testid="stButton"] button:hover,
    div[data-testid="stButton"] button:focus {
        border-color: #d8ba7f !important;
        color: #f6e3ba;
        outline: none !important;
        box-shadow: none !important;
    }
    .examples-title, .filters-title {
        direction: rtl;
        text-align: right;
        color: #aaa9a3;
        margin: 1rem 0 .45rem;
    }
    .section-title {
        direction: rtl;
        text-align: right;
        color: #eee9dd;
        font-family: 'Amiri', 'Traditional Arabic', serif !important;
        font-weight: 400;
        font-size: 2rem;
        margin: 2.3rem 0 .3rem;
    }
    .section-hint {direction: rtl; text-align: right; color: #aaa9a3; margin: 0 0 1rem;}
    .query-info {
        direction: rtl;
        text-align: right;
        color: #aaa9a3;
        background: rgba(17, 25, 43, .65);
        border-radius: 8px;
        padding: .65rem .85rem;
        margin: .5rem 0 .8rem;
        line-height: 1.7;
    }
    .divider {border: 0; border-top: 1px solid #293044; margin: 1.8rem 0;}
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.case-card-marker) {
        border: 1px solid #31384b;
        border-radius: 10px;
        background: #11192b;
        padding: .75rem 1rem;
    }
    .case-card-marker {height: 0; overflow: hidden;}
    .outcome-badge {
        direction: rtl;
        display: inline-block;
        background: rgba(202, 167, 102, .12);
        color: #d8ba7f;
        border: 1px solid rgba(202, 167, 102, .45);
        border-radius: 20px;
        padding: .28rem .75rem;
        margin: .25rem 0 .65rem;
        font-size: .88rem;
        font-weight: 500;
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
    div[data-testid="stExpander"] summary {direction: rtl; justify-content: flex-start; gap: .6rem;}
    div[data-testid="stExpander"] summary p {margin: 0; white-space: nowrap;}
    div[data-testid="stExpander"] summary [data-testid="stIconMaterial"] {display: none !important;}
    div[data-testid="stVerticalBlockBorderWrapper"] h3 {font-size: 1.45rem; line-height: 1.65; margin: .25rem 0;}
    .disclaimer {
        direction: rtl;
        color: #a8a79f;
        font-size: .85rem;
        text-align: center;
        line-height: 1.8;
        margin-top: 3rem;
    }
    .plans-heading {direction:rtl;text-align:center;margin:0 auto 1.6rem;}
    .plans-heading h2 {font-family:'Amiri',serif!important;font-size:2.2rem;color:#f1eee5;margin:.4rem 0;}
    .plans-heading p {text-align:center!important;color:#a8afbd;font-size:.95rem;}
    .plans-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;direction:rtl;}
    .plan-card {background:linear-gradient(145deg,#151e31,#101829);border:1px solid #303c52;border-radius:20px;padding:26px 22px;position:relative;direction:rtl;text-align:right;}
    .plan-card.featured {border-color:#caa766;background:linear-gradient(145deg,#222535,#141c2e);box-shadow:0 12px 36px #00000025;}
    .plan-kicker {color:#a7afbf;font-size:.8rem;margin-bottom:14px;}
    .plan-name {font-size:1.25rem;font-weight:700;color:#f1eee5;margin-bottom:10px;}
    .plan-description {color:#a7afbf;font-size:.88rem;line-height:1.8;min-height:52px;}
    .plan-price {color:#f2e5cb;font-family:'Tajawal',sans-serif;font-size:2.7rem;font-weight:700;line-height:1.3;margin:20px 0 3px;}
    .plan-price small {font-size:.8rem;font-weight:400;color:#afb5c2;}
    .plan-annual {color:#caa766;font-size:.85rem;min-height:36px;}
    .plan-rule {border-top:1px solid #343c4f;margin:18px 0;}
    .plan-feature {color:#d2d6df;font-size:.88rem;line-height:1.85;margin:10px 0;}
    .plan-feature::before {content:'✓';color:#caa766;margin-left:9px;}
    .plan-tag {display:inline-block;color:#ddbf87;background:#caa76615;border:1px solid #caa76655;border-radius:20px;padding:4px 12px;font-size:.75rem;margin-top:16px;}
    .plans-note {direction:rtl;text-align:center!important;color:#929bad;font-size:.85rem;line-height:1.8;margin:22px 0 14px;}
    .hero p {text-align:center!important;}
    @media(max-width:700px) {.plans-grid {grid-template-columns:1fr;} .plan-description {min-height:0;}}
    a {color: #d8ba7f !important;}
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

RESULT_LABELS = {
    1: "النتيجة الأولى",
    2: "النتيجة الثانية",
    3: "النتيجة الثالثة",
    4: "النتيجة الرابعة",
    5: "النتيجة الخامسة",
}

# Public interest form; deployments may override it with the environment variable.
INTEREST_FORM_URL = os.environ.get(
    "ESNAD_INTEREST_FORM_URL",
    "https://docs.google.com/forms/d/e/1FAIpQLSeBk0dC1jnbgXCh_IrQvop5Oww8VsPzApFfrIWW4pXNxVx9ow/viewform?usp=publish-editor",
).strip()
FREE_JUDGMENT_LIMIT = 2


def interest_button(key: str) -> None:
    if INTEREST_FORM_URL.startswith("https://"):
        st.link_button("سجّل اهتمامك بالاشتراك", INTEREST_FORM_URL,
                       use_container_width=True)
    else:
        st.button("سجّل اهتمامك بالاشتراك", key=key, disabled=True,
                  use_container_width=True)
        st.caption("سيُتاح تسجيل الاهتمام قريبًا؛ رابط النموذج قيد التجهيز.")
    st.caption("تسجيل اهتمام فقط، دون دفع أو التزام بالشراء.")


def judgment_id(hit: dict) -> str:
    """Use a source-scoped ID; never identify a judgment by result position."""
    source = content(hit.get("source"))
    case_id = content(hit.get("case_id"))
    if case_id:
        return hashlib.sha256(f"{source}|{case_id}".encode()).hexdigest()
    # A dataset landing URL alone is not a unique judgment identifier.
    payload = "|".join(content(hit.get(key)) for key in
                       ("source", "title", "facts", "reasoning", "verdict"))
    return hashlib.sha256(payload.encode()).hexdigest()


def show_plans() -> None:
    st.markdown('''<div id="plans" class="plans-heading"><div class="eyebrow">باقات إسناد</div><h2>ابدأ بالبحث، وتعمّق في التفاصيل</h2><p>خيارات تناسب المحامي الفرد وفريق المكتب</p></div>
<div class="plans-grid">
<div class="plan-card"><div class="plan-kicker">اكتشف إسناد</div><div class="plan-name">المجاني</div><div class="plan-description">جرّب البحث في الأحكام التجارية وتعرّف على النتائج الأقرب لقضيتك.</div><div class="plan-price">مجانًا</div><div class="plan-annual">ابدأ التجربة دون دفع</div><div class="plan-rule"></div><div class="plan-feature">البحث بوصف القضية</div><div class="plan-feature">معاينة مقتطفات الأحكام</div><div class="plan-feature">التصنيف والفلترة حسب اتجاه الحكم</div><div class="plan-feature">تفاصيل حكمين خلال الجلسة الحالية</div><div class="plan-tag">متاح الآن</div></div>
<div class="plan-card featured"><div class="plan-kicker">للبحث الفردي المتعمّق</div><div class="plan-name">المحامي الفرد</div><div class="plan-description">وصول إلى تفاصيل أحكام إضافية لدعم البحث في قضيتك التجارية.</div><div class="plan-price">60 <small>ريالًا / شهريًا</small></div><div class="plan-annual">أو 598 ريالًا سنويًا</div><div class="plan-rule"></div><div class="plan-feature">جميع مزايا التجربة المجانية</div><div class="plan-feature">فتح تفاصيل أحكام إضافية</div><div class="plan-feature">الوقائع والتسبيب ومنطوق الحكم</div><div class="plan-feature">المواد القانونية المتاحة</div><div class="plan-tag">قريبًا</div></div>
<div class="plan-card"><div class="plan-kicker">للمكاتب الناشئة والصغيرة</div><div class="plan-name">مكتب المحاماة</div><div class="plan-description">باقة مخططة تجمع فريق المكتب في اشتراك واحد للبحث القضائي.</div><div class="plan-price">199 <small>ريالًا / شهريًا</small></div><div class="plan-annual">أو 1,990 ريالًا سنويًا</div><div class="plan-rule"></div><div class="plan-feature">حتى 5 مستخدمين</div><div class="plan-feature">مزايا الباقة الفردية للفريق</div><div class="plan-feature">حساب مستقل لكل مستخدم</div><div class="plan-feature">مخصصة للعمل داخل المكتب</div><div class="plan-tag">قريبًا · باقة مخططة</div></div>
</div><p class="plans-note">الاشتراكات قيد التجهيز. سجّل اهتمامك لنخبرك عند الإطلاق، دون دفع أو التزام بالشراء.</p>''', unsafe_allow_html=True)
    _, action_column, _ = st.columns([1, 2, 1])
    with action_column:
        interest_button("plans_interest")


@st.cache_resource(show_spinner=False)
def load_engine() -> LegalSearchEngine:
    return LegalSearchEngine()


def content(value: object) -> str:
    """Display stored fields without inventing missing case details."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "\n".join(str(part) for part in value if part)
    return str(value).strip()


def result_label(number: int) -> str:
    return RESULT_LABELS.get(number, f"النتيجة رقم {number}")


def show_result(hit: dict, number: int) -> None:
    source = "وزارة العدل" if hit.get("source") == "MOJ" else "مجموعة ALARB"
    label = result_label(number)
    title = content(hit.get("title")) or f"حكم تجاري · {label}"
    facts = content(hit.get("facts"))
    summary = content(hit.get("summary"))
    outcome_category = hit.get("outcome_category", "other")
    outcome_label = OUTCOME_LABELS.get(outcome_category, OUTCOME_LABELS["other"])

    with st.container(border=True):
        st.markdown('<span class="case-card-marker"></span>', unsafe_allow_html=True)
        st.caption(f"{source}  ·  {label}")
        st.markdown(
            f'<div class="outcome-badge">اتجاه الحكم: {outcome_label}</div>',
            unsafe_allow_html=True,
        )
        st.subheader(title)
        excerpt = summary or facts
        if excerpt:
            st.write((excerpt[:330] + "…") if len(excerpt) > 330 else excerpt)

        identity = judgment_id(hit)
        opened = st.session_state.opened_judgments
        if identity not in opened:
            if len(opened) >= FREE_JUDGMENT_LIMIT:
                st.markdown("**اطّلعت على تفاصيل حكمين مجانًا**")
                st.write("سجّل اهتمامك وسنتواصل معك عند إطلاق الاشتراك للوصول إلى تفاصيل أحكام إضافية.")
                interest_button(f"interest_{identity}_{number}")
                return
            remaining = FREE_JUDGMENT_LIMIT - len(opened)
            st.caption(f"متبقي للاطلاع المجاني: {remaining} من الأحكام خلال هذه الجلسة.")
            if st.button("فتح تفاصيل الحكم مجانًا", key=f"unlock_{identity}_{number}",
                         use_container_width=True):
                # Count only explicit opens, not rendering or expanding a card.
                st.session_state.opened_judgments = opened | {identity}
                st.rerun()
            return

        with st.expander("تفاصيل الحكم — متاحة لك", expanded=True):
            for field_label, key in (
                ("الوقائع", "facts"),
                ("تسبيب المحكمة", "reasoning"),
                ("الحكم", "verdict"),
                ("المواد المذكورة", "applicable_laws"),
            ):
                value = content(hit.get(key))
                if value:
                    st.markdown(f"**{field_label}**")
                    st.write(value)

            source_url = content(hit.get("source_url"))
            if hit.get("source") == "ALARB":
                case_id = content(hit.get("case_id"))
                if case_id:
                    st.caption("رقم القضية في مجموعة البيانات، وليس رقم الحكم الرسمي:")
                    st.write(case_id)
                if source_url:
                    st.link_button("الاطلاع على مجموعة البيانات", source_url)
            elif source_url:
                st.link_button("فتح المصدر", source_url)
            else:
                st.caption("رابط الحكم المباشر غير متوفر في البيانات الحالية.")


st.markdown(
    '<div class="hero"><div class="eyebrow">البحث في الأحكام التجارية السعودية</div>'
    '<h1>إسناد</h1><p>ابحث بلغتك عن أحكام قضائية مشابهة</p></div>',
    unsafe_allow_html=True,
)

if "query_text" not in st.session_state:
    st.session_state.query_text = ""
if "selected_outcome" not in st.session_state:
    st.session_state.selected_outcome = "all"
if "opened_judgments" not in st.session_state:
    st.session_state.opened_judgments = set()

left_space, search_column, right_space = st.columns([1, 8, 1])
with search_column:
    st.text_input(
        "وصف القضية أو موضوع البحث",
        key="query_text",
        placeholder="مثال: شركة وردت بضاعة ولم يُسدّد المشتري الثمن",
        label_visibility="collapsed",
    )
    submitted = st.button("ابحث في الأحكام", use_container_width=True)

st.markdown('<div class="examples-title">جرّب البحث عن:</div>', unsafe_allow_html=True)
example_columns = st.columns(2)
for index, example in enumerate(EXAMPLES):
    if example_columns[index % 2].button(example, key=f"sample_{index}", use_container_width=True):
        st.session_state.active_query = example
        st.session_state.selected_outcome = "all"

if submitted:
    st.session_state.active_query = st.session_state.query_text.strip()
    st.session_state.selected_outcome = "all"

query = st.session_state.get("active_query", "")
if query:
    try:
        # Reuse results when opening details, changing filters, or showing plans.
        if st.session_state.get("response_query") != query:
            with st.spinner("جاري البحث في الأحكام… قد يستغرق تحميل النموذج وقتًا عند أول تشغيل"):
                fresh_response = load_engine().search(query, top_k=5)
            st.session_state.search_response = fresh_response
            st.session_state.response_query = query
        response = st.session_state.search_response
    except (FileNotFoundError, ValueError) as exc:
        st.error(f"تعذر تشغيل البحث: {exc}")
    except Exception:
        st.error("تعذر إكمال البحث. يرجى التحقق من تثبيت المكتبات وملفات الفهرسة، ثم المحاولة مرة أخرى.")
    else:
        results = response.get("results", [])
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">الأحكام الأقرب إلى بحثك</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-hint">نتائج مرتّبة حسب التشابه الدلالي، وقد تختلف ظروف كل قضية.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="query-info"><strong>الاستفسار:</strong> {escape(query)}'
            f' &nbsp;·&nbsp; <strong>عدد النتائج:</strong> {len(results)}</div>',
            unsafe_allow_html=True,
        )

        outcome_counts = Counter(hit.get("outcome_category", "other") for hit in results)
        available_categories = [
            category for category in OUTCOME_LABELS if outcome_counts.get(category, 0) > 0
        ]
        if st.session_state.selected_outcome not in {"all", *available_categories}:
            st.session_state.selected_outcome = "all"

        st.markdown(
            '<div class="filters-title">فلترة النتائج حسب اتجاه الحكم:</div>',
            unsafe_allow_html=True,
        )
        filter_options = [("all", f"كل النتائج ({len(results)})")]
        filter_options.extend(
            (category, f"{OUTCOME_LABELS[category]} ({outcome_counts[category]})")
            for category in available_categories
        )

        filter_columns = st.columns(3)
        for index, (category, button_label) in enumerate(filter_options):
            is_selected = st.session_state.selected_outcome == category
            visible_label = f"✓ {button_label}" if is_selected else button_label
            if filter_columns[index % 3].button(
                visible_label,
                key=f"outcome_filter_{category}",
                use_container_width=True,
            ):
                st.session_state.selected_outcome = category
                st.rerun()

        selected_outcome = st.session_state.selected_outcome
        filtered_results = (
            results
            if selected_outcome == "all"
            else [
                hit
                for hit in results
                if hit.get("outcome_category", "other") == selected_outcome
            ]
        )

        for number, hit in enumerate(filtered_results, start=1):
            show_result(hit, number)
        if not filtered_results:
            st.info("لا توجد نتائج ضمن هذا التصنيف.")

st.markdown('<hr class="divider">', unsafe_allow_html=True)
show_plans()

st.markdown(
    '<div class="disclaimer">إسناد أداة للبحث والاطلاع على أحكام منشورة. '
    'النتائج ليست رأيًا قانونيًا ولا تتنبأ بنتيجة القضية.</div>',
    unsafe_allow_html=True,
)
