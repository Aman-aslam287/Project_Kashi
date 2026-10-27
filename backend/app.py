import math
import uuid
from flask import Flask, jsonify, request
from flask_cors import CORS
from db import get_db_connection

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return jsonify({
        "message": "Project Kashi Banking API is running!"
    })


@app.route("/api/test-db")
def test_db():
    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("SELECT DATABASE()")
        result = cursor.fetchone()

        return jsonify({
            "message": "Database connection successful!",
            "database": result[0]
        })

    except Exception:
        app.logger.exception("Database test failed")
        return jsonify({
            "error": "Database connection failed"
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()



@app.route("/api/open-account", methods=["POST"])
def open_account():
    db = None
    cursor = None

    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "error": "Please provide customer and account details."
            }), 400

        required_fields = [
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "mobile",
            "email",
            "address",
            "city",
            "account_type",
            "branch_id"
        ]

        missing_fields = [
            field for field in required_fields
            if data.get(field) is None
            or str(data.get(field)).strip() == ""
        ]

        if missing_fields:
            return jsonify({
                "error": "Missing required fields.",
                "fields": missing_fields
            }), 400

        allowed_account_types = ["Saving", "Current", "Salary"]

        if data["account_type"] not in allowed_account_types:
            return jsonify({
                "error": "Account type must be Saving, Current, or Salary."
            }), 400

        try:
            branch_id = int(data["branch_id"])
            if branch_id <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify({
                "error": "Branch ID must be a positive integer."
            }), 400

        db = get_db_connection()
        cursor = db.cursor()

        # All database changes succeed together or are rolled back.
        db.start_transaction()

        # 1. Create the customer. MySQL generates CustomerID.
        cursor.execute("""
            INSERT INTO CUSTOMER (
                First_name,
                Last_name,
                DateOFBirth,
                Gender,
                Mobile,
                Email,
                Address,
                City,
                RegistrationDate
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURDATE())
        """, (
            data["first_name"].strip(),
            data["last_name"].strip(),
            data["date_of_birth"],
            data["gender"].strip(),
            data["mobile"].strip(),
            data["email"].strip(),
            data["address"].strip(),
            data["city"].strip()
        ))

        customer_id = cursor.lastrowid

        # 2. Generate the next account number.
        # Lock account rows during generation to reduce concurrent conflicts.
        cursor.execute("""
            SELECT AccountNumber
            FROM ACCOUNT
            FOR UPDATE
        """)

        account_numbers = [
            row[0] for row in cursor.fetchall()
            if row[0] is not None
        ]

        suffixes = [
            int(number[4:])
            for number in account_numbers
            if number.startswith("KASH")
            and number[4:].isdigit()
        ]

        next_number = max(suffixes, default=100000) + 1
        account_number = f"KASH{next_number:06d}"

        # 3. Create the account. MySQL generates AccountID.
        cursor.execute("""
            INSERT INTO ACCOUNT (
                AccountNumber,
                AccountType,
                OpeningDate,
                Balance,
                Status,
                BranchID
            )
            VALUES (%s, %s, CURDATE(), 0.00, 'Active', %s)
        """, (
            account_number,
            data["account_type"],
            branch_id
        ))

        account_id = cursor.lastrowid

        # 4. Link the customer to the new account.
        cursor.execute("""
            INSERT INTO ACCOUNT_HOLDER (
                CustomerID,
                AccountID,
                HolderSince,
                HolderType
            )
            VALUES (%s, %s, CURDATE(), 'Primary')
        """, (
            customer_id,
            account_id
        ))

        db.commit()

        return jsonify({
            "message": "Customer registered and bank account opened successfully!",
            "customer_id": customer_id,
            "account_id": account_id,
            "account_number": account_number
        }), 201

    except Exception:
        if db is not None and db.is_connected():
            db.rollback()

        app.logger.exception("Account opening failed")

        return jsonify({
            "error": "Could not open account. Check the submitted details and database constraints."
        }), 400

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()






@app.route("/api/customers/<int:customer_id>/accounts", methods=["GET"])
def get_customer_accounts(customer_id):
    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.callproc("GetCustomerAccounts", [customer_id])

        accounts = []
        for result in cursor.stored_results():
            accounts = result.fetchall()

        if not accounts:
            return jsonify({
                "message": "No customer or accounts found for this CustomerID."
            }), 404

        return jsonify({
            "customer_id": customer_id,
            "accounts": accounts
        }), 200

    except Exception:
        app.logger.exception("Failed to retrieve customer accounts")
        return jsonify({
            "error": "Could not retrieve customer accounts."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()



@app.route("/api/deposit", methods=["POST"])
def deposit():
    db = None
    cursor = None

    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Please provide account_id and amount."}), 400

        account_id = data.get("account_id")
        amount = data.get("amount")

        if account_id is None or amount is None:
            return jsonify({"error": "account_id and amount are required."}), 400

        try:
            account_id = int(account_id)
            amount = float(amount)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid account ID or amount."}), 400

        if account_id <= 0 or not math.isfinite(amount) or amount <= 0:
            return jsonify({"error": "Account ID and amount must be valid and positive."}), 400

        # Bank amounts must have at most two decimal places.
        if round(amount, 2) != amount:
            return jsonify({"error": "Amount cannot have more than two decimal places."}), 400

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        db.start_transaction()

        # Lock the account row while processing the deposit.
        cursor.execute(
            "SELECT AccountID, Balance, Status FROM ACCOUNT "
            "WHERE AccountID = %s FOR UPDATE",
            (account_id,)
        )
        account = cursor.fetchone()

        if account is None:
            db.rollback()
            return jsonify({"error": "Account not found."}), 404

        if account["Status"] != "Active":
            db.rollback()
            return jsonify({"error": "This account is not active."}), 400

        cursor.execute(
            "UPDATE ACCOUNT SET Balance = Balance + %s WHERE AccountID = %s",
            (amount, account_id)
        )

        cursor.execute("""
            INSERT INTO TRANSACTIONS (
                AccountID, TransactionType, Amount, TransactionDate,
                Description, ReferenceNumber, TransactionStatus
            )
            VALUES (%s, 'DEPOSIT', %s, CURDATE(),
                    'Cash deposit', %s, 'SUCCESS')
        """, (account_id, amount, f"DEP-{uuid.uuid4().hex[:12].upper()}"))

        transaction_id = cursor.lastrowid

        db.commit()

        return jsonify({
            "message": "Deposit successful.",
            "transaction_id": transaction_id,
            "account_id": account_id,
            "amount": amount
        }), 201

    except Exception:
        if db is not None and db.is_connected():
            db.rollback()

        app.logger.exception("Deposit failed")
        return jsonify({"error": "Deposit failed. Please check the account and try again."}), 400

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()


@app.route("/api/withdraw", methods=["POST"])
def withdraw():
    db = None
    cursor = None

    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Please provide account_id and amount."}), 400

        account_id = data.get("account_id")
        amount = data.get("amount")

        if account_id is None or amount is None:
            return jsonify({"error": "account_id and amount are required."}), 400

        try:
            account_id = int(account_id)
            amount = float(amount)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid account ID or amount."}), 400

        if account_id <= 0 or not math.isfinite(amount) or amount <= 0:
            return jsonify({"error": "Account ID and amount must be valid and positive."}), 400

        if round(amount, 2) != amount:
            return jsonify({"error": "Amount cannot have more than two decimal places."}), 400

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        db.start_transaction()

        cursor.execute(
            "SELECT AccountID, Balance, Status FROM ACCOUNT "
            "WHERE AccountID = %s FOR UPDATE",
            (account_id,)
        )
        account = cursor.fetchone()

        if account is None:
            db.rollback()
            return jsonify({"error": "Account not found."}), 404

        if account["Status"] != "Active":
            db.rollback()
            return jsonify({"error": "This account is not active."}), 400

        if account["Balance"] is None or float(account["Balance"]) < amount:
            db.rollback()
            return jsonify({"error": "Insufficient balance."}), 400

        cursor.execute(
            "UPDATE ACCOUNT SET Balance = Balance - %s WHERE AccountID = %s",
            (amount, account_id)
        )

        cursor.execute("""
            INSERT INTO TRANSACTIONS (
                AccountID, TransactionType, Amount, TransactionDate,
                Description, ReferenceNumber, TransactionStatus
            )
            VALUES (%s, 'WITHDRAWAL', %s, CURDATE(),
                    'Cash withdrawal', %s, 'SUCCESS')
        """, (account_id, amount, f"WDR-{uuid.uuid4().hex[:12].upper()}"))

        transaction_id = cursor.lastrowid

        db.commit()

        return jsonify({
            "message": "Withdrawal successful.",
            "transaction_id": transaction_id,
            "account_id": account_id,
            "amount": amount
        }), 201

    except Exception:
        if db is not None and db.is_connected():
            db.rollback()

        app.logger.exception("Withdrawal failed")
        return jsonify({"error": "Withdrawal failed. Please check the account and try again."}), 400

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()



@app.route("/api/accounts/<int:account_id>/transactions", methods=["GET"])
def get_transaction_history(account_id):
    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Check whether the account exists.
        cursor.execute(
            "SELECT AccountID FROM ACCOUNT WHERE AccountID = %s",
            (account_id,)
        )

        if cursor.fetchone() is None:
            return jsonify({"error": "Account not found."}), 404

        # Retrieve the account's transaction history.
        cursor.execute("""
            SELECT
                TransactionID,
                AccountID,
                TransactionType,
                Amount,
                TransactionDate,
                Description,
                ReferenceNumber,
                TransactionStatus
            FROM TRANSACTIONS
            WHERE AccountID = %s
            ORDER BY TransactionID DESC
        """, (account_id,))

        transactions = cursor.fetchall()

        # Convert dates and decimal amounts into JSON-friendly values.
        for transaction in transactions:
            if transaction["TransactionDate"] is not None:
                transaction["TransactionDate"] = (
                    transaction["TransactionDate"].isoformat()
                )

            if transaction["Amount"] is not None:
                transaction["Amount"] = float(transaction["Amount"])

        return jsonify({
            "account_id": account_id,
            "total_transactions": len(transactions),
            "transactions": transactions
        }), 200

    except Exception:
        app.logger.exception("Transaction history retrieval failed")
        return jsonify({"error": "Could not retrieve transaction history."}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()


@app.route("/api/transfer", methods=["POST"])
def transfer():
    db = None
    cursor = None

    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "error": "Please provide from_account_id, to_account_id and amount."
            }), 400

        from_id = data.get("from_account_id")
        to_id = data.get("to_account_id")
        amount = data.get("amount")

        if from_id is None or to_id is None or amount is None:
            return jsonify({
                "error": "All three fields are required."
            }), 400

        try:
            from_id = int(from_id)
            to_id = int(to_id)
            amount = float(amount)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid account ID or amount."}), 400

        if from_id <= 0 or to_id <= 0:
            return jsonify({"error": "Account IDs must be positive."}), 400

        if from_id == to_id:
            return jsonify({
                "error": "Source and destination accounts must be different."
            }), 400

        if not math.isfinite(amount) or amount <= 0:
            return jsonify({"error": "Amount must be positive and valid."}), 400

        if round(amount, 2) != amount:
            return jsonify({
                "error": "Amount cannot have more than two decimal places."
            }), 400

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        db.start_transaction()

        # Lock both accounts in a consistent order.
        account_ids = sorted([from_id, to_id])

        cursor.execute("""
            SELECT AccountID, Balance, Status
            FROM ACCOUNT
            WHERE AccountID IN (%s, %s)
            ORDER BY AccountID
            FOR UPDATE
        """, (account_ids[0], account_ids[1]))

        accounts = {row["AccountID"]: row for row in cursor.fetchall()}

        if from_id not in accounts or to_id not in accounts:
            db.rollback()
            return jsonify({"error": "One or both accounts were not found."}), 404

        sender = accounts[from_id]
        recipient = accounts[to_id]

        if sender["Status"] != "Active" or recipient["Status"] != "Active":
            db.rollback()
            return jsonify({"error": "Both accounts must be active."}), 400

        if sender["Balance"] is None or float(sender["Balance"]) < amount:
            db.rollback()
            return jsonify({"error": "Insufficient balance."}), 400

        # Update both account balances.
        cursor.execute(
            "UPDATE ACCOUNT SET Balance = Balance - %s WHERE AccountID = %s",
            (amount, from_id)
        )

        cursor.execute(
            "UPDATE ACCOUNT SET Balance = Balance + %s WHERE AccountID = %s",
            (amount, to_id)
        )

        reference = f"TRF-{uuid.uuid4().hex[:12].upper()}"

        # Record the sender's debit.
        cursor.execute("""
            INSERT INTO TRANSACTIONS (
                AccountID, TransactionType, Amount, TransactionDate,
                Description, ReferenceNumber, TransactionStatus
            )
            VALUES (%s, 'TRANSFER_OUT', %s, CURDATE(),
                    %s, %s, 'SUCCESS')
        """, (
            from_id,
            amount,
            f"Transfer to account {to_id}",
            reference
        ))

        # Record the recipient's credit.
        cursor.execute("""
            INSERT INTO TRANSACTIONS (
                AccountID, TransactionType, Amount, TransactionDate,
                Description, ReferenceNumber, TransactionStatus
            )
            VALUES (%s, 'TRANSFER_IN', %s, CURDATE(),
                    %s, %s, 'SUCCESS')
        """, (
            to_id,
            amount,
            f"Transfer from account {from_id}",
            reference
        ))

        db.commit()

        return jsonify({
            "message": "Transfer successful.",
            "from_account_id": from_id,
            "to_account_id": to_id,
            "amount": amount,
            "reference_number": reference
        }), 201

    except Exception:
        if db is not None and db.is_connected():
            db.rollback()

        app.logger.exception("Transfer failed")
        return jsonify({"error": "Transfer failed. Please try again."}), 400

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()


@app.route("/api/accounts", methods=["GET"])
def get_all_accounts():
    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
    SELECT
        AccountID,
        AccountNumber,
        AccountType,
        OpeningDate,
        Balance,
        Status,
        BranchID
    FROM CustomerAccountDetails
    ORDER BY AccountID
""")

        accounts = cursor.fetchall()

        for account in accounts:
            if account["OpeningDate"] is not None:
                account["OpeningDate"] = account["OpeningDate"].isoformat()

            if account["Balance"] is not None:
                account["Balance"] = float(account["Balance"])

        return jsonify({
            "total_accounts": len(accounts),
            "accounts": accounts
        }), 200

    except Exception:
        app.logger.exception("Account retrieval failed")
        return jsonify({"error": "Could not retrieve accounts."}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()


@app.route("/api/loans", methods=["GET"])
def get_loans():
    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                L.LoanID,
                L.CustomerID,
                CONCAT(C.First_name, ' ', C.Last_name) AS CustomerName,
                L.BranchID,
                L.LoanType,
                L.LoanAmount,
                L.InterestRate,
                L.StartDate,
                L.TenureMonths,
                L.LoanStatus
            FROM LOAN L
            JOIN CUSTOMER C ON L.CustomerID = C.CustomerID
            ORDER BY L.LoanID
        """)

        loans = cursor.fetchall()

        for loan in loans:
            if loan["StartDate"] is not None:
                loan["StartDate"] = loan["StartDate"].isoformat()

            if loan["LoanAmount"] is not None:
                loan["LoanAmount"] = float(loan["LoanAmount"])

            if loan["InterestRate"] is not None:
                loan["InterestRate"] = float(loan["InterestRate"])

        return jsonify({
            "total_loans": len(loans),
            "loans": loans
        }), 200

    except Exception:
        app.logger.exception("Loan retrieval failed")
        return jsonify({"error": "Could not retrieve loans."}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()


@app.route("/api/loans", methods=["POST"])
def create_loan():
    db = None
    cursor = None

    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Please provide loan details."}), 400

        required_fields = [
            "customer_id",
            "branch_id",
            "loan_type",
            "loan_amount",
            "interest_rate",
            "start_date",
            "tenure_months"
        ]

        missing_fields = [
            field for field in required_fields
            if data.get(field) is None or str(data.get(field)).strip() == ""
        ]

        if missing_fields:
            return jsonify({
                "error": "Missing required fields.",
                "fields": missing_fields
            }), 400

        try:
            customer_id = int(data["customer_id"])
            branch_id = int(data["branch_id"])
            loan_amount = float(data["loan_amount"])
            interest_rate = float(data["interest_rate"])
            tenure_months = int(data["tenure_months"])
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid loan details."}), 400

        if customer_id <= 0 or branch_id <= 0 or tenure_months <= 0:
            return jsonify({
                "error": "Customer ID, branch ID and tenure must be positive."
            }), 400

        if not math.isfinite(loan_amount) or loan_amount <= 0:
            return jsonify({"error": "Loan amount must be positive."}), 400

        if not math.isfinite(interest_rate) or not 0 <= interest_rate <= 100:
            return jsonify({
                "error": "Interest rate must be between 0 and 100."
            }), 400

        if round(loan_amount, 2) != loan_amount:
            return jsonify({
                "error": "Loan amount cannot have more than two decimal places."
            }), 400

        if round(interest_rate, 2) != interest_rate:
            return jsonify({
                "error": "Interest rate cannot have more than two decimal places."
            }), 400

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            "SELECT CustomerID FROM CUSTOMER WHERE CustomerID = %s",
            (customer_id,)
        )
        if cursor.fetchone() is None:
            return jsonify({"error": "Customer not found."}), 404

        cursor.execute(
            "SELECT BranchID FROM BRANCH WHERE BranchID = %s",
            (branch_id,)
        )
        if cursor.fetchone() is None:
            return jsonify({"error": "Branch not found."}), 404

        cursor.execute("""
            INSERT INTO LOAN (
                CustomerID,
                BranchID,
                LoanType,
                LoanAmount,
                InterestRate,
                StartDate,
                TenureMonths,
                LoanStatus
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Active')
        """, (
            customer_id,
            branch_id,
            str(data["loan_type"]).strip(),
            loan_amount,
            interest_rate,
            data["start_date"],
            tenure_months
        ))

        loan_id = cursor.lastrowid
        db.commit()

        return jsonify({
            "message": "Loan registered successfully.",
            "loan_id": loan_id
        }), 201

    except Exception:
        if db is not None and db.is_connected():
            db.rollback()

        app.logger.exception("Loan registration failed")
        return jsonify({
            "error": "Could not register loan. Check the submitted details."
        }), 400

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()


@app.route("/api/loans/<int:loan_id>/payments", methods=["GET"])
def get_loan_payments(loan_id):
    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT LoanID FROM LOAN WHERE LoanID = %s",
            (loan_id,)
        )
        if cursor.fetchone() is None:
            return jsonify({"error": "Loan not found."}), 404

        cursor.execute("""
            SELECT
                PaymentID,
                LoanID,
                PaymentDate,
                Amount,
                PaymentMode,
                ReferenceNumber
            FROM LOAN_PAYMENT
            WHERE LoanID = %s
            ORDER BY PaymentDate DESC, PaymentID DESC
        """, (loan_id,))

        payments = cursor.fetchall()

        for payment in payments:
            if payment["PaymentDate"] is not None:
                payment["PaymentDate"] = payment["PaymentDate"].isoformat()

            if payment["Amount"] is not None:
                payment["Amount"] = float(payment["Amount"])

        return jsonify({
            "loan_id": loan_id,
            "total_payments": len(payments),
            "payments": payments
        }), 200

    except Exception:
        app.logger.exception("Loan payment retrieval failed")
        return jsonify({"error": "Could not retrieve loan payments."}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()



@app.route("/api/loans/<int:loan_id>/payments", methods=["POST"])
def record_loan_payment(loan_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "Payment details are required"}), 400

    db = None
    cursor = None

    try:
        amount = float(data.get("amount", 0))
        payment_date = data.get("payment_date")
        payment_mode = data.get("payment_mode")

        if amount <= 0:
            return jsonify({
                "error": "Payment amount must be greater than zero"
            }), 400

        if not payment_date or not payment_mode:
            return jsonify({
                "error": "Payment date and payment mode are required"
            }), 400

        # Establish the database connection
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Verify that the loan exists
        cursor.execute(
            "SELECT LoanID FROM LOAN WHERE LoanID = %s",
            (loan_id,)
        )

        if not cursor.fetchone():
            return jsonify({"error": "Loan not found"}), 404

        # Insert the payment
        cursor.execute(
            """
            INSERT INTO LOAN_PAYMENT
                (LoanID, PaymentDate, Amount, PaymentMode, ReferenceNumber)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (loan_id, payment_date, amount, payment_mode, None)
        )

        payment_id = cursor.lastrowid
        reference_number = f"KASH-PAY-{payment_id:05d}"

        # Generate the payment reference number
        cursor.execute(
            """
            UPDATE LOAN_PAYMENT
            SET ReferenceNumber = %s
            WHERE PaymentID = %s
            """,
            (reference_number, payment_id)
        )

        db.commit()

        return jsonify({
            "message": "Loan payment recorded successfully",
            "payment_id": payment_id,
            "loan_id": loan_id,
            "reference_number": reference_number
        }), 201

    except Exception as error:
        if db is not None:
            db.rollback()

        app.logger.exception("Failed to record loan payment")
        return jsonify({"error": str(error)}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None:
            db.close()


@app.route("/api/customers/<int:customer_id>/accounts-procedure")
def get_customer_accounts_procedure(customer_id):
    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.callproc("GetCustomerAccounts", [customer_id])

        accounts = []
        for result in cursor.stored_results():
            accounts = result.fetchall()

        if not accounts:
            return jsonify({"message": "No accounts found."}), 404

        return jsonify({
            "customer_id": customer_id,
            "accounts": accounts
        }), 200

    except Exception:
        app.logger.exception("Stored procedure call failed")
        return jsonify({"error": "Could not retrieve customer accounts."}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if db is not None and db.is_connected():
            db.close()



@app.route("/api/customers/<int:customer_id>/total-balance", methods=["GET"])
def get_customer_total_balance(customer_id):
    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT GetCustomerTotalBalance(%s) AS TotalBalance",
            (customer_id,)
        )

        result = cursor.fetchone()

        return jsonify({
            "customer_id": customer_id,
            "total_balance": result["TotalBalance"]
        }), 200

    except Exception:
        app.logger.exception("Failed to calculate customer total balance")
        return jsonify({
            "error": "Could not calculate customer total balance."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()




@app.route("/api/customer-account-details", methods=["GET"])
def get_customer_account_details():
    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM CustomerAccountDetails
        """)

        details = cursor.fetchall()

        return jsonify({
            "customer_account_details": details
        }), 200

    except Exception:
        app.logger.exception("Failed to retrieve customer account details")
        return jsonify({
            "error": "Could not retrieve customer account details."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()




@app.route("/api/loans/<int:loan_id>/interest", methods=["GET"])
def get_loan_interest(loan_id):
    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                LoanID,
                LoanAmount,
                InterestRate,
                TenureMonths
            FROM LOAN
            WHERE LoanID = %s
        """, (loan_id,))

        loan = cursor.fetchone()

        if loan is None:
            return jsonify({"error": "Loan not found."}), 404

        tenure_years = loan["TenureMonths"] / 12

        cursor.execute("""
            SELECT CalcLoanInterest(%s, %s, %s) AS EstimatedInterest
        """, (
            loan["LoanAmount"],
            loan["InterestRate"],
            tenure_years
        ))

        result = cursor.fetchone()

        return jsonify({
            "loan_id": loan_id,
            "loan_amount": loan["LoanAmount"],
            "interest_rate": loan["InterestRate"],
            "tenure_months": loan["TenureMonths"],
            "estimated_interest": result["EstimatedInterest"]
        }), 200

    except Exception:
        app.logger.exception("Failed to calculate loan interest")
        return jsonify({
            "error": "Could not calculate loan interest."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if db is not None and db.is_connected():
            db.close()



@app.route("/api/branch-account-summary", methods=["GET"])
def get_branch_account_summary():
    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM BranchAccountSummary")
        summaries = cursor.fetchall()

        return jsonify({
            "branch_account_summary": summaries
        }), 200

    except Exception:
        app.logger.exception("Failed to retrieve branch account summary")
        return jsonify({
            "error": "Could not retrieve branch account summary."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if db is not None and db.is_connected():
            db.close()



@app.route("/api/branches/<int:branch_id>/account-summary", methods=["GET"])
def get_branch_account_summary_procedure(branch_id):
    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.callproc("GetBranchAccountSummary", [branch_id])

        summaries = []
        for result in cursor.stored_results():
            summaries = result.fetchall()

        if not summaries:
            return jsonify({
                "message": "No summary found for this branch.",
                "branch_id": branch_id
            }), 404

        return jsonify({
            "branch_account_summary": summaries
        }), 200

    except Exception:
        app.logger.exception("Branch summary procedure failed")
        return jsonify({
            "error": "Could not retrieve branch summary."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
