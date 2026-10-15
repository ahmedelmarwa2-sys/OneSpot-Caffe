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
    
    # 2. إعدادات العنوان الرئيسي والشعار
    col_logo, col_title = st.columns(2)
    with col_logo:
        try:
            st.image("logo.png", width=90)
        except:
            st.write("☕") 
    with col_title:
        st.title("Onespot Cafe Financial Management System")
    
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
    
    # القوائم الثابتة لبنود الحسابات المدمجة
    INCOME_CATS = [
        "Dine-in Sales (مبيعات الصالة)", 
        "Takeaway/Drive-thru (سفري وسيارة)", 
        "Delivery Sales (مبيعات التوصيل)", 
        "Retail Sales (بن وأدوات تجزئة)",
        "Event Catering (ضيافة وفعاليات)", 
        "Other Income (إيرادات أخرى)"
    ]
    EXPENSE_CATS = [
        "Coffee Beans & Milk (مواد خام)", 
        "Staff Salaries (رواتب الموظفين)", 
        "Rent & Utilities (إيجار وفواتير)", 
        "Maintenance (صيانة آلات)", 
        "Marketing (تسويق وإعلانات)", 
        "Packaging (أكواب ومطبوعات)",
        "Other Expense (مصروفات أخرى)"
    ]
    
    # 3. نموذج الإدخال الذكي مع تصفية البنود تلقائياً بعد اختيار النوع
    st.subheader("📝 Record New Transaction")
    
    if "radio_reset_key" not in st.session_state:
        st.session_state["radio_reset_key"] = 0
        
    tx_type = st.radio(
        "Transaction Type:", 
        ["Income", "Expense"], 
        index=None, 
        horizontal=True,
        key=f"type_radio_{st.session_state['radio_reset_key']}"
    )
    
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
            tx_amount = st.number_input("Amount (\$):", min_value=0.0, step=10.0, format="%.2f")
            tx_description = st.text_input("Description / Notes (البيان):")
            
            submit_button = st.form_submit_button(label="💾 Save Transaction", type="primary")
        
        if submit_button:
            if tx_amount == 0 or tx_description == "":
                st.error("⚠️ Please fill in all fields!")
            else:
                next_id = int(df_all["ID"].max() + 1) if not df_all.empty else 1
                new_row = pd.DataFrame([{
                    "ID": next_id,
                    "Date": str(tx_date), 
                    "Month_No": tx_date.month, 
                    "Category": tx_category, 
                    "Type": tx_type, 
                    "Amount": tx_amount, 
                    "Description": tx_description
                }])
                df_all = pd.concat([df_all, new_row], ignore_index=True)
                df_all.to_csv(DATA_FILE, index=False)
                
                st.session_state["radio_reset_key"] += 1
                st.success("✅ Successfully Recorded!")
                st.rerun()  
                
    st.markdown("---")
    
    # 4. عرض التقارير والجداول التفاعلية (الألسنة الثلاثة)
    tab1, tab2, tab3 = st.tabs(["📊 Monthly Report Dashboard", "📅 Daily Transactions Log", "🛠️ Edit / Delete Actions"])
    
    with tab1:
        st.subheader("Monthly Performance (Profit & Loss)")
        if not df_all.empty:
            df_all['Amount'] = pd.to_numeric(df_all['Amount'])
            df_all['Month_No'] = pd.to_numeric(df_all['Month_No'])
            
            monthly_summary = df_all.groupby('Month_No').apply(lambda x: pd.Series({
                'Total Income': x[x['Type'] == 'Income']['Amount'].sum(),
                'Total Expense': x[x['Type'] == 'Expense']['Amount'].sum(),
                'Net Profit': x[x['Type'] == 'Income']['Amount'].sum() - x[x['Type'] == 'Expense']['Amount'].sum()
            }), include_groups=False).reset_index()
            
            months_names = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
            monthly_summary['Month'] = monthly_summary['Month_No'].map(months_names)
            st.dataframe(monthly_summary[['Month', 'Total Income', 'Total Expense', 'Net Profit']], use_container_width=True, hide_index=True)
            
            st.subheader("🔍 Breakdown (تحليل بنود الحسابات بالتاريخ)")
            col_inc, col_exp = st.columns(2)
            with col_inc:
                st.write("**Income Analysis (الإيرادات بالتاريخ)**")
                df_inc = df_all[df_all['Type'] == 'Income']
                if not df_inc.empty:
                    inc_breakdown = df_inc.groupby(['Date', 'Category'])['Amount'].sum().reset_index()
                    st.dataframe(inc_breakdown.rename(columns={'Date': 'Date التاريخ', 'Category': 'Income Item', 'Amount': 'Total Income (\$)'}), use_container_width=True, hide_index=True)
                else:
                    st.write("No income recorded.")
            with col_exp:
                st.write("**Expense Analysis (المصروفات بالتاريخ)**")
                df_expenses = df_all[df_all['Type'] == 'Expense']
                if not df_expenses.empty:
                    expense_breakdown = df_expenses.groupby(['Date', 'Category'])['Amount'].sum().reset_index()
                    st.dataframe(expense_breakdown.rename(columns={'Date': 'Date التاريخ', 'Category': 'Expense Item', 'Amount': 'Total Spent (\$)'}), use_container_width=True, hide_index=True)
                else:
                    st.write("No expenses recorded.")
        else:
            st.info("No data recorded yet.")
            
    with tab2:
        st.subheader("All Records Saved")
        if not df_all.empty:
            st.dataframe(df_all, use_container_width=True, hide_index=True)
        else:
            st.info("No data recorded yet.")

    with tab3:
        st.subheader("🛠️ Modify or Remove a Transaction")
        if not df_all.empty:
            selected_id = st.selectbox("Select Transaction ID to Action:", df_all["ID"].tolist())
            row_filtered = df_all[df_all["ID"] == selected_id]
            
            if not row_filtered.empty:
                # [التعديل الجوهري الحاسم]: إضافة [0] بعد iloc لاستخراج السطر كقيم مفردة وصافية تماماً لإصلاح الـ Bug نهائياً
                row_data = row_filtered.iloc[0]
                
                curr_date = str(row_data["Date"])
                curr_cat = str(row_data["Category"])
                curr_type = str(row_data["Type"])
                curr_amount = float(row_data["Amount"])
                curr_desc = str(row_data["Description"])
                
                st.info(f"📋 **Current Active Record:** ID: `{selected_id}` | Date: `{curr_date}` | Item: `{curr_cat}` | Type: `{curr_type}` | Amount: `${curr_amount}`")
                st.markdown("---")
                
                st.subheader("✏️ Option 1: Edit & Update Record")
                cat_options = INCOME_CATS if curr_type == "Income" else EXPENSE_CATS
                try:
                    default_idx = cat_options.index(curr_cat)
                except ValueError:
                    default_idx = 0
                    
                edit_cat = st.selectbox("New Category البند الجديد:", options=cat_options, index=default_idx, key=f"cat_{selected_id}")
                edit_amount = st.number_input("New Amount (\$):", value=curr_amount, key=f"amt_{selected_id}")
                edit_desc = st.text_input("New Description / Notes:", value=curr_desc, key=f"dsc_{selected_id}")
                
                if st.button("💾 Save Changes and Update"):
                    df_all.loc[df_all["ID"] == selected_id, "Category"] = edit_cat
                    df_all.loc[df_all["ID"] == selected_id, "Amount"] = edit_amount
                    df_all.loc[df_all["ID"] == selected_id, "Description"] = edit_desc
                    df_all.to_csv(DATA_FILE, index=False)
                    st.success(f"Transaction ID {selected_id} updated successfully!")
                    st.rerun()
                    
                st.markdown("---")
                st.subheader("🗑️ Option 2: Delete Record")
                st.warning("⚠️ Warning: This action cannot be undone. Clicking below will erase this transaction permanently.")
                
