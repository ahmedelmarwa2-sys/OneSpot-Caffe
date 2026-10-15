import streamlit as st
import pandas as pd
import datetime
import os

# 1. إعدادات الحماية والأمان بالباسورد
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.set_page_config(page_title="Login Required", page_icon="🔒", layout="wide")
        st.title("🔒 Cafe System - Secure Login")
        st.text_input("Enter Cafe Password:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 Cafe System - Secure Login")
        st.text_input("Enter Cafe Password:", type="password", on_change=password_entered, key="password")
        st.error("❌ Incorrect password. Please try again.")
        return False
    else:
        return True

if check_password():
    
    # 2. إعدادات العنوان الرئيسي والشعار (تم ضبط المسافات هنا بدقة تامة لتفادي الخطأ)
    col_logo, col_title = st.columns([1, 8])
    
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
    
    DATA_FILE = "cafe_data.csv"
