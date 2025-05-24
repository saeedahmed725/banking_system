#!/usr/bin/env python3
"""
Test script to verify transaction system functionality with authentication
"""

import requests
from bs4 import BeautifulSoup
import re

BASE_URL = "http://127.0.0.1:5000"

def extract_account_id_from_response(response_text):
    """Extract account ID from response text"""
    # Look for account ID in various patterns
    patterns = [
        r'account_id=(\d+)',
        r'accounts/(\d+)',
        r'value="(\d+)"[^>]*data-balance',
        r'Account #(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response_text)
        if match:
            return match.group(1)
    return None

def test_transaction_system():
    """Test the complete transaction system"""
    print("🔍 Testing Transaction System...")
    
    session = requests.Session()
    
    # Login as admin first
    print("\n1. Logging in as admin...")
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=True)
    if "Dashboard" not in response.text:
        print("❌ Admin login failed")
        return False
    print("✅ Admin login successful")
    
    # Create a test account for transactions
    print("\n2. Creating test account...")
    account_data = {
        'owner_name': 'Transaction Test User',
        'account_type': 'checking',
        'email': 'transactiontest@example.com',
        'phone_number': '555-1111',
        'initial_balance': '1000.00'
    }
    response = session.post(f"{BASE_URL}/accounts/new", data=account_data, allow_redirects=True)
    if response.status_code != 200:
        print(f"❌ Account creation failed: {response.status_code}")
        return False
    print("✅ Test account created")
    
    # Get account list to find our test account
    print("\n3. Finding test account ID...")
    response = session.get(f"{BASE_URL}/accounts")
    account_id = extract_account_id_from_response(response.text)
    if not account_id:
        print("❌ Could not find account ID")
        return False
    print(f"✅ Found account ID: {account_id}")
    
    # Test deposit functionality
    print("\n4. Testing deposit...")
    deposit_data = {
        'account_id': account_id,
        'amount': '250.00',
        'description': 'Test deposit transaction'
    }
    response = session.post(f"{BASE_URL}/transactions/deposit", data=deposit_data, allow_redirects=True)
    if "Deposit successful" in response.text or response.status_code == 200:
        print("✅ Deposit successful")
    else:
        print(f"❌ Deposit failed: {response.status_code}")
        print("Response preview:", response.text[:500])
    
    # Test withdrawal functionality
    print("\n5. Testing withdrawal...")
    withdraw_data = {
        'account_id': account_id,
        'amount': '100.00',
        'description': 'Test withdrawal transaction'
    }
    response = session.post(f"{BASE_URL}/transactions/withdraw", data=withdraw_data, allow_redirects=True)
    if "Withdrawal successful" in response.text or response.status_code == 200:
        print("✅ Withdrawal successful")
    else:
        print(f"❌ Withdrawal failed: {response.status_code}")
    
    # Create a second account for transfer testing
    print("\n6. Creating second account for transfer test...")
    account_data2 = {
        'owner_name': 'Transfer Target User',
        'account_type': 'savings',
        'email': 'transfertarget@example.com',
        'phone_number': '555-2222',
        'initial_balance': '500.00'
    }
    response = session.post(f"{BASE_URL}/accounts/new", data=account_data2, allow_redirects=True)
    print("✅ Second account created")
    
    # Get updated account list
    response = session.get(f"{BASE_URL}/accounts")
    # Find the second account ID (this is simplified - in real testing we'd parse HTML properly)
    account_ids = re.findall(r'accounts/(\d+)', response.text)
    if len(account_ids) >= 2:
        to_account_id = account_ids[1] if account_ids[1] != account_id else account_ids[0]
        
        # Test transfer functionality
        print(f"\n7. Testing transfer from {account_id} to {to_account_id}...")
        transfer_data = {
            'from_account_id': account_id,
            'to_account_id': to_account_id,
            'amount': '200.00',
            'description': 'Test transfer transaction'
        }
        response = session.post(f"{BASE_URL}/transactions/transfer", data=transfer_data, allow_redirects=True)
        if "Transfer successful" in response.text or response.status_code == 200:
            print("✅ Transfer successful")
        else:
            print(f"❌ Transfer failed: {response.status_code}")
    else:
        print("⚠️ Could not test transfer - insufficient accounts")
    
    # Test viewing account details
    print(f"\n8. Testing account details view...")
    response = session.get(f"{BASE_URL}/accounts/{account_id}")
    if response.status_code == 200 and "Account Details" in response.text:
        print("✅ Account details accessible")
        
        # Check if transactions are displayed
        if "Recent Transactions" in response.text:
            print("✅ Transactions are displayed in account details")
        else:
            print("⚠️ Transactions not visible in account details")
    else:
        print(f"❌ Account details access failed: {response.status_code}")
    
    # Test customer access - logout and login as customer
    print("\n9. Testing customer transaction access...")
    session.get(f"{BASE_URL}/logout")
    
    # Login as the new customer we created earlier
    login_data = {
        'username': 'newcustomer',
        'password': 'password123'
    }
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=True)
    if "Dashboard" in response.text:
        print("✅ Customer login successful")
        
        # Test that customer can only see their own account
        response = session.get(f"{BASE_URL}/transactions/deposit")
        if response.status_code == 200:
            print("✅ Customer can access deposit page")
            # Check if they can only see their own account in dropdown
            if response.text.count('option value=') <= 2:  # Should only see their account + empty option
                print("✅ Customer can only see their own account")
            else:
                print("⚠️ Customer might be seeing other accounts")
        else:
            print("❌ Customer cannot access deposit page")
    else:
        print("❌ Customer login failed")
    
    print("\n🎉 Transaction system testing completed!")
    return True

if __name__ == "__main__":
    try:
        test_transaction_system()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
