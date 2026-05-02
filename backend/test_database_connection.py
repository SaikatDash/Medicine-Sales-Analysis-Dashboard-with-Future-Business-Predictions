"""
Database Connection & Registration Test Script
Tests if the backend can properly store user data in PostgreSQL
"""

import requests
import json
from datetime import datetime
from sqlalchemy import inspect
from database import SessionLocal, engine
from database_model import Base, User
import sys

print("=" * 60)
print("🔍 DATABASE & REGISTRATION TEST")
print("=" * 60)

# ============================================
# TEST 1: Database Connection
# ============================================
print("\n[TEST 1] Testing Database Connection...")
try:
    # Try to connect to database
    connection = engine.connect()
    connection.close()
    print("✅ Database connection SUCCESSFUL")
except Exception as e:
    print(f"❌ Database connection FAILED: {str(e)}")
    print("   Make sure PostgreSQL is running on localhost:5432")
    print("   Database: loginDatabase")
    print("   User: postgres")
    sys.exit(1)

# ============================================
# TEST 2: Check Tables Exist
# ============================================
print("\n[TEST 2] Checking if tables exist...")
try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if 'users' in tables:
        print("✅ 'users' table EXISTS")
        columns = inspector.get_columns('users')
        print("   Columns:")
        for col in columns:
            print(f"   - {col['name']}: {col['type']}")
    else:
        print("❌ 'users' table NOT FOUND")
        print("   Creating tables now...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully")
except Exception as e:
    print(f"❌ Error checking tables: {str(e)}")
    sys.exit(1)

# ============================================
# TEST 3: Test Direct Database Insert
# ============================================
print("\n[TEST 3] Testing direct database insert...")
try:
    db = SessionLocal()
    
    # Create test user
    test_email = f"test_direct_{datetime.now().timestamp()}@example.com"
    from main import hash_password
    
    test_user = User(
        email=test_email,
        full_name="Test Direct User",
        password=hash_password("testpass123"),
        is_active=1,
        role="user"
    )
    
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    print(f"✅ Direct insert SUCCESSFUL")
    print(f"   User ID: {test_user.id}")
    print(f"   Email: {test_user.email}")
    
    # Verify it was saved
    saved_user = db.query(User).filter(User.email == test_email).first()
    if saved_user:
        print(f"✅ Verification: User found in database")
    else:
        print(f"❌ Verification FAILED: User not found after insert")
    
    # Clean up test user
    db.delete(test_user)
    db.commit()
    print("✅ Test user cleaned up")
    
    db.close()
except Exception as e:
    print(f"❌ Direct insert FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================
# TEST 4: Test Backend API
# ============================================
print("\n[TEST 4] Testing backend API...")
try:
    print("   Checking if FastAPI server is running on port 8000...")
    
    response = requests.get("http://localhost:8000/health", timeout=2)
    if response.status_code == 404:
        # health endpoint doesn't exist, try the root
        response = requests.get("http://localhost:8000/", timeout=2)
    
    print("✅ Backend API server is RUNNING")
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to backend server")
    print("   Make sure FastAPI is running:")
    print("   $ cd backend && python run_server.py")
    print("\n   You need the backend running for the next tests")
except Exception as e:
    print(f"⚠️  Unexpected error: {str(e)}")

# ============================================
# TEST 5: Test Registration Endpoint
# ============================================
print("\n[TEST 5] Testing registration endpoint...")
try:
    test_email = f"api_test_{datetime.now().timestamp()}@example.com"
    test_password = "testpass123"
    
    response = requests.post(
        "http://localhost:8000/api/register",
        json={"email": test_email, "password": test_password},
        timeout=5
    )
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code in [200, 201]:
        print("✅ Registration endpoint WORKING")
        
        # Verify in database
        db = SessionLocal()
        user = db.query(User).filter(User.email == test_email).first()
        if user:
            print(f"✅ User data FOUND in database")
            print(f"   ID: {user.id}, Email: {user.email}")
            
            # Clean up
            db.delete(user)
            db.commit()
        else:
            print(f"❌ User NOT found in database after registration")
        db.close()
    else:
        print(f"❌ Registration endpoint returned error: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to backend - START IT FIRST")
    print("   $ cd backend && python run_server.py")
except Exception as e:
    print(f"❌ API test failed: {str(e)}")
    import traceback
    traceback.print_exc()

# ============================================
# TEST 6: Count existing users
# ============================================
print("\n[TEST 6] Current database status...")
try:
    db = SessionLocal()
    user_count = db.query(User).count()
    print(f"✅ Total users in database: {user_count}")
    
    users = db.query(User).all()
    if users:
        print("   Existing users:")
        for user in users:
            print(f"   - {user.email} (ID: {user.id})")
    
    db.close()
except Exception as e:
    print(f"❌ Error counting users: {str(e)}")

# ============================================
# SUMMARY
# ============================================
print("\n" + "=" * 60)
print("📋 SUMMARY & NEXT STEPS")
print("=" * 60)

print("""
If all tests passed (✅):
  Your system is working correctly!
  
If TEST 1 failed (❌):
  ➜ PostgreSQL is not running
  ➜ Start PostgreSQL and check connection details in database.py
  
If TEST 4 failed (❌):
  ➜ FastAPI backend is not running
  ➜ Start it with: cd backend && python run_server.py
  
If TEST 5 failed (❌):
  ➜ The registration endpoint has an issue
  ➜ Check backend/main.py for errors
  ➜ Look at terminal output from FastAPI server
  
If data isn't storing even when tests pass:
  ➜ Check database.py credentials match your PostgreSQL setup
  ➜ Verify tables were created: loginDatabase database
  ➜ Check for any constraint violations

📞 QUICK DEBUG CHECKLIST:
  ☐ PostgreSQL is running (test with psql)
  ☐ Database 'loginDatabase' exists
  ☐ FastAPI server is running on port 8000
  ☐ No error messages in backend terminal
  ☐ Database credentials match in database.py
  ☐ Streamlit is connecting to correct API_BASE_URL
""")

print("=" * 60)
