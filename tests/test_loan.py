import unittest
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.account import AccountManager
from src.transaction import TransactionManager
from src.loan import LoanManager


class TestLoanManager(unittest.TestCase):
    """Test cases for the Loan Manager functionality"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create managers
        self.account_manager = AccountManager()
        self.transaction_manager = TransactionManager()
        self.loan_manager = LoanManager()
        
        # Create test account
        self.account = self.account_manager.create_account(
            owner_name='Test User',
            account_type='checking',
            email='test@example.com',
            initial_balance=2000.0
        )
        
        # Sample loan data
        self.loan_data = {
            'account_id': self.account['account_id'],
            'loan_amount': 5000.0,
            'interest_rate': 5.5,
            'term_months': 12
        }
    
    def tearDown(self):
        """Clean up after each test"""
        # Delete all accounts created during tests (cascade deletes loans and transactions)
        accounts = self.account_manager.get_all_accounts()
        for account in accounts:
            self.account_manager.delete_account(account['account_id'])
    
    def test_apply_for_loan(self):
        """Test loan application functionality"""
        # Apply for a loan
        loan = self.loan_manager.apply_for_loan(**self.loan_data)
        
        # Verify loan was created
        self.assertIsNotNone(loan)
        self.assertEqual(loan['account_id'], self.loan_data['account_id'])
        self.assertEqual(loan['loan_amount'], self.loan_data['loan_amount'])
        self.assertEqual(loan['interest_rate'], self.loan_data['interest_rate'])
        self.assertEqual(loan['term_months'], self.loan_data['term_months'])
        self.assertEqual(loan['status'], 'pending')
        self.assertEqual(loan['remaining_amount'], self.loan_data['loan_amount'])
    
    def test_approve_loan(self):
        """Test loan approval process"""
        # Apply for a loan
        loan = self.loan_manager.apply_for_loan(**self.loan_data)
        
        # Approve the loan
        approved_loan = self.loan_manager.approve_loan(loan['loan_id'])
        
        # Verify loan was approved
        self.assertEqual(approved_loan['status'], 'active')
        self.assertIsNotNone(approved_loan['start_date'])
        self.assertIsNotNone(approved_loan['end_date'])
        
        # Verify funds were disbursed to the account
        updated_account = self.account_manager.get_account(self.account['account_id'])
        self.assertEqual(
            updated_account['balance'], 
            self.account['balance'] + self.loan_data['loan_amount']
        )
        
        # Verify transaction was created
        transactions = self.transaction_manager.get_account_transactions(self.account['account_id'])
        self.assertTrue(any(
            t['transaction_type'] == 'deposit' and 
            t['amount'] == self.loan_data['loan_amount'] and
            'Loan disbursement' in t['description']
            for t in transactions
        ))
    
    def test_reject_loan(self):
        """Test loan rejection process"""
        # Apply for a loan
        loan = self.loan_manager.apply_for_loan(**self.loan_data)
        
        # Reject the loan
        rejected_loan = self.loan_manager.reject_loan(loan['loan_id'])
        
        # Verify loan was rejected
        self.assertEqual(rejected_loan['status'], 'rejected')
        
        # Verify account balance was not changed
        updated_account = self.account_manager.get_account(self.account['account_id'])
        self.assertEqual(updated_account['balance'], self.account['balance'])
    
    def test_make_payment(self):
        """Test loan payment process"""
        # Apply for and approve a loan
        loan = self.loan_manager.apply_for_loan(**self.loan_data)
        approved_loan = self.loan_manager.approve_loan(loan['loan_id'])
        
        # Make a payment
        payment_amount = 500.0
        payment_result = self.loan_manager.make_payment(approved_loan['loan_id'], payment_amount)
        
        # Verify payment was applied to loan
        self.assertEqual(
            payment_result['remaining_amount'], 
            approved_loan['remaining_amount'] - payment_amount
        )
        
        # Verify transaction was created
        transactions = self.transaction_manager.get_account_transactions(self.account['account_id'])
        self.assertTrue(any(
            t['transaction_type'] == 'withdrawal' and 
            t['amount'] == payment_amount and
            'Loan payment' in t['description']
            for t in transactions
        ))
        
        # Verify account balance was updated
        updated_account = self.account_manager.get_account(self.account['account_id'])
        expected_balance = (self.account['balance'] + 
                            self.loan_data['loan_amount'] - 
                            payment_amount)
        self.assertEqual(updated_account['balance'], expected_balance)
    
    def test_payment_fully_pays_loan(self):
        """Test making a payment that fully pays off a loan"""
        # Apply for and approve a smaller loan
        small_loan_data = self.loan_data.copy()
        small_loan_data['loan_amount'] = 1000.0
        
        loan = self.loan_manager.apply_for_loan(**small_loan_data)
        approved_loan = self.loan_manager.approve_loan(loan['loan_id'])
        
        # Make a payment that fully pays off the loan
        payment_result = self.loan_manager.make_payment(approved_loan['loan_id'], 1000.0)
        
        # Verify loan is marked as paid
        self.assertEqual(payment_result['status'], 'paid')
        self.assertEqual(payment_result['remaining_amount'], 0)
    
    def test_calculate_monthly_payment(self):
        """Test loan payment calculation"""
        # Test cases
        test_cases = [
            # (loan_amount, interest_rate, term_months, expected_payment)
            (10000, 5, 12, 856.07),  # 5% annual interest, 1 year
            (10000, 0, 12, 833.33),  # 0% interest (edge case)
            (50000, 3.5, 60, 911.39)  # 3.5% annual interest, 5 years
        ]
        
        for loan_amount, interest_rate, term_months, expected_payment in test_cases:
            payment = self.loan_manager.calculate_monthly_payment(
                loan_amount, interest_rate, term_months
            )
            # Using assertAlmostEqual with a small delta to account for rounding differences
            self.assertAlmostEqual(payment, expected_payment, delta=0.1)


if __name__ == '__main__':
    unittest.main()