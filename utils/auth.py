import streamlit as st
import pymongo
import hashlib
import datetime
import re
import uuid
from utils.db import get_db_connection

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Email validation
def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

# User registration
def register(name, email, password):
    # Input validation
    if not name or not email or not password:
        return {"success": False, "message": "All fields are required"}
    
    if not is_valid_email(email):
        return {"success": False, "message": "Invalid email format"}
    
    if len(password) < 6:
        return {"success": False, "message": "Password must be at least 6 characters"}
    
    # Connect to database
    db = get_db_connection()
    if db is None:
        return {"success": False, "message": "Database connection error"}
    
    # Check if user already exists
    try:
        existing_user = db.users.find_one({"email": email})
        if existing_user is not None:
            return {"success": False, "message": "Email already registered"}
        
        # Check if username already exists
        username = email.split('@')[0]
        existing_username = db.users.find_one({"username": username})
        if existing_username is not None:
            # Generate a unique username by adding a timestamp
            username = f"{username}_{int(datetime.datetime.now().timestamp())}"
        
        # Create new user
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(password)
        
        new_user = {
            "user_id": user_id,
            "name": name,
            "email": email,
            "username": username,
            "password": hashed_password,
            "role": "user",  # Default role is user
            "created_at": datetime.datetime.now(),
            "last_login": None
        }
        
        db.users.insert_one(new_user)
        return {"success": True, "message": "Registration successful! Please log in."}
    except Exception as e:
        return {"success": False, "message": f"Registration failed: {str(e)}"}

# User login
def login(email, password):
    # Input validation
    if not email or not password:
        return {"success": False, "message": "Email and password are required"}
    
    # Connect to database
    db = get_db_connection()
    if db is None:
        return {"success": False, "message": "Database connection error"}
    
    try:
        # Find user by email
        user = db.users.find_one({"email": email})
        
        if user is None:
            return {"success": False, "message": "User not found"}
        
        # Verify password
        hashed_password = hash_password(password)
        if user["password"] != hashed_password:
            return {"success": False, "message": "Incorrect password"}
        
        # Update last login time
        db.users.update_one(
            {"email": email},
            {"$set": {"last_login": datetime.datetime.now()}}
        )
        
        # Set session state
        st.session_state.user = {
            "user_id": user["user_id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
        st.session_state.authenticated = True
        
        return {"success": True, "message": "Login successful!"}
    except Exception as e:
        return {"success": False, "message": f"Login failed: {str(e)}"}

# User logout
def logout():
    for key in ["user", "authenticated"]:
        if key in st.session_state:
            del st.session_state[key]

# Check if user is logged in
def check_session():
    return st.session_state.get("authenticated", False)

# Check if user is admin
def is_admin():
    if not check_session():
        return False
    return st.session_state.get("user", {}).get("role") == "admin"

# Require login
def require_login():
    if not check_session():
        st.error("Please login to access this page")
        st.stop()

# Require admin
def require_admin():
    if not check_session():
        st.error("Please login to access this page")
        st.stop()
    
    if not is_admin():
        st.error("You don't have permission to access this page")
        st.stop()
