import streamlit as st
import pandas as pd
import sqlite3
import os
import re
import json
import time
import datetime

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
                # ======= CSV =======
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

                # ======= Excel =======
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
# 🎨 واجهة Streamlit
# =========================================================

st.set_page_config(
    page_title="محوّل الملفات",
    page_icon="🔄",
    layout="wide"
)

st.title("🔄 محوّل Excel و CSV لقاعدة بيانات")
st.markdown("ارفع ملفاتك وسيتم تحويلها تلقائياً إلى قاعدة بيانات مع تقارير كاملة")

st.divider()

# ======= رفع الملفات =======
uploaded_files = st.file_uploader(
    "📂 ارفع ملفاتك هنا",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"📁 تم رفع {len(uploaded_files)} ملف")

    if st.button("🚀 ابدأ المعالجة", type="primary"):

        with st.spinner("⏳ جاري المعالجة..."):
            stats, details, execution_time, success_rate, db_path = process_files(uploaded_files)

        st.divider()

        # ======= الإحصاءات =======
        st.subheader("📊 النتائج")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("📁 الملفات", stats["total_files"])
        col2.metric("✅ نجاح", stats["success"])
        col3.metric("❌ أخطاء", stats["errors"])
        col4.metric("⏱️ الوقت", f"{execution_time}s")

        st.progress(success_rate / 100)
        st.caption(f"نسبة النجاح: {success_rate}%")

        st.divider()

        # ======= تفاصيل كل ملف =======
        st.subheader("📋 تفاصيل الملفات")

        for item in details:
            with st.expander(f"{item['status']} - {item['file']}"):

                if "sheet" in item:
                    st.write(f"📄 الشيت: {item['sheet']}")

                if "rows" in item:
                    st.write(f"📝 عدد الصفوف: {item['rows']}")

                if "table" in item:
                    st.write(f"🗄️ اسم الجدول: {item['table']}")

                if "reason" in item:
                    st.warning(f"السبب: {item['reason']}")

                if "message" in item:
                    st.error(f"الخطأ: {item['message']}")

                if "df" in item:
                    st.dataframe(item["df"].head(10))

        st.divider()

        # ======= تحميل قاعدة البيانات =======
        st.subheader("💾 تحميل النتائج")

        with open(db_path, "rb") as f:
            st.download_button(
                label="⬇️ تحميل قاعدة البيانات",
                data=f,
                file_name="database.db",
                mime="application/octet-stream"
            )

else:
    st.warning("👆 ارفع ملف CSV أو Excel للبدء")