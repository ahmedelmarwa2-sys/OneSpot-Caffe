    with tab3:
        st.subheader("🛠️ Modify or Remove a Transaction")
        
        if not df_all.empty:
            # ترتيب الأرقام لسهولة الاختيار
            available_ids = sorted(df_all["ID"].unique())
            selected_id = st.selectbox("Select Transaction ID to Action:", options=available_ids)
            
            if selected_id:
                # جلب بيانات الفاتورة المحددة
                row_idx = df_all[df_all["ID"] == selected_id].index[0]
                current_row = df_all.loc[row_idx]
                
                st.markdown("### 📝 Edit or Delete From Here (التعديل أو الحذف من هنا):")
                
                # وضع خيارات التعديل في نموذج (Form) ملموم عشان يظهر في نص الشاشة
                with st.form(key=f"edit_form_{selected_id}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_date = st.date_input("Transaction Date:", pd.to_datetime(current_row["Date"]).date())
                        # اختيار البند بناء على نوع الفاتورة الأصلية
                        cats_list = INCOME_CATS if current_row["Type"] == "Income" else EXPENSE_CATS
                        # تحديد الترتيب الحالي للبند في القائمة لمنع الأخطاء
                        try:
                            cat_index = cats_list.index(current_row["Category"])
                        except:
                            cat_index = 0
                        new_category = st.selectbox("Category البند:", cats_list, index=cat_index)
                    
                    with col2:
                        new_amount = st.number_input("Amount ($):", min_value=0.0, value=float(current_row["Amount"]), step=10.0, format="%.2f")
                        new_description = st.text_input("Description / Notes (البيان):", value=str(current_row["Description"]))
                    
                    st.markdown("---")
                    
                    # أزرار التحكم: التحديث والحذف جنب بعض عل طول عشان تشوفهم فوراً
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        update_button = st.form_submit_button("💾 Update Transaction (حفظ التعديل)", type="primary", use_container_width=True)
                    with btn_col2:
                        delete_button = st.form_submit_button("🗑️ Delete Permanently (حذف نهائي)", type="secondary", use_container_width=True)
                
                # تنفيذ أمر التعديل والتحديث
                if update_button:
                    if new_amount == 0 or new_description == "":
                        st.error("⚠️ Please fill in all fields!")
                    else:
                        df_all.at[row_idx, "Date"] = str(new_date)
                        df_all.at[row_idx, "Month_No"] = new_date.month
                        df_all.at[row_idx, "Category"] = new_category
                        df_all.at[row_idx, "Amount"] = new_amount
                        df_all.at[row_idx, "Description"] = new_description
                        
                        df_all.to_csv(DATA_FILE, index=False)
                        st.success("✅ Transaction updated successfully!")
                        st.rerun()
                
                # تنفيذ أمر المسح الفوري
                if delete_button:
                    df_all = df_all[df_all["ID"] != selected_id]
                    df_all.to_csv(DATA_FILE, index=False)
                    st.success(f"✅ Transaction ID {selected_id} deleted successfully!")
                    st.rerun()
        else:
            st.info("💡 There are no transactions to modify or delete.")
