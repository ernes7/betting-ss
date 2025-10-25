"""Streamlit web interface for Sports Betting Analysis Tool."""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Sports Betting Analysis",
    page_icon="🎯",
    layout="wide"
)

# Main content
st.title("🎯 Sports Betting Analysis Tool")
st.write("Welcome to the AI-powered betting analysis system!")

st.markdown("""
## Hello World!

This is a basic Streamlit interface for the sports betting analysis tool.

### Supported Sports
- 🏈 NFL
- 🏀 NBA

### Features (Coming Soon)
- Generate AI predictions
- View past predictions
- Track results and analytics
""")

# Simple interactive element
if st.button("Click me!"):
    st.success("Streamlit is working! 🎉")
