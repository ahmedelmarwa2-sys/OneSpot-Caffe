    # 2. إعدادات العنوان الرئيسي والشعار (تصميم فخم واحترافي متكامل)
    # تم دمج الشعار والنصوص داخل حاوية واحدة بخلفية مخصصة وظل ناعم لتظهر كشريط علوي احترافي ومستقل
    st.markdown(
        """
        <div style='
            display: flex; 
            align-items: center; 
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%); 
            padding: 18px 25px; 
            border-radius: 16px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.05); 
            border-bottom: 3px solid #d4af37; 
            margin-bottom: 25px;
            gap: 20px;
        '>
            <!-- حاوية الشعار التوضيحية لتأمين المساحة (Streamlit سيضع الصورة الأصلية فوقها أو بجانبها) -->
            <div style='display: flex; align-items: center; justify-content: center;'>
                <span style='font-size: 32px; filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.1));'>☕</span>
            </div>
            
            <!-- النصوص بتنسيق خطوط وأوزان احترافية ومريحة للعين -->
            <div style='flex-grow: 1;'>
                <h1 style='
                    margin: 0; 
                    padding: 0; 
                    font-family: "Inter", "Segoe UI", sans-serif; 
                    font-size: 28px; 
                    color: #1a252f; 
                    font-weight: 800; 
                    letter-spacing: -0.5px;
                '>
                    Onespot Cafe 
                    <span style='
                        font-size: 18px; 
                        color: #7f8c8d; 
                        font-weight: 400; 
                        border-left: 2px solid #e2e8f0; 
                        padding-left: 15px; 
                        margin-left: 12px;
                        display: inline-block;
                        vertical-align: middle;
                    '>
                        Financial Management System
                    </span>
                </h1>
            </div>
            
            <!-- شارة إضافية تمنح النظام طابعاً رسمياً وموثوقاً -->
            <div style='
                background-color: #ebfbee; 
                color: #2b8a3e; 
                padding: 6px 14px; 
                border-radius: 20px; 
                font-size: 12px; 
                font-weight: 700; 
                text-transform: uppercase; 
                letter-spacing: 0.5px;
            '>
                Secure Server
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
