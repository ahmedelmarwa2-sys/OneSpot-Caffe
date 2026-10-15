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

# تشغيل البرنامج إذا كان الباسورد صحيحاً
if check_password():
    st.title("☕ One☕spot Cafe Financial Management System")
    
    DATA_FILE = "cafe_data.csv"
    
    def load_data():
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            if "ID" not in df.columns:
                df.insert(0, "ID", range(1, len(df) + 1))
            return df
        else:
            return pd.DataFrame(columns=["ID", "Date", "Month_No", "Category", "Type", "Amount", "Description"])
    
    df_all = load_data()
    st.markdown("---")
    
    # القوائم المحددة الثابتة للبند
    INCOME_CATS = ["Daily Sales", "Event Catering", "Other Income"]
    EXPENSE_CATS = ["Coffee Beans & Milk", "Staff Salaries", "Rent & Utilities", "Maintenance", "Marketing", "Other Expense"]
    
    # 2. نموذج الإدخال الثابت والمحمي بالـ Session State لمنع اختفاء البيانات
    st.subheader("📝 Record New Transaction")
    
    if "form_type" not in st.session_state:
        st.session_state["form_type"] = None

    tx_date = st.date_input("Transaction Date:", datetime.date.today())
    tx_type = st.radio("Transaction Type:", ["Income", "Expense"], index=None, horizontal=True, key="type_radio")
    
    if tx_type == "Income":
        tx_category = st.selectbox("Category البند:", INCOME_CATS, key="income_select")
    elif tx_type == "Expense":
        tx_category = st.selectbox("Category البند:", EXPENSE_CATS, key="expense_select")
    else:
        st.info("💡 Please select Transaction Type (Income / Expense) first to view categories.")
        tx_category = None
        
    tx_amount = st.number_input("Amount (\$):", min_value=0.0, step=10.0, format="%.2f")
    tx_description = st.text_input("Description / Notes (البيان):")
    
    if st.button("💾 Save Transaction", type="primary"):
        if tx_type is None:
            st.error("⚠️ Please select Transaction Type (Income or Expense)!")
        elif tx_amount == 0 or tx_description == "":
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
            st.success("✅ Successfully Recorded!")
            st.rerun()
            
    st.markdown("---")
    
    # 3. عرض التقارير والجداول المحدثة
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
            
            st.subheader("🔍 Expense Breakdown (تحليل بند المصروفات)")
            df_expenses = df_all[df_all['Type'] == 'Expense']
            if not df_expenses.empty:
                expense_breakdown = df_expenses.groupby('Category')['Amount'].sum().reset_index()
                st.dataframe(expense_breakdown.rename(columns={'Category': 'Expense Item', 'Amount': 'Total Spent (\$)'}), use_container_width=True, hide_index=True)
        else:
            st.info("No data recorded yet.")
            
    with tab2:
        st.subheader("All Records Saved")
        st.dataframe(df_all, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("🛠️ Modify or Remove a Transaction")
        if not df_all.empty:
            selected_id = st.selectbox("Select Transaction ID to Action:", df_all["ID"].tolist())
            
            # [التصحيح السحري هنا] أضفنا .iloc[0] لضمان جلب السطر كبيانات مفردة بدون أخطاء تجميعية
            row_data = df_all[df_all["ID"] == selected_id].iloc[0]
            
            st.markdown(f"**Current Data:** Item: `{row_data['Category']}` | Type: `{row_data['Type']}` | Amount: `${row_data['Amount']}` | Note: `{row_data['Description']}`")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Option A: Edit Selected Item**")
                current_type = row_data["Type"]
                cat_options = INCOME_CATS if current_type == "Income" else EXPENSE_CATS
                
                try:
                    default_idx = cat_options.index(row_data["Category"])
                except ValueError:
                    default_idx = 0
                    
                edit_cat = st.selectbox("New Category البند الجديد:", options=cat_options, index=default_idx, key=f"cat_{selected_id}")
                edit_amount = st.number_input("New Amount (\$):", value=float(row_data["Amount"]), key=f"amt_{selected_id}")
                edit_desc = st.text_input("New Description / Notes:", value=str(row_data["Description"]), key=f"dsc_{selected_id}")
                
                if st.button("✏️ Save Changes"):
                    df_all.loc[df_all["ID"] == selected_id, "Category"] = edit_cat
                    df_all.loc[df_all["ID"] == selected_id, "Amount"] = edit_amount
                    df_all.loc[df_all["ID"] == selected_id, "Description"] = edit_desc
                    df_all.to_csv(DATA_FILE, index=False)
                    st.success(f"Transaction ID {selected_id} updated successfully!")
                    st.rerun()
                    
            with col2:
                st.write("**Option B: Delete Selected Item**")
                st.write("Warning: This action cannot be undone.")
                if st.button("🗑️ Permanently Delete", type="primary"):
                    df_all = df_all[df_all["ID"] != selected_id]
                    df_all.to_csv(DATA_FILE, index=False)
                    st.warning(f"Transaction ID {selected_id} has been deleted!")
                    st.rerun()
        else:
            st.info("No data available to edit or delete.")
