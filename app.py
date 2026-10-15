    # 2. إعدادات البانر الرئيسي الفخم (مصحح المسافات بنسبة 100%)
    try:
        st.image("banner.png", use_container_width=True)
    except:
        st.markdown(
            """
            <div style='background: #1a1a1a; padding: 20px; border-radius: 12px; text-align: center; border-bottom: 3px solid #d4af37;'>
                <h1 style='color: #ffffff; margin: 0; font-family: "Segoe UI", sans-serif;'>OneSpot Cafe</h1>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    st.markdown(
        """
        <div style='text-align: center; margin-top: -10px; margin-bottom: 25px;'>
            <p style='font-family: "Segoe UI", sans-serif; font-size: 20px; color: #7f8c8d; font-weight: 500; letter-spacing: 1px;'>
                Financial Management System
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )
