"""আলুর সার ক্যালকুলেটর (ডেমো), একটাই ফাইল।

চালানোর নিয়ম:  streamlit run alu_calculator.py
"""

from decimal import Decimal, ROUND_HALF_UP

import pandas as pd
import streamlit as st

D = Decimal

FERTILIZERS = ["ইউরিয়া", "টিএসপি", "এমওপি", "জিপসাম", "জিংক সালফেট"]

# ---------------------------------------------------------------- বেস মাত্রা
# সারের কেজি প্রতি ১ শতাংশ। শুধু "গোবর না" সারি; গোবরের প্রভাব গুণক দিয়ে ধরা হয়।
# জমি: মাঝারি, সেচ: হ্যাঁ।
BASE_DOSE = {
    "বেলে":     ("1.20", "0.90", "1.30", "0.50", "0.04"),
    "দোআঁশ":    ("1.00", "0.75", "1.10", "0.45", "0.04"),
    "কাদামাটি": ("0.90", "0.65", "1.00", "0.40", "0.04"),
}

# ---------------------------------------------------------------- গুণক টেবিল
# (ইউরিয়া, টিএসপি, এমওপি, জিপসাম, জিংক)
# মাটির গুণক ব্যবহার হয় না: মাটির প্রভাব বেস মাত্রায় আছে (দুইবার গণনা এড়াতে)।
FACTORS = {
    "land_type": {
        "উঁচু":   ("1.00", "1.00", "1.00", "1.00", "1.00"),
        "মাঝারি": ("1.00", "1.00", "1.00", "1.00", "1.00"),
        "নিচু":   ("0.95", "0.95", "0.95", "0.95", "1.00"),
    },
    "irrigation": {
        "হ্যাঁ":       ("1.00", "1.00", "1.00", "1.00", "1.00"),
        "না":          ("0.90", "0.95", "0.95", "0.95", "1.00"),
        "কখনো কখনো":  ("0.95", "1.00", "1.00", "1.00", "1.00"),
    },
    "organic_manure": {
        "হ্যাঁ": ("0.90", "0.90", "0.90", "0.90", "1.00"),
        "না":    ("1.00", "1.00", "1.00", "1.00", "1.00"),
    },
    "previous_crop": {
        "ধান":        ("1.00", "1.00", "1.00", "1.00", "1.00"),
        "ভুট্টা":     ("1.05", "1.00", "1.05", "1.00", "1.00"),
        "সবজি":       ("0.95", "0.95", "0.95", "1.00", "1.00"),
        "কিছু করিনি": ("1.00", "1.00", "1.00", "1.00", "1.00"),
    },
    "potato_variety": {
        "ডায়মন্ড":  ("1.00", "1.00", "1.00", "1.00", "1.00"),
        "কার্ডিনাল": ("1.00", "1.00", "1.00", "1.00", "1.00"),
        "অ্যাটলাস":  ("1.00", "1.00", "1.00", "1.00", "1.00"),
        "অন্য":      ("1.00", "1.00", "1.00", "1.00", "1.00"),
    },
    "plant_age": {
        "0-20":  ("0.80", "1.00", "0.80", "1.00", "1.00"),
        "21-40": ("1.00", "1.00", "1.00", "1.00", "1.00"),
        "41-60": ("1.10", "1.00", "1.10", "1.00", "1.00"),
    },
    "leaf_condition": {
        "সবুজ": ("1.00", "1.00", "1.00", "1.00", "1.00"),
        "হলদে": ("1.10", "1.00", "1.00", "1.00", "1.00"),
        "ছোট":  ("1.05", "1.00", "1.00", "1.00", "1.00"),
        "পোড়া": ("0.95", "0.95", "0.95", "1.00", "1.00"),
    },
    "tuber_stage": {
        "এখনো না":   ("1.00", "1.00", "1.00", "1.00", "1.00"),
        "শুরু":      ("1.05", "1.00", "1.10", "1.00", "1.00"),
        "বাড়ছে":    ("1.10", "1.00", "1.15", "1.00", "1.00"),
        "বড় হচ্ছে": ("1.05", "1.00", "1.10", "1.00", "1.00"),
    },
    "weather_condition": {
        "বৃষ্টি":    ("1.05", "1.00", "1.00", "1.00", "1.00"),
        "স্বাভাবিক": ("1.00", "1.00", "1.00", "1.00", "1.00"),
        "খরা":       ("0.90", "0.95", "0.95", "0.95", "1.00"),
    },
    "budget": {
        "কম":     ("0.80", "0.80", "0.80", "0.80", "0.80"),
        "মাঝারি": ("1.00", "1.00", "1.00", "1.00", "1.00"),
        "বেশি":   ("1.10", "1.10", "1.10", "1.10", "1.00"),
    },
}

# ---------------------------------------------------------------- বিকল্পসমূহ (UI এর জন্য)
OPTIONS = {
    "land_unit": ["শতাংশ", "বিঘা", "একর"],
    "soil_type": list(BASE_DOSE),
    "land_type": list(FACTORS["land_type"]),
    "irrigation": list(FACTORS["irrigation"]),
    "organic_manure": list(FACTORS["organic_manure"]),
    "previous_crop": list(FACTORS["previous_crop"]),
    "potato_variety": list(FACTORS["potato_variety"]),
    "leaf_condition": list(FACTORS["leaf_condition"]),
    "tuber_stage": list(FACTORS["tuber_stage"]),
    "weather_condition": list(FACTORS["weather_condition"]),
    "budget": list(FACTORS["budget"]),
}

# এক একক = কত শতাংশ (বিঘা অঞ্চলভেদে ভিন্ন হয়; এখানে ৩৩ শতাংশ ধরা হয়েছে)
UNIT_TO_DECIMAL = {"শতাংশ": D("1"), "বিঘা": D("33"), "একর": D("100")}

MIN_TOTAL_FACTOR = D("0.6")
MAX_TOTAL_FACTOR = D("1.4")
LATE_STAGES = ("বাড়ছে", "বড় হচ্ছে")
MAX_TOP_DRESSING_AGE = 60

DISCLAIMER = ("এটি একটি ডেমো। প্রকৃত সার প্রয়োগের আগে "
              "স্থানীয় কৃষি অফিসারের পরামর্শ নিন।")


def _row(field, value):
    return [D(x) for x in FACTORS[field][value]]


def _age_bucket(age_days):
    if age_days <= 20:
        return "0-20"
    if age_days <= 40:
        return "21-40"
    return "41-60"


def round2(x):
    return x.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def grams(kg):
    return int((kg * 1000).quantize(D("1"), rounding=ROUND_HALF_UP))


def calculate(land_size, land_unit, soil_type, land_type, irrigation,
              organic_manure, previous_crop, potato_variety, plant_age_days,
              leaf_condition, tuber_stage, weather_condition, budget):
    """ফলাফল ডিকশনারি ফেরত দেয়।

    keys: ok, message, warnings, decimals, items (প্রতি সারের তথ্য)
    """
    land_size = D(str(land_size))
    if land_size <= 0:
        raise ValueError("জমির পরিমাণ শূন্যের বেশি হতে হবে।")
    decimals = land_size * UNIT_TO_DECIMAL[land_unit]

    warnings = []
    if leaf_condition == "হলদে":
        warnings.append("পাতা হলদে হলে শুধু সারের অভাব নয়, রোগ বা পানির সমস্যাও "
                        "হতে পারে। কৃষি অফিসারকে দেখান।")
    if leaf_condition == "পোড়া":
        warnings.append("পাতা পোড়া হলে রোগ বা অতিরিক্ত সারের সমস্যা হতে পারে। "
                        "সার বাড়ানোর আগে কৃষি অফিসারকে দেখান।")

    if plant_age_days > MAX_TOP_DRESSING_AGE:
        return {"ok": False, "decimals": decimals, "warnings": warnings, "items": [],
                "message": "গাছের বয়স ৬০ দিনের বেশি হলে সাধারণত আর উপরি সার দেওয়ার "
                           "দরকার হয় না।"}

    base = [D(x) for x in BASE_DOSE[soil_type]]

    # গাছের বয়স ও কন্দের পর্যায়: একই কারণে দুইবার না ধরে, বড় গুণকটি নেওয়া হয়।
    age_f = _row("plant_age", _age_bucket(plant_age_days))
    stage_f = _row("tuber_stage", tuber_stage)
    if tuber_stage == "এখনো না":
        growth_f = age_f
    else:
        growth_f = [max(a, s) for a, s in zip(age_f, stage_f)]
    if tuber_stage in LATE_STAGES:
        growth_f[0] = D("1.00")  # কন্দ বাড়ার সময় ইউরিয়া বাড়ানো হয় না

    other_fields = ["organic_manure", "land_type", "irrigation", "previous_crop",
                    "potato_variety", "leaf_condition", "weather_condition", "budget"]
    chosen = {
        "organic_manure": organic_manure, "land_type": land_type,
        "irrigation": irrigation, "previous_crop": previous_crop,
        "potato_variety": potato_variety, "leaf_condition": leaf_condition,
        "weather_condition": weather_condition, "budget": budget,
    }

    items = []
    for i, name in enumerate(FERTILIZERS):
        total = growth_f[i]
        for f in other_fields:
            total *= _row(f, chosen[f])[i]
        raw_total = total
        total = min(max(total, MIN_TOTAL_FACTOR), MAX_TOTAL_FACTOR)
        per_decimal = base[i] * total
        amount = per_decimal * decimals
        items.append({
            "name": name,
            "base": base[i],
            "factor": total,
            "capped": raw_total != total,
            "per_decimal_kg": per_decimal,
            "kg": amount,
            "kg_text": round2(amount),
            "grams": grams(amount),
        })

    return {"ok": True, "message": "", "warnings": warnings,
            "decimals": decimals, "items": items}


st.set_page_config(page_title="আলুর সার ক্যালকুলেটর", page_icon="🥔", layout="centered")

BN_DIGITS = str.maketrans("0123456789.", "০১২৩৪৫৬৭৮৯.")


def bn(value):
    """ইংরেজি সংখ্যাকে বাংলা সংখ্যায় রূপান্তর।"""
    return str(value).translate(BN_DIGITS)


def fmt_land(size):
    size = Decimal(str(size)).normalize()
    return bn(f"{size:f}")


# ------------------------------------------------------------------ স্টাইল
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stApp, button, input, select, textarea {
    font-family: 'Noto Sans Bengali', 'Kalpurush', 'SolaimanLipi', sans-serif !important;
}
.stApp { background: #F3F6F1; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 880px; padding-top: 1.6rem; }

.hero { background: #25523A; color: #fff; border-radius: 14px;
        padding: 26px 30px; margin-bottom: 22px; }
.hero h1 { margin: 0 0 6px 0; font-size: 1.9rem; font-weight: 700; color: #fff; }
.hero p { margin: 0; font-size: 1.02rem; color: #D5E6D9; line-height: 1.6; }

.section-title { font-weight: 600; color: #25523A; font-size: 1.05rem;
                 margin: 6px 0 2px 0; padding-left: 10px;
                 border-left: 4px solid #D9A23B; }

.result-head { font-size: 1.25rem; font-weight: 700; color: #2A2118; margin: 22px 0 12px 0; }
.card { background: #fff; border: 1px solid #DCE4D8; border-radius: 12px;
        padding: 16px 14px; text-align: center; height: 100%; }
.card .n { color: #5B6B5E; font-size: .95rem; font-weight: 500; }
.card .v { color: #25523A; font-size: 1.9rem; font-weight: 700; line-height: 1.3; }
.card .v span { font-size: .95rem; font-weight: 500; color: #5B6B5E; }
.card .g { color: #8A6A1F; font-size: .9rem; font-weight: 500; }

.notice { background: #FFF6E0; border: 1px solid #EAD49A; color: #5A4310;
          border-radius: 10px; padding: 12px 16px; margin: 10px 0; font-size: .95rem; }
.info { background: #E8F1EA; border: 1px solid #C5DACB; color: #1F4630;
        border-radius: 10px; padding: 12px 16px; margin: 10px 0; }
.disclaimer { color: #6B6B60; font-size: .85rem; margin-top: 18px; }

div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    background: #25523A; color: #fff; border: none; border-radius: 10px;
    padding: .65rem 1.4rem; font-weight: 600; font-size: 1.05rem; width: 100%; }
div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
    background: #1B3F2C; color: #fff; }
div.stButton > button:focus-visible, div[data-testid="stFormSubmitButton"] > button:focus-visible {
    outline: 3px solid #D9A23B; }
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------ সাইডবার
with st.sidebar:
    st.markdown("### ব্যবহারের নিয়ম")
    st.markdown(
        "১. আপনার জমি ও ফসলের তথ্য দিন\n\n"
        "২. **সারের পরিমাণ দেখুন** বাটনে চাপ দিন\n\n"
        "৩. ফলাফল দেখুন ও প্রয়োজনে সংরক্ষণ করুন"
    )
    st.markdown("### জমির মাপ")
    st.markdown("১ বিঘা = ৩৩ শতাংশ\n\n১ একর = ১০০ শতাংশ")
    st.caption(DISCLAIMER)

# ------------------------------------------------------------------ হেডার
st.markdown(
    """
<div class="hero">
  <h1>🥔 আলুর সার ক্যালকুলেটর</h1>
  <p>আপনার জমি ও গাছের অবস্থা বলুন। জানিয়ে দেব কোন সার কত কেজি লাগবে।</p>
</div>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------ ইনপুট ফর্ম
with st.form("input_form"):
    st.markdown('<div class="section-title">জমি</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    land_size = c1.number_input("জমির পরিমাণ", min_value=0.01, value=1.0, step=0.5)
    land_unit = c2.selectbox("একক", OPTIONS["land_unit"])
    soil_type = c3.selectbox("মাটির ধরন", OPTIONS["soil_type"], index=1)

    c1, c2, c3 = st.columns(3)
    land_type = c1.selectbox("জমির উচ্চতা", OPTIONS["land_type"], index=1)
    irrigation = c2.selectbox("সেচের ব্যবস্থা", OPTIONS["irrigation"])
    organic_manure = c3.selectbox("গোবর বা জৈব সার দিয়েছেন?", OPTIONS["organic_manure"])

    st.markdown('<div class="section-title">ফসল ও গাছের অবস্থা</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    previous_crop = c1.selectbox("আগের ফসল", OPTIONS["previous_crop"])
    potato_variety = c2.selectbox("আলুর জাত", OPTIONS["potato_variety"])
    plant_age_days = c3.number_input("গাছের বয়স (দিন)", min_value=0, max_value=150,
                                     value=30, step=1)

    c1, c2, c3 = st.columns(3)
    leaf_condition = c1.selectbox("পাতার অবস্থা", OPTIONS["leaf_condition"])
    tuber_stage = c2.selectbox("আলু ধরার অবস্থা", OPTIONS["tuber_stage"], index=1)
    weather_condition = c3.selectbox("আবহাওয়া", OPTIONS["weather_condition"], index=1)

    c1, c2 = st.columns([1, 2])
    budget = c1.selectbox("সারের বাজেট", OPTIONS["budget"], index=1)
    notes = c2.text_input("অতিরিক্ত তথ্য (ঐচ্ছিক)", placeholder="যেমন: পানি জমে না")

    submitted = st.form_submit_button("সারের পরিমাণ দেখুন")

# ------------------------------------------------------------------ ফলাফল
if submitted:
    try:
        result = calculate(
            land_size, land_unit, soil_type, land_type, irrigation, organic_manure,
            previous_crop, potato_variety, plant_age_days, leaf_condition,
            tuber_stage, weather_condition, budget,
        )
    except ValueError as err:
        st.error(str(err))
        st.stop()

    land_text = f"{fmt_land(land_size)} {land_unit}"

    for w in result["warnings"]:
        st.markdown(f'<div class="notice">⚠️ {w}</div>', unsafe_allow_html=True)

    if not result["ok"]:
        st.markdown(f'<div class="info">{result["message"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="disclaimer">{DISCLAIMER}</div>', unsafe_allow_html=True)
        st.stop()

    st.markdown(f'<div class="result-head">আপনার {land_text} জমির জন্য:</div>',
                unsafe_allow_html=True)

    cols = st.columns(5)
    for col, item in zip(cols, result["items"]):
        col.markdown(
            f"""<div class="card">
                <div class="n">{item["name"]}</div>
                <div class="v">{bn(item["kg_text"])} <span>কেজি</span></div>
                <div class="g">{bn(item["grams"])} গ্রাম</div>
            </div>""",
            unsafe_allow_html=True,
        )

    # চার্ট
    chart_df = pd.DataFrame(
        {"কেজি": [float(i["kg_text"]) for i in result["items"]]},
        index=[i["name"] for i in result["items"]],
    )
    st.markdown("&nbsp;", unsafe_allow_html=True)
    st.bar_chart(chart_df, color="#25523A", height=260)

    # হিসাবের বিবরণ
    with st.expander("হিসাব কীভাবে হলো দেখুন"):
        detail = pd.DataFrame(
            {
                "সার": [i["name"] for i in result["items"]],
                "মূল মাত্রা (কেজি/শতাংশ)": [bn(i["base"]) for i in result["items"]],
                "মোট গুণক": [bn(round(i["factor"], 3)) + (" (সীমায় আটকানো)" if i["capped"] else "")
                             for i in result["items"]],
                "প্রতি শতাংশে (কেজি)": [bn(f'{i["per_decimal_kg"]:.3f}') for i in result["items"]],
            }
        )
        st.dataframe(detail, hide_index=True, width="stretch")
        st.caption(
            "চূড়ান্ত মাত্রা = মূল মাত্রা × মোট গুণক × জমির পরিমাণ (শতাংশে)। "
            f"আপনার জমি = {bn(round(result['decimals'], 2))} শতাংশ।"
        )

    # সংরক্ষণ
    lines = [f"আলুর সার সুপারিশ ({land_text} জমির জন্য)", ""]
    lines += [f"{i['name']}: {bn(i['kg_text'])} কেজি ({bn(i['grams'])} গ্রাম)"
              for i in result["items"]]
    lines += ["", f"মাটি: {soil_type} | সেচ: {irrigation} | গোবর: {organic_manure}",
              f"আলুর জাত: {potato_variety} | গাছের বয়স: {bn(plant_age_days)} দিন"]
    if notes:
        lines.append(f"অতিরিক্ত তথ্য: {notes}")
    lines += ["", DISCLAIMER]
    st.download_button("ফলাফল সংরক্ষণ করুন (টেক্সট ফাইল)", "\n".join(lines),
                       file_name="alu_shar_shuparish.txt", mime="text/plain")

    st.markdown(f'<div class="disclaimer">{DISCLAIMER}</div>', unsafe_allow_html=True)
