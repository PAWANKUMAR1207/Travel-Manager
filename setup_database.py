"""
MongoDB Atlas Database Setup Script for Travel Manager

This script will:
1. Connect to MongoDB Atlas
2. Create a new database named 'travel_manager'
3. Create collections with proper schema validation
4. Create indexes for performance optimization
5. Create an admin user
"""

import pymongo
import datetime
import hashlib
import json
import sys

# Connection string 
CONNECTION_STRING = "mongodb+srv://Pawan:admin@cluster0.tfeq9pn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

def setup_database():
    try:
        # Connect to MongoDB Atlas
        client = pymongo.MongoClient(CONNECTION_STRING)
        
        # Test connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")
        
        # Create or get database
        db = client.travel_manager
        print("📦 Setting up 'travel_manager' database...")
        
        # Drop existing collections to reset
        for collection in db.list_collection_names():
            db[collection].drop()
            print(f"   🗑️ Dropped existing {collection} collection")
        
        # Set up users collection with schema validation
        print("\n🔐 Setting up users collection...")
        db.create_collection("users", validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "email", "username", "password", "role"],
                "properties": {
                    "user_id": {
                        "bsonType": "string",
                        "description": "Unique identifier for the user"
                    },
                    "name": {
                        "bsonType": "string",
                        "description": "Full name of the user"
                    },
                    "email": {
                        "bsonType": "string",
                        "description": "Email address of the user",
                        "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                    },
                    "username": {
                        "bsonType": "string",
                        "description": "Username for the user"
                    },
                    "password": {
                        "bsonType": "string",
                        "description": "Hashed password for the user"
                    },
                    "role": {
                        "enum": ["user", "admin"],
                        "description": "Role of the user"
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "Date when the user was created"
                    },
                    "last_login": {
                        "bsonType": ["date", "null"],
                        "description": "Date of the last login"
                    }
                }
            }
        })
        db.users.create_index([("email", pymongo.ASCENDING)], unique=True)
        db.users.create_index([("username", pymongo.ASCENDING)], unique=True)
        print("   📑 Created users collection with schema validation")
        print("   🔍 Created unique indexes on email and username")
        
        # Set up trips collection with schema validation
        print("\n🌍 Setting up trips collection...")
        db.create_collection("trips", validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["trip_id", "user_id", "title", "destination", "start_date", "end_date"],
                "properties": {
                    "trip_id": {
                        "bsonType": "string",
                        "description": "Unique identifier for the trip"
                    },
                    "user_id": {
                        "bsonType": "string",
                        "description": "ID of the user who owns this trip"
                    },
                    "title": {
                        "bsonType": "string",
                        "description": "Title of the trip"
                    },
                    "destination": {
                        "bsonType": "string",
                        "description": "Destination of the trip"
                    },
                    "start_date": {
                        "bsonType": "date", 
                        "description": "Start date of the trip"
                    },
                    "end_date": {
                        "bsonType": "date",
                        "description": "End date of the trip"
                    },
                    "description": {
                        "bsonType": "string",
                        "description": "Description of the trip"
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "Date when the trip was created"
                    },
                    "updated_at": {
                        "bsonType": "date",
                        "description": "Date when the trip was last updated"
                    },
                    "status": {
                        "enum": ["planned", "active", "completed", "cancelled"],
                        "description": "Status of the trip"
                    }
                }
            }
        })
        db.trips.create_index([("user_id", pymongo.ASCENDING)])
        db.trips.create_index([("start_date", pymongo.DESCENDING)])
        print("   📑 Created trips collection with schema validation")
        print("   🔍 Created indexes on user_id and start_date")
        
        # Set up bookings collection with schema validation
        print("\n🏨 Setting up bookings collection...")
        db.create_collection("bookings", validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["booking_id", "user_id", "trip_id", "type", "provider", "start_date", "end_date", "price"],
                "properties": {
                    "booking_id": {
                        "bsonType": "string",
                        "description": "Unique identifier for the booking"
                    },
                    "user_id": {
                        "bsonType": "string",
                        "description": "ID of the user who made this booking"
                    },
                    "trip_id": {
                        "bsonType": "string",
                        "description": "ID of the trip this booking belongs to"
                    },
                    "type": {
                        "enum": ["flight", "hotel", "car", "activity", "other"],
                        "description": "Type of booking"
                    },
                    "provider": {
                        "bsonType": "string",
                        "description": "Name of the provider (airline, hotel, etc.)"
                    },
                    "booking_reference": {
                        "bsonType": "string",
                        "description": "Reference number for the booking"
                    },
                    "start_date": {
                        "bsonType": "date",
                        "description": "Start date of the booking"
                    },
                    "end_date": {
                        "bsonType": "date",
                        "description": "End date of the booking"
                    },
                    "price": {
                        "bsonType": "double",
                        "description": "Price of the booking"
                    },
                    "currency": {
                        "bsonType": "string",
                        "description": "Currency of the price"
                    },
                    "status": {
                        "enum": ["confirmed", "pending", "cancelled"],
                        "description": "Status of the booking"
                    },
                    "notes": {
                        "bsonType": "string",
                        "description": "Additional notes for the booking"
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "Date when the booking was created"
                    },
                    "updated_at": {
                        "bsonType": "date",
                        "description": "Date when the booking was last updated"
                    }
                }
            }
        })
        db.bookings.create_index([("trip_id", pymongo.ASCENDING)])
        db.bookings.create_index([("user_id", pymongo.ASCENDING)])
        db.bookings.create_index([("start_date", pymongo.ASCENDING)])
        print("   📑 Created bookings collection with schema validation")
        print("   🔍 Created indexes on trip_id, user_id, and start_date")
        
        # Set up expenses collection with schema validation
        print("\n💰 Setting up expenses collection...")
        db.create_collection("expenses", validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["expense_id", "user_id", "trip_id", "category", "amount", "currency", "date"],
                "properties": {
                    "expense_id": {
                        "bsonType": "string",
                        "description": "Unique identifier for the expense"
                    },
                    "user_id": {
                        "bsonType": "string",
                        "description": "ID of the user who recorded this expense"
                    },
                    "trip_id": {
                        "bsonType": "string",
                        "description": "ID of the trip this expense belongs to"
                    },
                    "category": {
                        "bsonType": "string",
                        "description": "Category of the expense"
                    },
                    "amount": {
                        "bsonType": "double",
                        "description": "Amount of the expense"
                    },
                    "currency": {
                        "bsonType": "string",
                        "description": "Currency of the amount"
                    },
                    "date": {
                        "bsonType": "date",
                        "description": "Date of the expense"
                    },
                    "description": {
                        "bsonType": "string",
                        "description": "Description of the expense"
                    },
                    "payment_method": {
                        "bsonType": "string",
                        "description": "Method of payment"
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "Date when the expense was recorded"
                    },
                    "updated_at": {
                        "bsonType": "date",
                        "description": "Date when the expense was last updated"
                    }
                }
            }
        })
        db.expenses.create_index([("trip_id", pymongo.ASCENDING)])
        db.expenses.create_index([("user_id", pymongo.ASCENDING)])
        db.expenses.create_index([("date", pymongo.DESCENDING)])
        print("   📑 Created expenses collection with schema validation")
        print("   🔍 Created indexes on trip_id, user_id, and date")
        
        # Set up tourist spots collection with schema validation
        print("\n🗿 Setting up tourist_spots collection...")
        db.create_collection("tourist_spots", validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["spot_id", "name", "location", "category"],
                "properties": {
                    "spot_id": {
                        "bsonType": "string",
                        "description": "Unique identifier for the tourist spot"
                    },
                    "name": {
                        "bsonType": "string",
                        "description": "Name of the tourist spot"
                    },
                    "location": {
                        "bsonType": "string", 
                        "description": "Location of the tourist spot"
                    },
                    "description": {
                        "bsonType": "string",
                        "description": "Description of the tourist spot"
                    },
                    "category": {
                        "bsonType": "string",
                        "description": "Category of the tourist spot"
                    },
                    "rating": {
                        "bsonType": "double",
                        "description": "Rating of the tourist spot"
                    },
                    "coordinates": {
                        "bsonType": "object",
                        "required": ["lat", "lng"],
                        "properties": {
                            "lat": {
                                "bsonType": "double",
                                "description": "Latitude of the tourist spot"
                            },
                            "lng": {
                                "bsonType": "double",
                                "description": "Longitude of the tourist spot"
                            }
                        }
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "Date when the tourist spot was added"
                    },
                    "updated_at": {
                        "bsonType": "date",
                        "description": "Date when the tourist spot was last updated"
                    }
                }
            }
        })
        db.tourist_spots.create_index([("location", pymongo.TEXT)])
        db.tourist_spots.create_index([("name", pymongo.ASCENDING)])
        print("   📑 Created tourist_spots collection with schema validation")
        print("   🔍 Created text index on location and index on name")
        
        # Set up partners collection with schema validation
        print("\n🤝 Setting up partners collection...")
        db.create_collection("partners", validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["partner_id", "name", "type", "contact_email"],
                "properties": {
                    "partner_id": {
                        "bsonType": "string",
                        "description": "Unique identifier for the partner"
                    },
                    "name": {
                        "bsonType": "string",
                        "description": "Name of the partner"
                    },
                    "type": {
                        "enum": ["hotel", "airline", "car_rental", "tour_operator", "restaurant", "other"],
                        "description": "Type of partner"
                    },
                    "contact_email": {
                        "bsonType": "string",
                        "description": "Contact email of the partner"
                    },
                    "contact_phone": {
                        "bsonType": "string",
                        "description": "Contact phone of the partner"
                    },
                    "website": {
                        "bsonType": "string",
                        "description": "Website of the partner"
                    },
                    "description": {
                        "bsonType": "string",
                        "description": "Description of the partner"
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "Date when the partner was added"
                    },
                    "updated_at": {
                        "bsonType": "date",
                        "description": "Date when the partner was last updated"
                    }
                }
            }
        })
        db.partners.create_index([("name", pymongo.ASCENDING)])
        db.partners.create_index([("type", pymongo.ASCENDING)])
        print("   📑 Created partners collection with schema validation")
        print("   🔍 Created indexes on name and type")
        
        # Set up feedback collection with schema validation
        print("\n📝 Setting up feedback collection...")
        db.create_collection("feedback", validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["feedback_id", "user_id", "rating", "comment"],
                "properties": {
                    "feedback_id": {
                        "bsonType": "string",
                        "description": "Unique identifier for the feedback"
                    },
                    "user_id": {
                        "bsonType": "string",
                        "description": "ID of the user who submitted this feedback"
                    },
                    "rating": {
                        "bsonType": "int",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "Rating from 1-5"
                    },
                    "comment": {
                        "bsonType": "string",
                        "description": "Feedback comment"
                    },
                    "category": {
                        "bsonType": "string",
                        "description": "Category of the feedback"
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "Date when the feedback was submitted"
                    }
                }
            }
        })
        db.feedback.create_index([("user_id", pymongo.ASCENDING)])
        db.feedback.create_index([("created_at", pymongo.DESCENDING)])
        print("   📑 Created feedback collection with schema validation")
        print("   🔍 Created indexes on user_id and created_at")
        
        # Create admin user
        print("\n👤 Creating admin user...")
        admin_user = {
            "user_id": "admin",
            "name": "Admin",
            "email": "admin@travelmanager.com",
            "username": "admin",
            "password": hashlib.sha256("admin123".encode()).hexdigest(),
            "role": "admin",
            "created_at": datetime.datetime.now(),
            "last_login": None
        }
        db.users.insert_one(admin_user)
        print("   ✅ Created admin user (email: admin@travelmanager.com, password: admin123)")
        
        # Create sample data (optional)
        print("\n🌟 Successfully set up the Travel Manager database in MongoDB Atlas!")
        print("   Database name: travel_manager")
        print("   Collections: users, trips, bookings, expenses, tourist_spots, partners, feedback")
        
        return True
    
    except Exception as e:
        print(f"❌ Error setting up database: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Running MongoDB Atlas Database Setup for Travel Manager")
    success = setup_database()
    if success:
        print("\n✅ Database setup completed successfully!")
    else:
        print("\n❌ Database setup failed. Please check the errors above.")
        sys.exit(1)