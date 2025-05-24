from src.database import Database
from src.account import AccountManager
from src.transaction import TransactionManager


class LoanManager:
    """Handle operations related to loans"""
    
    def __init__(self, db=None):
        """Initialize with a database connection"""
        self.db = db if db else Database()
    
    def apply_for_loan(self, account_id, loan_amount, interest_rate, term_months):
        """Apply for a new loan"""
        # Validate loan parameters
        if loan_amount <= 0:
            raise ValueError("Loan amount must be positive")
        
        if interest_rate < 0 or interest_rate > 100:
            raise ValueError("Interest rate must be between 0 and 100")
        
        if term_months <= 0:
            raise ValueError("Loan term must be positive")
        
        # Check if account exists
        account_manager = AccountManager(self.db)
        account = account_manager.get_account(account_id)
        
        if not account:
            raise ValueError(f"Account with ID {account_id} not found")
        
        # Create new loan application
        query = """
            INSERT INTO loans (
                account_id, loan_amount, interest_rate, term_months,
                remaining_amount, status, application_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            account_id, loan_amount, interest_rate, term_months,
            loan_amount, 'pending', self.db.get_current_timestamp()
        )
        
        loan_id = self.db.execute_query(query, params)
        
        # Return the newly created loan
        return self.get_loan(loan_id)
    
    def get_loan(self, loan_id):
        """Get loan by ID"""
        query = "SELECT * FROM loans WHERE loan_id = ?"
        loan = self.db.execute_query(query, (loan_id,), 'one')
        
        if loan:
            return dict(loan)
        return None
    
    def get_account_loans(self, account_id):
        """Get all loans for a specific account"""
        query = "SELECT * FROM loans WHERE account_id = ? ORDER BY application_date DESC"
        loans = self.db.execute_query(query, (account_id,), 'all')
        
        return [dict(loan) for loan in loans] if loans else []
    
    def get_all_loans(self, status=None):
        """Get all loans in the system, optionally filtered by status"""
        if status:
            query = "SELECT * FROM loans WHERE status = ? ORDER BY application_date DESC"
            loans = self.db.execute_query(query, (status,), 'all')
        else:
            query = "SELECT * FROM loans ORDER BY application_date DESC"
            loans = self.db.execute_query(query, fetch_mode='all')
        
        return [dict(loan) for loan in loans] if loans else []
    
    def update_loan_status(self, loan_id, new_status):
        """Update the status of a loan"""
        valid_statuses = ['pending', 'approved', 'active', 'rejected', 'paid', 'defaulted']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid loan status. Must be one of: {', '.join(valid_statuses)}")
        
        # Get current loan info
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan with ID {loan_id} not found")
        
        # Update status
        query = "UPDATE loans SET status = ? WHERE loan_id = ?"
        self.db.execute_query(query, (new_status, loan_id))
        
        # Return the updated loan
        return self.get_loan(loan_id)
    
    def approve_loan(self, loan_id):
        """Approve a loan application and disburse funds"""
        # Get loan info
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan with ID {loan_id} not found")
        
        # Check if loan is in pending state
        if loan['status'] != 'pending':
            raise ValueError(f"Cannot approve loan that is not in pending state. Current status: {loan['status']}")
        
        # Get account info
        account_manager = AccountManager(self.db)
        account = account_manager.get_account(loan['account_id'])
        
        if not account:
            raise ValueError(f"Account with ID {loan['account_id']} not found")
          # Update loan status and dates
        current_time = self.db.get_current_timestamp()
        
        # Calculate end date based on term_months using proper date arithmetic
        # Adding months properly using datetime calculations
        year_increase = (current_time.month + loan['term_months'] - 1) // 12
        new_month = (current_time.month + loan['term_months'] - 1) % 12 + 1  # 1-based month
        end_date = current_time.replace(year=current_time.year + year_increase, month=new_month)
        
        query = """
            UPDATE loans 
            SET status = 'active', start_date = ?, end_date = ?
            WHERE loan_id = ?
        """
        self.db.execute_query(query, (current_time, end_date, loan_id))
        
        # Disburse loan amount to account
        transaction_manager = TransactionManager(self.db)
          # Record loan disbursement transaction
        transaction = transaction_manager.record_transaction(
            account_id=loan['account_id'],
            transaction_type='deposit',
            amount=loan['loan_amount'],
            description=f"Loan disbursement for loan #{loan_id}"
        )
        
        # Update account balance
        new_balance = account['balance'] + loan['loan_amount']
        account_manager.update_balance(loan['account_id'], new_balance)
          # Return updated loan
        updated_loan = self.get_loan(loan_id)
        
        return updated_loan
    
    def reject_loan(self, loan_id):
        """Reject a loan application"""
        # Get loan info
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan with ID {loan_id} not found")
        
        # Check if loan is in pending state
        if loan['status'] != 'pending':
            raise ValueError(f"Cannot reject loan that is not in pending state. Current status: {loan['status']}")
        
        # Update loan status
        return self.update_loan_status(loan_id, 'rejected')
    
    def make_payment(self, loan_id, payment_amount):
        """Make a payment toward a loan"""
        # Get loan info
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan with ID {loan_id} not found")
        
        # Check if loan is active
        if loan['status'] != 'active':
            raise ValueError(f"Cannot make payment on a loan that is not active. Current status: {loan['status']}")
        
        # Validate payment amount
        if payment_amount <= 0:
            raise ValueError("Payment amount must be positive")
        
        if payment_amount > loan['remaining_amount']:
            raise ValueError(f"Payment amount (${payment_amount}) exceeds remaining loan balance (${loan['remaining_amount']})")
        
        # Get account info
        account_manager = AccountManager(self.db)
        account = account_manager.get_account(loan['account_id'])
        
        if not account:
            raise ValueError(f"Account with ID {loan['account_id']} not found")
        
        # Check if account has sufficient funds
        if payment_amount > account['balance']:
            raise ValueError("Insufficient funds in account for loan payment")
        
        # Withdraw from account
        transaction_manager = TransactionManager(self.db)        # Record loan payment transaction
        transaction = transaction_manager.record_transaction(
            account_id=loan['account_id'],
            transaction_type='withdrawal',
            amount=payment_amount,
            description=f"Loan payment for loan #{loan_id}"
        )
        
        # Update account balance
        new_balance = account['balance'] - payment_amount
        account_manager.update_balance(loan['account_id'], new_balance)
        
        # Update loan remaining amount
        new_remaining = loan['remaining_amount'] - payment_amount
        current_time = self.db.get_current_timestamp()
        
        if new_remaining <= 0:
            # Loan is paid off
            query = """
                UPDATE loans 
                SET remaining_amount = 0, status = 'paid', last_payment_date = ?
                WHERE loan_id = ?
            """
            self.db.execute_query(query, (current_time, loan_id))
        else:
            # Loan still has remaining balance
            query = """
                UPDATE loans 
                SET remaining_amount = ?, last_payment_date = ?
                WHERE loan_id = ?
            """
            self.db.execute_query(query, (new_remaining, current_time, loan_id))
          # Return updated loan
        updated_loan = self.get_loan(loan_id)
        
        return updated_loan
    
    def calculate_monthly_payment(self, loan_amount, interest_rate, term_months):
        """Calculate the monthly payment for a loan"""
        # Convert annual interest rate to monthly
        monthly_rate = interest_rate / 100 / 12
        
        if monthly_rate == 0:
            # Handle 0% interest case
            return loan_amount / term_months
        
        # Standard loan formula: PMT = P * (r * (1+r)^n) / ((1+r)^n - 1)
        numerator = monthly_rate * ((1 + monthly_rate) ** term_months)
        denominator = ((1 + monthly_rate) ** term_months) - 1
        
        return loan_amount * (numerator / denominator)
    
    def get_loan_summary(self, loan_id):
        """Get a summary of a loan including payment schedule"""
        # Get loan info
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan with ID {loan_id} not found")
        
        # Get account info
        account_manager = AccountManager(self.db)
        account = account_manager.get_account(loan['account_id'])
        
        # Calculate payment info
        monthly_payment = self.calculate_monthly_payment(
            loan['loan_amount'], loan['interest_rate'], loan['term_months']
        )
        
        total_payments = monthly_payment * loan['term_months']
        total_interest = total_payments - loan['loan_amount']
        
        # Get payment transactions
        transaction_manager = TransactionManager(self.db)
        payments = transaction_manager.search_transactions(
            account_id=loan['account_id'],
            transaction_type='loan_payment',
            description_contains=f"loan #{loan_id}"
        )
        
        # Build payment schedule
        payment_schedule = []
        remaining = loan['loan_amount']
        
        for month in range(1, loan['term_months'] + 1):
            # Calculate interest for this month
            interest_payment = remaining * (loan['interest_rate'] / 100 / 12)
            principal_payment = monthly_payment - interest_payment
            
            # Handle final payment rounding issues
            if month == loan['term_months']:
                principal_payment = remaining
                payment_amount = principal_payment + interest_payment
            else:
                payment_amount = monthly_payment
                remaining -= principal_payment
            
            payment_schedule.append({
                'month': month,
                'payment_amount': payment_amount,
                'principal_payment': principal_payment,
                'interest_payment': interest_payment,
                'remaining_balance': max(0, remaining)
            })
        
        return {
            'loan': loan,
            'account': account,
            'monthly_payment': monthly_payment,
            'total_payments': total_payments,
            'total_interest': total_interest,
            'payments_made': payments,
            'payment_schedule': payment_schedule
        }