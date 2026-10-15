    # 2. إعدادات البانر الرئيسي الفخم (تم دمج صورة OneSpot الأصلية بكامل وضوحها)
    # تأكد من تسمية الصورة في مجلد المشروع باسم banner.png أو تعديل الاسم في الكود بالأسفل
    try:
        # عرض صورة البانر بعرض الشاشة بالكامل لتظهر تفاصيل حبوب القهوة بدقة عالية
        st.image("banner.png", use_container_width=True)
    except:
        # حل بديل مرن في حال لم يتم العثور على ملف الصورة مؤقتاً
        st.markdown(
            """
            <div style='background: #1a1a1a; padding: 20px; border-radius: 12px; text-align: center; border-bottom: 3px solid #d4af37;'>
                <h1 style='color: #ffffff; margin: 0; font-family: "Segoe UI", sans-serif;'>OneSpot Cafe</h1>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    # إضافة عنوان النظام أسفل البانر مباشرة بتنسيق ناعم ومتناسق مع الألوان الدافئة للصورة
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
