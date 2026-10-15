import streamlit as st
import pandas as pd

# 1. إعدادات عنوان الصفحة والمظهر
st.set_page_config(page_title="Cafe System", page_icon="☕", layout="wide")
st.title("☕ Cafe Financial Dashboard")

# 2. عرض المؤشرات السريعة أعلى الشاشة مباشرة
col1, col2, col3 = st.columns(3)
col1.metric("📈 October Income", "$2,720.00")
col2.metric("📉 October Expenses", "$1,200.00")
col3.metric("💰 Net Profit", "$1,520.00")

st.markdown("---")
st.success("Your Cafe Financial Web Application is running successfully!")
st.info("Next Step: We will connect your real SQL database tables here.")
