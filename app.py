    with tab3:
        st.subheader("🛠️ Edit or Delete Transactions")
        if not df_all.empty:
            st.write("📌 **Select a row from the table below to Edit or Delete:**")
            
            # عرض جدول التعديل التفاعلي
            event = st.dataframe(
                df_all[["ID", "Date", "Category", "Type", "Amount", "Description"]],
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            # استخراج السطر المختار بأمان كـ لستة
            selected_rows = event.get("selection", {}).get("rows", [])
            
            # التحقق من أن المستخدم اختار سطر بالفعل
            if len(selected_rows) > 0:
                selected_row_idx = int(selected_rows[0]) # تحويل الفهرس لرقم صحيح ليعمل الفلتر بدقة
                selected_row = df_all.iloc[selected_row_idx]
                
                st.markdown("---")
                st.markdown(f"### 🔄 Modifying Transaction [ ID: {selected_row['ID']} ]")
                
                # حقول التعديل محملة بالبيانات تلقائياً
                edit_date = st.date_input("Edit Date:", datetime.datetime.strptime(str(selected_row["Date"]), "%Y-%m-%d").date(), key="edit_date")
                edit_type = st.radio("Edit Type:", ["Income", "Expense"], index=0 if selected_row["Type"] == "Income" else 1, horizontal=True, key="edit_type")
                
                cats_list = INCOME_CATS if edit_type == "Income" else EXPENSE_CATS
                
                if selected_row["Category"] in cats_list:
                    cat_index = cats_list.index(selected_row["Category"])
                else:
                    cat_index = 0
                    
                edit_category = st.selectbox("Edit Category:", cats_list, index=cat_index, key="edit_category")
                edit_amount = st.number_input("Edit Amount ($):", min_value=0.0, value=float(selected_row["Amount"]), step=10.0, format="%.2f", key="edit_amount")
                edit_description = st.text_input("Edit Description:", value=str(selected_row["Description"]), key="edit_description")
                
                btn_col1, btn_col2 = st.columns(2)
                
                with btn_col1:
                    if st.button("📝 Update Transaction", type="primary", use_container_width=True):
                        df_all.at[selected_row_idx, "Date"] = str(edit_date)
                        df_all.at[selected_row_idx, "Month_No"] = int(edit_date.month)
                        df_all.at[selected_row_idx, "Type"] = edit_type
                        df_all.at[selected_row_idx, "Category"] = edit_category
                        df_all.at[selected_row_idx, "Amount"] = edit_amount
                        df_all.at[selected_row_idx, "Description"] = edit_description
                        
                        df_all.to_csv(DATA_FILE, index=False)
                        st.success("✅ Transaction updated successfully!")
                        st.rerun()
                        
                with btn_col2:
                    if st.button("🗑️ Delete Transaction", type="secondary", use_container_width=True):
                        df_all = df_all.drop(selected_row_idx).reset_index(drop=True)
                        df_all.to_csv(DATA_FILE, index=False)
                        st.success("🗑️ Transaction deleted successfully!")
                        st.rerun()
            else:
                st.info("💡 Click on the checkbox on the left of any row in the table above to reveal Edit and Delete controls.")
        else:
            st.info("No data available to manage.")
