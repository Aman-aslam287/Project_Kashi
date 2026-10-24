-- ==========================================
-- PROJECT KASHI: SAMPLE DATA
-- ==========================================

-- 1. CUSTOMER DATA
INSERT INTO CUSTOMER
(CustomerID, First_name, Last_name, DateOFBirth, Gender, Mobile, Email, Address, City, RegistrationDate)
VALUES
(1, 'Aman', 'Aslam', '2004-05-15', 'Male', '9876543210', 'aman@example.com', 'MG Road', 'Mangalore', '2025-01-10'),
(2, 'Rahul', 'Sharma', '2003-08-22', 'Male', '9876543211', 'rahul@example.com', 'Balmatta', 'Mangalore', '2025-02-15'),
(3, 'Priya', 'Shetty', '2004-02-10', 'Female', '9876543212', 'priya@example.com', 'Kadri', 'Mangalore', '2025-03-20'),
(4, 'Sneha', 'Rao', '2002-11-05', 'Female', '9876543213', 'sneha@example.com', 'Hampankatta', 'Mangalore', '2025-04-12'),
(5, 'Arjun', 'Kumar', '2001-07-18', 'Male', '9876543214', 'arjun@example.com', 'Bendoor', 'Mangalore', '2025-05-25');


-- 2. BRANCH DATA
INSERT INTO BRANCH
(BranchID, BranchName, IFSC_Code, Address, City, State, ContactNumber)
VALUES
(1, 'Kashi Main Branch', 'KASH0001001', 'MG Road', 'Mangalore', 'Karnataka', '8242221001'),
(2, 'Kashi City Branch', 'KASH0001002', 'Balmatta Road', 'Mangalore', 'Karnataka', '8242221002'),
(3, 'Kashi Bengaluru Branch', 'KASH0001003', 'Brigade Road', 'Bengaluru', 'Karnataka', '8022221003');


-- 3. EMPLOYEE DATA
INSERT INTO EMPLOYEE
(EmployeeID, EmployeeName, Mobile, Email, Designation, Salary, JoiningDate, BranchID)
VALUES
(101, 'Kiran Rao', '9876501001', 'kiran@kashi.example', 'Manager', 65000.00, '2022-06-15', 1),
(102, 'Meera Shetty', '9876501002', 'meera@kashi.example', 'Cashier', 35000.00, '2023-01-10', 1),
(103, 'Rohit Kumar', '9876501003', 'rohit@kashi.example', 'Accountant', 42000.00, '2023-08-20', 2),
(104, 'Ananya Rao', '9876501004', 'ananya@kashi.example', 'Cashier', 34000.00, '2024-02-12', 2),
(105, 'Vikram Das', '9876501005', 'vikram@kashi.example', 'Manager', 62000.00, '2021-11-05', 3);


-- 4. ACCOUNT DATA
INSERT INTO ACCOUNT
(AccountID, AccountNumber, AccountType, OpeningDate, Balance, Status, BranchID)
VALUES
(201, 'KASH100001', 'Saving', '2025-01-15', 17000.00, 'Active', 1),
(202, 'KASH100002', 'Current', '2025-02-20', 60000.00, 'Active', 1),
(203, 'KASH100003', 'Salary', '2025-03-10', 47000.00, 'Active', 2),
(204, 'KASH100004', 'Saving', '2025-04-05', 8000.00, 'Active', 2),
(205, 'KASH100005', 'Saving', '2025-05-12', 4500.00, 'Inactive', 3),
(206, 'KASH100006', 'Current', '2025-06-18', 120000.00, 'Active', 3);


-- 5. ACCOUNT_HOLDER DATA
INSERT INTO ACCOUNT_HOLDER
(CustomerID, AccountID, HolderSince, HolderType)
VALUES
(1, 201, '2025-01-15', 'Primary'),
(2, 202, '2025-02-20', 'Primary'),
(3, 203, '2025-03-10', 'Primary'),
(4, 204, '2025-04-05', 'Primary'),
(5, 205, '2025-05-12', 'Primary'),
(1, 206, '2025-06-18', 'Joint');


-- 6. TRANSACTIONS DATA
INSERT INTO TRANSACTIONS
(TransactionID, AccountID, TransactionType, Amount, TransactionDate, Description, ReferenceNumber, TransactionStatus)
VALUES
(301, 201, 'DEPOSIT', 10000.00, '2025-06-01', 'Initial deposit', 'REF1001', 'Success'),
(302, 201, 'WITHDRAWAL', 2000.00, '2025-06-05', 'ATM withdrawal', 'REF1002', 'Success'),
(303, 202, 'DEPOSIT', 25000.00, '2025-06-07', 'Cash deposit', 'REF1003', 'Success'),
(304, 203, 'WITHDRAWAL', 5000.00, '2025-06-10', 'Cash withdrawal', 'REF1004', 'Success'),
(305, 204, 'DEPOSIT', 7000.00, '2025-06-12', 'Salary credit', 'REF1005', 'Success'),
(306, 206, 'TRANSFER_IN', 15000.00, '2025-06-15', 'Incoming transfer', 'REF1006', 'Success'),
(307, 201, 'TRANSFER_OUT', 3000.00, '2025-06-18', 'Outgoing transfer', 'REF1007', 'Success'),
(308, 205, 'DEPOSIT', 500.00, '2025-06-20', 'Cash deposit', 'REF1008', 'Success');


-- 7. LOAN DATA
INSERT INTO LOAN
(LoanID, CustomerID, BranchID, LoanType, LoanAmount, InterestRate, StartDate, TenureMonths, LoanStatus)
VALUES
(401, 1, 1, 'Home Loan', 2500000.00, 8.50, '2025-01-10', 240, 'Active'),
(402, 2, 1, 'Education Loan', 500000.00, 7.25, '2025-02-15', 60, 'Active'),
(403, 3, 2, 'Personal Loan', 200000.00, 11.00, '2025-03-20', 36, 'Active'),
(404, 4, 2, 'Vehicle Loan', 750000.00, 9.00, '2025-04-12', 60, 'Active'),
(405, 5, 3, 'Education Loan', 300000.00, 7.50, '2025-05-25', 48, 'Closed');


-- 8. LOAN_PAYMENT DATA
INSERT INTO LOAN_PAYMENT
(PaymentID, LoanID, PaymentDate, Amount, PaymentMode, ReferenceNumber)
VALUES
(501, 401, '2025-02-10', 25000.00, 'Online', 'LPAY1001'),
(502, 401, '2025-03-10', 25000.00, 'Online', 'LPAY1002'),
(503, 402, '2025-03-15', 10000.00, 'UPI', 'LPAY1003'),
(504, 403, '2025-04-20', 7500.00, 'Online', 'LPAY1004'),
(505, 404, '2025-05-12', 15000.00, 'Cheque', 'LPAY1005'),
(506, 405, '2025-06-25', 10000.00, 'UPI', 'LPAY1006');
