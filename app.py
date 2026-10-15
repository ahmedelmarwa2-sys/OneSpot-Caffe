import streamlit as st
import pandas as pd
import datetime
import os

# 1. إعدادات الحماية والأمان بالباسورد
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.set_page_config(page_title="Login Required", page_icon="🔒")
        st.title("🔒 Cafe System - Secure Login")
        st.text_input("Enter Cafe Password:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 Cafe System - Secure Login")
        st.text_input("Enter Cafe Password:", type="password", on_change=password_entered, key="password")
        st.error("❌ Incorrect password. Please try again.")
        return False
    else:
        return True

# تشغيل البرنامج إذا كان الباسورد صحيحاً
if check_password():
    st.title("☕ Cafe Financial Management System")
    
    DATA_FILE = "cafe_data.csv"
    
    def load_data():
        if os.path.exists(DATA_FILE):
            return pd.read_csv(DATA_FILE)
        else:
            # أضفنا عمود جديد باسم Sub_Category للقائمة المنسدلة
            return pd.DataFrame(columns=["Date", "Month_No", "Category", "Type", "Amount", "Description"])
    
    df_all = load_data()
    st.markdown("---")
    
    # 2. تصميم نموذج الإدخال (Form) المطور بالقوائم المنسدلة
    st.subheader("📝 Record New Transaction")
    with st.form(key="cafe_entry_form", clear_on_submit=True):
        tx_date = st.date_input("Transaction Date:", datetime.date.today())
        tx_type = st.radio("Transaction Type:", ["Income", "Expense"], horizontal=True)
        
        # القائمة المنسدلة الذكية: تتغير محتوياتها تلقائياً بناءً على اختيارك (إيرادات أم مصروفات)
        if tx_type == "Income":
            tx_category = st.selectbox("Category البند:", ["Daily Sales", "Event Catering", "Other Income"])
        else:
            tx_category = st.selectbox("Category البند:", ["Coffee Beans & Milk", "Staff Salaries", "Rent & Utilities", "Maintenance", "Marketing", "Other Expense"])
            
        tx_amount = st.number_input("Amount ($):", min_value=0.0, step=10.0, format="%.2f")
        tx_description = st.text_input("Description / Notes (البيان):")
        
        submit_button = st.form_submit_button(label="Save & Update")
    
    if submit_button:
        if tx_amount == 0 or tx_description == "":
            st.error("⚠️ Please fill in all fields!")
        else:
            # ترحيل البيانات بالبند الجديد
            new_row = pd.DataFrame([{
                "Date": str(tx_date), 
                "Month_No": tx_date.month, 
                "Category": tx_category, 
                "Type": tx_type, 
                "Amount": tx_amount, 
                "Description": tx_description
            }])
            df_all = pd.concat([df_all, new_row], ignore_index=True)
            df_all.to_csv(DATA_FILE, index=False)
            st.success("✅ Successfully Recorded!")
            st.balloons()
            
    st.markdown("---")
    
    # 3. عرض التقارير والجداول المحدثة
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
            
            # ميزة جديدة: جدول تحليل المصروفات حسب كل بند
            st.subheader("🔍 Expense Breakdown (تحليل بند المصروفات)")
            df_expenses = df_all[df_all['Type'] == 'Expense']
            if not df_expenses.empty:
                expense_breakdown = df_expenses.groupby('Category')['Amount'].sum().reset_index()
                st.dataframe(expense_breakdown.rename(columns={'Category': 'Expense Item', 'Amount': 'Total Spent ($)'}), use_container_width=True, hide_index=True)
        else:
            st.info("No data recorded yet.")
            
    with tab2:
        st.subheader("All Records Saved")
        st.dataframe(df_all, use_container_width=True, hide_index=True)
