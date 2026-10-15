    # 2. نموذج الإدخال الثابت والمحمي بالـ Session State لمنع اختفاء البيانات
    st.subheader("📝 Record New Transaction")
    
    if "form_type" not in st.session_state:
        st.session_state["form_type"] = None

    # إضافة ميزة تفريغ الخانات عبر التحكم بالـ keys وإدخال قيم افتراضية مرنة
    tx_date = st.date_input("Transaction Date:", datetime.date.today(), key="tx_date_key")
    tx_type = st.radio("Transaction Type:", ["Income", "Expense"], index=None, horizontal=True, key="type_radio")
    
    if tx_type == "Income":
        tx_category = st.selectbox("Category البند:", INCOME_CATS, key="income_select")
    elif tx_type == "Expense":
        tx_category = st.selectbox("Category البند:", EXPENSE_CATS, key="expense_select")
    else:
        st.info("💡 Please select Transaction Type (Income / Expense) first to view categories.")
        tx_category = None
        
    tx_amount = st.number_input("Amount (\$):", min_value=0.0, step=10.0, format="%.2f", key="tx_amount_key")
    tx_description = st.text_input("Description / Notes (البيان):", key="tx_description_key")
    
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
            
            # 🔥 الحل السحري: نقوم بمسح قيم الخانات من الذاكرة لتظهر فارغة بعد التحديث
            if "type_radio" in st.session_state: st.session_state["type_radio"] = None
            if "income_select" in st.session_state: del st.session_state["income_select"]
            if "expense_select" in st.session_state: del st.session_state["expense_select"]
            if "tx_amount_key" in st.session_state: st.session_state["tx_amount_key"] = 0.0
            if "tx_description_key" in st.session_state: st.session_state["tx_description_key"] = ""
            
            st.success("✅ Successfully Recorded!")
            st.rerun()
