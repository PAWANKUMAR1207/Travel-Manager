import streamlit as st
import os
from utils.auth import login, register, logout, check_session
from utils.db import initialize_database

# Page configuration
st.set_page_config(
    page_title="Travel Manager",
    page_icon="🧳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on first load
initialize_database()

# App title and description
def main_page():
    col1, col2 = st.columns([1, 5])
    
    with col1:
        st.markdown("""
        <svg width="50" height="50" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#f63366" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M2 17L12 22L22 17" stroke="#f63366" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M2 12L12 17L22 12" stroke="#f63366" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        """, unsafe_allow_html=True)
    
    with col2:
        st.title("Travel Manager")
    
    st.write("Plan your trips, manage bookings, and track expenses all in one place.")

# Authentication and session management
def auth_section():
    # Check if user is already logged in
    if check_session():
        user_info = st.session_state.user
        st.sidebar.success(f"Logged in as: {user_info['name']}")
        
        if st.sidebar.button("Logout"):
            logout()
            st.rerun()
    else:
        # Login/Register tabs
        auth_tab1, auth_tab2 = st.sidebar.tabs(["Login", "Register"])
        
        with auth_tab1:
            with st.form("login_form"):
                st.subheader("Login")
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    result = login(email, password)
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
        
        with auth_tab2:
            with st.form("register_form"):
                st.subheader("Register")
                name = st.text_input("Full Name", key="reg_name")
                email = st.text_input("Email", key="reg_email")
                password = st.text_input("Password", type="password", key="reg_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
                submit = st.form_submit_button("Register")
                
                if submit:
                    if password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        result = register(name, email, password)
                        if result["success"]:
                            st.success(result["message"])
                            # Automatically log in the user after registration
                            login(email, password)
                            st.rerun()
                        else:
                            st.error(result["message"])

# Dashboard preview (only shown when logged in)
def dashboard_preview():
    if check_session():
        st.subheader("Your Travel Dashboard")
        
        # Stats in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Upcoming Trips", value="0")
        with col2:
            st.metric(label="Active Bookings", value="0")
        with col3:
            st.metric(label="Total Expenses", value="$0")
        
        # Quick links
        st.subheader("Quick Links")
        quick_links = st.columns(4)
        with quick_links[0]:
            if st.button("➕ New Trip"):
                st.switch_page("pages/1_Trip_Planning.py")
        with quick_links[1]:
            if st.button("🏨 Bookings"):
                st.switch_page("pages/2_Bookings.py")
        with quick_links[2]:
            if st.button("💰 Expenses"):
                st.switch_page("pages/3_Expenses.py")
        with quick_links[3]:
            if st.button("💬 Feedback"):
                st.switch_page("pages/5_User_Feedback.py")
        
        # Recent activity
        st.subheader("Recent Activity")
        st.info("No recent activity. Start by creating a new trip!")
    else:
        st.info("Please login or register to access the Travel Manager features.")
        
        # Feature highlights for non-logged in users
        st.subheader("Features")
        
        feature_col1, feature_col2 = st.columns(2)
        
        with feature_col1:
            st.markdown("### 🗺️ Trip Planning")
            st.write("Create detailed itineraries for your trips")
            
            st.markdown("### 🏨 Booking Management")
            st.write("Keep track of flights, hotels, and rentals")
        
        with feature_col2:
            st.markdown("### 💰 Expense Tracking")
            st.write("Monitor your travel expenses and stay on budget")
            
            st.markdown("### 📊 Analytics")
            st.write("Visualize your travel data and expenses")

def main():
    # Sidebar for navigation and authentication
    with st.sidebar:
        auth_section()
        
        # Navigation (only show if logged in)
        if check_session():
            st.sidebar.title("Navigation")
            st.sidebar.page_link("app.py", label="Home", icon="🏠")
            st.sidebar.page_link("pages/1_Trip_Planning.py", label="Trip Planning", icon="🗺️")
            st.sidebar.page_link("pages/2_Bookings.py", label="Bookings", icon="🏨")
            st.sidebar.page_link("pages/3_Expenses.py", label="Expenses", icon="💰")
            
            # Only show admin panel for admin users
            if st.session_state.get("user", {}).get("role") == "admin":
                st.sidebar.page_link("pages/4_Admin_Panel.py", label="Admin Panel", icon="⚙️")
            
            st.sidebar.page_link("pages/5_User_Feedback.py", label="Feedback", icon="💬")
    
    # Main content
    main_page()
    dashboard_preview()

if __name__ == "__main__":
    main()
