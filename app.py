    # 2. نموذج الإدخال الثابت والمحمي لمنع اختفاء البيانات وتصفير الحقول بعد الحفظ
    st.subheader("📝 Record New Transaction")
    
    # تهيئة مفاتيح الـ Session State للحقول إذا لم تكن موجودة
    if "amount_val" not in st.session_state:
        st.session_state["amount_val"] = 0.0
    if "desc_val" not in st.session_state:
        st.session_state["desc_val"] = ""

    tx_date = st.date_input("Transaction Date:", datetime.date.today())
    tx_type = st.radio("Transaction Type:", ["Income", "Expense"], index=None, horizontal=True, key="type_radio")
    
    if tx_type == "Income":
        tx_category = st.selectbox("Category البند:", INCOME_CATS, key="income_select")
    elif tx_type == "Expense":
        tx_category = st.selectbox("Category البند:", EXPENSE_CATS, key="expense_select")
    else:
        st.info("💡 Please select Transaction Type (Income / Expense) first to view categories.")
        tx_category = None
        
    # ربط الحقول بالـ session_state عبر قيمة value
    tx_amount = st.number_input("Amount (\$):", min_value=0.0, step=10.0, format="%.2f", key="amount_input", value=st.session_state["amount_val"])
    tx_description = st.text_input("Description / Notes (البيان):", key="desc_input", value=st.session_state["desc_val"])
    
    if st.button("💾 Save Transaction", type="primary"):
        if tx_type is None:
            st.error("⚠️ Please select Transaction Type (Income or Expense)!")
        elif tx_amount == 0 or tx_description == "":
            st.error("⚠️ Please fill in all fields!")
        else:
            # حفظ البيانات في ملف الـ CSV
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
            
            # [التعديل الجديد]: تصفير وإعادة تعيين الحقول في السيرفر قبل إعادة التحميل
            del st.session_state["type_radio"] # لإعادة اختيار نوع المعاملة إلى None
            st.session_state["amount_val"] = 0.0
            st.session_state["desc_val"] = ""
            
            st.success("✅ Successfully Recorded!")
            st.rerun()
