import streamlit as st
import pandas as pd
import datetime
import os

# 1. إعدادات الحماية والأمان (تتحقق من وجود كلمة المرور في السيرفر)
def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        # جلب كلمة المرور السرية المخزنة بأمان في السيرفر
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # حذفها من الذاكرة للأمان
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # شاشة تسجيل الدخول الأولى
        st.set_page_config(page_title="Login Required", page_icon="🔒")
        st.title("🔒 Cafe System - Secure Login")
        st.text_input("Enter Cafe Password:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # إذا كتب كلمة مرور خاطئة
        st.title("🔒 Cafe System - Secure Login")
        st.text_input("Enter Cafe Password:", type="password", on_change=password_entered, key="password")
        st.error("❌ Incorrect password. Please try again.")
        return False
    else:
        return True

# إذا كانت كلمة المرور صحيحة، يعرض البرنامج بالكامل بالأسفل
if check_password():
    
    # 2. إعدادات الصفحة والعنوان الرئيسي
    st.title("☕ Cafe Financial Management System")
    
    DATA_FILE = "cafe_data.csv"
    
    def load_data():
        if os.path.exists(DATA_FILE):
            return pd.read_csv(DATA_FILE)
        else:
            return pd.DataFrame(columns=["Date", "Month_No", "Description", "Type", "Amount"])
    
    df_all = load_data()
    st.markdown("---")
    
    # 3. نموذج الإدخال (Form)
    st.subheader("📝 Record New Transaction")
    with st.form(key="cafe_entry_form", clear_on_submit=True):
        tx_date = st.date_input("Transaction Date:", datetime.date.today())
        tx_type = st.radio("Transaction Type:", ["Income", "Expense"], horizontal=True)
        tx_amount = st.number_input("Amount ($):", min_value=0.0, step=10.0, format="%.2f")
        tx_description = st.text_input("Description / Notes:")
        submit_button = st.form_submit_button(label="Save & Update")
    
    if submit_button:
        if tx_amount == 0 or tx_description == "":
            st.error("⚠️ Please fill in all fields!")
        else:
            new_row = pd.DataFrame([{"Date": str(tx_date), "Month_No": tx_date.month, "Description": tx_description, "Type": tx_type, "Amount": tx_amount}])
            df_all = pd.concat([df_all, new_row], ignore_index=True)
            df_all.to_csv(DATA_FILE, index=False)
            st.success("✅ Successfully Recorded!")
            st.balloons()
            
    st.markdown("---")
    
    # 4. عرض التقارير والجداول
    tab1, tab2 = st.tabs(["📊 Monthly Report Dashboard", "📅 Daily Transactions Log"])
    with tab1:
        st.subheader("Monthly Performance (Profit & Loss)")
        if not df_all.empty:
            df_all['Amount'] = pd.to_numeric(df_all['Amount'])
            df_all['Month_No'] = pd.to_numeric(df_all['Month_No'])
            monthly_summary = df_all.groupby('Month_No').apply(lambda x: pd.Series({
                'Total Income': x[x['Type'] == 'Income']['Amount'].sum(),
                'Total Expense': x[x['Type'] == 'Expense']['Amount'].sum(),
                'Net Profit': x[x['Type'] == 'Income']['Amount'].sum() - x[x['Type'] == 'Expense']['Amount'].sum()
            })).reset_index()
            months_names = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
            monthly_summary['Month'] = monthly_summary['Month_No'].map(months_names)
            st.dataframe(monthly_summary[['Month', 'Total Income', 'Total Expense', 'Net Profit']], use_container_width=True, hide_index=True)
        else:
            st.info("No data recorded yet.")
    with tab2:
        st.subheader("All Records Saved")
        st.dataframe(df_all, use_container_width=True, hide_index=True)
