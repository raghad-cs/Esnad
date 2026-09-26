"""Esnad MVP: Arabic search interface for the two commercial judgment indexes."""

from __future__ import annotations

import streamlit as st

from search_engine import LegalSearchEngine


st.set_page_config(page_title="إسناد | بحث الأحكام التجارية", page_icon="⚖️", layout="centered")

st.markdown(
    """<style>
    @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Tajawal:wght@400;500;700&display=swap');
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {background:#0d1323;color:#eee9dd;}
    [data-testid="stHeader"] {background:transparent;}
    [data-testid="stMainBlockContainer"] {max-width:920px;padding-top:3.3rem;padding-bottom:4rem;}
    html, body, div[data-testid="stMarkdownContainer"], div[data-testid="stCaptionContainer"], input, button {font-family:'Tajawal',sans-serif;}
    .material-symbols-rounded, .material-symbols-outlined, .material-icons {font-family:'Material Symbols Rounded'!important;}
    .hero {text-align:center;direction:rtl;padding:2.6rem 0 1.2rem;}
    .hero h1, .hero h1 * {font-family:'Amiri',serif!important;font-weight:400;color:#f1eee5;font-size:5rem;line-height:1.2;margin:0;}
    .hero p {color:#a8a79f;font-size:1rem;margin:.2rem auto;}
    .eyebrow {color:#caa766;font-size:.8rem;letter-spacing:.05em;}
    .section-title {direction:rtl;text-align:right;color:#eee9dd;font-family:'Amiri',serif!important;font-weight:400;font-size:2rem;margin:2.3rem 0 .3rem;}
    .section-hint {direction:rtl;text-align:right;color:#aaa9a3;margin:0 0 1rem;}
    .divider {border:0;border-top:1px solid #293044;margin:1.8rem 0;}
    .disclaimer {direction:rtl;color:#a8a79f;font-size:.85rem;text-align:center;line-height:1.8;margin-top:3rem;}
    div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"]:has(.case-card-marker) {border:1px solid #31384b;border-radius:8px;background:#11192b;padding:.65rem 1rem;}
    .case-card-marker {height:0;overflow:hidden;}
    div[data-testid="stTextInput"] input {direction:rtl;text-align:right;background:#11192b;color:#f2ecdf;border:1px solid #424a5c;border-radius:4px;outline:none;box-shadow:none;}
    div[data-testid="stTextInput"] input:focus {border-color:#d8ba7f!important;outline:none!important;box-shadow:none!important;}
    div[data-testid="stTextInput"] [data-testid="InputInstructions"] {display:none!important;}
    div[data-testid="stTextInput"] label {direction:rtl;color:#c9c6be;}
    div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button {background:#151c2e;color:#d8ba7f;border:1px solid #5c5141;border-radius:4px;}
    div[data-testid="stButton"] button:hover, div[data-testid="stFormSubmitButton"] button:hover {border-color:#d8ba7f;color:#f6e3ba;}
    div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] h3 {direction:rtl;text-align:right;line-height:1.75;}
    div[data-testid="stExpander"] {direction:rtl;background:#10182a;border:1px solid #323a4b;border-radius:5px;}
    div[data-testid="stExpander"] summary {direction:rtl;justify-content:flex-start;gap:.6rem;}
    div[data-testid="stExpander"] summary p {margin:0;white-space:nowrap;}
    div[data-testid="stExpander"] svg {flex:0 0 auto;}
    div[data-testid="stExpander"] summary [data-testid="stIconMaterial"], div[data-testid="stExpander"] summary .material-symbols-rounded, div[data-testid="stExpander"] summary .material-symbols-outlined {display:none!important;}
    div[data-testid="stVerticalBlockBorderWrapper"] h3 {font-size:1.45rem;line-height:1.65;margin:.25rem 0;}
    a {color:#d8ba7f!important;}
    </style>""",
    unsafe_allow_html=True,
)

EXAMPLES = (
    "التعسف في استعمال الحق",
    "مبدأ حسن النية في العقود",
    "الفسخ القضائي للعقد",
    "المطالبة بباقي ثمن سيارة بالتقسيط",
)


@st.cache_resource(show_spinner=False)
def load_engine() -> LegalSearchEngine:
    return LegalSearchEngine()


def content(value: object) -> str:
    """Display stored fields as text without inventing missing case details."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "\n".join(str(part) for part in value if part)
    return str(value).strip()


def show_result(hit: dict, number: int) -> None:
    source = "وزارة العدل" if hit["source"] == "MOJ" else "مجموعة ALARB"
    title = content(hit.get("title"))
    if not title:
        title = f"حكم تجاري · نتيجة {number}"
    facts = content(hit.get("facts"))
    summary = content(hit.get("summary"))

    with st.container(border=True):
        st.markdown('<span class="case-card-marker"></span>', unsafe_allow_html=True)
        st.caption(f"{source}  ·  نتيجة {number}")
        st.subheader(title)
        excerpt = summary or facts
        if excerpt:
            st.write((excerpt[:330] + "…") if len(excerpt) > 330 else excerpt)

        with st.expander("تفاصيل الحكم"):
            for label, key in (
                ("الوقائع", "facts"),
                ("تسبيب المحكمة", "reasoning"),
                ("الحكم", "verdict"),
                ("المواد المذكورة", "applicable_laws"),
            ):
                value = content(hit.get(key))
                if value:
                    st.markdown(f"**{label}**")
                    st.write(value)
            if hit["source"] == "ALARB":
                st.caption("رقم القضية في مجموعة البيانات، وليس رقم الحكم الرسمي:")
                st.write(content(hit.get("case_id")))
                st.link_button("اطلاع على مجموعة البيانات", hit["source_url"])
            elif content(hit.get("source_url")):
                st.link_button("فتح المصدر", hit["source_url"])
            else:
                st.caption("رابط الحكم المباشر غير متوفر في البيانات الحالية.")


st.markdown('<div class="hero"><div class="eyebrow">البحث في الأحكام التجارية السعودية</div><h1>إسناد</h1><p>ابحث بلغتك عن أحكام قضائية مشابهة</p></div>', unsafe_allow_html=True)

if "query_text" not in st.session_state:
    st.session_state.query_text = ""

with st.form("search_form"):
    st.text_input("وصف القضية أو موضوع البحث", key="query_text", placeholder="مثال: شركة وردت بضاعة ولم يُسدّد المشتري الثمن")
    submitted = st.form_submit_button("ابحث في الأحكام", use_container_width=True)

st.caption("جرّب البحث عن:")
cols = st.columns(2)
for i, example in enumerate(EXAMPLES):
    if cols[i % 2].button(example, key=f"sample_{i}", use_container_width=True):
        st.session_state.active_query = example

if submitted:
    st.session_state.active_query = st.session_state.query_text.strip()

query = st.session_state.get("active_query", "")
if query:
    try:
        with st.spinner("جاري البحث في الأحكام… قد يستغرق تحميل النموذج وقتًا عند أول تشغيل"):
            response = load_engine().search(query, top_k=5)
    except (FileNotFoundError, ValueError) as exc:
        st.error(f"تعذر تشغيل البحث: {exc}")
    except Exception:
        st.error("تعذر إكمال البحث. تحققي من تثبيت المكتبات وملفات الفهرسة، ثم حاولي مرة أخرى.")
    else:
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">الأحكام الأقرب إلى بحثك</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-hint">نتائج مرتّبة حسب التشابه الدلالي، وقد تختلف ظروف كل قضية.</div>', unsafe_allow_html=True)
        st.caption(f"الاستفسار: {query}  ·  النتائج المعروضة: {response['result_count']}")
        for i, hit in enumerate(response["results"], 1):
            show_result(hit, i)
        if not response["results"]:
            st.info("لا توجد نتائج في البيانات الحالية. جرّبي وصفًا آخر للقضية.")

st.markdown('<div class="disclaimer">إسناد أداة للبحث والاطلاع على أحكام منشورة. النتائج ليست رأيًا قانونيًا ولا تتنبأ بنتيجة القضية.</div>', unsafe_allow_html=True)
