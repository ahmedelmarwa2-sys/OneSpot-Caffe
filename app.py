    # 2. إعدادات البانر الرئيسي الفخم (مقاس وسط وأنيق)
    # تم تخصيص ثلاثة أعمدة لوضع الصورة في العمود الأوسط لتقليل حجمها وعرضها بشكل متناسق
    col_space1, col_img, col_space2 = st.columns([1, 3, 1])
    
    with col_img:
        st.image("banner.png", use_container_width=True)
        
    st.markdown(
        """
        <div style='text-align: center; margin-top: 10px; margin-bottom: 25px;'>
            <p style='font-family: "Segoe UI", sans-serif; font-size: 20px; color: #7f8c8d; font-weight: 500; letter-spacing: 1px;'>
                Financial Management System
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )
