
# PROJECT KASHI

## Banking Management System

## 1. Introduction

Project Kashi is a database-driven Banking Management System developed to demonstrate the design of a relational database and its integration with a web application.

The system manages customer and account information, deposits, withdrawals, fund transfers, transaction history, loans, and loan payments through a web interface connected to MySQL.

## 2. Objectives

The objectives of Project Kashi are:

- To design a relational database for banking operations.
- To maintain customer, branch, employee, account, transaction, and loan records.
- To establish relationships using primary and foreign keys.
- To maintain data integrity through constraints and triggers.
- To implement business-oriented SQL queries.
- To demonstrate views, stored procedures, functions, and transaction control.
- To connect MySQL to a web application using Flask.
- To provide an interface for the supported banking operations.

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| MySQL 8.0 | Relational database management |
| Python | Backend programming |
| Flask | Backend web framework and API endpoints |
| MySQL Connector/Python | Communication between Flask and MySQL |
| HTML | Web page structure |
| CSS | Styling and layout |
| JavaScript | Frontend interactions and API requests |
| Visual Studio Code / Cursor | Code development and editing |
| MySQL Workbench | Database development and inspection |
| Git and GitHub | Source-code version control |

## 4. System Architecture

Project Kashi follows a frontend–backend–database architecture.

### 4.1 Frontend

The frontend uses HTML, CSS, and JavaScript to display the interface, collect user input, send requests to the backend, and display responses.

### 4.2 Backend

The backend uses Python and Flask to receive requests, process operations, communicate with MySQL, and return responses to the frontend.

### 4.3 Database

The MySQL database, `project_kashi`, contains eight related tables:

- `CUSTOMER`
- `BRANCH`
- `EMPLOYEE`
- `ACCOUNT`
- `ACCOUNT_HOLDER`
- `TRANSACTIONS`
- `LOAN`
- `LOAN_PAYMENT`

### 4.4 Request Flow

1. The user performs an operation through the frontend.
2. JavaScript sends a request to a Flask endpoint.
3. Flask processes the request and executes the required database operation.
4. MySQL retrieves or updates the relevant records.
5. Flask returns a response.
6. The frontend displays the result.

**Architecture:**

`HTML/CSS/JavaScript → Flask → MySQL Connector/Python → MySQL Database`

## 5. Database Design

The database is named `project_kashi` and contains eight tables with 59 columns in the documented original design.

The tables cover customer information, bank branches, employees, account details, customer-account ownership, transactions, loans, and loan payments.

The design uses:

- Primary keys to identify records.
- Foreign keys to connect related tables.
- A composite primary key in `ACCOUNT_HOLDER`.
- A UNIQUE constraint for account numbers.
- An ENUM definition for account types.
- Triggers for selected data-validation rules.

The `ACCOUNT_HOLDER` table implements the many-to-many relationship between customers and accounts. The remaining relationships connect branches, employees, accounts, transactions, loans, and loan payments.

The complete attributes, keys, constraints, and ER diagram are documented in `database_design.md`.

## 6. Main Application Features

The website integrates the database with the frontend through the Flask backend.

| Feature | Description |
|---|---|
| Account management | Create and retrieve account information through the supported endpoints |
| Deposits | Add funds to an account |
| Withdrawals | Withdraw funds subject to the implemented validation |
| Fund transfers | Transfer funds between accounts |
| Transaction history | Retrieve recorded transaction information |
| Customer account lookup | Retrieve a customer's associated accounts |
| Customer balance summary | Calculate the total balance across a customer's linked accounts |
| Branch account summary | Retrieve account totals and balances by branch |
| Loan management | Register and manage loan information |
| Loan payments | Record payments associated with loans |

These features describe the functionality implemented and tested during development; they do not imply that the application provides production-grade banking services.

## 7. SQL Implementation

The SQL scripts are organised into separate files.

| File | Purpose |
|---|---|
| `01_database_setup.sql` | Database setup |
| `02_create_tables.sql` | Table creation and relationship definitions |
| `03_insert_data.sql` | Sample data insertion |
| `04_queries.sql` | Business and analytical queries |
| `05_advanced_sql.sql` | Advanced SQL demonstrations |

### 7.1 Business Queries

The business queries demonstrate:

- Retrieving customer and account details using joins.
- Filtering saving accounts.
- Identifying customers holding multiple accounts.
- Calculating account balances by branch.
- Finding customers who have not taken a loan.
- Calculating average employee salaries by branch.
- Summarising deposit and withdrawal amounts while excluding transfers.
- Finding loans above the average loan amount.
- Ranking accounts by balance using `DENSE_RANK()`.
- Identifying customers whose total loan payments exceed 10,000.

These queries demonstrate joins, filtering, grouping, aggregate functions, subqueries, and window functions.

### 7.2 Advanced SQL

The advanced SQL implementation includes the following objects:

| Object | Name | Purpose |
|---|---|---|
| View | `CustomerAccountDetails` | Presents customer and account information |
| View | `BranchAccountSummary` | Summarises account counts and balances by branch |
| Stored procedure | `GetCustomerAccounts` | Retrieves account information for a specified customer |
| Stored procedure | `GetBranchAccountSummary` | Retrieves account totals and balances for a specified branch |
| Function | `GetCustomerTotalBalance` | Calculates a customer's total linked account balance |
| Function | `CalcLoanInterest` | Calculates simple interest using the supplied amount, rate, and tenure in years |
| Trigger | `BeforeWithdrawalInsert` | Rejects successful withdrawal transactions with zero or negative amounts |
| Trigger | `BeforeAccountBalanceUpdate` | Prevents an account balance from becoming negative during an update |

The SQL scripts also demonstrate transaction control using `START TRANSACTION`, `SAVEPOINT`, `ROLLBACK TO`, and `ROLLBACK`.

## 8. Backend Implementation

The backend is developed using Python and Flask. MySQL Connector/Python provides the connection between Flask and the MySQL database.

The backend processes requests from the frontend, executes database operations, and returns responses. User-provided values should be handled using parameterised queries where applicable.

The backend supports the implemented account, transaction, customer lookup, branch summary, loan, and loan-payment operations.

## 9. Frontend Implementation

The frontend uses HTML, CSS, and JavaScript.

HTML defines the page structure, CSS controls the appearance, and JavaScript handles form interactions and API requests.

The interface includes pages for account-related operations, transactions, transfers, transaction history, and loan-related features.

The frontend communicates with Flask rather than connecting directly to MySQL.

## 10. Testing and Verification

Testing was performed during development to check the database, advanced SQL objects, and website functionality.

| Test Area | Verification |
|---|---|
| MySQL connection | Connection established during development |
| Table creation | Eight tables created |
| Sample data | Sample records inserted |
| Business SQL queries | Executed; screenshots captured |
| Customer account lookup | Tested |
| Customer total balance function | Tested |
| Customer account retrieval procedure | Tested |
| Branch account summary procedure | Tested |
| Loan interest function | Tested |
| Negative-balance trigger | Tested |
| Withdrawal-validation trigger | Tested |
| Website banking operations | Tested during development |
| Loan management and payments | Reported working during development |

The tested trigger rules reject the specific invalid operations described in Section 7.2. Testing these scenarios does not establish that every possible input or failure condition has been covered.

## 11. Screenshots and Supporting Evidence

Screenshots of business-query outputs are stored in:

`screenshots/business_queries/`

They provide evidence of query execution. Additional screenshots of advanced SQL results or website features can be included when required by the assignment.

Each screenshot should correspond to an actual query output or application result.

## 12. Project Structure

The project is organised into database, backend, frontend, documentation, and screenshot folders.

```text
Project-Kashi/
│
├── .gitignore
├── README.md
│
├── backend/
│   ├── app.py
│   └── db.py
│
├── database/
│   ├── 01_database_setup.sql
│   ├── 02_create_tables.sql
│   ├── 03_insert_data.sql
│   ├── 04_queries.sql
│   └── 05_advanced_sql.sql
│
├── documentations/
│   ├── database_design.md
│   └── project_report.md
│
├── frontend/
│   ├── HTML pages
│   ├── style.css
│   └── script.js
│
└── screenshots/
    └── business_queries/
```

This is a simplified representation of the project structure. The actual repository may contain additional frontend pages and supporting files.

## 13. Limitations

Project Kashi is an academic project intended to demonstrate DBMS concepts and database-backed application development.

It is not a production-ready banking platform. Real-world deployment would require stronger authentication and authorisation, security controls, audit mechanisms, comprehensive testing, and additional safeguards for financial transactions.

## 14. Future Enhancements

Possible future improvements include:

- Adding secure authentication and role-based access.
- Expanding automated testing for database and API operations.
- Improving error handling and input validation.
- Enhancing transaction auditing and financial reporting.
- Improving the interface's usability and accessibility.
- Strengthening configuration and credential management.

## 15. Conclusion

Project Kashi demonstrates relational database design and integration with a web application. It includes eight related tables, primary and foreign keys, integrity rules, business SQL queries, views, stored procedures, functions, triggers, and transaction-control demonstrations.

The Flask backend connects the MySQL database to an HTML, CSS, and JavaScript interface for supported account, transaction, and loan operations.

The project provides practical experience in database design, SQL implementation, data validation, and database-backed application development.
