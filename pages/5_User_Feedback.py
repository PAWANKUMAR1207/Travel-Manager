import streamlit as st
import datetime
import pandas as pd
from utils.auth import check_session, require_login
from utils.db import add_feedback, get_user_feedback

# Page config
st.set_page_config(
    page_title="Feedback - Travel Manager",
    page_icon="💬",
    layout="wide"
)

# Require login
require_login()
user = st.session_state.user

# Page title
st.title("💬 User Feedback")
st.write("Share your thoughts and help us improve!")

# Tabs
tab1, tab2 = st.tabs(["Submit Feedback", "Your Previous Feedback"])

# Submit Feedback
with tab1:
    with st.form("feedback_form"):
        st.subheader("Share Your Feedback")
        
        rating = st.slider("How would you rate your experience?", 1, 5, 4)
        
        # Visual stars
        st.write("Your rating: " + "⭐" * rating)
        
        category = st.selectbox(
            "What aspect are you giving feedback on?",
            options=["general", "trip planning", "bookings", "expenses", "user interface", "feature request", "bug report"],
            format_func=lambda x: x.capitalize()
        )
        
        comment = st.text_area("Your feedback", placeholder="Tell us what you think...")
        
        submit_button = st.form_submit_button("Submit Feedback")
        
        if submit_button:
            if not comment:
                st.error("Please provide your feedback in the comment field")
            else:
                feedback_data = {
                    "user_id": user["user_id"],
                    "rating": rating,
                    "category": category,
                    "comment": comment
                }
                
                result = add_feedback(feedback_data)
                
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])
    
    # Some guidance for feedback
    with st.expander("Feedback Guidelines"):
        st.write("""
        ### Help us serve you better
        
        - Be specific about what you liked or what could be improved
        - If reporting a bug, include steps to reproduce it
        - For feature requests, explain how it would benefit your travel planning
        - Remember that your feedback helps shape the future of Travel Manager!
        """)

# Previous Feedback
with tab2:
    st.subheader("Your Previous Feedback")
    
    # Get user's feedback
    user_feedback = get_user_feedback(user["user_id"])
    
    if user_feedback:
        # Convert to DataFrame for display
        feedback_df = pd.DataFrame(user_feedback)
        
        # Add rating visualization
        feedback_df["rating_display"] = feedback_df["rating"].apply(lambda x: "⭐" * int(x))
        
        # Format the data for display
        display_df = feedback_df[["created_at", "rating_display", "category", "comment"]]
        display_df = display_df.rename(columns={
            "created_at": "Date",
            "rating_display": "Rating",
            "category": "Category",
            "comment": "Comment"
        })
        
        # Format the date
        display_df["Date"] = pd.to_datetime(display_df["Date"]).dt.strftime("%Y-%m-%d %H:%M")
        
        # Sort by date (most recent first)
        display_df = display_df.sort_values("Date", ascending=False)
        
        # Display table
        st.dataframe(display_df, hide_index=True, use_container_width=True)
    else:
        st.info("You haven't submitted any feedback yet.")
        st.write("We value your opinion! Please consider sharing your thoughts on the 'Submit Feedback' tab.")
