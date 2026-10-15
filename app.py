    # 2. إعدادات العنوان الرئيسي والشعار (تصميم فخم واحترافي متكامل)
    # تم ضبط المسافات بـ 4 مسافات دقيقة لتفادي خطأ الـ IndentationError
    col_logo, col_title = st.columns([1, 8]) # تحديد نسب دقيقة ليظهر اللوجو بجانب النص تماماً
    
    with col_logo:
        try:
            st.image("logo.png", width=75)
        except:
            st.markdown("<h1 style='margin:0; padding:0; text-align:center;'>☕</h1>", unsafe_allow_html=True)
            
    with col_title:
        st.markdown(
            """
            <div style='
                display: flex; 
                align-items: center; 
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%); 
                padding: 10px 20px; 
                border-radius: 12px; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.04); 
                border-bottom: 3px solid #d4af37; 
                height: 75px;
            '>
                <h1 style='
                    margin: 0; 
                    padding: 0; 
                    font-family: "Segoe UI", sans-serif; 
                    font-size: 26px; 
                    color: #1a252f; 
                    font-weight: 700;
                '>
                    Onespot Cafe 
                    <span style='
                        font-size: 18px; 
                        color: #7f8c8d; 
                        font-weight: 400; 
                        border-left: 2px solid #bdc3c7; 
                        padding-left: 12px; 
                        margin-left: 10px;
                        display: inline-block;
                        vertical-align: middle;
                    '>
                        Financial Management System
                    </span>
                </h1>
            </div>
            """, 
            unsafe_allow_html=True
        )
