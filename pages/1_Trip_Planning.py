import streamlit as st
import datetime
import pandas as pd
from streamlit_folium import folium_static
import folium
from utils.auth import check_session, require_login
from utils.db import (
    create_trip, get_user_trips, get_trip_by_id, 
    update_trip, delete_trip, get_tourist_spots
)

# Page config
st.set_page_config(
    page_title="Trip Planning - Travel Manager",
    page_icon="🗺️",
    layout="wide"
)

# Require login
require_login()
user = st.session_state.user

# Page title
st.title("🗺️ Trip Planning")
st.write("Plan your upcoming trips and create detailed itineraries")

# Simple tab setup
tab1, tab2 = st.tabs(["My Trips", "Create New Trip"])

# Function to display trip details
def show_trip_details(trip):
    with st.expander(f"{trip['title']} - {trip['destination']} ({trip['start_date'].strftime('%d %b %Y')} to {trip['end_date'].strftime('%d %b %Y')})", expanded=False):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(trip["title"])
            st.write(f"**Destination:** {trip['destination']}")
            st.write(f"**Dates:** {trip['start_date'].strftime('%d %b %Y')} to {trip['end_date'].strftime('%d %b %Y')}")
            
            if trip.get("description"):
                st.write(f"**Description:** {trip['description']}")
            
            # Status badge
            status = trip.get("status", "planned")
            status_colors = {
                "planned": "blue",
                "active": "green",
                "completed": "gray",
                "cancelled": "red"
            }
            st.markdown(f"<span style='background-color:{status_colors.get(status, 'blue')};color:white;padding:3px 8px;border-radius:10px;font-size:0.8em'>{status.upper()}</span>", unsafe_allow_html=True)
            
            # Edit trip button
            if st.button("Edit Trip", key=f"edit_{trip['trip_id']}"):
                st.session_state.trip_to_edit = trip
                st.rerun()
            
            # Delete trip button (with confirmation)
            if st.button("Delete Trip", key=f"delete_{trip['trip_id']}"):
                st.session_state.trip_to_delete = trip
                st.rerun()
        
        with col2:
            # Show a map with the destination
            try:
                # Get tourist spots for the destination
                spots = get_tourist_spots()
                destination_spots = [spot for spot in spots if trip['destination'].lower() in spot['location'].lower()]
                
                # Create map centered on the first spot if available
                if destination_spots:
                    m = folium.Map(
                        location=[destination_spots[0]['coordinates']['lat'], destination_spots[0]['coordinates']['lng']], 
                        zoom_start=12
                    )
                    
                    # Add markers for all spots
                    for spot in destination_spots:
                        folium.Marker(
                            [spot['coordinates']['lat'], spot['coordinates']['lng']],
                            popup=spot['name'],
                            tooltip=spot['name']
                        ).add_to(m)
                else:
                    # Default map with destination name geocoded
                    m = folium.Map(location=[0, 0], zoom_start=2)
                    folium.Marker([0, 0], popup=trip['destination']).add_to(m)
                
                folium_static(m, width=300, height=200)
            except Exception as e:
                st.error(f"Error displaying map: {e}")

# Function to handle trip creation form
def trip_creation_form():
    with st.form("create_trip_form"):
        st.subheader("Trip Details")
        
        title = st.text_input("Trip Title", placeholder="Summer Vacation 2023")
        destination = st.text_input("Destination", placeholder="Paris, France")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", min_value=datetime.date.today())
        with col2:
            end_date = st.date_input("End Date", min_value=start_date)
        
        description = st.text_area("Description (Optional)", placeholder="Trip details, goals, etc.")
        
        submit_button = st.form_submit_button("Create Trip")
        
        if submit_button:
            if not title or not destination:
                st.error("Trip title and destination are required")
            elif start_date > end_date:
                st.error("End date must be after start date")
            else:
                trip_data = {
                    "title": title,
                    "destination": destination,
                    "start_date": start_date,
                    "end_date": end_date,
                    "description": description,
                    "status": "planned"
                }
                
                result = create_trip(user["user_id"], trip_data)
                
                if result["success"]:
                    st.success(result["message"])
                    # Clear form and refresh
                    st.session_state.trip_created = True
                    st.rerun()
                else:
                    st.error(result["message"])

# Function to handle trip edit form
def trip_edit_form(trip):
    with st.form("edit_trip_form"):
        st.subheader(f"Edit Trip: {trip['title']}")
        
        title = st.text_input("Trip Title", value=trip["title"])
        destination = st.text_input("Destination", value=trip["destination"])
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=trip["start_date"])
        with col2:
            end_date = st.date_input("End Date", value=trip["end_date"])
        
        description = st.text_area("Description", value=trip.get("description", ""))
        
        status_options = ["planned", "active", "completed", "cancelled"]
        status = st.selectbox("Status", options=status_options, index=status_options.index(trip.get("status", "planned")))
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Save Changes")
        with col2:
            cancel_button = st.form_submit_button("Cancel")
        
        if cancel_button:
            if "trip_to_edit" in st.session_state:
                del st.session_state.trip_to_edit
            st.rerun()
        
        if submit_button:
            if not title or not destination:
                st.error("Trip title and destination are required")
            elif start_date > end_date:
                st.error("End date must be after start date")
            else:
                trip_data = {
                    "title": title,
                    "destination": destination,
                    "start_date": start_date,
                    "end_date": end_date,
                    "description": description,
                    "status": status
                }
                
                result = update_trip(trip["trip_id"], trip_data)
                
                if result["success"]:
                    st.success(result["message"])
                    # Remove edit state and refresh
                    if "trip_to_edit" in st.session_state:
                        del st.session_state.trip_to_edit
                    st.rerun()
                else:
                    st.error(result["message"])

# Function to display delete confirmation
def confirm_delete_trip(trip):
    st.warning(f"Are you sure you want to delete the trip '{trip['title']}'? This will also delete all related bookings and expenses.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, Delete Trip"):
            result = delete_trip(trip["trip_id"])
            
            if result["success"]:
                st.success(result["message"])
                # Remove delete state and refresh
                if "trip_to_delete" in st.session_state:
                    del st.session_state.trip_to_delete
                st.rerun()
            else:
                st.error(result["message"])
    with col2:
        if st.button("Cancel"):
            if "trip_to_delete" in st.session_state:
                del st.session_state.trip_to_delete
            st.rerun()

# Display content in My Trips tab
with tab1:
    # Check if a trip needs to be edited
    if "trip_to_edit" in st.session_state:
        trip_edit_form(st.session_state.trip_to_edit)
    
    # Check if a trip is to be deleted
    elif "trip_to_delete" in st.session_state:
        confirm_delete_trip(st.session_state.trip_to_delete)
    
    else:
        # Fetch user's trips
        trips = get_user_trips(user["user_id"])
        
        if trips:
            st.write(f"You have {len(trips)} trips planned.")
            
            # Sort trips by date - comparing datetime objects consistently
            current_date = datetime.datetime.now()
            upcoming_trips = [trip for trip in trips if trip["start_date"] >= current_date]
            past_trips = [trip for trip in trips if trip["start_date"] < current_date]
            
            if upcoming_trips:
                st.subheader("Upcoming Trips")
                for trip in sorted(upcoming_trips, key=lambda x: x["start_date"]):
                    show_trip_details(trip)
            
            if past_trips:
                st.subheader("Past Trips")
                for trip in sorted(past_trips, key=lambda x: x["start_date"], reverse=True):
                    show_trip_details(trip)
        else:
            st.info("You don't have any trips yet. Create a new trip to get started!")
            # Simple button that just selects the second tab
            if st.button("Create Your First Trip"):
                # We'll redirect this in a future update if needed
                st.info("Please click on the 'Create New Trip' tab above")

# Create new trip
with tab2:
    # Always show the trip creation form in the Create New Trip tab
    # Removed conditional that was preventing form from showing
    trip_creation_form()
