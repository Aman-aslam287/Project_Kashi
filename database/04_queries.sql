-- Query 1 (Display customers with their account numbers and types)
SELECT
    c.First_name,
    c.Last_name,
    a.AccountNumber,
    a.AccountType
FROM Customer c
JOIN Account_Holder ah
ON c.CustomerID = ah.CustomerID
JOIN Account a
ON ah.AccountID = a.AccountID;

-- Query 2 (Display accounts of a specified type)
SELECT AccountNumber, AccountType, Balance
FROM ACCOUNT
WHERE AccountType = 'Saving';

-- Query 3 (Find customers who own multiple accounts)
SELECT
C.CustomerID,
C.First_name,
C.Last_name,
COUNT(A.AccountID) AS TotalAccounts
FROM CUSTOMER C
JOIN ACCOUNT_HOLDER AH
ON C.CustomerID = AH.CustomerID
JOIN ACCOUNT A
ON AH.AccountID = A.AccountID
GROUP BY C.CustomerID, C.First_name, C.Last_name
HAVING COUNT(A.AccountID) > 1;

-- Query 4 (Calculate total balance at each branch)

SELECT
    B.BranchID,
    B.BranchName,
    SUM(A.Balance) AS TotalBalance
FROM BRANCH B
JOIN ACCOUNT A
ON B.BranchID = A.BranchID
GROUP BY B.BranchID, B.BranchName
ORDER BY TotalBalance DESC;


-- Query 5 (Find customers who have never taken a loan)

SELECT
    C.CustomerID,
    C.First_name,
    C.Last_name
FROM CUSTOMER C
LEFT JOIN LOAN L
ON C.CustomerID = L.CustomerID
WHERE L.LoanID IS NULL;


-- Query 6 (Calculate average employee salary at each branch)

SELECT
    B.BranchName,
    AVG(E.Salary) AS AverageSalary
FROM BRANCH B
JOIN EMPLOYEE E
ON B.BranchID = E.BranchID
GROUP BY B.BranchID, B.BranchName;


-- Query 7 (Calculate total deposits and withdrawals per account)

SELECT
    A.AccountNumber,
    SUM(CASE
        WHEN T.TransactionType = 'DEPOSIT'
        THEN T.Amount ELSE 0
    END) AS TotalDeposits,
    SUM(CASE
        WHEN T.TransactionType = 'WITHDRAWAL'
        THEN T.Amount ELSE 0
    END) AS TotalWithdrawals
FROM ACCOUNT A
LEFT JOIN TRANSACTIONS T
ON A.AccountID = T.AccountID
GROUP BY A.AccountID, A.AccountNumber;


-- Query 8 (Find loans greater than the average loan amount)

SELECT
    LoanID,
    CustomerID,
    LoanType,
    LoanAmount
FROM LOAN
WHERE LoanAmount > (
    SELECT AVG(LoanAmount)
    FROM LOAN
);


-- Query 9 (Rank accounts by balance from highest to lowest)

SELECT
    AccountNumber,
    AccountType,
    Balance,
    DENSE_RANK() OVER (
        ORDER BY Balance DESC
    ) AS BalanceRank
FROM ACCOUNT;


-- Query 10 (Find customers whose total loan payments exceed 20000)

SELECT
    C.CustomerID,
    C.First_name,
    C.Last_name,
    SUM(LP.Amount) AS TotalPayments
FROM CUSTOMER C
JOIN LOAN L
ON C.CustomerID = L.CustomerID
JOIN LOAN_PAYMENT LP
ON L.LoanID = LP.LoanID
GROUP BY C.CustomerID, C.First_name, C.Last_name
HAVING SUM(LP.Amount) > 20000;
