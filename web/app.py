from flask import Flask, render_template, request, redirect, url_for, flash, session
import sys
import os
from pathlib import Path
from datetime import datetime
from functools import wraps

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.account import AccountManager
from src.transaction import TransactionManager
from src.loan import LoanManager
from src.bug_tracker import BugTracker
from src.user_manager import UserManager

app = Flask(__name__)
app.secret_key = 'banking_system_secret_key'  # Used for flash messages and sessions

# Helper function for date formatting
def format_date(date_obj, format_str='%b %d, %Y'):
    if date_obj is None:
        return 'N/A'
    
    if isinstance(date_obj, str):
        try:
            dt = datetime.strptime(date_obj, '%Y-%m-%d %H:%M:%S.%f')
            return dt.strftime(format_str)
        except:
            return date_obj
    else:
        return date_obj.strftime(format_str)

# Initialize managers
account_manager = AccountManager()
transaction_manager = TransactionManager()
loan_manager = LoanManager()
bug_tracker = BugTracker()
user_manager = UserManager()


# Authentication decorators
def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        user = user_manager.get_user_by_id(session['user_id'])
        if not user or user['user_type'] != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def customer_access_check(account_id):
    """Check if customer can access specific account"""
    if 'user_id' not in session:
        return False
    
    user = user_manager.get_user_by_id(session['user_id'])
    if not user:
        return False
    
    # Admin can access everything
    if user['user_type'] == 'admin':
        return True
    
    # Customer can only access their own account
    return user['account_id'] == account_id


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = user_manager.authenticate_user(username, password)
        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        phone_number = request.form.get('phone_number')
        account_type = request.form.get('account_type')
        
        # Validate password confirmation
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('signup.html')
        
        try:
            # Check if username or email already exists
            if user_manager.get_user_by_username(username):
                flash('Username already exists.', 'danger')
                return render_template('signup.html')
            
            if user_manager.get_user_by_email(email):
                flash('Email already registered.', 'danger')
                return render_template('signup.html')
            
            # Create bank account first
            account = account_manager.create_account(
                owner_name=full_name,
                account_type=account_type,
                email=email,
                phone_number=phone_number,
                initial_balance=0.0
            )
            
            # Create user account and link to bank account
            user = user_manager.create_user(
                username=username,
                password=password,
                email=email,
                full_name=full_name,
                user_type='customer',
                account_id=account['account_id']
            )
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'danger')
    
    return render_template('signup.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard - redirects to appropriate view based on user type"""
    user = user_manager.get_user_by_id(session['user_id'])
    
    if user['user_type'] == 'admin':
        return redirect(url_for('index'))  # Admin sees full dashboard
    else:
        return redirect(url_for('customer_dashboard'))  # Customer sees limited view


@app.route('/customer-dashboard')
@login_required
def customer_dashboard():
    """Customer dashboard - limited view for regular users"""
    user = user_manager.get_user_by_id(session['user_id'])
    
    if user['user_type'] == 'admin':
        return redirect(url_for('index'))
    
    if not user['account_id']:
        flash('No bank account linked to your profile.', 'warning')
        return render_template('customer_dashboard.html', account=None, user=user)
    
    # Get customer's account details
    account = account_manager.get_account(user['account_id'])
    recent_transactions = transaction_manager.get_account_transactions(user['account_id'], limit=5)
    account_loans = loan_manager.get_account_loans(user['account_id'])
    
    # Format dates
    if account:
        account['created_at'] = format_date(account['created_at'])
    
    for transaction in recent_transactions:
        transaction['transaction_date'] = format_date(transaction['transaction_date'])
    
    return render_template('customer_dashboard.html', 
                          account=account, 
                          recent_transactions=recent_transactions,
                          loans=account_loans,
                          user=user)


@app.route('/')
@login_required
def index():
    """Home page route with dashboard statistics - Admin only"""
    user = user_manager.get_user_by_id(session['user_id'])
    
    # Redirect customers to their dashboard
    if user['user_type'] != 'admin':
        return redirect(url_for('customer_dashboard'))
    
    # Get total accounts
    all_accounts = account_manager.get_all_accounts()
    total_accounts = len(all_accounts)
    
    # Get transaction count (this is an approximation since we don't have a direct count method)
    # In a real app, you'd have a more efficient way to get this count
    total_transactions = 0
    for account in all_accounts:
        transactions = transaction_manager.get_account_transactions(account['account_id'], limit=1000)
        total_transactions += len(transactions)
    
    # Get active loans
    all_loans = loan_manager.get_all_loans()
    active_loans = len([loan for loan in all_loans if loan['status'] == 'active'])
    
    # Get open bugs
    all_bugs = bug_tracker.get_all_bugs()
    open_bugs = len([bug for bug in all_bugs if bug['status'] == 'open'])
    
    return render_template('index.html', 
                          total_accounts=total_accounts,
                          total_transactions=total_transactions,
                          active_loans=active_loans,
                          open_bugs=open_bugs)


@app.route('/accounts')
@admin_required
def accounts():
    """List all accounts - Admin only"""
    all_accounts = account_manager.get_all_accounts()
    
    # Format dates and account types for display
    for account in all_accounts:
        account['created_at'] = format_date(account['created_at'])
    
    return render_template('accounts.html', accounts=all_accounts)


@app.route('/accounts/new', methods=['GET', 'POST'])
@admin_required
def new_account():
    """Create a new account - Admin only"""
    if request.method == 'POST':
        # Get form data
        owner_name = request.form.get('owner_name')
        account_type = request.form.get('account_type')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        initial_balance = float(request.form.get('initial_balance', 0))
        
        try:
            # Create the account
            account = account_manager.create_account(
                owner_name=owner_name,
                account_type=account_type,
                email=email,
                phone_number=phone_number,
                initial_balance=initial_balance
            )
            
            flash(f'Account created successfully with number: {account["account_number"]}', 'success')
            return redirect(url_for('accounts'))
        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'danger')
    
    return render_template('new_account.html')


@app.route('/accounts/<int:account_id>')
@login_required
def view_account(account_id):
    """View account details"""
    # Check access permissions
    if not customer_access_check(account_id):
        flash('Access denied. You can only view your own account.', 'danger')
        return redirect(url_for('dashboard'))
    
    account = account_manager.get_account(account_id)
    if not account:
        flash('Account not found', 'danger')
        return redirect(url_for('accounts') if session.get('user_type') == 'admin' else url_for('customer_dashboard'))
    
    # Get transactions for this account
    transactions = transaction_manager.get_account_transactions(account_id)
    
    # Get loans for this account
    loans = loan_manager.get_account_loans(account_id)    # Format dates for display
    account['created_at'] = format_date(account['created_at'])
    account['updated_at'] = format_date(account['updated_at'])
    
    # Format transaction dates
    for transaction in transactions:
        transaction['transaction_date'] = format_date(transaction['transaction_date'])
    
    # Format loan dates
    for loan in loans:
        for date_field in ['application_date', 'start_date', 'end_date', 'last_payment_date']:
            if date_field in loan and loan[date_field]:
                loan[date_field] = format_date(loan[date_field])
      # Get current user for role-based UI controls
    user = user_manager.get_user_by_id(session['user_id'])
    
    return render_template(
        'account_details.html', 
        account=account, 
        transactions=transactions,
        loans=loans,
        user=user
    )


@app.route('/accounts/<int:account_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_account(account_id):
    """Edit account details - Admin only"""
    account = account_manager.get_account(account_id)
    if not account:
        flash('Account not found', 'danger')
        return redirect(url_for('accounts'))
    
    if request.method == 'POST':
        # Get form data
        owner_name = request.form.get('owner_name')
        account_type = request.form.get('account_type')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        
        try:
            # Update the account
            account = account_manager.update_account(
                account_id,
                owner_name=owner_name,
                account_type=account_type,
                email=email,
                phone_number=phone_number
            )
            
            flash('Account updated successfully', 'success')
            return redirect(url_for('view_account', account_id=account_id))
        except Exception as e:
            flash(f'Error updating account: {str(e)}', 'danger')
    
    return render_template('edit_account.html', account=account)


@app.route('/accounts/<int:account_id>/delete', methods=['POST'])
@admin_required
def delete_account(account_id):
    """Delete an account - Admin only"""
    try:
        result = account_manager.delete_account(account_id)
        if result:
            flash('Account deleted successfully', 'success')
        else:
            flash('Failed to delete account', 'danger')
    except Exception as e:
        flash(f'Error deleting account: {str(e)}', 'danger')
    
    return redirect(url_for('accounts'))


@app.route('/transactions/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    """Deposit money into an account"""
    user = user_manager.get_user_by_id(session['user_id'])
    
    if request.method == 'POST':
        account_id = int(request.form.get('account_id'))
        
        # Check access permissions
        if not customer_access_check(account_id):
            flash('Access denied. You can only deposit to your own account.', 'danger')
            return redirect(url_for('dashboard'))
        
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        
        try:
            transaction_manager.deposit(account_id, amount, description)
            flash('Deposit successful', 'success')
            return redirect(url_for('view_account', account_id=account_id))
        except Exception as e:
            flash(f'Error making deposit: {str(e)}', 'danger')
      # Get accounts for dropdown - admin sees all, customer sees only their own
    if user['user_type'] == 'admin':
        all_accounts = account_manager.get_all_accounts()
    else:
        if user['account_id']:
            account = account_manager.get_account(user['account_id'])
            all_accounts = [account] if account else []
        else:
            all_accounts = []
    
    return render_template('deposit.html', accounts=all_accounts)


@app.route('/transactions/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    """Withdraw money from an account"""
    user = user_manager.get_user_by_id(session['user_id'])
    
    if request.method == 'POST':
        account_id = int(request.form.get('account_id'))
        
        # Check access permissions
        if not customer_access_check(account_id):
            flash('Access denied. You can only withdraw from your own account.', 'danger')
            return redirect(url_for('dashboard'))
        
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        
        try:
            transaction_manager.withdraw(account_id, amount, description)
            flash('Withdrawal successful', 'success')
            return redirect(url_for('view_account', account_id=account_id))
        except Exception as e:
            flash(f'Error making withdrawal: {str(e)}', 'danger')
    
    # Get accounts for dropdown - admin sees all, customer sees only their own
    if user['user_type'] == 'admin':
        all_accounts = account_manager.get_all_accounts()
    else:
        if user['account_id']:
            account = account_manager.get_account(user['account_id'])
            all_accounts = [account] if account else []
        else:
            all_accounts = []
    
    return render_template('withdraw.html', accounts=all_accounts)


@app.route('/transactions/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    """Transfer money between accounts"""
    user = user_manager.get_user_by_id(session['user_id'])
    
    if request.method == 'POST':
        from_account_id = int(request.form.get('from_account_id'))
        to_account_id = int(request.form.get('to_account_id'))
        
        # Check access permissions for source account
        if not customer_access_check(from_account_id):
            flash('Access denied. You can only transfer from your own account.', 'danger')
            return redirect(url_for('dashboard'))
        
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        
        try:
            transaction_manager.transfer(from_account_id, to_account_id, amount, description)
            flash('Transfer successful', 'success')
            return redirect(url_for('view_account', account_id=from_account_id))
        except Exception as e:
            flash(f'Error making transfer: {str(e)}', 'danger')
    
    # Get accounts for dropdowns - admin sees all, customer sees only their own for source
    if user['user_type'] == 'admin':
        all_accounts = account_manager.get_all_accounts()
    else:
        if user['account_id']:
            account = account_manager.get_account(user['account_id'])
            all_accounts = [account] if account else []
        else:
            all_accounts = []
    
    # For destination, everyone can see all accounts (you can transfer to anyone)
    all_destination_accounts = account_manager.get_all_accounts()
    
    return render_template('transfer.html', accounts=all_accounts, destination_accounts=all_destination_accounts)


@app.route('/loans')
@login_required
def loans():
    """List loans - admin sees all, customers see only their own"""
    user = user_manager.get_user_by_id(session['user_id'])
    
    if user['user_type'] == 'admin':
        # Admin sees all loans
        all_accounts = account_manager.get_all_accounts()
        account_loans = []
        
        for account in all_accounts:
            loans = loan_manager.get_account_loans(account['account_id'])
            for loan in loans:
                loan_data = dict(loan)
                loan_data['account_number'] = account['account_number']
                loan_data['owner_name'] = account['owner_name']
                
                # Format loan dates
                for date_field in ['application_date', 'start_date', 'end_date', 'last_payment_date']:
                    if date_field in loan_data and loan_data[date_field]:
                        loan_data[date_field] = format_date(loan_data[date_field])
                        
                account_loans.append(loan_data)
    else:
        # Customer sees only their own loans
        account_loans = []
        if user['account_id']:
            account = account_manager.get_account(user['account_id'])
            loans = loan_manager.get_account_loans(user['account_id'])
            
            for loan in loans:
                loan_data = dict(loan)
                loan_data['account_number'] = account['account_number']
                loan_data['owner_name'] = account['owner_name']
                  # Format loan dates
                for date_field in ['application_date', 'start_date', 'end_date', 'last_payment_date']:
                    if date_field in loan_data and loan_data[date_field]:
                        loan_data[date_field] = format_date(loan_data[date_field])
                        
                account_loans.append(loan_data)
    
    return render_template('loans.html', loans=account_loans, user=user)


@app.route('/loans/apply', methods=['GET', 'POST'])
@login_required
def apply_for_loan():
    """Apply for a new loan"""
    user = user_manager.get_user_by_id(session['user_id'])
    
    if request.method == 'POST':
        account_id = int(request.form.get('account_id'))
        
        # Check access permissions
        if not customer_access_check(account_id):
            flash('Access denied. You can only apply for loans on your own account.', 'danger')
            return redirect(url_for('dashboard'))
        
        loan_amount = float(request.form.get('loan_amount'))
        interest_rate = float(request.form.get('interest_rate'))
        term_months = int(request.form.get('term_months'))
        
        try:
            loan = loan_manager.apply_for_loan(
                account_id=account_id,
                loan_amount=loan_amount,
                interest_rate=interest_rate,
                term_months=term_months
            )
            
            # Calculate monthly payment for display
            monthly_payment = loan_manager.calculate_monthly_payment(
                loan_amount, interest_rate, term_months
            )
            
            flash(f'Loan application submitted successfully. Monthly payment: ${monthly_payment:.2f}', 'success')
            return redirect(url_for('loans'))
        except Exception as e:
            flash(f'Error applying for loan: {str(e)}', 'danger')
    
    # Get accounts for dropdown - admin sees all, customer sees only their own
    if user['user_type'] == 'admin':
        all_accounts = account_manager.get_all_accounts()
    else:
        if user['account_id']:
            account = account_manager.get_account(user['account_id'])
            all_accounts = [account] if account else []
        else:
            all_accounts = []
    
    return render_template('apply_loan.html', accounts=all_accounts)


@app.route('/loans/<int:loan_id>/approve', methods=['POST'])
@admin_required
def approve_loan(loan_id):
    """Approve a loan application - Admin only"""
    try:
        loan = loan_manager.approve_loan(loan_id)
        flash('Loan approved and funds disbursed', 'success')
    except Exception as e:
        flash(f'Error approving loan: {str(e)}', 'danger')
    
    return redirect(url_for('loans'))


@app.route('/loans/<int:loan_id>/reject', methods=['POST'])
@admin_required
def reject_loan(loan_id):
    """Reject a loan application - Admin only"""
    try:
        loan = loan_manager.reject_loan(loan_id)
        flash('Loan application rejected', 'success')
    except Exception as e:
        flash(f'Error rejecting loan: {str(e)}', 'danger')
    
    return redirect(url_for('loans'))


@app.route('/loans/<int:loan_id>/payment', methods=['GET', 'POST'])
@login_required
def make_payment(loan_id):
    """Make a payment on a loan"""
    loan = loan_manager.get_loan(loan_id)
    if not loan:
        flash('Loan not found', 'danger')
        return redirect(url_for('loans'))
    
    # Check access permissions
    if not customer_access_check(loan['account_id']):
        flash('Access denied. You can only make payments on your own loans.', 'danger')
        return redirect(url_for('dashboard'))
    
    account = account_manager.get_account(loan['account_id'])
    
    if request.method == 'POST':
        payment_amount = float(request.form.get('payment_amount'))
        
        try:
            payment_result = loan_manager.make_payment(loan_id, payment_amount)
            flash('Payment applied successfully', 'success')
            return redirect(url_for('loans'))
        except Exception as e:
            flash(f'Error making payment: {str(e)}', 'danger')
    
    return render_template('loan_payment.html', loan=loan, account=account)


@app.route('/bug_report', methods=['GET', 'POST'])
@login_required
def report_bug():
    """Report a bug in the system"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        severity = request.form.get('severity')
        module = request.form.get('module')
        steps = request.form.get('steps_to_reproduce')
        
        try:
            bug = bug_tracker.log_bug(
                title=title,
                description=description,
                severity=severity,
                module=module,
                steps_to_reproduce=steps
            )
            
            flash('Bug reported successfully', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error reporting bug: {str(e)}', 'danger')
    
    return render_template('report_bug.html')


@app.route('/bugs')
@admin_required
def bugs():
    """View all reported bugs - Admin only"""
    all_bugs = bug_tracker.get_all_bugs()

    # Format dates in Python, so template doesn’t need to
    for bug in all_bugs:
        if 'reported_date' in bug and bug['reported_date']:
            bug['reported_date'] = format_date(bug['reported_date'], '%Y-%m-%d %H:%M')

    return render_template('bugs.html', bugs=all_bugs)


if __name__ == '__main__':
    # Create tables if they don't exist
    db = account_manager.db
    db.initialize_database()
      # Create default admin user if it doesn't exist
    try:
        if not user_manager.get_user_by_username('admin'):
            # Create admin account first
            admin_account = account_manager.create_account(
                owner_name='System Administrator',
                account_type='checking',
                email='admin@bankingsystem.com',
                initial_balance=0.0
            )
            
            # Create admin user
            admin_user = user_manager.create_user(
                username='admin',
                password='admin123',
                email='admin@bankingsystem.com',
                full_name='System Administrator',
                user_type='admin',
                account_id=admin_account['account_id']
            )
            print("✓ Default admin user created (username: admin, password: admin123)")
        else:
            print("✓ Admin user already exists")
    except Exception as e:
        print(f"⚠ Warning: Could not create admin user: {e}")
    
    # Run the app
    app.run(debug=True)

# Initialize database and admin user on server startup for deployment
def initialize_system():
    """Initialize the system with database and default admin user"""
    try:
        db = account_manager.db
        db.initialize_database()
          # Create default admin user if it doesn't exist
        if not user_manager.get_user_by_username('admin'):
            # Create admin account first
            admin_account = account_manager.create_account(
                owner_name='System Administrator',
                account_type='checking',
                email='admin@bankingsystem.com',
                initial_balance=0.0
            )
            
            # Create admin user
            admin_user = user_manager.create_user(
                username='admin',
                password='admin123',
                email='admin@bankingsystem.com',
                full_name='System Administrator',
                user_type='admin',
                account_id=admin_account['account_id']
            )
            print("✓ Default admin user created")
    except Exception as e:
        print(f"⚠ Warning: System initialization issue: {e}")

# Initialize system
initialize_system()

# For Vercel serverless deployment
# app is already defined above and will be used by the WSGI server

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)