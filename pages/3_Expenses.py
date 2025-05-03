import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
from utils.auth import check_session, require_login
from utils.db import (
    get_user_trips, get_trip_by_id, add_expense,
    get_trip_expenses, get_user_expenses, delete_expense
)

# Page config
st.set_page_config(
    page_title="Expenses - Travel Manager",
    page_icon="💰",
    layout="wide"
)

# Require login
require_login()
user = st.session_state.user

# Page title
st.title("💰 Expense Tracking")
st.write("Track and analyze your travel expenses")

# Initialize session state for tab index
if "expense_tab" not in st.session_state:
    st.session_state.expense_tab = "Expense List"

# Tab selection using radio buttons
tab_labels = ["Expense List", "Add Expense", "Analytics"]
selected_tab = st.radio("Select Tab", tab_labels, index=tab_labels.index(st.session_state.expense_tab))
st.session_state.expense_tab = selected_tab

# Conditional rendering of tab content
tab1 = (selected_tab == "Expense List")
tab2 = (selected_tab == "Add Expense")
tab3 = (selected_tab == "Analytics")

# Function to display expense details
def show_expense_details(expense, trips_map):
    category_icons = {
        "accommodation": "🏨",
        "food": "🍽️",
        "transportation": "🚌",
        "activities": "🎭",
        "shopping": "🛍️",
        "other": "📝"
    }
    
    icon = category_icons.get(expense.get("category", "other"), "📝")
    
    with st.expander(f"{icon} {expense['description']} - {expense['date'].strftime('%d %b %Y')}", expanded=False):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"{icon} {expense['category'].capitalize()}")
            st.write(f"**Description:** {expense['description']}")
            st.write(f"**Date:** {expense['date'].strftime('%d %b %Y')}")
            
            if expense.get("payment_method"):
                st.write(f"**Payment Method:** {expense['payment_method']}")
            
            # Get trip information
            trip_name = trips_map.get(expense["trip_id"], "Unknown Trip")
            st.write(f"**Trip:** {trip_name}")
        
        with col2:
            # Show amount
            st.metric(
                label="Amount",
                value=f"{expense['amount']} {expense['currency']}"
            )
            
            # Delete expense button
            if st.button("Delete", key=f"delete_{expense['expense_id']}"):
                st.session_state.expense_to_delete = expense
                st.rerun()

# Function to handle expense creation form
def expense_creation_form():
    # Get user's trips for the dropdown
    trips = get_user_trips(user["user_id"])
    
    if not trips:
        st.warning("You need to create a trip before adding expenses.")
        if st.button("Create a Trip"):
            # Navigate to trip planning page
            st.session_state.expense_tab = 0  # Optionally reset tab index if needed
            st.experimental_rerun()
    
    with st.form("create_expense_form"):
        st.subheader("Expense Details")
        
        # Select trip
        trip_options = {f"{trip['title']} ({trip['destination']})": trip["trip_id"] for trip in trips}
        selected_trip_name = st.selectbox("Select Trip", options=list(trip_options.keys()))
        selected_trip_id = trip_options[selected_trip_name]
        
        # Get the selected trip details
        selected_trip = next((trip for trip in trips if trip["trip_id"] == selected_trip_id), None)
        
        # Expense category
        category = st.selectbox(
            "Category", 
            options=["accommodation", "food", "transportation", "activities", "shopping", "other"],
            format_func=lambda x: x.capitalize()
        )
        
        description = st.text_input("Description", placeholder="Hotel stay, dinner, taxi, etc.")
        
        # Date (default to trip dates if available)
        min_date = selected_trip["start_date"] if selected_trip else datetime.date.today() - datetime.timedelta(days=30)
        max_date = selected_trip["end_date"] if selected_trip else datetime.date.today()

        # Convert min_date and max_date to date if they are datetime
        if isinstance(min_date, datetime.datetime):
            min_date = min_date.date()
        if isinstance(max_date, datetime.datetime):
            max_date = max_date.date()

        # Adjust default date to be within min and max date range
        default_date = datetime.date.today()
        if default_date < min_date:
            default_date = min_date
        elif default_date > max_date:
            default_date = max_date

        expense_date = st.date_input("Date", 
                                   value=default_date,
                                   min_value=min_date,
                                   max_value=max_date)
        
        # Amount information
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("Amount", min_value=0.0, step=0.01)
        with col2:
            currency = st.selectbox("Currency", options=["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "INR"])
        
        payment_method = st.selectbox(
            "Payment Method", 
            options=["credit card", "debit card", "cash", "mobile payment", "other"],
            format_func=lambda x: x.capitalize()
        )
        
        submit_button = st.form_submit_button("Add Expense")
        
        if submit_button:
            if not description:
                st.error("Description is required")
            elif amount <= 0:
                st.error("Amount must be greater than zero")
            else:
                expense_data = {
                    "user_id": user["user_id"],
                    "trip_id": selected_trip_id,
                    "category": category,
                    "description": description,
                    "date": expense_date,
                    "amount": amount,
                    "currency": currency,
                    "payment_method": payment_method
                }
                
                result = add_expense(expense_data)
                
                if result["success"]:
                    st.success(result["message"])
                    # Clear form and refresh
                    st.session_state.expense_created = True
                    st.rerun()
                else:
                    st.error(result["message"])

# Function to display expense analytics
def show_expense_analytics():
    # Fetch user's expenses
    expenses = get_user_expenses(user["user_id"])
    
    if not expenses:
        st.info("You don't have any expenses yet. Add expenses to see analytics.")
        return
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(expenses)
    
    # Get trip names
    trips = get_user_trips(user["user_id"])
    trips_map = {trip["trip_id"]: trip["title"] for trip in trips}
    df["trip_name"] = df["trip_id"].map(trips_map)
    
    st.subheader("Expense Summary")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        selected_currency = st.selectbox(
            "Currency", 
            options=["All"] + sorted(df["currency"].unique().tolist())
        )
    
    with col2:
        selected_trip = st.selectbox(
            "Trip", 
            options=["All"] + sorted(df["trip_name"].unique().tolist())
        )
    
    # Apply filters
    filtered_df = df.copy()
    if selected_currency != "All":
        filtered_df = filtered_df[filtered_df["currency"] == selected_currency]
    
    if selected_trip != "All":
        filtered_df = filtered_df[filtered_df["trip_name"] == selected_trip]
    
    if filtered_df.empty:
        st.info("No expenses match the selected filters.")
        return
    
    # Summary metrics
    total_by_currency = filtered_df.groupby("currency")["amount"].sum().reset_index()
    
    # Display totals in columns
    metric_cols = st.columns(len(total_by_currency) or 1)
    for i, (_, row) in enumerate(total_by_currency.iterrows()):
        with metric_cols[i]:
            st.metric(
                label=f"Total ({row['currency']})",
                value=f"{row['amount']:.2f} {row['currency']}"
            )
    
    # Expense by category chart
    st.subheader("Expenses by Category")
    
    category_totals = filtered_df.groupby(["category", "currency"]).agg(
        total=("amount", "sum")
    ).reset_index()
    
    if not category_totals.empty:
        # One chart per currency
        currencies = category_totals["currency"].unique()
        
        for currency in currencies:
            curr_data = category_totals[category_totals["currency"] == currency]
            
            fig = px.pie(
                curr_data, 
                values="total", 
                names="category",
                title=f"Expense Distribution ({currency})",
                color="category",
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
    
    # Expense over time chart
    st.subheader("Expenses Over Time")
    
    # Create date series for line chart
    time_series = filtered_df.copy()
    time_series["date"] = pd.to_datetime(time_series["date"])
    time_series = time_series.sort_values("date")
    
    # Group by date and currency
    by_date = time_series.groupby([pd.Grouper(key="date", freq="D"), "currency"]).agg(
        daily_total=("amount", "sum")
    ).reset_index()
    
    # Cumulative sum by currency
    for curr in by_date["currency"].unique():
        curr_mask = by_date["currency"] == curr
        by_date.loc[curr_mask, "cumulative"] = by_date.loc[curr_mask, "daily_total"].cumsum()
    
    # Create line chart per currency
    currencies = by_date["currency"].unique()
    
    for currency in currencies:
        curr_data = by_date[by_date["currency"] == currency]
        
        fig = px.line(
            curr_data,
            x="date",
            y="cumulative",
            title=f"Cumulative Expenses Over Time ({currency})",
            markers=True
        )
        fig.update_layout(xaxis_title="Date", yaxis_title=f"Cumulative Amount ({currency})")
        st.plotly_chart(fig, use_container_width=True)
    
    # Expense by trip chart (if 'All' trips selected)
    if selected_trip == "All":
        st.subheader("Expenses by Trip")
        
        trip_totals = filtered_df.groupby(["trip_name", "currency"]).agg(
            total=("amount", "sum")
        ).reset_index()
        
        for currency in trip_totals["currency"].unique():
            curr_data = trip_totals[trip_totals["currency"] == currency]
            
            fig = px.bar(
                curr_data,
                x="trip_name",
                y="total",
                title=f"Total Expenses by Trip ({currency})",
                color="trip_name"
            )
            fig.update_layout(xaxis_title="Trip", yaxis_title=f"Total Amount ({currency})")
            st.plotly_chart(fig, use_container_width=True)

# Function to display delete expense confirmation
def confirm_delete_expense(expense):
    st.warning(f"Are you sure you want to delete this expense: {expense['description']}?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, Delete Expense"):
            result = delete_expense(expense["expense_id"])
            
            if result["success"]:
                st.success(result["message"])
                # Remove delete state and refresh
                if "expense_to_delete" in st.session_state:
                    del st.session_state.expense_to_delete
                st.rerun()
            else:
                st.error(result["message"])
    with col2:
        if st.button("Cancel"):
            if "expense_to_delete" in st.session_state:
                del st.session_state.expense_to_delete
            st.rerun()

# Display expenses list
if tab1:
    # Check if an expense is to be deleted
    if "expense_to_delete" in st.session_state:
        confirm_delete_expense(st.session_state.expense_to_delete)
    else:
        # Fetch user's expenses
        expenses = get_user_expenses(user["user_id"])
        
        # Get trips information for display
        trips = get_user_trips(user["user_id"])
        trips_map = {trip["trip_id"]: trip["title"] for trip in trips}
        
        if expenses:
            st.write(f"You have recorded {len(expenses)} expenses.")
            
            # Filter options
            col1, col2 = st.columns(2)
            
            with col1:
                expense_categories = ["All"] + sorted(list(set(e["category"] for e in expenses)))
                selected_category = st.selectbox("Filter by Category", options=expense_categories)
            
            with col2:
                trip_options = ["All"] + sorted([trips_map.get(trip_id, "Unknown") for trip_id in set(e["trip_id"] for e in expenses)])
                selected_trip_name = st.selectbox("Filter by Trip", options=trip_options)
            
            # Apply filters
            filtered_expenses = expenses
            if selected_category != "All":
                filtered_expenses = [e for e in filtered_expenses if e["category"] == selected_category]
            
            if selected_trip_name != "All":
                trip_id = next((id for id, name in trips_map.items() if name == selected_trip_name), None)
                if trip_id:
                    filtered_expenses = [e for e in filtered_expenses if e["trip_id"] == trip_id]
            
            # Sort by date (most recent first)
            filtered_expenses = sorted(filtered_expenses, key=lambda x: x["date"], reverse=True)
            
            if filtered_expenses:
                for expense in filtered_expenses:
                    show_expense_details(expense, trips_map)
            else:
                st.info("No expenses match the selected filters.")
        else:
            st.info("You don't have any expenses yet. Add an expense to get started!")
            if st.button("Add Your First Expense"):
                st.session_state.expense_tab = "Add Expense"
                st.experimental_rerun()

# Create new expense
if tab2:
    expense_creation_form()

# Analytics
if tab3:
    show_expense_analytics()
