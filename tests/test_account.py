import unittest
import os
import sys
import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from src.account import AccountManager
from test_config import DatabaseHelper, setup_test_database, cleanup_test_database


class TestAccountManager(unittest.TestCase):
    """Test cases for the Account Manager functionality"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create a test database and account manager
        self.test_db = setup_test_database()
        self.account_manager = AccountManager()
        self.account_manager.db = self.test_db  # Use test database
        
        # Sample account data for testing
        self.test_account_data = {
            'owner_name': 'Test User',
            'account_type': 'checking',
            'email': 'test@example.com',
            'phone_number': '555-1234',
            'initial_balance': 1000.0
        }
    
    def tearDown(self):
        """Clean up after each test"""
        # Clean up test data with proper balance handling
        try:
            accounts = self.account_manager.get_all_accounts()
            for account in accounts:
                # Set balance to zero for cleanup
                self.account_manager.update_balance(account['account_id'], 0.0)
                # Now delete the account
                self.account_manager.delete_account(account['account_id'])
        except Exception:
            pass  # Ignore cleanup errors
          # Clean up test database
        self.test_db.cleanup_test_db()
        cleanup_test_database()
    
    def test_create_account(self):
        """Test account creation functionality"""
        # Create a new account
        account = self.account_manager.create_account(**self.test_account_data)
        
        # Verify account was created
        self.assertIsNotNone(account)
        self.assertEqual(account['owner_name'], self.test_account_data['owner_name'])
        self.assertEqual(account['account_type'], self.test_account_data['account_type'])
        self.assertEqual(account['email'], self.test_account_data['email'])
        self.assertEqual(account['balance'], self.test_account_data['initial_balance'])
    
    def test_get_account(self):
        """Test retrieving account by ID"""
        # Create an account
        created_account = self.account_manager.create_account(**self.test_account_data)
        
        # Get the account by ID
        account = self.account_manager.get_account(created_account['account_id'])
        
        # Verify the account data
        self.assertIsNotNone(account)
        self.assertEqual(account['account_id'], created_account['account_id'])
    
    def test_get_account_by_number(self):
        """Test retrieving account by account number"""
        # Create an account
        created_account = self.account_manager.create_account(**self.test_account_data)
        
        # Get the account by number
        account = self.account_manager.get_account_by_number(created_account['account_number'])
        
        # Verify the account data
        self.assertIsNotNone(account)
        self.assertEqual(account['account_number'], created_account['account_number'])
    
    def test_update_account(self):
        """Test updating account details"""
        # Create an account
        account = self.account_manager.create_account(**self.test_account_data)
        
        # Update account details
        updated_data = {
            'owner_name': 'Updated User',
            'email': 'updated@example.com'
        }
        
        updated_account = self.account_manager.update_account(
            account['account_id'], 
            **updated_data
        )
        
        # Verify updates
        self.assertEqual(updated_account['owner_name'], updated_data['owner_name'])
        self.assertEqual(updated_account['email'], updated_data['email'])
          # Verify unchanged fields remain the same
        self.assertEqual(updated_account['account_type'], account['account_type'])
        self.assertEqual(updated_account['phone_number'], account['phone_number'])
    
    def test_delete_account(self):
        """Test deleting an account"""
        # Create an account
        account = self.account_manager.create_account(**self.test_account_data)
        
        # Get the account ID
        account_id = account['account_id']
        
        # Set balance to zero (business requirement for account deletion)
        self.account_manager.update_balance(account_id, 0.0)
        
        # Delete the account
        result = self.account_manager.delete_account(account_id)
        
        # Verify deletion
        self.assertTrue(result)
        
        # Verify account no longer exists
        deleted_account = self.account_manager.get_account(account_id)
        self.assertIsNone(deleted_account)
    
    def test_update_balance(self):
        """Test updating account balance"""
        # Create an account
        account = self.account_manager.create_account(**self.test_account_data)
        
        # Update balance
        new_balance = 1500.0
        updated_account = self.account_manager.update_balance(account['account_id'], new_balance)
        
        # Verify balance update
        self.assertEqual(updated_account['balance'], new_balance)


if __name__ == '__main__':
    unittest.main()