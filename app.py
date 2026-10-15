import streamlit as st
import pandas as pd
import datetime
import os
import io

# 1. إعدادات الحماية والأمان بالباسورد (نسخة التشغيل المحلي)
def check_password():
    def password_entered():
        if st.session_state["password"] == "1234":  
            st.session_state["password_correct"] = True
            del st.session_state["password"]  
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.set_page_config(page_title="Login Required", page_icon="🔒", layout="wide")
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
    col_space1, col_img, col_space2 = st.columns([1, 3, 1])
    with col_img:
        try:
            st.image("banner.png", use_container_width=True)
        except:
            st.markdown("<div style='background: #1a1a1a; padding: 15px; border-radius: 12px; text-align: center; border-bottom: 3px solid #d4af37;'><h2 style='color: #ffffff; margin: 0; font-family: \"Segoe UI\", sans-serif;'>OneSpot Cafe</h2></div>", unsafe_allow_html=True)
        
    st.markdown("<div style='text-align: center; margin-top: 5px; margin-bottom: 25px;'><p style='font-family: \"Segoe UI\", sans-serif; font-size: 20px; color: #7f8c8d; font-weight: 500; letter-spacing: 1px;'>Financial Management System</p></div>", unsafe_allow_html=True)
    
    DATA_FILE = "cafe_data.csv"
    
    def load_data():
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            df = df.dropna(subset=["Category", "Amount", "Type"], how="any")
            if "ID" not in df.columns:
                df.insert(0, "ID", range(1, len(df) + 1))
            return df
        else:
            return pd.DataFrame(columns=["ID", "Date", "Month_No", "Category", "Type", "Amount", "Description"])
    
    df_all = load_data()
    
    st.markdown("---")
    st.subheader("📝 Record New Transaction")
    
    if "radio_reset_key" not in st.session_state:
        st.session_state["radio_reset_key"] = 0
        
    tx_type = st.radio("Transaction Type:", ["Income", "Expense"], index=None, horizontal=True, key=f"type_radio_{st.session_state['radio_reset_key']}")
    
    INCOME_CATS = ["Takeaway (سفره وسيارة)", "Daily Sales (المبيعات اليوميه)", "PS (play staion)", "Other Income (إيرادات أخرى)"]
    EXPENSE_CATS = ["Coffee Beans & Milk (مواد خام)", "Staff Salaries (رواتب الموظفين)", "Rent & Utilities (إيجار وفواتير)", "(valu installments) (اقساط فاليو)", "Packaging (أكواب ومطبوعات)", "Other Expense (مصروفات أخرى)"]
    
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
                new_row = pd.DataFrame([{"ID": next_id, "Date": str(tx_date), "Month_No": tx_date.month, "Category": tx_category, "Type": tx_type, "Amount": tx_amount, "Description": tx_description}])
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
            df_all['Amount'] = pd.to_numeric(df_all['Amount'])
            df_all['Month_No'] = pd.to_numeric(df_all['Month_No'])
            
            total_income_all = df_all[df_all['Type'] == 'Income']['Amount'].sum()
            total_expense_all = df_all[df_all['Type'] == 'Expense']['Amount'].sum()
            net_profit_all = total_income_all - total_expense_all
            
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric(label="Total Income (إجمالي الإيرادات)", value=f"${total_income_all:,.2f}")
            m_col2.metric(label="Total Expenses (إجمالي المصروفات)", value=f"${total_expense_all:,.2f}")
            m_col3.metric(label="Net Profit (صافي الربح الكلي)", value=f"${net_profit_all:,.2f}", delta=f"${net_profit_all:,.2f}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # حساب جدول الأداء الشهري
            monthly_summary = df_all.groupby('Month_No').apply(lambda x: pd.Series({'Total Income': x[x['Type'] == 'Income']['Amount'].sum(), 'Total Expense': x[x['Type'] == 'Expense']['Amount'].sum(), 'Net Profit': x[x['Type'] == 'Income']['Amount'].sum() - x[x['Type'] == 'Expense']['Amount'].sum()}), include_groups=False).reset_index()
            months_names = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
            monthly_summary['Month'] = monthly_summary['Month_No'].map(months_names)
            
            styled_summary = monthly_summary[['Month', 'Total Income', 'Total Expense', 'Net Profit']]
            st.dataframe(styled_summary, use_container_width=True, hide_index=True)
            
            st.markdown("<br><hr style='border: 1px dashed #ccc;'><br>", unsafe_allow_html=True)
            st.subheader("🔍 Breakdown (تحليل بنود الحسابات بالتاريخ)")
            
            col_inc, col_exp = st.columns(2)
            df_inc = df_all[df_all['Type'] == 'Income']
            df_expenses = df_all[df_all['Type'] == 'Expense']
            
            inc_data = pd.DataFrame()
            exp_data = pd.DataFrame()
            
            with col_inc:
                st.write("**Income Analysis (الإيرادات بالتاريخ)**")
                if not df_inc.empty:
                    inc_data = df_inc.groupby(['Date', 'Category'])['Amount'].sum().reset_index().rename(columns={'Date': 'Date التاريخ', 'Category': 'Income Item', 'Amount': 'Total Income ($)'})
                    st.dataframe(inc_data, use_container_width=True, hide_index=True)
                else:
                    st.write("No income recorded.")
            with col_exp:
                st.write("**Expense Analysis (المصروفات بالتاريخ)**")
                if not df_expenses.empty:
                    exp_data = df_expenses.groupby(['Date', 'Category'])['Amount'].sum().reset_index().rename(columns={'Date': 'Date التاريخ', 'Category': 'Expense Item', 'Amount': 'Total Spent ($)'})
                    st.dataframe(exp_data, use_container_width=True, hide_index=True)
                else:
                    st.write("No expenses recorded.")
            
            # بناء التقرير المدمج الجديد للطباعة الفورية
            st.markdown("<br><hr>", unsafe_allow_html=True)
            st.subheader("📥 تصدير التقرير والتحليل للطباعة")
            
            output = io.StringIO()
            output.write("--- ONE SPOT CAFE - MONTHLY PERFORMANCE REPORT ---\n\n")
            output.write(f"Report Date: {datetime.date.today()}\n")
            output.write(f"Total Income: ${total_income_all:,.2f} | Total Expenses: ${total_expense_all:,.2f} | Net Profit: ${net_profit_all:,.2f}\n\n")
            
            output.write("1. SUMMARY PER MONTH (ملخص الأداء الشهري):\n")
            styled_summary.to_csv(output, index=False)
            
            output.write("\n\n2. BREAKDOWN: INCOME ANALYSIS (تحليل بنود الإيرادات بالتاريخ):\n")
            if not inc_data.empty:
                inc_data.to_csv(output, index=False)
            else:
                output.write("No income data recorded.\n")
                
            output.write("\n\n3. BREAKDOWN: EXPENSE ANALYSIS (تحليل بنود المصروفات بالتاريخ):\n")
            if not exp_data.empty:
                exp_data.to_csv(output, index=False)
            else:
                output.write("No expense data recorded.\n")
                
            combined_csv = output.getvalue().encode('utf-8-sig')
            
            # زر التحميل الموحد الكبير والمميز لطباعة التقرير الشامل (تم إغلاق الأقواس بالكامل)
            st.download_button(
                label="🖨️ تحميل تقرير الأداء المجمع + تحليل البنود بالتاريخ (Excel جاهز للطباعة)",
                data=combined_csv,
                file_name=f"OneSpot_Full_Financial_Report_{datetime.date.today()}.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
            
        else:
            st.info("No data recorded yet.")
                
    with tab2:
