-- 1. CUSTOMER
CREATE TABLE CUSTOMER (
    CustomerID INT PRIMARY KEY AUTO_INCREMENT,
    First_name VARCHAR(50),
    Last_name VARCHAR(50),
    DateOFBirth DATE,
    Gender VARCHAR(10),
    Mobile VARCHAR(15),
    Email VARCHAR(100),
    Address VARCHAR(100),
    City VARCHAR(50),
    RegistrationDate DATE
);


-- 2. BRANCH
CREATE TABLE BRANCH (
    BranchID INT PRIMARY KEY,
    BranchName VARCHAR(100),
    IFSC_Code VARCHAR(20),
    Address VARCHAR(100),
    City VARCHAR(50),
    State VARCHAR(50),
    ContactNumber VARCHAR(15)
);


-- 3. EMPLOYEE
CREATE TABLE EMPLOYEE (
    EmployeeID INT PRIMARY KEY,
    EmployeeName VARCHAR(50),
    Mobile VARCHAR(15),
    Email VARCHAR(100),
    Designation VARCHAR(50),
    Salary DECIMAL(10,2),
    JoiningDate DATE,
    BranchID INT,
    FOREIGN KEY (BranchID)
        REFERENCES BRANCH(BranchID)
);


-- 4. ACCOUNT
CREATE TABLE ACCOUNT (
    AccountID INT PRIMARY KEY AUTO_INCREMENT,
    AccountNumber VARCHAR(20) NOT NULL,
    AccountType ENUM('Saving', 'Current', 'Salary') NOT NULL,
    OpeningDate DATE,
    Balance DECIMAL(10,2),
    Status VARCHAR(20),
    BranchID INT,
    UNIQUE (AccountNumber),
    FOREIGN KEY (BranchID)
        REFERENCES BRANCH(BranchID),
    CONSTRAINT chk_account_status
        CHECK (Status IN ('ACTIVE', 'INACTIVE', 'CLOSED')),
    CONSTRAINT chk_account_balance
        CHECK (Balance >= 0)
);


-- 5. ACCOUNT_HOLDER
CREATE TABLE ACCOUNT_HOLDER (
    CustomerID INT,
    AccountID INT,
    HolderSince DATE,
    HolderType VARCHAR(50),
    PRIMARY KEY (CustomerID, AccountID),
    FOREIGN KEY (AccountID)
        REFERENCES ACCOUNT(AccountID),
    FOREIGN KEY (CustomerID)
        REFERENCES CUSTOMER(CustomerID)
);


-- 6. TRANSACTIONS
CREATE TABLE TRANSACTIONS (
    TransactionID INT PRIMARY KEY AUTO_INCREMENT,
    AccountID INT,
    TransactionType VARCHAR(20),
    Amount DECIMAL(10,2),
    TransactionDate DATE,
    Description VARCHAR(50),
    ReferenceNumber VARCHAR(50),
    TransactionStatus VARCHAR(20),
    FOREIGN KEY (AccountID)
        REFERENCES ACCOUNT(AccountID),
    CONSTRAINT chk_transaction_amount
        CHECK (Amount > 0)
);


-- 7. LOAN
CREATE TABLE LOAN (
    LoanID INT PRIMARY KEY AUTO_INCREMENT,
    CustomerID INT,
    BranchID INT,
    LoanType VARCHAR(50),
    LoanAmount DECIMAL(10,2),
    InterestRate DECIMAL(5,2),
    StartDate DATE,
    TenureMonths INT,
    LoanStatus VARCHAR(20),
    FOREIGN KEY (CustomerID)
        REFERENCES CUSTOMER(CustomerID),
    FOREIGN KEY (BranchID)
        REFERENCES BRANCH(BranchID),
    CONSTRAINT chk_loan_amount
        CHECK (LoanAmount > 0),
    CONSTRAINT chk_loan_tenure
        CHECK (TenureMonths > 0)
);


-- 8. LOAN_PAYMENT
CREATE TABLE LOAN_PAYMENT (
    PaymentID INT PRIMARY KEY AUTO_INCREMENT,
    LoanID INT,
    PaymentDate DATE,
    Amount DECIMAL(10,2),
    PaymentMode VARCHAR(20),
    ReferenceNumber VARCHAR(50),
    FOREIGN KEY (LoanID)
        REFERENCES LOAN(LoanID),
    CONSTRAINT chk_payment_amount
        CHECK (Amount > 0)
);