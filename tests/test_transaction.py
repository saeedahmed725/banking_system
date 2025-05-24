import unittest
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from src.account import AccountManager
from src.transaction import TransactionManager
from test_config import DatabaseHelper, setup_test_database, cleanup_test_database


class TestTransactionManager(unittest.TestCase):
    """Test cases for the Transaction Manager functionality"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create test database
        self.test_db = setup_test_database()
          # Create account and transaction managers with test database
        self.account_manager = AccountManager(self.test_db)
        
        self.transaction_manager = TransactionManager(self.test_db)
        
        # Create test accounts
        self.account1 = self.account_manager.create_account(
            owner_name='Test User 1',
            account_type='checking',
            email='test1@example.com',
            initial_balance=1000.0
        )
        
        self.account2 = self.account_manager.create_account(
            owner_name='Test User 2',
            account_type='savings',
            email='test2@example.com',
            initial_balance=500.0        )
    
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
    
    def test_deposit(self):
        """Test deposit functionality"""
        # Deposit amount
        amount = 500.0
        description = "Test deposit"
        
        # Perform deposit
        transaction = self.transaction_manager.deposit(
            self.account1['account_id'],
            amount,
            description
        )
        
        # Verify transaction was created
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction['transaction_type'], 'deposit')
        self.assertEqual(transaction['amount'], amount)
        self.assertEqual(transaction['description'], description)
        
        # Verify account balance was updated
        updated_account = self.account_manager.get_account(self.account1['account_id'])
        self.assertEqual(updated_account['balance'], self.account1['balance'] + amount)
    
    def test_withdraw(self):
        """Test withdrawal functionality"""
        # Withdrawal amount
        amount = 300.0
        description = "Test withdrawal"
        
        # Perform withdrawal
        transaction = self.transaction_manager.withdraw(
            self.account1['account_id'],
            amount,
            description
        )
        
        # Verify transaction was created
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction['transaction_type'], 'withdrawal')
        self.assertEqual(transaction['amount'], amount)
        self.assertEqual(transaction['description'], description)
        
        # Verify account balance was updated
        updated_account = self.account_manager.get_account(self.account1['account_id'])
        self.assertEqual(updated_account['balance'], self.account1['balance'] - amount)
    
    def test_withdraw_insufficient_funds(self):
        """Test withdrawal with insufficient funds"""
        # Withdrawal amount larger than balance
        amount = self.account1['balance'] + 100.0
        
        # Attempt withdrawal should raise an error
        with self.assertRaises(ValueError):
            self.transaction_manager.withdraw(
                self.account1['account_id'],
                amount,
                "Test insufficient funds"
            )
        
        # Verify account balance remains unchanged
        updated_account = self.account_manager.get_account(self.account1['account_id'])
        self.assertEqual(updated_account['balance'], self.account1['balance'])
    
    def test_transfer(self):
        """Test transfer between accounts"""
        # Transfer amount
        amount = 200.0
        description = "Test transfer"
        
        # Perform transfer
        transfer = self.transaction_manager.transfer(
            self.account1['account_id'],
            self.account2['account_id'],
            amount,
            description
        )
        
        # Verify transfer details
        self.assertEqual(transfer['from_account'], self.account1['account_id'])
        self.assertEqual(transfer['to_account'], self.account2['account_id'])
        self.assertEqual(transfer['amount'], amount)
        
        # Verify account balances were updated
        updated_account1 = self.account_manager.get_account(self.account1['account_id'])
        updated_account2 = self.account_manager.get_account(self.account2['account_id'])
        
        self.assertEqual(updated_account1['balance'], self.account1['balance'] - amount)
        self.assertEqual(updated_account2['balance'], self.account2['balance'] + amount)
    
    def test_get_account_transactions(self):
        """Test retrieving all transactions for an account"""
        # Create multiple transactions
        self.transaction_manager.deposit(self.account1['account_id'], 100.0, "Deposit 1")
        self.transaction_manager.deposit(self.account1['account_id'], 200.0, "Deposit 2")
        self.transaction_manager.withdraw(self.account1['account_id'], 50.0, "Withdrawal 1")
        
        # Get all transactions for the account
        transactions = self.transaction_manager.get_account_transactions(self.account1['account_id'])
        
        # Verify the number of transactions
        self.assertEqual(len(transactions), 3)
        
        # Check transaction types
        transaction_types = [t['transaction_type'] for t in transactions]
        self.assertEqual(transaction_types.count('deposit'), 2)
        self.assertEqual(transaction_types.count('withdrawal'), 1)


if __name__ == '__main__':
    unittest.main()