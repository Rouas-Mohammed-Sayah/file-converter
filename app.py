import streamlit as st
import pandas as pd
import sqlite3
import os
import re
import time

# =========================================================
# 🎨 إعدادات الصفحة
# =========================================================

st.set_page_config(
    page_title="محوّل الملفات",
    page_icon="🔄",
    layout="wide"
)

# =========================================================
# 🎨 CSS مخصص
# =========================================================

st.markdown("""
<style>
    /* الخلفية العامة */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    /* البطاقات */
    .card {
        background: white;
        border-radius: 20px;
        padding: 30px;
        margin: 10px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }

    /* العنوان الرئيسي */
    .main-title {
        text-align: center;
        color: white;
        font-size: 3em;
        font-weight: bold;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    /* العنوان الفرعي */
    .sub-title {
        text-align: center;
        color: rgba(255,255,255,0.9);
        font-size: 1.2em;
        margin-bottom: 30px;
    }

    /* بطاقات الإحصاءات */
    .metric-card {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        color: white;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }

    .metric-value {
        font-size: 2.5em;
        font-weight: bold;
    }

    .metric-label {
        font-size: 0.9em;
        opacity: 0.9;
        margin-top: 5px;
    }

    /* زر الرفع */
    .uploadedFile {
        border-radius: 15px !important;
    }

    /* زر البدء */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 15px 40px !important;
        font-size: 1.1em !important;
        font-weight: bold !important;
        width: 100% !important;
        box-shadow: 0 5px 15px rgba(102,126,234,0.4) !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(102,126,234,0.6) !important;
    }

    /* شريط التقدم */
    .stProgress > div > div {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        border-radius: 10px !important;
    }

    /* إخفاء عناصر Streamlit الافتراضية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# =========================================================
# 🧠 دوال المعالجة
# =========================================================

def clean_columns(columns):
    clean_cols = []
    seen = set()
    for i, col in enumerate(columns):
        col = str(col).strip()
        if col.lower() in ("nan", ""):
            col = f"column_{i}"
        col = re.sub(r'\W+', '_', col)
        if col in seen:
            col = f"{col}_{i}"
        seen.add(col)
        clean_cols.append(col)
    return clean_cols


def detect_header(df, max_rows=20):
    if df is None or df.empty:
        return 0
    max_rows = min(max_rows, len(df))
    best_row, max_non_null = 0, 0
    for i in range(max_rows):
        non_null_count = df.iloc[i].notna().sum()
        if non_null_count > max_non_null:
            max_non_null = non_null_count
            best_row = i
    return best_row


def process_files(uploaded_files):
    db_path = "database.db"
    details = []
    stats = {
        "total_files": 0,
        "success": 0,
        "errors": 0,
        "skipped": 0,
        "tables_created": 0
    }

    start_time = time.time()

    with sqlite3.connect(db_path) as conn:
        for uploaded_file in uploaded_files:
            stats["total_files"] += 1
            file_name = uploaded_file.name

            try:
                if file_name.lower().endswith(".csv"):
                    try:
                        df = pd.read_csv(uploaded_file, encoding="utf-8", low_memory=False)
                    except UnicodeDecodeError:
                        df = pd.read_csv(uploaded_file, encoding="latin-1", low_memory=False)

                    df = df.dropna(how="all").drop_duplicates()

                    if df.empty:
                        stats["skipped"] += 1
                        details.append({"file": file_name, "status": "⚠️ تجاوز", "reason": "ملف فارغ"})
                        continue

                    df.columns = clean_columns(df.columns)
                    table_name = re.sub(r'\W+', '_', os.path.splitext(file_name)[0])
                    df.to_sql(table_name, conn, if_exists="replace", index=False)

                    stats["success"] += 1
                    stats["tables_created"] += 1
                    details.append({
                        "file": file_name,
                        "status": "✅ نجاح",
                        "rows": len(df),
                        "table": table_name,
                        "df": df
                    })

                elif file_name.lower().endswith((".xlsx", ".xls")):
                    excel_file = pd.ExcelFile(uploaded_file)
                    file_base = os.path.splitext(file_name)[0]

                    for sheet_name in excel_file.sheet_names:
                        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                        df = df.dropna(how="all")

                        if df.empty:
                            stats["skipped"] += 1
                            details.append({"file": file_name, "sheet": sheet_name, "status": "⚠️ تجاوز", "reason": "شيت فارغ"})
                            continue

                        header_row = detect_header(df)
                        df.columns = df.iloc[header_row].astype(str)
                        df = df[header_row + 1:].dropna(how="all").drop_duplicates()

                        if df.empty:
                            stats["skipped"] += 1
                            continue

                        df.columns = clean_columns(df.columns)
                        table_name = re.sub(r'\W+', '_', f"{file_base}_{sheet_name}")
                        df.to_sql(table_name, conn, if_exists="replace", index=False)

                        stats["success"] += 1
                        stats["tables_created"] += 1
                        details.append({
                            "file": file_name,
                            "sheet": sheet_name,
                            "status": "✅ نجاح",
                            "rows": len(df),
                            "table": table_name,
                            "df": df
                        })

                else:
                    stats["skipped"] += 1
                    details.append({"file": file_name, "status": "⚠️ تجاوز", "reason": "صيغة غير مدعومة"})

            except Exception as e:
                stats["errors"] += 1
                details.append({"file": file_name, "status": "❌ خطأ", "message": str(e)})

    execution_time = round(time.time() - start_time, 2)
    success_rate = round((stats["success"] / stats["total_files"]) * 100, 2) if stats["total_files"] else 0

    return stats, details, execution_time, success_rate, db_path


# =========================================================
# 🎨 الواجهة
# =========================================================

# العنوان الرئيسي
st.markdown('<p class="main-title">🔄 محوّل الملفات</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">حوّل ملفات Excel و CSV إلى قاعدة بيانات بضغطة واحدة</p>', unsafe_allow_html=True)

# منطقة رفع الملفات
st.markdown('<div class="card">', unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "📂 اسحب ملفاتك هنا أو اضغط للاختيار",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=True,
    help="يدعم ملفات CSV و Excel"
)

if uploaded_files:
    st.success(f"✅ تم رفع {len(uploaded_files)} ملف بنجاح")

st.markdown('</div>', unsafe_allow_html=True)

# زر المعالجة
if uploaded_files:
    if st.button("🚀 ابدأ المعالجة الآن"):

        with st.spinner("⏳ جاري معالجة ملفاتك..."):
            stats, details, execution_time, success_rate, db_path = process_files(uploaded_files)

        # الإحصاءات
        st.markdown("---")
        st.markdown("### 📊 نتائج المعالجة")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{stats["total_files"]}</div>
                <div class="metric-label">📁 الملفات</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{stats["success"]}</div>
                <div class="metric-label">✅ نجاح</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{stats["errors"]}</div>
                <div class="metric-label">❌ أخطاء</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{execution_time}s</div>
                <div class="metric-label">⏱️ الوقت</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        progress_value = min(max(success_rate / 100, 0.0), 1.0)
        st.progress(progress_value)
        st.caption(f"✨ نسبة النجاح: {success_rate}%")

        # تفاصيل الملفات
        st.markdown("---")
        st.markdown("### 📋 تفاصيل الملفات")

        for item in details:
            with st.expander(f"{item['status']} ← {item['file']}"):
                if "sheet" in item:
                    st.write(f"📄 الشيت: **{item['sheet']}**")
                if "rows" in item:
                    st.write(f"📝 عدد الصفوف: **{item['rows']}**")
                if "table" in item:
                    st.write(f"🗄️ اسم الجدول: **{item['table']}**")
                if "reason" in item:
                    st.warning(f"السبب: {item['reason']}")
                if "message" in item:
                    st.error(f"الخطأ: {item['message']}")
                if "df" in item:
                    st.dataframe(item["df"].head(10), use_container_width=True)

        # تحميل قاعدة البيانات
        st.markdown("---")
        st.markdown("### 💾 تحميل النتائج")

        with open(db_path, "rb") as f:
            st.download_button(
                label="⬇️ تحميل قاعدة البيانات",
                data=f,
                file_name="database.db",
                mime="application/octet-stream"
            )

else:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.info("👆 ارفع ملف CSV أو Excel للبدء")
    st.markdown('</div>', unsafe_allow_html=True)
