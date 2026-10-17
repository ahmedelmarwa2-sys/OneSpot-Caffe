import streamlit as st
import pandas as pd
import datetime
import os

# 1. إعدادات الحماية والأمان بالباسورد (تتحقق من السيرفر السحابي)
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.set_page_config(page_title="Login Required", page_icon="🔒", layout="wide")
        st.title("🔒 OneSpot Cafe System - Secure Login")
        st.text_input("Enter Cafe Password:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 OneSpot Cafe System - Secure Login")
        st.text_input("Enter Cafe Password:", type="password", on_change=password_entered, key="password")
        st.error("❌ Incorrect password. Please try again.")
        return False
    else:
        return True

# تشغيل البرنامج بالكامل إذا كانت كلمة المرور صحيحة
if check_password():
    
    # 2. إعدادات البانر الرئيسي بمقاس وسط متناسق وأنيق ومحاذاة مضبوطة
    col_space1, col_img, col_space2 = st.columns([1, 2, 1])
    
    with col_img:
        try:
            st.image("banner.png", use_container_width=True)
        except:
            st.markdown(
                """
                <div style='background: #1a1a1a; padding: 15px; border-radius: 12px; text-align: center; border-bottom: 3px solid #d4af37;'>
                    <h2 style='color: #ffffff; margin: 0; font-family: "Segoe UI", sans-serif;'>OneSpot Cafe</h2>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
    st.markdown(
        """
        <div style='text-align: center; margin-top: 5px; margin-bottom: 25px;'>
            <p style='font-family: "Segoe UI", sans-serif; font-size: 20px; color: #7f8c8d; font-weight: 500; letter-spacing: 1px;'>
                Financial Management System
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    DATA_FILE = "cafe_data.csv"
    
    # قراءة سريعة ومحمية للبيانات
    if os.path.exists(DATA_FILE):
        df_all = pd.read_csv(DATA_FILE)
        df_all = df_all.dropna(subset=["Category", "Amount", "Type"], how="any")
        if "ID" not in df_all.columns:
            df_all.insert(0, "ID", range(1, len(df_all) + 1))
        df_all["ID"] = df_all["ID"].astype(int)
    else:
        df_all = pd.DataFrame(columns=["ID", "Date", "Month_No", "Category", "Type", "Amount", "Description"])
        
    st.markdown("---")
    
    # القوائم الثابتة لبنود الحسابات المدمجة الخاصة بـ OneSpot Cafe
    INCOME_CATS = ["Daily Sales (المبيعات اليوميه)", "Other Income (إيرادات أخرى)"]
    EXPENSE_CATS = [
        "Coffee Beans & Milk (مواد خام)", 
        "Staff Salaries (رواتب الموظفين)", 
        "Rent & Utilities (إيجار وفواتير)", 
        "(valu installments) (اقساط فاليو)", 
        "Packaging (أكواب ومطبوعات)",
        "Other Expense (مصروفات أخرى)"
    ]
    
    # استخدام مفتاح تحديث فريد لتصفير النموذج بنجاح وبدون تداخل
    if "form_version" not in st.session_state:
        st.session_state["form_version"] = 0

    # --- جزء إدخال البيانات فائق السرعة والمحمي مع ميزة التصفير التلقائي الفوري ---
    @st.fragment
    def transaction_form_fragment():
        st.subheader("📝 Record New Transaction")
        
        # ربط الـ key بمتغير التحديث لضمان تصفير الخانات فوراً عند الحفظ
        v = st.session_state["form_version"]
        
        tx_date = st.date_input("Transaction Date:", datetime.date.today(), key=f"dt_{v}")
        tx_type = st.radio("Transaction Type:", ["Income", "Expense"], index=None, horizontal=True, key=f"tp_{v}")
        
        if tx_type == "Income":
            tx_category = st.selectbox("Category البند:", INCOME_CATS, key=f"cat_in_{v}")
        elif tx_type == "Expense":
            tx_category = st.selectbox("Category البند:", EXPENSE_CATS, key=f"cat_ex_{v}")
        else:
            st.info("💡 Please select Transaction Type (Income / Expense) first to view categories.")
            tx_category = None
            
        tx_amount = st.number_input("Amount ($):", min_value=0.0, step=10.0, format="%.2f", key=f"amt_{v}")
        tx_description = st.text_input("Description / Notes (البيان):", key=f"desc_{v}")
        
        if st.button("💾 Save Transaction", type="primary", key=f"btn_{v}"):
            if tx_type is None:
                st.error("⚠️ Please select Transaction Type (Income or Expense)!")
            elif tx_amount == 0 or tx_description == "":
                st.error("⚠️ Please fill in all fields!")
            else:
                global df_all
                next_id = int(df_all["ID"].max() + 1) if not df_all.empty else 1
                new_row = pd.DataFrame([{
                    "ID": next_id,
                    "Date": str(tx_date), 
                    "Month_No": int(tx_date.month), 
                    "Category": tx_category, 
                    "Type": tx_type, 
                    "Amount": tx_amount, 
                    "Description": tx_description
                }])
                df_all = pd.concat([df_all, new_row], ignore_index=True)
                df_all.to_csv(DATA_FILE, index=False)
                
                # تحديث رقم الإصدار لتصفير كافة خانات النموذج فوراً بصمت وبسرعة
                st.session_state["form_version"] += 1
                st.success("✅ Successfully Recorded & Form Cleared!")
                st.rerun()

    # تشغيل نموذج الإدخال السريع والمطور
    transaction_form_fragment()
    st.markdown("---")
    
    # 4. عرض التقارير والجداول المحدثة والتفاعلية (الألسنة الثلاثة)
    tab1, tab2, tab3 = st.tabs(["📊 Monthly Report Dashboard", "📅 Daily Transactions Log", "🗑️ Delete Actions"])
    
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
            
            # احتساب مالي سريع ومباشر ومحسن للأداء
            pivot_df = df_all.pivot_table(index='Month_No', columns='Type', values='Amount', aggfunc='sum').fillna(0).reset_index()
            if 'Income' not in pivot_df.columns: pivot_df['Income'] = 0.0
            if 'Expense' not in pivot_df.columns: pivot_df['Expense'] = 0.0
            
            pivot_df['Net Profit'] = pivot_df['Income'] - pivot_df['Expense']
            months_names = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
            pivot_df['Month'] = pivot_df['Month_No'].map(months_names)
            
            styled_summary = pivot_df.rename(columns={'Income': 'Total Income', 'Expense': 'Total Expense'})[['Month', 'Total Income', 'Total Expense', 'Net Profit']]
            st.dataframe(
                styled_summary.style.format({
                    'Total Income': '${:,.2f}',
                    'Total Expense': '${:,.2f}',
                    'Net Profit': '${:,.2f}'
                }).map(lambda val: 'color: #27ae60; font-weight: bold;' if val > 0 else 'color: #c0392b; font-weight: bold;', subset=['Net Profit']),
                use_container_width=True, 
                hide_index=True
            )
            
            st.subheader("🔍 Breakdown (تحليل بنود الحسابات بالتاريخ)")
            col_inc, col_exp = st.columns(2)
            with col_inc:
                st.write("**Income Analysis (إيرادات بالتاريخ)**")
                st.dataframe(df_all[df_all['Type'] == 'Income'][['Date', 'Category', 'Amount', 'Description']], use_container_width=True, hide_index=True)
            with col_exp:
                st.write("**Expense Analysis (مصروفات بالتاريخ)**")
                st.dataframe(df_all[df_all['Type'] == 'Expense'][['Date', 'Category', 'Amount', 'Description']], use_container_width=True, hide_index=True)
        else:
            st.info("No data available yet.")

    with tab2:
        st.subheader("📅 Daily Transactions Log")
        if not df_all.empty:
            st.dataframe(df_all[["ID", "Date", "Category", "Type", "Amount", "Description"]], use_container_width=True, hide_index=True)
        else:
            st.info("No data available to display.")

    
    with tab3:
        st.subheader("🗑️ Delete a Transaction (مصدر مسح القيود)")
        if not df_all.empty:
            # جزء مسح قيود منعزل وسريع ومحمي داخل التاب الجديدة
            @st.fragment
            def delete_transaction_tab_fragment():
                global df_all

                delete_options = df_all.apply(
                    lambda r: f"ID: {r['ID']} | {r['Date']} | {r['Type']} | ${r['Amount']} | {str(r['Description'])[:30]}...",
                    axis=1
                ).tolist()

                selected_to_delete = st.selectbox(
                    "🎯 اختر القيد الذي تريد مسحه نهائياً من الحسابات:",
                    ["-- اختر القيد --"] + delete_options,
                    key="tab_del_select"
                )

                if selected_to_delete != "-- اختر القيد --":
                    # استخراج الـ ID من أول جزء في النص المختار
                    selected_id = selected_to_delete.split("|")[0].replace("ID:", "").strip()

                    st.write(f"القيد المختار للحذف: {selected_id}")

                    if st.button("🗑️ تأكيد حذف القيد", key="confirm_delete_transaction"):
                        st.warning("أضف هنا كود الحذف الفعلي وحفظ البيانات بعد التأكد من طريقة تخزين معاملاتك.")

            delete_transaction_tab_fragment()
        else:
            st.info("لا توجد قيود متاحة للحذف.")
