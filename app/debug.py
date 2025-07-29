"""
debug_auth_imports.py - Debug auth.py import issues step by step
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_individual_imports():
    """Test each import in auth.py individually"""
    print("🔍 Testing Individual Imports from auth.py...")
    
    try:
        print("1. Testing datetime imports...")
        from datetime import datetime, timedelta, timezone
        print("   ✅ datetime imports OK")
    except Exception as e:
        print(f"   ❌ datetime import failed: {e}")
        return False
    
    try:
        print("2. Testing typing imports...")
        from typing import Optional
        print("   ✅ typing imports OK")
    except Exception as e:
        print(f"   ❌ typing import failed: {e}")
        return False
    
    try:
        print("3. Testing FastAPI imports...")
        from fastapi import Depends, HTTPException, status
        from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
        print("   ✅ FastAPI imports OK")
    except Exception as e:
        print(f"   ❌ FastAPI import failed: {e}")
        return False
    
    try:
        print("4. Testing jose imports...")
        from jose import jwt, JWTError
        print("   ✅ jose imports OK")
    except Exception as e:
        print(f"   ❌ jose import failed: {e}")
        print("   💡 Try: pip install python-jose[cryptography]")
        return False
    
    try:
        print("5. Testing passlib imports...")
        from passlib.context import CryptContext
        print("   ✅ passlib imports OK")
    except Exception as e:
        print(f"   ❌ passlib import failed: {e}")
        print("   💡 Try: pip install passlib[bcrypt]")
        return False
    
    try:
        print("6. Testing pydantic imports...")
        from pydantic import BaseModel
        print("   ✅ pydantic imports OK")
    except Exception as e:
        print(f"   ❌ pydantic import failed: {e}")
        return False
    
    try:
        print("7. Testing sqlalchemy imports...")
        from sqlalchemy.orm import Session
        print("   ✅ sqlalchemy imports OK")
    except Exception as e:
        print(f"   ❌ sqlalchemy import failed: {e}")
        return False
    
    return True

def test_app_imports():
    """Test importing from your app modules"""
    print("\n🔍 Testing App Module Imports...")
    
    try:
        print("1. Testing config import...")
        from app.config import get_settings
        settings = get_settings()
        print("   ✅ config import OK")
        
        # Check critical settings
        if not settings.JWT_SECRET_KEY:
            print("   ⚠️  JWT_SECRET_KEY not set!")
        
    except Exception as e:
        print(f"   ❌ config import failed: {e}")
        return False
    
    try:
        print("2. Testing database import...")
        from app.database import get_db
        print("   ✅ database import OK")
    except Exception as e:
        print(f"   ❌ database import failed: {e}")
        return False
    
    try:
        print("3. Testing models import...")
        from app.models import User
        print("   ✅ models import OK")
    except Exception as e:
        print(f"   ❌ models import failed: {e}")
        return False
    
    return True

def test_auth_module():
    """Test importing the entire auth module"""
    print("\n🔍 Testing Complete Auth Module...")
    
    try:
        print("Importing auth.py...")
        import app.auth
        print("✅ auth.py imports successfully")
        
        # Test specific functions
        print("Testing auth functions...")
        
        # Test password hashing
        hashed = app.auth.get_password_hash("test123")
        print("✅ Password hashing works")
        
        # Test password verification
        is_valid = app.auth.verify_password("test123", hashed)
        print(f"✅ Password verification works: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"❌ auth.py import failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def test_main_with_auth():
    """Test importing main.py with auth imports"""
    print("\n🔍 Testing main.py with auth imports...")
    
    try:
        print("Importing main.py...")
        from app.main import app
        print("✅ main.py imports successfully with auth")
        
        # Check if auth endpoints are registered
        auth_routes = [route for route in app.routes if hasattr(route, 'path') and '/auth/' in route.path]
        print(f"✅ Found {len(auth_routes)} auth routes")
        
        return True
        
    except Exception as e:
        print(f"❌ main.py import failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all import tests"""
    print("🐛 Debugging Auth Import Issues")
    print("=" * 50)
    
    # Test individual imports
    if not test_individual_imports():
        print("\n❌ Basic imports failed - install missing packages")
        return
    
    # Test app imports
    if not test_app_imports():
        print("\n❌ App module imports failed - check your modules")
        return
    
    # Test auth module
    if not test_auth_module():
        print("\n❌ Auth module failed - check auth.py for syntax errors")
        return
    
    # Test main with auth
    if not test_main_with_auth():
        print("\n❌ Main with auth failed - check main.py imports")
        return
    
    print("\n" + "=" * 50)
    print("🎉 All imports work correctly!")
    print("The issue might be elsewhere. Try starting the server:")
    print("   python -m app.main")

if __name__ == "__main__":
    main()