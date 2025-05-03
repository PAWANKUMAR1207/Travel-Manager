import streamlit as st
import datetime
import pandas as pd
from utils.auth import check_session, require_login
from utils.db import (
    get_user_trips, get_trip_by_id, create_booking,
    get_trip_bookings, get_user_bookings, delete_booking,
    get_partners
)

# Page config
st.set_page_config(
    page_title="Bookings - Travel Manager",
    page_icon="🏨",
    layout="wide"
)

# Require login
require_login()
user = st.session_state.user

# Page title
st.title("🏨 Bookings Management")
st.write("Manage your travel bookings - flights, hotels, car rentals, and activities")

# Tab setup
tab1, tab2 = st.tabs(["My Bookings", "Add New Booking"])

# Function to display booking details
def show_booking_details(booking):
    # Determine icon based on booking type
    icons = {
        "flight": "✈️",
        "hotel": "🏨",
        "car": "🚗",
        "activity": "🎭",
        "other": "📝"
    }
    booking_icon = icons.get(booking.get("type", "other"), "📝")
    
    with st.expander(f"{booking_icon} {booking['provider']} - {booking['start_date'].strftime('%d %b %Y')}", expanded=False):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"{booking_icon} {booking['type'].capitalize()}: {booking['provider']}")
            st.write(f"**Reference:** {booking['booking_reference']}")
            st.write(f"**Dates:** {booking['start_date'].strftime('%d %b %Y')} to {booking['end_date'].strftime('%d %b %Y')}")
            
            if booking.get("notes"):
                st.write(f"**Notes:** {booking['notes']}")
            
            # Get trip information
            trip = get_trip_by_id(booking["trip_id"])
            if trip:
                st.write(f"**Trip:** {trip['title']} ({trip['destination']})")
            
            # Status badge
            status = booking.get("status", "confirmed")
            status_colors = {
                "confirmed": "green",
                "pending": "orange",
                "cancelled": "red"
            }
            st.markdown(f"<span style='background-color:{status_colors.get(status, 'blue')};color:white;padding:3px 8px;border-radius:10px;font-size:0.8em'>{status.upper()}</span>", unsafe_allow_html=True)
        
        with col2:
            # Show price information
            st.metric(
                label="Price",
                value=f"{booking['price']} {booking['currency']}"
            )
            
            # Delete booking button
            if st.button("Delete", key=f"delete_{booking['booking_id']}"):
                st.session_state.booking_to_delete = booking
                st.rerun()

# Function to handle booking creation form
def booking_creation_form():
    # Get user's trips for the dropdown
    trips = get_user_trips(user["user_id"])
    
    if not trips:
        st.warning("You need to create a trip before adding bookings.")
        if st.button("Create a Trip"):
            st.switch_page("pages/1_Trip_Planning.py")
        return
    
    # Get partners for suggestions
    partners = get_partners()
    
    with st.form("create_booking_form"):
        st.subheader("Booking Details")
        
        # Select trip
        trip_options = {f"{trip['title']} ({trip['destination']})": trip["trip_id"] for trip in trips}
        selected_trip_name = st.selectbox("Select Trip", options=list(trip_options.keys()))
        selected_trip_id = trip_options[selected_trip_name]
        
        # Get the selected trip details
        selected_trip = next((trip for trip in trips if trip["trip_id"] == selected_trip_id), None)
        
        # Booking type
        booking_type = st.selectbox(
            "Booking Type", 
            options=["flight", "hotel", "car", "activity", "other"],
            format_func=lambda x: x.capitalize()
        )
        
        # Partner/provider suggestions based on type
        if partners:
            filtered_partners = [p["name"] for p in partners if p["type"].lower() == booking_type]
            
            if filtered_partners:
                provider = st.selectbox("Provider", options=[""] + filtered_partners)
                if not provider:  # If empty selection, allow custom input
                    provider = st.text_input("Provider Name", placeholder=f"Enter {booking_type} provider name")
            else:
                provider = st.text_input("Provider Name", placeholder=f"Enter {booking_type} provider name")
        else:
            provider = st.text_input("Provider Name", placeholder=f"Enter {booking_type} provider name")
        
        booking_reference = st.text_input("Booking Reference", placeholder="Confirmation number, reservation ID, etc.")
        
        # Dates (default to trip dates if available)
        col1, col2 = st.columns(2)
        with col1:
            min_date = selected_trip["start_date"] if selected_trip else datetime.date.today()
            max_date = selected_trip["end_date"] if selected_trip else None
            
            start_date = st.date_input("Start Date", 
                                      value=min_date,
                                      min_value=min_date,
                                      max_value=max_date)
        with col2:
            min_end_date = start_date if start_date else datetime.date.today()
            max_end_date = selected_trip["end_date"] if selected_trip else None
            
            end_date = st.date_input("End Date", 
                                    value=max_end_date if max_end_date else min_end_date,
                                    min_value=min_end_date,
                                    max_value=max_end_date)
        
        # Price information
        col1, col2 = st.columns(2)
        with col1:
            price = st.number_input("Price", min_value=0.0, step=0.01)
        with col2:
            currency = st.selectbox("Currency", options=["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "INR"])
        
        # Status and notes
        status = st.selectbox("Status", options=["confirmed", "pending", "cancelled"])
        notes = st.text_area("Notes (Optional)", placeholder="Additional booking details, confirmation emails, etc.")
        
        submit_button = st.form_submit_button("Add Booking")
        
        if submit_button:
            if not provider or not booking_reference:
                st.error("Provider and booking reference are required")
            elif start_date > end_date:
                st.error("End date must be after start date")
            else:
                booking_data = {
                    "user_id": user["user_id"],
                    "trip_id": selected_trip_id,
                    "type": booking_type,
                    "provider": provider,
                    "booking_reference": booking_reference,
                    "start_date": start_date,
                    "end_date": end_date,
                    "price": price,
                    "currency": currency,
                    "status": status,
                    "notes": notes
                }
                
                result = create_booking(booking_data)
                
                if result["success"]:
                    st.success(result["message"])
                    # Clear form and refresh
                    st.session_state.booking_created = True
                    st.rerun()
                else:
                    st.error(result["message"])

# Function to display delete booking confirmation
def confirm_delete_booking(booking):
    st.warning(f"Are you sure you want to delete this {booking['type']} booking with {booking['provider']}?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, Delete Booking"):
            result = delete_booking(booking["booking_id"])
            
            if result["success"]:
                st.success(result["message"])
                # Remove delete state and refresh
                if "booking_to_delete" in st.session_state:
                    del st.session_state.booking_to_delete
                st.rerun()
            else:
                st.error(result["message"])
    with col2:
        if st.button("Cancel"):
            if "booking_to_delete" in st.session_state:
                del st.session_state.booking_to_delete
            st.rerun()

# Display bookings list
with tab1:
    # Check if a booking is to be deleted
    if "booking_to_delete" in st.session_state:
        confirm_delete_booking(st.session_state.booking_to_delete)
    
    else:
        # Fetch user's bookings
        bookings = get_user_bookings(user["user_id"])
        
        if bookings:
            st.write(f"You have {len(bookings)} bookings.")
            
            # Sort bookings by date
            # Convert start_date to date if it is datetime to avoid TypeError
            today_date = datetime.datetime.now().date()
            upcoming_bookings = [b for b in bookings if (b["start_date"].date() if isinstance(b["start_date"], datetime.datetime) else b["start_date"]) >= today_date]
            past_bookings = [b for b in bookings if (b["start_date"].date() if isinstance(b["start_date"], datetime.datetime) else b["start_date"]) < today_date]
            
            # Filter options
            booking_types = ["All"] + list(set(b["type"] for b in bookings))
            selected_type = st.selectbox("Filter by Type", options=booking_types)
            
            # Get all trips
            trips = get_user_trips(user["user_id"])
            trip_map = {trip["trip_id"]: trip["title"] for trip in trips}
            
            trip_options = ["All"] + [trip["title"] for trip in trips]
            selected_trip = st.selectbox("Filter by Trip", options=trip_options)
            
            # Apply filters
            if selected_type != "All":
                upcoming_bookings = [b for b in upcoming_bookings if b["type"] == selected_type]
                past_bookings = [b for b in past_bookings if b["type"] == selected_type]
            
            if selected_trip != "All":
                selected_trip_id = next((trip["trip_id"] for trip in trips if trip["title"] == selected_trip), None)
                if selected_trip_id:
                    upcoming_bookings = [b for b in upcoming_bookings if b["trip_id"] == selected_trip_id]
                    past_bookings = [b for b in past_bookings if b["trip_id"] == selected_trip_id]
            
            # Display filtered bookings
            if upcoming_bookings:
                st.subheader("Upcoming Bookings")
                for booking in sorted(upcoming_bookings, key=lambda x: x["start_date"]):
                    show_booking_details(booking)
            
            if past_bookings:
                st.subheader("Past Bookings")
                for booking in sorted(past_bookings, key=lambda x: x["start_date"], reverse=True):
                    show_booking_details(booking)
            
            # Calculate total spend by currency
            if bookings:
                st.subheader("Booking Expenses Summary")
                
                # Group by currency
                expenses_by_currency = {}
                for booking in bookings:
                    currency = booking["currency"]
                    if currency not in expenses_by_currency:
                        expenses_by_currency[currency] = 0
                    expenses_by_currency[currency] += booking["price"]
                
                # Display in columns
                cols = st.columns(len(expenses_by_currency) or 1)
                for i, (currency, amount) in enumerate(expenses_by_currency.items()):
                    with cols[i % len(cols)]:
                        st.metric(f"Total ({currency})", f"{amount:.2f} {currency}")
        else:
            st.info("You don't have any bookings yet. Add a new booking to get started!")
            if st.button("Add Your First Booking"):
                st.switch_tab("Add New Booking")

# Create new booking
with tab2:
    booking_creation_form()
