-- VIEWS 

-- VIEW 1: Customer Account Details

CREATE VIEW CustomerAccountDetails AS
SELECT
    C.CustomerID,
    C.First_name,
    C.Last_name,
    A.AccountNumber,
    A.AccountType,
    A.Balance
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


-- TRANSACTIONS:

-- Transaction 1 (Deposit with commit): 

START TRANSACTION;

UPDATE ACCOUNT
SET Balance = Balance + 5000
WHERE AccountID = 201;

INSERT INTO TRANSACTIONS
(TransactionID, AccountID, TransactionType, Amount,
 TransactionDate, Description, ReferenceNumber, TransactionStatus)
VALUES
(901, 201, 'DEPOSIT', 5000, CURDATE(),
 'Cash deposit', 'REF901', 'SUCCESS');

COMMIT;


-- Transaction 2 (Withdrawal with commit):

START TRANSACTION;

UPDATE ACCOUNT
SET Balance = Balance - 2000
WHERE AccountID = 201
AND Balance >= 2000;

INSERT INTO TRANSACTIONS
(TransactionID, AccountID, TransactionType, Amount,
 TransactionDate, Description, ReferenceNumber, TransactionStatus)
VALUES
(902, 201, 'WITHDRAWAL', 2000, CURDATE(),
 'Cash withdrawal', 'REF902', 'SUCCESS');

COMMIT;


-- TRANSACTION 3 (ROLLBACK DEMONSTRATION):

SET AUTOCOMMIT = 0;

START TRANSACTION;

UPDATE ACCOUNT
SET Balance = Balance + 1000
WHERE AccountID = 201;

SAVEPOINT A;

UPDATE ACCOUNT
SET Balance = Balance + 500
WHERE AccountID = 201;

SAVEPOINT B;

SELECT AccountID, Balance
FROM ACCOUNT
WHERE AccountID = 201;

ROLLBACK TO A;

SELECT AccountID, Balance
FROM ACCOUNT
WHERE AccountID = 201;

COMMIT;

SET AUTOCOMMIT = 1;



-- PROCEDURES:

-- procedure 1

DELIMITER // 
CREATE PROCEDURE GetCustomerAccounts(IN p_CustomerID INT) 
BEGIN 
    SELECT 
        C.CustomerID, 
        C.First_name, 
        C.Last_name, 
        A.AccountNumber, 
        A.AccountType, 
        A.Balance, 
        A.Status 
    FROM CUSTOMER C 
    JOIN ACCOUNT_HOLDER AH 
    ON C.CustomerID = AH.CustomerID 
    JOIN ACCOUNT A 
    ON AH.AccountID = A.AccountID 
    WHERE C.CustomerID = p_CustomerID; 
END // 
DELIMITER ;

-- Procedure 2;
DELIMITER // CREATE PROCEDURE GetBranchAccountSummary(IN p_BranchID INT) 
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

 -- FUNTIONS

 -- Function 1: 

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


-- Function 2:

DELIMITER //

CREATE FUNCTION GetCustomerTotalBalance(p_CustomerID INT)
RETURNS DECIMAL(10,2)
NOT DETERMINISTIC
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

-- TRIGGERS: 

-- TRIGGER 1: Prevent withdrawals exceeding account balance

DELIMITER //

CREATE TRIGGER BeforeWithdrawalInsert
BEFORE INSERT ON TRANSACTIONS
FOR EACH ROW
BEGIN
    DECLARE current_balance DECIMAL(10,2);

    IF NEW.TransactionType = 'WITHDRAWAL'
       AND NEW.TransactionStatus = 'SUCCESS' THEN

        SELECT Balance
        INTO current_balance
        FROM ACCOUNT
        WHERE AccountID = NEW.AccountID;

        IF current_balance < NEW.Amount THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Insufficient account balance';
        END IF;

    END IF;
END //

DELIMITER ;


-- TRIGGER 2: Update account status when balance changes

DELIMITER //

CREATE TRIGGER AfterAccountBalanceUpdate
AFTER UPDATE ON ACCOUNT
FOR EACH ROW
BEGIN
    IF NEW.Balance <= 0 THEN
        UPDATE ACCOUNT
        SET Status = 'Inactive'
        WHERE AccountID = NEW.AccountID;
    END IF;
END //

DELIMITER ;


