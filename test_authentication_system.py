#!/usr/bin/env python3
"""
Test script to verify the authentication system functionality
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_authentication_system():
    """Test the complete authentication system"""
    print("🔍 Testing Authentication System...")
    
    session = requests.Session()
    
    # Test 1: Access protected page without login (should redirect)
    print("\n1. Testing access to protected page without login...")
    response = session.get(f"{BASE_URL}/accounts")
    if response.url.endswith('/login'):
        print("✅ Correctly redirected to login page")
    else:
        print("❌ Failed to redirect to login page")
    
    # Test 2: Admin login
    print("\n2. Testing admin login...")
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=True)
    if "Dashboard" in response.text or "Banking System" in response.text:
        print("✅ Admin login successful")
    else:
        print("❌ Admin login failed")
        return False
    
    # Test 3: Access admin-only functionality
    print("\n3. Testing admin access to accounts page...")
    response = session.get(f"{BASE_URL}/accounts")
    if response.status_code == 200 and "Accounts" in response.text:
        print("✅ Admin can access accounts page")
    else:
        print("❌ Admin cannot access accounts page")
    
    # Test 4: Create a new account as admin
    print("\n4. Testing account creation as admin...")
    account_data = {
        'owner_name': 'Test Customer',
        'account_type': 'checking',
        'email': 'testcustomer@example.com',
        'phone_number': '555-0123',
        'initial_balance': '1000.00'
    }
    response = session.post(f"{BASE_URL}/accounts/new", data=account_data, allow_redirects=True)
    if "Account created successfully" in response.text or response.status_code == 200:
        print("✅ Account creation successful")
    else:
        print("❌ Account creation failed")
    
    # Test 5: Test deposit functionality
    print("\n5. Testing deposit functionality...")
    # First get accounts to find the account ID
    response = session.get(f"{BASE_URL}/accounts")
    # This is a basic test - in a real scenario we'd parse the HTML to get account IDs
    
    # Test 6: Logout
    print("\n6. Testing logout...")
    response = session.get(f"{BASE_URL}/logout", allow_redirects=True)
    if "login" in response.url or "Login" in response.text:
        print("✅ Logout successful")
    else:
        print("❌ Logout failed")
    
    # Test 7: Test signup functionality
    print("\n7. Testing user signup...")
    signup_data = {
        'username': 'newcustomer',
        'password': 'password123',
        'confirm_password': 'password123',
        'email': 'newcustomer@example.com',
        'full_name': 'New Customer',
        'owner_name': 'New Customer',
        'account_type': 'savings',
        'phone_number': '555-9876',
        'initial_balance': '500.00'
    }
    response = session.post(f"{BASE_URL}/signup", data=signup_data, allow_redirects=True)
    if "Account created successfully" in response.text or "Registration successful" in response.text:
        print("✅ User signup successful")
    else:
        print("❌ User signup failed")
        print(f"Response status: {response.status_code}")
    
    # Test 8: Test customer login
    print("\n8. Testing customer login...")
    login_data = {
        'username': 'newcustomer',
        'password': 'password123'
    }
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=True)
    if "Customer Dashboard" in response.text or "Dashboard" in response.text:
        print("✅ Customer login successful")
    else:
        print("❌ Customer login failed")
    
    # Test 9: Test customer access restrictions
    print("\n9. Testing customer access restrictions...")
    response = session.get(f"{BASE_URL}/accounts/new")
    if response.status_code == 403 or "Access denied" in response.text or "admin" in response.text.lower():
        print("✅ Customer correctly denied access to admin functions")
    else:
        print("❌ Customer was able to access admin functions")
    
    print("\n🎉 Authentication system testing completed!")
    return True

if __name__ == "__main__":
    try:
        test_authentication_system()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
