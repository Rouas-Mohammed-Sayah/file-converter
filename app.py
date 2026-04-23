import streamlit as st
import pandas as pd
import sqlite3
import os
import re
import time

# =========================================================
# 🌍 الترجمات
# =========================================================

translations = {
    "ar": {
        "page_title": "محوّل الملفات",
        "main_title": "🔄 محوّل الملفات",
        "sub_title": "حوّل ملفات Excel و CSV إلى قاعدة بيانات بضغطة واحدة",
        "upload_label": "📂 اسحب ملفاتك هنا أو اضغط للاختيار",
        "upload_success": "✅ تم رفع {} ملف بنجاح",
        "start_button": "🚀 ابدأ المعالجة الآن",
        "processing": "⏳ جاري معالجة ملفاتك...",
        "results_title": "📊 نتائج المعالجة",
        "files_label": "📁 الملفات",
        "success_label": "✅ نجاح",
        "errors_label": "❌ أخطاء",
        "time_label": "⏱️ الوقت",
        "success_rate": "✨ نسبة النجاح: {}%",
        "details_title": "📋 تفاصيل الملفات",
        "sheet_label": "📄 الشيت: ",
        "rows_label": "📝 عدد الصفوف: ",
        "table_label": "🗄️ اسم الجدول: ",
        "download_title": "💾 تحميل النتائج",
        "download_button": "⬇️ تحميل قاعدة البيانات",
        "upload_hint": "👆 ارفع ملف CSV أو Excel للبدء",
        "direction": "rtl",
        "font": "Tajawal",
    },
    "fr": {
        "page_title": "Convertisseur de Fichiers",
        "main_title": "🔄 Convertisseur de Fichiers",
        "sub_title": "Convertissez vos fichiers Excel et CSV en base de données en un clic",
        "upload_label": "📂 Glissez vos fichiers ici ou cliquez pour choisir",
        "upload_success": "✅ {} fichier(s) téléchargé(s) avec succès",
        "start_button": "🚀 Lancer le traitement",
        "processing": "⏳ Traitement en cours...",
        "results_title": "📊 Résultats",
        "files_label": "📁 Fichiers",
        "success_label": "✅ Succès",
        "errors_label": "❌ Erreurs",
        "time_label": "⏱️ Temps",
        "success_rate": "✨ Taux de succès: {}%",
        "details_title": "📋 Détails des fichiers",
        "sheet_label": "📄 Feuille: ",
        "rows_label": "📝 Nombre de lignes: ",
        "table_label": "🗄️ Nom de la table: ",
        "download_title": "💾 Télécharger les résultats",
        "download_button": "⬇️ Télécharger la base de données",
        "upload_hint": "👆 Importez un fichier CSV ou Excel pour commencer",
        "direction": "ltr",
        "font": "Inter",
    },
    "en": {
        "page_title": "File Converter",
        "main_title": "🔄 File Converter",
        "sub_title": "Convert your Excel and CSV files into a database with one click",
        "upload_label": "📂 Drag your files here or click to choose",
        "upload_success": "✅ {} file(s) uploaded successfully",
        "start_button": "🚀 Start Processing",
        "processing": "⏳ Processing your files...",
        "results_title": "📊 Results",
        "files_label": "📁 Files",
        "success_label": "✅ Success",
        "errors_label": "❌ Errors",
        "time_label": "⏱️ Time",
        "success_rate": "✨ Success rate: {}%",
        "details_title": "📋 File Details",
        "sheet_label": "📄 Sheet: ",
        "rows_label": "📝 Number of rows: ",
        "table_label": "🗄️ Table name: ",
        "download_title": "💾 Download Results",
        "download_button": "⬇️ Download Database",
        "upload_hint": "👆 Upload a CSV or Excel file to get started",
        "direction": "ltr",
        "font": "Inter",
    }
}

# =========================================================
# 🌍 اختيار اللغة في Session
# =========================================================

if "lang" not in st.session_state:
    st.session_state.lang = "ar"

t = translations[st.session_state.lang]

# =========================================================
# 🎨 إعدادات الصفحة
# =========================================================

st.set_page_config(
    page_title=t["page_title"],
    page_icon="🔄",
    layout="wide"
)

# =========================================================
# 🎨 CSS
# =========================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&family=Inter:wght@400;700&display=swap');

    /* فقط العناصر التي نحددها */
    .stApp {{
        background-color: #f8f9fa;
        direction: {t["direction"]};
        font-family: '{t["font"]}', sans-serif;
        font-size: 17px;
    }}

    .main-title {{
        text-align: center;
        color: #1a1a2e;
        font-size: 2.2em;
        font-weight: bold;
        margin-bottom: 5px;
        font-family: '{t["font"]}', sans-serif;
    }}

    .sub-title {{
        text-align: center;
        color: #6c757d;
        font-size: 1.1em;
        margin-bottom: 30px;
        font-family: '{t["font"]}', sans-serif;
    }}

    .metric-card {{
        background: white;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        color: #1a1a2e;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border: 1px solid #e9ecef;
        font-family: '{t["font"]}', sans-serif;
    }}

    .metric-value {{
        font-size: 2.2em;
        font-weight: bold;
        color: #1a1a2e;
    }}

    .metric-label {{
        font-size: 1em;
        color: #6c757d;
        margin-top: 5px;
    }}

    /* الأزرار فقط */
    .stButton > button {{
        background: #1a1a2e !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 15px 40px !important;
        font-size: 1em !important;
        font-weight: bold !important;
        width: 100% !important;
        font-family: '{t["font"]}', sans-serif !important;
        transition: all 0.3s ease !important;
    }}

    .stButton > button:hover {{
        background: #2d2d4e !important;
        transform: translateY(-2px) !important;
    }}

    /* شريط التقدم */
    .stProgress > div > div {{
        background: #1a1a2e !important;
        border-radius: 10px !important;
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 🌍 شريط تغيير اللغة
# =========================================================

# استبدل قسم شريط اللغة كاملاً بهذا

col1, col2, col3 = st.columns([6, 1, 1])

with col3:
    lang_choice = st.selectbox(
        "",
        options=["🇸🇦 AR", "🇫🇷 FR", "🇬🇧 EN"],
        index=["ar", "fr", "en"].index(st.session_state.lang),
        label_visibility="collapsed"
    )

    lang_map = {"🇸🇦 AR": "ar", "🇫🇷 FR": "fr", "🇬🇧 EN": "en"}

    if lang_map[lang_choice] != st.session_state.lang:
        st.session_state.lang = lang_map[lang_choice]
        st.rerun()
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
                        details.append({"file": file_name, "status": "⚠️", "reason": "ملف فارغ"})
                        continue

                    df.columns = clean_columns(df.columns)
                    table_name = re.sub(r'\W+', '_', os.path.splitext(file_name)[0])
                    df.to_sql(table_name, conn, if_exists="replace", index=False)

                    stats["success"] += 1
                    stats["tables_created"] += 1
                    details.append({
                        "file": file_name,
                        "status": "✅",
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
                            details.append({"file": file_name, "sheet": sheet_name, "status": "⚠️", "reason": "شيت فارغ"})
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
                            "status": "✅",
                            "rows": len(df),
                            "table": table_name,
                            "df": df
                        })

                else:
                    stats["skipped"] += 1
                    details.append({"file": file_name, "status": "⚠️", "reason": "صيغة غير مدعومة"})

            except Exception as e:
                stats["errors"] += 1
                details.append({"file": file_name, "status": "❌", "message": str(e)})

    execution_time = round(time.time() - start_time, 2)
    success_rate = round((stats["success"] / stats["total_files"]) * 100, 2) if stats["total_files"] else 0

    return stats, details, execution_time, success_rate, db_path


# =========================================================
# 🎨 الواجهة الرئيسية
# =========================================================

st.markdown(f'<p class="main-title">{t["main_title"]}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">{t["sub_title"]}</p>', unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    t["upload_label"],
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=True,
    help="CSV / Excel"
)

if uploaded_files:
    st.success(t["upload_success"].format(len(uploaded_files)))

    if st.button(t["start_button"]):

        with st.spinner(t["processing"]):
            stats, details, execution_time, success_rate, db_path = process_files(uploaded_files)

        st.markdown("---")
        st.markdown(f"### {t['results_title']}")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{stats["total_files"]}</div>
                <div class="metric-label">{t["files_label"]}</div>
            </div>""", unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{stats["success"]}</div>
                <div class="metric-label">{t["success_label"]}</div>
            </div>""", unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{stats["errors"]}</div>
                <div class="metric-label">{t["errors_label"]}</div>
            </div>""", unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{execution_time}s</div>
                <div class="metric-label">{t["time_label"]}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        progress_value = min(max(success_rate / 100, 0.0), 1.0)
        st.progress(progress_value)
        st.caption(t["success_rate"].format(success_rate))

        st.markdown("---")
        st.markdown(f"### {t['details_title']}")

        for item in details:
            with st.expander(f"{item['status']} ← {item['file']}"):
                if "sheet" in item:
                    st.write(f"{t['sheet_label']}**{item['sheet']}**")
                if "rows" in item:
                    st.write(f"{t['rows_label']}**{item['rows']}**")
                if "table" in item:
                    st.write(f"{t['table_label']}**{item['table']}**")
                if "reason" in item:
                    st.warning(item["reason"])
                if "message" in item:
                    st.error(item["message"])
                if "df" in item:
                    st.dataframe(item["df"].head(10), use_container_width=True)

        st.markdown("---")
        st.markdown(f"### {t['download_title']}")

        with open(db_path, "rb") as f:
            st.download_button(
                label=t["download_button"],
                data=f,
                file_name="database.db",
                mime="application/octet-stream"
            )

else:
    st.info(t["upload_hint"])
