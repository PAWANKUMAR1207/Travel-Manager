import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
from utils.auth import check_session, require_admin
from utils.db import (
    add_tourist_spot, get_tourist_spots, delete_tourist_spot,
    add_partner, get_partners, delete_partner,
    get_all_feedback
)

# Page config
st.set_page_config(
    page_title="Admin Panel - Travel Manager",
    page_icon="⚙️",
    layout="wide"
)

# Require admin
require_admin()
user = st.session_state.user

# Page title
st.title("⚙️ Admin Panel")
st.write("Manage tourist spots, partner vendors, and user feedback")

# Tabs
tab1, tab2, tab3 = st.tabs(["Tourist Spots", "Partner Vendors", "User Feedback"])

# Tourist Spots Management
with tab1:
    st.header("Tourist Spots")
    
    # Create two columns for tourist spots
    spot_col1, spot_col2 = st.columns([1, 1])
    
    with spot_col1:
        st.subheader("Add New Tourist Spot")
        
        with st.form("add_tourist_spot_form"):
            spot_name = st.text_input("Name", placeholder="Eiffel Tower")
            spot_location = st.text_input("Location", placeholder="Paris, France")
            spot_category = st.selectbox(
                "Category",
                options=["landmark", "museum", "nature", "religious", "entertainment", "beach", "other"],
                format_func=lambda x: x.capitalize()
            )
            spot_description = st.text_area("Description", placeholder="Famous iron tower in Paris...")
            
            # Coordinates
            coord_col1, coord_col2 = st.columns(2)
            with coord_col1:
                lat = st.number_input("Latitude", value=0.0, format="%.6f")
            with coord_col2:
                lng = st.number_input("Longitude", value=0.0, format="%.6f")
            
            spot_rating = st.slider("Rating", min_value=1, max_value=5, value=4, step=1)
            
            submit_button = st.form_submit_button("Add Tourist Spot")
            
            if submit_button:
                if not spot_name or not spot_location:
                    st.error("Name and location are required")
                else:
                    spot_data = {
                        "name": spot_name,
                        "location": spot_location,
                        "category": spot_category,
                        "description": spot_description,
                        "coordinates": {"lat": lat, "lng": lng},
                        "rating": float(spot_rating)
                    }
                    
                    result = add_tourist_spot(spot_data)
                    
                    if result["success"]:
                        st.success(result["message"])
                        # Clear form and refresh
                        st.rerun()
                    else:
                        st.error(result["message"])
    
    with spot_col2:
        st.subheader("Existing Tourist Spots")
        
        # Get tourist spots
        spots = get_tourist_spots()
        
        if spots:
            # Display as a table with delete button
            spot_df = pd.DataFrame([
                {
                    "Name": spot["name"],
                    "Location": spot["location"],
                    "Category": spot["category"].capitalize(),
                    "Rating": "⭐" * int(spot["rating"]),
                    "Actions": spot["spot_id"]  # We'll replace this with buttons
                } for spot in spots
            ])
            
            # Convert to a data editor with actions
            edited_df = st.data_editor(
                spot_df,
                column_config={
                    "Delete": st.column_config.CheckboxColumn(
                        "Delete",
                        help="Select spots to delete",
                        default=False,
                    )
                },
                disabled=["Name", "Location", "Category", "Rating"],
                hide_index=True
            )
            
            # Check for spots to delete
            spots_to_delete = edited_df.loc[edited_df["Delete"], "Actions"].to_list()
            
            if spots_to_delete and st.button("Delete Selected Spots"):
                for spot_id in spots_to_delete:
                    result = delete_tourist_spot(spot_id)
                    if result["success"]:
                        st.success(f"Deleted: {next((spot['name'] for spot in spots if spot['spot_id'] == spot_id), '')}")
                    else:
                        st.error(f"Failed to delete spot: {result['message']}")
                st.rerun()
        else:
            st.info("No tourist spots added yet. Add your first spot!")

# Partner Vendors Management
with tab2:
    st.header("Partner Vendors")
    
    # Create two columns for partners
    partner_col1, partner_col2 = st.columns([1, 1])
    
    with partner_col1:
        st.subheader("Add New Partner")
        
        with st.form("add_partner_form"):
            partner_name = st.text_input("Partner Name", placeholder="Air France")
            partner_type = st.selectbox(
                "Type",
                options=["airline", "hotel", "car rental", "tour operator", "cruise", "restaurant", "other"],
                format_func=lambda x: x.capitalize()
            )
            partner_email = st.text_input("Contact Email", placeholder="contact@partner.com")
            partner_phone = st.text_input("Contact Phone (Optional)", placeholder="+1234567890")
            partner_website = st.text_input("Website (Optional)", placeholder="https://www.partner.com")
            partner_description = st.text_area("Description (Optional)", placeholder="Partner description...")
            
            submit_button = st.form_submit_button("Add Partner")
            
            if submit_button:
                if not partner_name or not partner_email:
                    st.error("Name and contact email are required")
                else:
                    partner_data = {
                        "name": partner_name,
                        "type": partner_type,
                        "contact_email": partner_email,
                        "contact_phone": partner_phone,
                        "website": partner_website,
                        "description": partner_description
                    }
                    
                    result = add_partner(partner_data)
                    
                    if result["success"]:
                        st.success(result["message"])
                        # Clear form and refresh
                        st.rerun()
                    else:
                        st.error(result["message"])
    
    with partner_col2:
        st.subheader("Existing Partners")
        
        # Get partners
        partners = get_partners()
        
        if partners:
            # Display as a table with delete button
            partner_df = pd.DataFrame([
                {
                    "Name": partner["name"],
                    "Type": partner["type"].capitalize(),
                    "Email": partner["contact_email"],
                    "Phone": partner.get("contact_phone", ""),
                    "Actions": partner["partner_id"]  # We'll replace this with buttons
                } for partner in partners
            ])
            
            # Convert to a data editor with actions
            edited_df = st.data_editor(
                partner_df,
                column_config={
                    "Delete": st.column_config.CheckboxColumn(
                        "Delete",
                        help="Select partners to delete",
                        default=False,
                    )
                },
                disabled=["Name", "Type", "Email", "Phone"],
                hide_index=True
            )
            
            # Check for partners to delete
            partners_to_delete = edited_df[edited_df["Actions"]]["Actions"].to_list()
            
            if partners_to_delete and st.button("Delete Selected Partners"):
                for partner_id in partners_to_delete:
                    result = delete_partner(partner_id)
                    if result["success"]:
                        st.success(f"Deleted: {next((partner['name'] for partner in partners if partner['partner_id'] == partner_id), '')}")
                    else:
                        st.error(f"Failed to delete partner: {result['message']}")
                st.rerun()
        else:
            st.info("No partners added yet. Add your first partner!")

# User Feedback Management
with tab3:
    st.header("User Feedback")
    
    # Get all feedback
    all_feedback = get_all_feedback()
    
    if all_feedback:
        # Convert to DataFrame for analysis
        feedback_df = pd.DataFrame(all_feedback)
        
        # Add user names if possible
        feedback_df["rating_stars"] = feedback_df["rating"].apply(lambda x: "⭐" * int(x))
        
        # Summary stats
        st.subheader("Feedback Summary")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Feedback", len(feedback_df))
        with col2:
            avg_rating = feedback_df["rating"].mean()
            st.metric("Average Rating", f"{avg_rating:.1f}/5")
        with col3:
            recent_count = len(feedback_df[feedback_df["created_at"] > (datetime.datetime.now() - datetime.timedelta(days=30))])
            st.metric("Recent Feedback (30 days)", recent_count)
        
        # Rating distribution
        st.subheader("Rating Distribution")
        
        rating_counts = feedback_df["rating"].value_counts().sort_index()
        
        fig = px.bar(
            x=rating_counts.index,
            y=rating_counts.values,
            labels={"x": "Rating", "y": "Count"},
            title="Feedback Rating Distribution"
        )
        fig.update_layout(xaxis=dict(tickmode="linear", tick0=1, dtick=1))
        st.plotly_chart(fig, use_container_width=True)
        
        # Feedback table
        st.subheader("All Feedback")
        
        # Category filter
        categories = ["All"] + sorted(feedback_df["category"].unique().tolist())
        selected_category = st.selectbox("Filter by Category", options=categories)
        
        # Apply filter
        if selected_category != "All":
            filtered_feedback = feedback_df[feedback_df["category"] == selected_category]
        else:
            filtered_feedback = feedback_df
        
        # Sort by date (newest first)
        filtered_feedback = filtered_feedback.sort_values("created_at", ascending=False)
        
        # Create display table
        display_df = filtered_feedback[["user_id", "rating_stars", "comment", "category", "created_at"]]
        display_df = display_df.rename(columns={
            "user_id": "User ID",
            "rating_stars": "Rating",
            "comment": "Comment",
            "category": "Category",
            "created_at": "Date"
        })
        
        # Format the date
        display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d %H:%M")
        
        st.dataframe(display_df, hide_index=True, use_container_width=True)
    else:
        st.info("No feedback submitted yet.")
