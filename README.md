# Banking System Application

## Overview
The Banking System is a comprehensive web-based application designed for managing banking operations. It provides a modern, intuitive interface for account management, transactions, loan processing, and system testing through a built-in bug tracker.

## Features

### Account Management
- Create and manage different types of bank accounts (Checking, Savings, Money Market, Certificate of Deposit)
- View account details and transaction history
- Update account information

### Transaction Processing
- Deposit funds into accounts
- Withdraw funds from accounts
- Transfer funds between accounts
- Track transaction history

### Loan Management
- Apply for loans with customizable terms
- Calculate estimated monthly payments
- Approve or reject loan applications
- Make payments on active loans
- Track loan status and remaining balances

### Bug Tracking System
- Report bugs with severity levels and detailed descriptions
- Track bug status (Open, In Progress, Fixed, Closed, Reopened)
- Generate bug reports
- Add comments and update bug status

## Technology Stack
- **Backend**: Python with Flask framework
- **Database**: SQLite for data storage
- **Frontend**: HTML, CSS, JavaScript with Bootstrap 5
- **UI Components**: Font Awesome for icons, Google Fonts for typography
- **Animation**: CSS animations for a modern interface

## Installation

### Prerequisites
- Python 3.8 or higher
- Pip package manager

### Setup
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/banking_system.git
   cd banking_system
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Run the application:
   ```
   python web/app.py
   ```

6. Access the application in your web browser at:
   ```
   http://127.0.0.1:5000/
   ```

## Project Structure
```
banking_system/
├── data/
│   └── banking.db        # SQLite database file
├── reports/              # Generated reports folder
│   └── bug_reports.log   
├── src/                  # Core application code
│   ├── account.py        # Account management module
│   ├── bug_tracker.py    # Bug tracking module
│   ├── database.py       # Database operations module
│   ├── loan.py           # Loan management module
│   └── transaction.py    # Transaction processing module
├── tests/                # Unit tests
│   ├── test_account.py
│   ├── test_loan.py
│   └── test_transaction.py
├── web/                  # Web interface
│   ├── app.py            # Flask application
│   └── templates/        # HTML templates
│       ├── account_details.html
│       ├── accounts.html
│       ├── apply_loan.html
│       ├── base.html     # Base template with common elements
│       └── ...           # Other template files
└── requirements.txt      # Python dependencies
```

## Usage
1. **Dashboard**: The home page displays system statistics and quick access to all features
2. **Account Management**: Create accounts, view account details, and manage account information
3. **Transactions**: Make deposits, withdrawals, and transfers between accounts
4. **Loans**: Apply for loans, approve/reject applications, and make payments on active loans
5. **Bug Tracking**: Report bugs, track their status, and generate reports

## Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.
