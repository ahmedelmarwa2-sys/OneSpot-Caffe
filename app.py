import streamlit as st
import pandas as pd
import datetime
import os

# ضبط إعدادات الصفحة لتكون عريضة واحترافية من أول سطر
st.set_page_config(page_title="OneSpot Cafe System", page_icon="☕", layout="wide")

# 1. إعدادات الحماية والأمان بالباسورد (نسخة التشغيل المحلي)
def check_password():
    def password_entered():
        if st.session_state["password"] == "1234":  
            st.session_state["password_correct"] = True
            del st.session_state["password"]  
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
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

if check_password():
    
    # 2. إعدادات البانر الرئيسي بمقاس وسط متناسق وأنيق
    col_space1, col_img, col_space2 = st.columns([1, 2, 1])
    with col_img:
        try:
            st.image("banner.png", use_container_width=True)
        except:
            st.markdown("<div style='background: #1a1a1a; padding: 15px; border-radius: 12px; text-align: center; border-bottom: 3px solid #d4af37;'><h2 style='color: #ffffff; margin: 0; font-family: \"Segoe UI\", sans-serif;'>OneSpot Cafe</h2></div>", unsafe_allow_html=True)
        
    st.markdown("<div style='text-align: center; margin-top: 5px; margin-bottom: 25px;'><p style='font-family: \"Segoe UI\", sans-serif; font-size: 20px; color: #7f8c8d; font-weight: 500; letter-spacing: 1px;'>Financial Management System</p></div>", unsafe_allow_html=True)
    
    DATA_FILE = "cafe_data.csv"
    columns_layout = ["ID", "Date", "Month_No", "Category", "Type", "Amount", "Description"]
    
    # دالة قراءة وتأمين البيانات وبنائها برمجياً لكسر التلف القديم
    def load_data():
        if os.path.exists(DATA_FILE):
            try:
                df = pd.read_csv(DATA_FILE)
                # إذا تسبب الملف القديم في قراءة فارغة أو مكسورة، يتم تصفيره وبنائه فوراً
                if df.empty or not isinstance(df, pd.DataFrame) or "Amount" not in df.columns:
                    return pd.DataFrame(columns=columns_layout)
                
                # إجبار الأعمدة على التطابق التام
                for col in columns_layout:
                    if col not in df.columns:
                        df[col] = ""
                
                # تأمين أرقام الـ ID والعمليات الحسابية
                df["ID"] = range(1, len(df) + 1)
                df["Amount"] = pd.to_numeric(df["Amount"], errors='coerce').fillna(0.0)
                df["Month_No"] = pd.to_numeric(df["Month_No"], errors='coerce').fillna(1).astype(int)
                df["Date"] = df["Date"].astype(str)
                df["Category"] = df["Category"].astype(str)
                df["Type"] = df["Type"].astype(str)
                df["Description"] = df["Description"].astype(str)
                return df
            except:
                return pd.DataFrame(columns=columns_layout)
        else:
            return pd.DataFrame(columns=columns_layout)
    
    df_all = load_data()
    st.markdown("---")
    
    # القوائم الثابتة لبنود الحسابات المدمجة
    INCOME_CATS = ["Takeaway (سفره وسيارة)", "Daily Sales (المبيعات اليوميه)", "PS (play staion)", "Other Income (إيرادات أخرى)"]
    EXPENSE_CATS = ["Coffee Beans & Milk (مواد خام)", "Staff Salaries (رواتب الموظفين)", "Rent & Utilities (إيجار وفواتير)", "(valu installments) (اقساط فاليو)", "Packaging (أكواب ومطبوعات)", "Other Expense (مصروفات أخرى)"]
    
    # 3. نموذج الإدخال الذكي مع تصفية البنود تلقائياً بعد اختيار النوع
    st.subheader("📝 Record New Transaction")
    
    if "radio_reset_key" not in st.session_state:
        st.session_state["radio_reset_key"] = 0
        
    tx_type = st.radio("Transaction Type:", ["Income", "Expense"], index=None, horizontal=True, key=f"type_radio_{st.session_state['radio_reset_key']}")
    
    if tx_type == "Income":
        current_cats = INCOME_CATS
    elif tx_type == "Expense":
        current_cats = EXPENSE_CATS
    else:
        current_cats = []
        st.info("💡 Please select Transaction Type (Income / Expense) first to view categories.")
        
    if tx_type is not None:
        with st.form(key=f"cafe_entry_form_{st.session_state['radio_reset_key']}", clear_on_submit=True):
            tx_date = st.date_input("Transaction Date:", datetime.date.today())
            tx_category = st.selectbox("Category البند:", current_cats)
            tx_amount = st.number_input("Amount ($):", min_value=0.0, step=10.0, format="%.2f")
            tx_description = st.text_input("Description / Notes (البيان):")
            submit_button = st.form_submit_button(label="💾 Save Transaction", type="primary")
        
        if submit_button:
            if tx_amount == 0 or tx_description == "":
                st.error("⚠️ Please fill in all fields!")
            else:
                next_id = int(df_all["ID"].max() + 1) if not df_all.empty else 1
                new_row = pd.DataFrame([{"ID": next_id, "Date": str(tx_date), "Month_No": int(tx_date.month), "Category": tx_category, "Type": tx_type, "Amount": float(tx_amount), "Description": tx_description}])
                df_all = pd.concat([df_all, new_row], ignore_index=True)
                df_all.to_csv(DATA_FILE, index=False)
                st.session_state["radio_reset_key"] += 1
                st.success("✅ Successfully Recorded!")
                st.rerun()  
                
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📊 Monthly Report Dashboard", "📅 Daily Transactions Log", "🛠️ Edit / Delete Actions"])

    with tab1:
        st.subheader("Monthly Performance (Profit & Loss)")
            
        if not df_all.empty:
            # احتساب الإجماليات والتقارير
            total_income_all = df_all[df_all['Type'] == 'Income']['Amount'].sum()
            total_expense_all = df_all[df_all['Type'] == 'Expense']['Amount'].sum()
            net_profit_all = total_income_all - total_expense_all
            
            # عرض لوحة التحكم التفاعلية
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric(label="Total Income (إجمالي الإيرادات)", value=f"${total_income_all:,.2f}")
            m_col2.metric(label="Total Expenses (إجمالي المصروفات)", value=f"${total_expense_all:,.2f}")
            m_col3.metric(label="Net Profit (صافي الربح الكلي)", value=f"${net_profit_all:,.2f}", delta=f"${net_profit_all:,.2f}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            monthly_summary = df_all.groupby('Month_No').apply(lambda x: pd.Series({'Total Income': x[x['Type'] == 'Income']['Amount'].sum(), 'Total Expense': x[x['Type'] == 'Expense']['Amount'].sum(), 'Net Profit': x[x['Type'] == 'Income']['Amount'].sum() - x[x['Type'] == 'Expense']['Amount'].sum()}), include_groups=False).reset_index()
            months_names = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
            monthly_summary['Month'] = monthly_summary['Month_No'].map(months_names)
            
            st.dataframe(monthly_summary[['Month', 'Total Income', 'Total Expense', 'Net Profit']], use_container_width=True, hide_index=True)
            
            st.markdown("<br><hr style='border: 1px dashed #ccc;'><br>", unsafe_allow_html=True)
            st.subheader("🔍 Breakdown (تحليل بنود الحسابات بالتاريخ)")
            
            col_inc, col_exp = st.columns(2)
            df_inc = df_all[df_all['Type'] == 'Income']
            df_expenses = df_all[df_all['Type'] == 'Expense']
            
            inc_html_rows = ""
            exp_html_rows = ""
            
            with col_inc:
                st.write("**Income Analysis (الإيرادات بالتاريخ)**")
                if not df_inc.empty:
                    inc_grouped = df_inc.groupby(['Date', 'Category'])['Amount'].sum().reset_index()
                    st.dataframe(inc_grouped.rename(columns={'Date': 'Date التاريخ', 'Category': 'Income Item', 'Amount': 'Total Income ($)'}), use_container_width=True, hide_index=True)
                    for _, row in inc_grouped.iterrows():
                        inc_html_rows += f"<tr><td>{row['Date']}</td><td>{row['Category']}</td><td>${row['Amount']:,.2f}</td></tr>"
                else:
                    st.write("No income recorded.")
                    inc_html_rows = "<tr><td colspan='3'>No income data.</td></tr>"
                    
            with col_exp:
                st.write("**Expense Analysis (المصروفات بالتاريخ)**")
                if not df_expenses.empty:
                    exp_grouped = df_expenses.groupby(['Date', 'Category'])['Amount'].sum().reset_index()
                    st.dataframe(exp_grouped.rename(columns={'Date': 'Date التاريخ', 'Category': 'Expense Item', 'Amount': 'Total Spent ($)'}), use_container_width=True, hide_index=True)
                    for _, row in exp_grouped.iterrows():
                        exp_html_rows += f"<tr><td>{row['Date']}</td><td>{row['Category']}</td><td>${row['Amount']:,.2f}</td></tr>"
                else:
                    st.write("No expenses recorded.")
                    exp_html_rows = "<tr><td colspan='3'>No expense data.</td></tr>"

            summary_html_rows = ""
            for _, row in monthly_summary.iterrows():
                profit_color = "#27ae60" if row['Net Profit'] >= 0 else "#c0392b"
