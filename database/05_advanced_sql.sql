-- VIEWS 

-- VIEW 1: Customer Account Details

CREATE VIEW CustomerAccountDetails AS
SELECT
    C.CustomerID,
    C.First_name,
    C.Last_name,
    A.AccountID,
    A.AccountNumber,
    A.AccountType,
    A.OpeningDate,
    A.Balance,
    A.Status,
    A.BranchID
FROM CUSTOMER C
JOIN ACCOUNT_HOLDER AH
    ON C.CustomerID = AH.CustomerID
JOIN ACCOUNT A
    ON AH.AccountID = A.AccountID;


-- VIEW 2: Branch Account Summary

CREATE VIEW BranchAccountSummary AS
SELECT
    B.BranchID,
    B.BranchName,
    COUNT(A.AccountID) AS TotalAccounts,
    COALESCE(SUM(A.Balance), 0) AS TotalBalance
FROM BRANCH B
LEFT JOIN ACCOUNT A
    ON B.BranchID = A.BranchID
GROUP BY B.BranchID, B.BranchName;


-- TRANSACTIONS

-- Transaction 1: Demonstrate ROLLBACK

START TRANSACTION;

UPDATE ACCOUNT
SET Balance = Balance + 100
WHERE AccountID = 201;

SELECT AccountID, Balance
FROM ACCOUNT
WHERE AccountID = 201;

ROLLBACK;

-- Verify the original balance is restored
SELECT AccountID, Balance
FROM ACCOUNT
WHERE AccountID = 201;


-- Transaction 2: Demonstrate SAVEPOINT and ROLLBACK TO

START TRANSACTION;

UPDATE ACCOUNT
SET Balance = Balance + 100
WHERE AccountID = 201;

SAVEPOINT A;

UPDATE ACCOUNT
SET Balance = Balance + 200
WHERE AccountID = 201;

SELECT AccountID, Balance
FROM ACCOUNT
WHERE AccountID = 201;

ROLLBACK TO A;

SELECT AccountID, Balance
FROM ACCOUNT
WHERE AccountID = 201;

ROLLBACK;

-- Verify the original balance is restored
SELECT AccountID, Balance
FROM ACCOUNT
WHERE AccountID = 201;


-- PROCEDURES:

-- Procedure 1: Get customer accounts

DELIMITER //

CREATE PROCEDURE GetCustomerAccounts(IN p_CustomerID INT)
BEGIN
    SELECT
        C.CustomerID,
        C.First_name,
        C.Last_name,
        C.Mobile,
        C.Email,
        A.AccountID,
        A.AccountNumber,
        A.AccountType,
        A.Balance,
        A.Status AS AccountStatus,
        B.BranchName,
        B.City AS BranchCity
    FROM CUSTOMER C
    JOIN ACCOUNT_HOLDER AH
        ON C.CustomerID = AH.CustomerID
    JOIN ACCOUNT A
        ON AH.AccountID = A.AccountID
    JOIN BRANCH B
        ON A.BranchID = B.BranchID
    WHERE C.CustomerID = p_CustomerID;
END //

-- Procedure 2: Get branch account summary

CREATE PROCEDURE GetBranchAccountSummary(IN p_BranchID INT)
BEGIN
    SELECT
        B.BranchID,
        B.BranchName,
        COUNT(A.AccountID) AS TotalAccounts,
        COALESCE(SUM(A.Balance), 0) AS TotalBalance
    FROM BRANCH B
    LEFT JOIN ACCOUNT A
        ON B.BranchID = A.BranchID
    WHERE B.BranchID = p_BranchID
    GROUP BY B.BranchID, B.BranchName;
END //

DELIMITER ;


-- FUNCTIONS

-- FUNCTION 1: Get total balance of a customer

DELIMITER //

CREATE FUNCTION GetCustomerTotalBalance(p_CustomerID INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE total_balance DECIMAL(10,2);

    SELECT COALESCE(SUM(A.Balance), 0)
    INTO total_balance
    FROM ACCOUNT A
    JOIN ACCOUNT_HOLDER AH
        ON A.AccountID = AH.AccountID
    WHERE AH.CustomerID = p_CustomerID;

    RETURN total_balance;
END //

DELIMITER ;


-- FUNCTION 2: Calculate simple interest on a loan

DELIMITER //

CREATE FUNCTION CalcLoanInterest(
    p_loan_amount DECIMAL(10,2),
    p_interest_rate DECIMAL(5,2),
    p_tenure_years INT
)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE v_interest DECIMAL(10,2);

    SET v_interest =
        (p_loan_amount * p_interest_rate * p_tenure_years) / 100;

    RETURN v_interest;
END //

DELIMITER ;


-- TRIGGERS:

-- TRIGGER 1: Prevent invalid withdrawal amounts

DELIMITER //

CREATE TRIGGER BeforeWithdrawalInsert
BEFORE INSERT ON TRANSACTIONS
FOR EACH ROW
BEGIN
    IF NEW.TransactionType = 'WITHDRAWAL'
       AND UPPER(NEW.TransactionStatus) = 'SUCCESS'
       AND NEW.Amount <= 0 THEN

        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Withdrawal amount must be greater than zero';

    END IF;
END //

DELIMITER ;


-- TRIGGER 2: Prevent negative account balances

DELIMITER //

CREATE TRIGGER BeforeAccountBalanceUpdate
BEFORE UPDATE ON ACCOUNT
FOR EACH ROW
BEGIN
    IF NEW.Balance < 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Account balance cannot be negative';
    END IF;
END //

DELIMITER ;