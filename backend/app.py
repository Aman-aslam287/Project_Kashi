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
            "customer_id",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "mobile",
            "email",
            "address",
            "city",
            "account_id",
            "account_number",
            "account_type",
            "branch_id"
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

        allowed_account_types = ["Saving", "Current", "Salary"]

        if data["account_type"] not in allowed_account_types:
            return jsonify({
                "error": "Account type must be Saving, Current, or Salary."
            }), 400

        db = get_db_connection()
        cursor = db.cursor()

        # Start a transaction so all inserts succeed or none do.
        db.start_transaction()

        # 1. Insert the customer.
        cursor.execute("""
            INSERT INTO CUSTOMER (
                CustomerID,
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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURDATE())
        """, (
            int(data["customer_id"]),
            data["first_name"].strip(),
            data["last_name"].strip(),
            data["date_of_birth"],
            data["gender"],
            data["mobile"].strip(),
            data["email"].strip(),
            data["address"].strip(),
            data["city"].strip()
        ))

        # 2. Create the bank account.
        cursor.execute("""
            INSERT INTO ACCOUNT (
                AccountID,
                AccountNumber,
                AccountType,
                OpeningDate,
                Balance,
                Status,
                BranchID
            )
            VALUES (%s, %s, %s, CURDATE(), 0.00, 'Active', %s)
        """, (
            int(data["account_id"]),
            data["account_number"].strip(),
            data["account_type"],
            int(data["branch_id"])
        ))

        # 3. Link the customer to their account.
        cursor.execute("""
            INSERT INTO ACCOUNT_HOLDER (
                CustomerID,
                AccountID,
                HolderSince,
                HolderType
            )
            VALUES (%s, %s, CURDATE(), 'Primary')
        """, (
            int(data["customer_id"]),
            int(data["account_id"])
        ))

        db.commit()

        return jsonify({
            "message": "Customer registered and bank account opened successfully!",
            "customer_id": int(data["customer_id"]),
            "account_id": int(data["account_id"]),
            "account_number": data["account_number"]
        }), 201

    except Exception as e:
        if db is not None and db.is_connected():
            db.rollback()

        app.logger.exception("Account opening failed")

        # Duplicate IDs, invalid branch IDs and other database errors
        # are reported without exposing internal database details.
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

        cursor.execute("""
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
            WHERE C.CustomerID = %s
        """, (customer_id,))

        accounts = cursor.fetchall()

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




@app.route("/api/transactions/deposit", methods=["POST"])
def deposit_money():
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
            return jsonify({"error": "Invalid account_id or amount."}), 400

        if account_id <= 0 or amount <= 0:
            return jsonify({"error": "Account ID and amount must be positive."}), 400

        db = get_db_connection()
        db.start_transaction()
        cursor = db.cursor(dictionary=True)

        # Lock the account row while processing the deposit.
        cursor.execute(
            "SELECT Balance, Status FROM ACCOUNT WHERE AccountID = %s FOR UPDATE",
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
            """
            UPDATE ACCOUNT
            SET Balance = Balance + %s
            WHERE AccountID = %s
            """,
            (amount, account_id)
        )

        cursor.execute(
            """
            INSERT INTO TRANSACTIONS (
                AccountID, TransactionType, Amount, TransactionDate,
                Description, ReferenceNumber, TransactionStatus
            )
            VALUES (%s, 'DEPOSIT', %s, NOW(), %s, %s, 'SUCCESS')
            """,
            (
                account_id,
                amount,
                "Cash deposit",
                f"DEP-{account_id}-{__import__('uuid').uuid4().hex[:12]}"
            )
        )

        transaction_id = cursor.lastrowid

        cursor.execute(
            "SELECT Balance FROM ACCOUNT WHERE AccountID = %s",
            (account_id,)
        )
        updated_account = cursor.fetchone()

        db.commit()

        return jsonify({
            "message": "Deposit successful.",
            "transaction_id": transaction_id,
            "account_id": account_id,
            "deposited_amount": amount,
            "new_balance": float(updated_account["Balance"])
        }), 201

    except Exception:
        if db is not None and db.is_connected():
            db.rollback()

        app.logger.exception("Deposit failed")
        return jsonify({"error": "Deposit failed. No changes were committed."}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()



if __name__ == "__main__":
    app.run(debug=True, port=5000)
