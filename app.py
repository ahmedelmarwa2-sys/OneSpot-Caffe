import streamlit as st
import pandas as pd
import datetime
import os

# 1. إعدادات الصفحة والعنوان
st.set_page_config(page_title="Cafe System", page_icon="☕", layout="wide")
st.title("☕ Cafe Financial Management System")

# اسم ملف البيانات الذي سيتم حفظ الحسابات داخله
DATA_FILE = "cafe_data.csv"

# دالة لتحميل البيانات من الملف أو إنشاء جدول فارغ إذا كان الملف جديداً
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["Date", "Month_No", "Description", "Type", "Amount"])

df_all = load_data()

st.markdown("---")

# 2. تصميم نموذج الإدخال (Form)
st.subheader("📝 Record New Transaction")
with st.form(key="cafe_entry_form", clear_on_submit=True):
    tx_date = st.date_input("Transaction Date:", datetime.date.today())
    tx_type = st.radio("Transaction Type:", ["Income", "Expense"], horizontal=True)
    tx_amount = st.number_input("Amount ($):", min_value=0.0, step=10.0, format="%.2f")
    tx_description = st.text_input("Description / Notes:")
    
    submit_button = st.form_submit_button(label="Save & Update")

# عند الضغط على زر الحفظ
if submit_button:
    if tx_amount == 0:
        st.error("⚠️ Please enter an amount greater than 0!")
    elif tx_description == "":
        st.error("⚠️ Please enter a description!")
    else:
        # تجهيز السطر الجديد لحفظه
        new_row = pd.DataFrame([{
            "Date": str(tx_date),
            "Month_No": tx_date.month,
            "Description": tx_description,
            "Type": tx_type,
            "Amount": tx_amount
        }])
        
        # إضافة السطر الجديد وحفظ الملف
        df_all = pd.concat([df_all, new_row], ignore_index=True)
        df_all.to_csv(DATA_FILE, index=False)
        
        st.success(f"✅ Successfully Recorded!")
        st.balloons()

st.markdown("---")

# 3. عرض التقارير والجداول التلقائية
tab1, tab2 = st.tabs(["📊 Monthly Report Dashboard", "📅 Daily Transactions Log"])

with tab1:
    st.subheader("Monthly Performance (Profit & Loss)")
    if not df_all.empty:
        # تجميع الحسابات ذكياً حسب الشهور
        df_all['Amount'] = pd.to_numeric(df_all['Amount'])
        df_all['Month_No'] = pd.to_numeric(df_all['Month_No'])
        
        monthly_summary = df_all.groupby('Month_No').apply(lambda x: pd.Series({
            'Total Income': x[x['Type'] == 'Income']['Amount'].sum(),
            'Total Expense': x[x['Type'] == 'Expense']['Amount'].sum(),
            'Net Profit': x[x['Type'] == 'Income']['Amount'].sum() - x[x['Type'] == 'Expense']['Amount'].sum()
        })).reset_index()
        
        # تحويل أرقام الشهور لأسماء مفهومة
        months_names = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
        monthly_summary['Month'] = monthly_summary['Month_No'].map(months_names)
        
        # عرض الجدول النهائي
        st.dataframe(monthly_summary[['Month', 'Total Income', 'Total Expense', 'Net Profit']], use_container_width=True, hide_index=True)
    else:
        st.info("No data recorded yet.")

with tab2:
    st.subheader("All Records Saved")
    st.dataframe(df_all, use_container_width=True, hide_index=True)
