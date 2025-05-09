from flask import Flask, render_template, request, redirect, url_for, flash, session
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.account import AccountManager
from src.transaction import TransactionManager
from src.loan import LoanManager
from src.bug_tracker import BugTracker

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


@app.route('/')
def index():
    """Home page route with dashboard statistics"""
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
def accounts():
    """List all accounts"""
    all_accounts = account_manager.get_all_accounts()
    
    # Format dates and account types for display
    for account in all_accounts:
        account['created_at'] = format_date(account['created_at'])
    
    return render_template('accounts.html', accounts=all_accounts)


@app.route('/accounts/new', methods=['GET', 'POST'])
def new_account():
    """Create a new account"""
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
def view_account(account_id):
    """View account details"""
    account = account_manager.get_account(account_id)
    if not account:
        flash('Account not found', 'danger')
        return redirect(url_for('accounts'))
    
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
    
    return render_template(
        'account_details.html', 
        account=account, 
        transactions=transactions,
        loans=loans
    )


@app.route('/accounts/<int:account_id>/edit', methods=['GET', 'POST'])
def edit_account(account_id):
    """Edit account details"""
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
def delete_account(account_id):
    """Delete an account"""
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
def deposit():
    """Deposit money into an account"""
    if request.method == 'POST':
        account_id = int(request.form.get('account_id'))
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        
        try:
            transaction_manager.deposit(account_id, amount, description)
            flash('Deposit successful', 'success')
            return redirect(url_for('view_account', account_id=account_id))
        except Exception as e:
            flash(f'Error making deposit: {str(e)}', 'danger')
    
    # Get all accounts for the dropdown
    all_accounts = account_manager.get_all_accounts()
    return render_template('deposit.html', accounts=all_accounts)


@app.route('/transactions/withdraw', methods=['GET', 'POST'])
def withdraw():
    """Withdraw money from an account"""
    if request.method == 'POST':
        account_id = int(request.form.get('account_id'))
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        
        try:
            transaction_manager.withdraw(account_id, amount, description)
            flash('Withdrawal successful', 'success')
            return redirect(url_for('view_account', account_id=account_id))
        except Exception as e:
            flash(f'Error making withdrawal: {str(e)}', 'danger')
    
    # Get all accounts for the dropdown
    all_accounts = account_manager.get_all_accounts()
    return render_template('withdraw.html', accounts=all_accounts)


@app.route('/transactions/transfer', methods=['GET', 'POST'])
def transfer():
    """Transfer money between accounts"""
    if request.method == 'POST':
        from_account_id = int(request.form.get('from_account_id'))
        to_account_id = int(request.form.get('to_account_id'))
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        
        try:
            transaction_manager.transfer(from_account_id, to_account_id, amount, description)
            flash('Transfer successful', 'success')
            return redirect(url_for('view_account', account_id=from_account_id))
        except Exception as e:
            flash(f'Error making transfer: {str(e)}', 'danger')
    
    # Get all accounts for the dropdowns
    all_accounts = account_manager.get_all_accounts()
    return render_template('transfer.html', accounts=all_accounts)


@app.route('/loans')
def loans():
    """List all loans"""
    # This would need a more complex query in a real system
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
    
    return render_template('loans.html', loans=account_loans)


@app.route('/loans/apply', methods=['GET', 'POST'])
def apply_for_loan():
    """Apply for a new loan"""
    if request.method == 'POST':
        account_id = int(request.form.get('account_id'))
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
    
    # Get all accounts for the dropdown
    all_accounts = account_manager.get_all_accounts()
    return render_template('apply_loan.html', accounts=all_accounts)


@app.route('/loans/<int:loan_id>/approve', methods=['POST'])
def approve_loan(loan_id):
    """Approve a loan application"""
    try:
        loan = loan_manager.approve_loan(loan_id)
        flash('Loan approved and funds disbursed', 'success')
    except Exception as e:
        flash(f'Error approving loan: {str(e)}', 'danger')
    
    return redirect(url_for('loans'))


@app.route('/loans/<int:loan_id>/reject', methods=['POST'])
def reject_loan(loan_id):
    """Reject a loan application"""
    try:
        loan = loan_manager.reject_loan(loan_id)
        flash('Loan application rejected', 'success')
    except Exception as e:
        flash(f'Error rejecting loan: {str(e)}', 'danger')
    
    return redirect(url_for('loans'))


@app.route('/loans/<int:loan_id>/payment', methods=['GET', 'POST'])
def make_payment(loan_id):
    """Make a payment on a loan"""
    loan = loan_manager.get_loan(loan_id)
    if not loan:
        flash('Loan not found', 'danger')
        return redirect(url_for('loans'))
    
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
def bugs():
    """View all reported bugs"""
    all_bugs = bug_tracker.get_all_bugs()
    return render_template('bugs.html', bugs=all_bugs)


@app.route('/reports/generate', methods=['GET', 'POST'])
def generate_report():
    """Generate system reports"""
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        
        if report_type == 'bug_report':
            include_closed = 'include_closed' in request.form
            report_file = bug_tracker.generate_bug_report(include_closed)
            flash(f'Bug report generated: {report_file}', 'success')
        else:
            flash('Invalid report type selected', 'danger')
    
    return render_template('generate_report.html')


if __name__ == '__main__':
    # Create tables if they don't exist
    db = account_manager.db
    db.initialize_database()
    
    # Run the app
    app.run(debug=True)

# Initialize database on server startup for Vercel
db = account_manager.db
db.initialize_database()

# For Vercel serverless deployment
# app is already defined above and will be used by the WSGI server