import streamlit as st
import pymongo
import os
import datetime

# MongoDB connection
@st.cache_resource
def get_db_connection():
    """
    Create a connection to MongoDB and return the database instance
    """
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://Pawan:admin@cluster0.tfeq9pn.mongodb.net/travel_manager?retryWrites=true&w=majority&appName=Cluster0")
    
    try:
        client = pymongo.MongoClient(MONGODB_URI)
        db = client.travel_manager
        return db
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None

def initialize_database():
    """
    Initialize database with required collections and indexes
    """
    db = get_db_connection()
    
    if db is None:
        return
    
    # For users collection, we'll drop and recreate it to fix the schema issues
    try:
        if "users" in db.list_collection_names():
            # Drop the collection to remove problematic indexes
            db.users.drop()
            print("Dropped users collection to fix schema issues")
            
        # Create users collection with proper indexes
        if "users" not in db.list_collection_names():
            db.create_collection("users")
            db.users.create_index([("email", pymongo.ASCENDING)], unique=True)
            db.users.create_index([("username", pymongo.ASCENDING)], unique=True)
            print("Created users collection with proper indexes")
    except Exception as e:
        print(f"Error while initializing users collection: {e}")
    
    # Initialize other collections if they don't exist
    if "trips" not in db.list_collection_names():
        db.create_collection("trips")
        db.trips.create_index([("user_id", pymongo.ASCENDING)])
    
    if "bookings" not in db.list_collection_names():
        db.create_collection("bookings")
        db.bookings.create_index([("trip_id", pymongo.ASCENDING)])
        db.bookings.create_index([("user_id", pymongo.ASCENDING)])
    
    if "expenses" not in db.list_collection_names():
        db.create_collection("expenses")
        db.expenses.create_index([("trip_id", pymongo.ASCENDING)])
        db.expenses.create_index([("user_id", pymongo.ASCENDING)])
    
    if "tourist_spots" not in db.list_collection_names():
        db.create_collection("tourist_spots")
    
    if "partners" not in db.list_collection_names():
        db.create_collection("partners")
    
    if "feedback" not in db.list_collection_names():
        db.create_collection("feedback")
        db.feedback.create_index([("user_id", pymongo.ASCENDING)])
    
    # Create admin user if it doesn't exist
    try:
        admin_exists = db.users.find_one({"email": "admin@travelmanager.com"})
        if admin_exists is None:
            import hashlib
            admin_user = {
                "user_id": "admin",
                "name": "Admin",
                "email": "admin@travelmanager.com",
                "username": "admin",  # Add username field
                "password": hashlib.sha256("admin123".encode()).hexdigest(),
                "role": "admin",
                "created_at": datetime.datetime.now(),
                "last_login": None
            }
            db.users.insert_one(admin_user)
            print("Created admin user")
    except Exception as e:
        print(f"Error creating admin user: {e}")

# Trip related functions
def create_trip(user_id, trip_data):
    """Create a new trip for a user"""
    db = get_db_connection()
    if db is None:
        return {"success": False, "message": "Database connection error"}
    
    trip_id = trip_data.get("trip_id", str(datetime.datetime.now().timestamp()))
    
    # Convert date objects to datetime for MongoDB compatibility
    start_date = trip_data["start_date"]
    end_date = trip_data["end_date"]
    
    # Convert to datetime if they're date objects
    if isinstance(start_date, datetime.date) and not isinstance(start_date, datetime.datetime):
        start_date = datetime.datetime.combine(start_date, datetime.datetime.min.time())
    
    if isinstance(end_date, datetime.date) and not isinstance(end_date, datetime.datetime):
        end_date = datetime.datetime.combine(end_date, datetime.datetime.min.time())
    
    trip = {
        "trip_id": trip_id,
        "user_id": user_id,
        "title": trip_data["title"],
        "destination": trip_data["destination"],
        "start_date": start_date,
        "end_date": end_date,
        "description": trip_data.get("description", ""),
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now(),
        "status": "planned"  # planned, active, completed, cancelled
    }
    
    try:
        db.trips.insert_one(trip)
        return {"success": True, "message": "Trip created successfully", "trip_id": trip_id}
    except Exception as e:
        return {"success": False, "message": f"Failed to create trip: {str(e)}"}

def get_user_trips(user_id):
    """Get all trips for a user"""
    db = get_db_connection()
    if db is None:
        return []
    
    trips = list(db.trips.find({"user_id": user_id}).sort("start_date", -1))
    return trips

def get_trip_by_id(trip_id):
    """Get a trip by ID"""
    db = get_db_connection()
    if db is None:
        return None
    
    trip = db.trips.find_one({"trip_id": trip_id})
    return trip

def update_trip(trip_id, trip_data):
    """Update a trip"""
    db = get_db_connection()
    if db is None:
        return {"success": False, "message": "Database connection error"}
    
    # Process dates to ensure they're MongoDB compatible
    if "start_date" in trip_data and isinstance(trip_data["start_date"], datetime.date) and not isinstance(trip_data["start_date"], datetime.datetime):
        trip_data["start_date"] = datetime.datetime.combine(trip_data["start_date"], datetime.datetime.min.time())
    
    if "end_date" in trip_data and isinstance(trip_data["end_date"], datetime.date) and not isinstance(trip_data["end_date"], datetime.datetime):
        trip_data["end_date"] = datetime.datetime.combine(trip_data["end_date"], datetime.datetime.min.time())
    
    trip_data["updated_at"] = datetime.datetime.now()
    
    try:
        result = db.trips.update_one(
            {"trip_id": trip_id},
            {"$set": trip_data}
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": "Trip updated successfully"}
        else:
            return {"success": False, "message": "Trip not found or no changes made"}
    except Exception as e:
        return {"success": False, "message": f"Failed to update trip: {str(e)}"}

def delete_trip(trip_id):
    """Delete a trip and all related bookings and expenses"""
    db = get_db_connection()
    if db is None:
        return {"success": False, "message": "Database connection error"}
    
    try:
        # Delete trip
        trip_result = db.trips.delete_one({"trip_id": trip_id})
        
        # Delete related bookings
        db.bookings.delete_many({"trip_id": trip_id})
        
        # Delete related expenses
        db.expenses.delete_many({"trip_id": trip_id})
        
        if trip_result.deleted_count > 0:
            return {"success": True, "message": "Trip and all related data deleted successfully"}
        else:
            return {"success": False, "message": "Trip not found"}
    except Exception as e:
        return {"success": False, "message": f"Failed to delete trip: {str(e)}"}

# Booking related functions
def create_booking(booking_data):
    """Create a new booking"""
    db = get_db_connection()
    if db is None:
        return {"success": False, "message": "Database connection error"}
    
    booking_id = booking_data.get("booking_id", str(datetime.datetime.now().timestamp()))
    
    # Convert date objects to datetime for MongoDB compatibility
    start_date = booking_data["start_date"]
    end_date = booking_data["end_date"]
    
    # Convert to datetime if they're date objects
    if isinstance(start_date, datetime.date) and not isinstance(start_date, datetime.datetime):
        start_date = datetime.datetime.combine(start_date, datetime.datetime.min.time())
    
    if isinstance(end_date, datetime.date) and not isinstance(end_date, datetime.datetime):
        end_date = datetime.datetime.combine(end_date, datetime.datetime.min.time())
    
    booking = {
        "booking_id": booking_id,
        "user_id": booking_data["user_id"],
        "trip_id": booking_data["trip_id"],
        "type": booking_data["type"],  # flight, hotel, car, activity
        "provider": booking_data["provider"],
        "booking_reference": booking_data["booking_reference"],
        "start_date": start_date,
        "end_date": end_date,
        "price": float(booking_data["price"]),  # Ensure price is a float
        "currency": booking_data["currency"],
        "status": booking_data.get("status", "confirmed"),  # confirmed, cancelled, pending
        "notes": booking_data.get("notes", ""),
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now()
    }
    
    try:
        db.bookings.insert_one(booking)
        return {"success": True, "message": "Booking created successfully", "booking_id": booking_id}
    except Exception as e:
        return {"success": False, "message": f"Failed to create booking: {str(e)}"}

def get_trip_bookings(trip_id):
    """Get all bookings for a trip"""
    db = get_db_connection()
    if db is None:
        return []
    
    bookings = list(db.bookings.find({"trip_id": trip_id}).sort("start_date", 1))
    return bookings

def get_user_bookings(user_id):
    """Get all bookings for a user"""
    db = get_db_connection()
    if db is None:
        return []
    
    bookings = list(db.bookings.find({"user_id": user_id}).sort("start_date", 1))
    return bookings

def delete_booking(booking_id):
    """Delete a booking"""
    db = get_db_connection()
    if db is None:
        return {"success": False, "message": "Database connection error"}
    
    try:
        result = db.bookings.delete_one({"booking_id": booking_id})
        
        if result.deleted_count > 0:
            return {"success": True, "message": "Booking deleted successfully"}
        else:
            return {"success": False, "message": "Booking not found"}
    except Exception as e:
        return {"success": False, "message": f"Failed to delete booking: {str(e)}"}

# Expense related functions
def add_expense(expense_data):
    """Add a new expense"""
    db = get_db_connection()
    if db is None:
        return {"success": False, "message": "Database connection error"}
    
    expense_id = expense_data.get("expense_id", str(datetime.datetime.now().timestamp()))
    
    # Convert date objects to datetime for MongoDB compatibility
    expense_date = expense_data["date"]
    
    # Convert to datetime if it's a date object
    if isinstance(expense_date, datetime.date) and not isinstance(expense_date, datetime.datetime):
        expense_date = datetime.datetime.combine(expense_date, datetime.datetime.min.time())
    
    expense = {
        "expense_id": expense_id,
        "user_id": expense_data["user_id"],
        "trip_id": expense_data["trip_id"],
        "category": expense_data["category"],
        "amount": float(expense_data["amount"]),  # Ensure amount is a float
        "currency": expense_data["currency"],
        "date": expense_date,
        "description": expense_data.get("description", ""),
        "payment_method": expense_data.get("payment_method", ""),
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now()
    }
    
    try:
        db.expenses.insert_one(expense)
        return {"success": True, "message": "Expense added successfully", "expense_id": expense_id}
    except Exception as e:
        return {"success": False, "message": f"Failed to add expense: {str(e)}"}

def get_trip_expenses(trip_id):
    """Get all expenses for a trip"""
    db = get_db_connection()
    if db is None:
        return []
    
    expenses = list(db.expenses.find({"trip_id": trip_id}).sort("date", -1))
    return expenses

def get_user_expenses(user_id):
    """Get all expenses for a user"""
    db = get_db_connection()
    if db is None:
        return []
    
    expenses = list(db.expenses.find({"user_id": user_id}).sort("date", -1))
    return expenses

def delete_expense(expense_id):
    """Delete an expense"""
    db = get_db_connection()
    if db is None:
        return {"success": False, "message": "Database connection error"}
    
    try:
        result = db.expenses.delete_one({"expense_id": expense_id})
        
        if result.deleted_count > 0:
            return {"success": True, "message": "Expense deleted successfully"}
        else:
            return {"success": False, "message": "Expense not found"}
    except Exception as e:
        return {"success": False, "message": f"Failed to delete expense: {str(e)}"}

# Tourist spot related functions (for admin)
def add_tourist_spot(spot_data):
    """Add a new tourist spot"""
    db = get_db_connection()
    if db is None:
        return {"success": False, "message": "Database connection error"}
    
    spot_id = spot_data.get("spot_id", str(datetime.datetime.now().timestamp()))
    
    spot = {
        "spot_id": spot_id,
        "name": spot_data["name"],
        "location": spot_data["location"],
        "description": spot_data["description"],
        "category": spot_data["category"],
        "rating": spot_data.get("rating", 0),
        "coordinates": spot_data.get("coordinates", {"lat": 0, "lng": 0}),
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now()
    }
    
    try:
        db.tourist_spots.insert_one(spot)
        return {"success": True, "message": "Tourist spot added successfully", "spot_id": spot_id}
    except Exception as e:
        return {"success": False, "message": f"Failed to add tourist spot: {str(e)}"}

def get_tourist_spots():
    """Get all tourist spots"""
    db = get_db_connection()
    if db is None:
        return []
    
    spots = list(db.tourist_spots.find().sort("name", 1))
    return spots

def delete_tourist_spot(spot_id):
    """Delete a tourist spot"""
    db = get_db_connection()
    if db is None:
        return {"success": False, "message": "Database connection error"}
    
    try:
        result = db.tourist_spots.delete_one({"spot_id": spot_id})
        
        if result.deleted_count > 0:
            return {"success": True, "message": "Tourist spot deleted successfully"}
        else:
            return {"success": False, "message": "Tourist spot not found"}
    except Exception as e:
        return {"success": False, "message": f"Failed to delete tourist spot: {str(e)}"}

# Partner related functions (for admin)
def add_partner(partner_data):
    """Add a new partner"""
    db = get_db_connection()
    if db is None:
        return {"success": False, "message": "Database connection error"}
    
    partner_id = partner_data.get("partner_id", str(datetime.datetime.now().timestamp()))
    
    partner = {
        "partner_id": partner_id,
        "name": partner_data["name"],
        "type": partner_data["type"],  # hotel, airline, car rental, etc.
        "contact_email": partner_data["contact_email"],
        "contact_phone": partner_data.get("contact_phone", ""),
        "website": partner_data.get("website", ""),
        "description": partner_data.get("description", ""),
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now()
    }
    
    try:
        db.partners.insert_one(partner)
        return {"success": True, "message": "Partner added successfully", "partner_id": partner_id}
    except Exception as e:
        return {"success": False, "message": f"Failed to add partner: {str(e)}"}

def get_partners():
    """Get all partners"""
    db = get_db_connection()
    if db is None:
        return []
    
    partners = list(db.partners.find().sort("name", 1))
    return partners

def delete_partner(partner_id):
    """Delete a partner"""
    db = get_db_connection()
    if db is None:
        return {"success": False, "message": "Database connection error"}
    
    try:
        result = db.partners.delete_one({"partner_id": partner_id})
        
        if result.deleted_count > 0:
            return {"success": True, "message": "Partner deleted successfully"}
        else:
            return {"success": False, "message": "Partner not found"}
    except Exception as e:
        return {"success": False, "message": f"Failed to delete partner: {str(e)}"}

# Feedback related functions
def add_feedback(feedback_data):
    """Add user feedback"""
    db = get_db_connection()
    if db is None:
        return {"success": False, "message": "Database connection error"}
    
    feedback_id = feedback_data.get("feedback_id", str(datetime.datetime.now().timestamp()))
    
    feedback = {
        "feedback_id": feedback_id,
        "user_id": feedback_data["user_id"],
        "rating": feedback_data["rating"],
        "comment": feedback_data["comment"],
        "category": feedback_data.get("category", "general"),
        "created_at": datetime.datetime.now()
    }
    
    try:
        db.feedback.insert_one(feedback)
        return {"success": True, "message": "Feedback submitted successfully", "feedback_id": feedback_id}
    except Exception as e:
        return {"success": False, "message": f"Failed to submit feedback: {str(e)}"}

def get_all_feedback():
    """Get all feedback (for admin)"""
    db = get_db_connection()
    if db is None:
        return []
    
    feedback = list(db.feedback.find().sort("created_at", -1))
    return feedback

def get_user_feedback(user_id):
    """Get feedback submitted by a user"""
    db = get_db_connection()
    if db is None:
        return []
    
    feedback = list(db.feedback.find({"user_id": user_id}).sort("created_at", -1))
    return feedback
