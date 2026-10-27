
const API = "http://127.0.0.1:5000";

const messageBox = document.getElementById("message");

function showMessage(message, success = true) {
    if (!messageBox) {
        alert(message);
        return;
    }

    messageBox.textContent = message;
    messageBox.className = success
        ? "message success"
        : "message error";
    messageBox.hidden = false;

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}

async function apiRequest(path, options = {}) {
    let response;

    try {
        response = await fetch(`${API}${path}`, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...options.headers
            }
        });
    } catch {
        throw new Error(
            "Cannot connect to Flask. Make sure the backend is running."
        );
    }

    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error("The server returned an invalid response.");
    }

    if (!response.ok) {
        throw new Error(
            data.error ||
            data.message ||
            "The request failed."
        );
    }

    return data;
}

function resetForm(form) {
    HTMLFormElement.prototype.reset.call(form);
}

function handleForm(formId, action) {
    const form = document.getElementById(formId);

    if (!form) return;

    form.addEventListener("submit", async event => {
        event.preventDefault();

        const button = form.querySelector('button[type="submit"]');

        if (button) button.disabled = true;

        try {
            await action(new FormData(form));
        } catch (error) {
            showMessage(error.message, false);
        } finally {
            if (button) button.disabled = false;
        }
    });
}

document.querySelectorAll(".back-button").forEach(button => {
    button.addEventListener("click", event => {
        event.preventDefault();

        const previousPage = document.referrer;

        if (previousPage) {
            try {
                const previousURL = new URL(previousPage);

                if (
                    previousURL.origin === window.location.origin &&
                    previousURL.pathname !== window.location.pathname
                ) {
                    window.history.back();
                    return;
                }
            } catch {
                // Fall back to the homepage.
            }
        }

        window.location.href = "index.html";
    });
});

async function loadAccounts() {
    const table = document.getElementById("accountsTable");

    if (!table) return;

    table.innerHTML = `
        <tr>
            <td colspan="7">Loading accounts...</td>
        </tr>
    `;

    try {
        const data = await apiRequest("/api/accounts");

        if (!Array.isArray(data.accounts)) {
            throw new Error("Unexpected account data from the server.");
        }

        if (data.accounts.length === 0) {
            table.innerHTML = `
                <tr>
                    <td colspan="7">No accounts found.</td>
                </tr>
            `;
            return;
        }

        table.innerHTML = data.accounts.map(account => `
            <tr>
                <td>${escapeLoanHTML(account.AccountID)}</td>
                <td>${escapeLoanHTML(account.AccountNumber)}</td>
                <td>${escapeLoanHTML(account.AccountType)}</td>
                <td>${escapeLoanHTML(account.OpeningDate)}</td>
                <td>₹${Number(account.Balance ?? 0).toFixed(2)}</td>
                <td>${escapeLoanHTML(account.Status)}</td>
                <td>${escapeLoanHTML(account.BranchID)}</td>
            </tr>
        `).join("");
    } catch (error) {
        console.error("Failed to load accounts:", error);

        table.innerHTML = `
            <tr>
                <td colspan="7">Could not load accounts.</td>
            </tr>
        `;

        showMessage(error.message, false);
    }
}

const refreshButton = document.getElementById("refreshAccounts");

if (refreshButton) {
    refreshButton.addEventListener("click", loadAccounts);
}

handleForm("openAccountForm", async form => {
    const data = Object.fromEntries(form.entries());

    data.branch_id = Number(data.branch_id);

    const result = await apiRequest("/api/open-account", {
        method: "POST",
        body: JSON.stringify(data)
    });

    showMessage(
        `${result.message} Customer ID: ${result.customer_id}. ` +
        `Account ID: ${result.account_id}. ` +
        `Account Number: ${result.account_number}`
    );

    resetForm(document.getElementById("openAccountForm"));
    await loadAccounts();
});

handleForm("depositForm", async form => {
    const result = await apiRequest("/api/deposit", {
        method: "POST",
        body: JSON.stringify({
            account_id: Number(form.get("deposit_account")),
            amount: Number(form.get("deposit_amount"))
        })
    });

    showMessage(
        `Deposit successful! Transaction ID: ${result.transaction_id}`
    );

    resetForm(document.getElementById("depositForm"));
    await loadAccounts();
});

handleForm("withdrawForm", async form => {
    const result = await apiRequest("/api/withdraw", {
        method: "POST",
        body: JSON.stringify({
            account_id: Number(form.get("withdraw_account")),
            amount: Number(form.get("withdraw_amount"))
        })
    });

    showMessage(
        `Withdrawal successful! Transaction ID: ${result.transaction_id}`
    );

    resetForm(document.getElementById("withdrawForm"));
    await loadAccounts();
});

handleForm("transferForm", async form => {
    const result = await apiRequest("/api/transfer", {
        method: "POST",
        body: JSON.stringify({
            from_account_id: Number(form.get("from_account")),
            to_account_id: Number(form.get("to_account")),
            amount: Number(form.get("transfer_amount"))
        })
    });

    showMessage(
        `${result.message} Reference: ${result.reference_number}`
    );

    resetForm(document.getElementById("transferForm"));
    await loadAccounts();
});

handleForm("historyForm", async form => {
    const accountId = Number(form.get("history_account"));

    const result = await apiRequest(
        `/api/accounts/${accountId}/transactions`
    );

    const table = document.getElementById("historyTable");

    if (!table) {
        throw new Error("The transaction history table is missing.");
    }

    if (!Array.isArray(result.transactions)) {
        throw new Error("Unexpected transaction data from the server.");
    }

    if (result.transactions.length === 0) {
        table.innerHTML = `
            <tr>
                <td colspan="6">No transactions found.</td>
            </tr>
        `;

        showMessage("No transaction records were found for this account.");
        return;
    }

    table.innerHTML = result.transactions.map(transaction => `
        <tr>
            <td>${escapeLoanHTML(transaction.TransactionID)}</td>
            <td>${escapeLoanHTML(transaction.TransactionType)}</td>
            <td>₹${Number(transaction.Amount ?? 0).toFixed(2)}</td>
            <td>${escapeLoanHTML(transaction.TransactionDate)}</td>
            <td>${escapeLoanHTML(transaction.Description)}</td>
            <td>${escapeLoanHTML(transaction.TransactionStatus)}</td>
        </tr>
    `).join("");

    showMessage(
        `Loaded ${result.total_transactions} transaction record(s).`
    );
});

loadAccounts();

function escapeLoanHTML(value) {
    return String(value ?? "—").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

function formatLoanAmount(amount) {
    return Number(amount ?? 0).toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function getLoanValue(loan, upperKey, lowerKey) {
    return loan[upperKey] ?? loan[lowerKey] ?? "—";
}

// NEW: Uses the existing Flask endpoint backed by CalcLoanInterest.
async function getEstimatedLoanInterest(loanId) {
    try {
        const result = await apiRequest(
            `/api/loans/${encodeURIComponent(loanId)}/interest`
        );

        return (
            result.estimated_interest ??
            result.EstimatedInterest ??
            result.estimatedInterest ??
            result.interest_amount ??
            result.InterestAmount ??
            result.interest ??
            result.Interest ??
            null
        );
    } catch (error) {
        console.error(
            `Could not calculate interest for loan ${loanId}:`,
            error
        );

        return null;
    }
}

// NEW: Adds calculated interest to each loan without changing the original loan API.
async function addEstimatedInterest(loans) {
    return Promise.all(
        loans.map(async loan => {
            const loanId = getLoanValue(loan, "LoanID", "loan_id");
            const estimatedInterest =
                await getEstimatedLoanInterest(loanId);

            return {
                ...loan,
                estimatedInterest
            };
        })
    );
}

function renderEstimatedInterest(loan) {
    if (loan.estimatedInterest == null) {
        return "—";
    }

    return `₹${formatLoanAmount(loan.estimatedInterest)}`;
}

async function loadLoansDashboard() {
    const tableBody = document.getElementById("loanTableBody");

    if (!tableBody) return;

    const loadingMessage = document.getElementById("loadingMessage");
    const errorMessage = document.getElementById("errorMessage");

    try {
        if (loadingMessage) loadingMessage.hidden = false;
        if (errorMessage) errorMessage.hidden = true;

        const data = await apiRequest("/api/loans");
        const loans = data.loans || [];

        const totalElement = document.getElementById("totalLoans");
        const activeElement = document.getElementById("activeLoans");
        const closedElement = document.getElementById("closedLoans");

        if (totalElement) {
            totalElement.textContent = data.total_loans ?? loans.length;
        }

        if (activeElement) {
            activeElement.textContent = loans.filter(loan =>
                String(getLoanValue(loan, "LoanStatus", "loan_status"))
                    .toLowerCase() === "active"
            ).length;
        }

        if (closedElement) {
            closedElement.textContent = loans.filter(loan =>
                String(getLoanValue(loan, "LoanStatus", "loan_status"))
                    .toLowerCase() === "closed"
            ).length;
        }

        if (loans.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="8">No loans found.</td>
                </tr>
            `;
            return;
        }

        const loansWithInterest = await addEstimatedInterest(loans);

        tableBody.innerHTML = loansWithInterest.map(loan => `
            <tr>
                <td>${escapeLoanHTML(getLoanValue(loan, "LoanID", "loan_id"))}</td>
                <td>${escapeLoanHTML(getLoanValue(loan, "CustomerName", "customer_name"))}</td>
                <td>${escapeLoanHTML(getLoanValue(loan, "LoanType", "loan_type"))}</td>
                <td>₹${formatLoanAmount(getLoanValue(loan, "LoanAmount", "loan_amount"))}</td>
                <td>${escapeLoanHTML(getLoanValue(loan, "InterestRate", "interest_rate"))}%</td>
                <td>${escapeLoanHTML(getLoanValue(loan, "TenureMonths", "tenure_months"))} months</td>
                <td>${escapeLoanHTML(renderEstimatedInterest(loan))}</td>
                <td>${escapeLoanHTML(getLoanValue(loan, "LoanStatus", "loan_status"))}</td>
            </tr>
        `).join("");
    } catch (error) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8">Unable to load loan records.</td>
            </tr>
        `;

        if (errorMessage) {
            errorMessage.textContent = error.message;
            errorMessage.hidden = false;
        } else {
            console.error("Failed to load loans:", error);
        }
    } finally {
        if (loadingMessage) loadingMessage.hidden = true;
    }
}

loadLoansDashboard();

async function loadManagementLoans() {
    const tableBody = document.getElementById("managementLoanTableBody");

    if (!tableBody) return;

    const message = document.getElementById("loanListMessage");

    try {
        if (message) message.hidden = true;

        tableBody.innerHTML = `
            <tr>
                <td colspan="9">Loading loans...</td>
            </tr>
        `;

        const data = await apiRequest("/api/loans");
        const loans = data.loans || [];

        if (loans.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="9">No loans found.</td>
                </tr>
            `;
            return;
        }

        const loansWithInterest = await addEstimatedInterest(loans);

        tableBody.innerHTML = loansWithInterest.map(loan => `
            <tr>
                <td>${escapeLoanHTML(getLoanValue(loan, "LoanID", "loan_id"))}</td>
                <td>${escapeLoanHTML(getLoanValue(loan, "CustomerName", "customer_name"))}</td>
                <td>${escapeLoanHTML(getLoanValue(loan, "BranchID", "branch_id"))}</td>
                <td>${escapeLoanHTML(getLoanValue(loan, "LoanType", "loan_type"))}</td>
                <td>₹${formatLoanAmount(getLoanValue(loan, "LoanAmount", "loan_amount"))}</td>
                <td>${escapeLoanHTML(getLoanValue(loan, "InterestRate", "interest_rate"))}%</td>
                <td>${escapeLoanHTML(getLoanValue(loan, "TenureMonths", "tenure_months"))} months</td>
                <td>${escapeLoanHTML(renderEstimatedInterest(loan))}</td>
                <td>${escapeLoanHTML(getLoanValue(loan, "LoanStatus", "loan_status"))}</td>
            </tr>
        `).join("");
    } catch (error) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="9">Could not load loans.</td>
            </tr>
        `;

        if (message) {
            message.textContent = error.message;
            message.hidden = false;
        } else {
            console.error("Failed to load loan records:", error);
        }
    }
}

const loanForm = document.getElementById("loanForm");

if (loanForm) {
    loanForm.addEventListener("submit", async event => {
        event.preventDefault();

        const message = document.getElementById("loanMessage");
        const submitButton = loanForm.querySelector('button[type="submit"]');

        const payload = {
            customer_id: Number(document.getElementById("customerId").value),
            branch_id: Number(document.getElementById("branchId").value),
            loan_type: document.getElementById("loanType").value,
            loan_amount: Number(document.getElementById("loanAmount").value),
            interest_rate: Number(document.getElementById("interestRate").value),
            start_date: document.getElementById("startDate").value,
            tenure_months: Number(document.getElementById("tenureMonths").value)
        };

        if (message) message.hidden = true;

        if (
            !Number.isInteger(payload.customer_id) ||
            payload.customer_id <= 0 ||
            !Number.isInteger(payload.branch_id) ||
            payload.branch_id <= 0 ||
            !payload.loan_type ||
            !payload.start_date ||
            !Number.isFinite(payload.loan_amount) ||
            payload.loan_amount <= 0 ||
            !Number.isFinite(payload.interest_rate) ||
            payload.interest_rate < 0 ||
            payload.interest_rate > 100 ||
            !Number.isInteger(payload.tenure_months) ||
            payload.tenure_months <= 0
        ) {
            if (message) {
                message.textContent = "Please enter valid loan details.";
                message.className = "message error";
                message.hidden = false;
            } else {
                alert("Please enter valid loan details.");
            }
            return;
        }

        try {
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = "Registering...";
            }

            const result = await apiRequest("/api/loans", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            if (message) {
                message.textContent =
                    result.message || "Loan registered successfully.";
                message.className = "message success";
                message.hidden = false;
            } else {
                alert(result.message || "Loan registered successfully.");
            }

            resetForm(loanForm);
            await loadManagementLoans();
        } catch (error) {
            if (message) {
                message.textContent = error.message;
                message.className = "message error";
                message.hidden = false;
            } else {
                alert(error.message);
            }
        } finally {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = "Register Loan";
            }
        }
    });
}

const refreshLoansButton = document.getElementById("refreshLoansButton");

if (refreshLoansButton) {
    refreshLoansButton.addEventListener("click", loadManagementLoans);
}

loadManagementLoans();

const loanPaymentForm = document.getElementById("loanPaymentForm");
const paymentHistoryForm = document.getElementById("paymentHistoryForm");

function showPaymentMessage(elementId, message, success = true) {
    const element = document.getElementById(elementId);

    if (!element) {
        alert(message);
        return;
    }

    element.textContent = message;
    element.className = success ? "message success" : "message error";
    element.hidden = false;
}

function formatPaymentAmount(amount) {
    const value = Number(amount);

    if (!Number.isFinite(value)) {
        return `₹${String(amount ?? "0")}`;
    }

    return `₹${value.toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    })}`;
}

function escapePaymentHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

function getPaymentValue(payment, keys) {
    for (const key of keys) {
        if (payment[key] !== undefined && payment[key] !== null) {
            return payment[key];
        }
    }

    return "";
}

async function loadLoanPayments(loanId) {
    const tableBody = document.getElementById("loanPaymentTableBody");

    if (!tableBody) return;

    tableBody.innerHTML = `
        <tr>
            <td colspan="6">Loading payments...</td>
        </tr>
    `;

    try {
        const result = await apiRequest(
            `/api/loans/${encodeURIComponent(loanId)}/payments`
        );

        const payments = Array.isArray(result)
            ? result
            : result.payments ?? result.data ?? [];

        if (!Array.isArray(payments)) {
            throw new Error("Unexpected payment data from the server.");
        }

        if (payments.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6">No payments found for this loan.</td>
                </tr>
            `;

            showPaymentMessage(
                "paymentHistoryMessage",
                "No payments have been recorded for this loan."
            );
            return;
        }

        tableBody.innerHTML = payments.map(payment => {
            const paymentId = getPaymentValue(payment, [
                "PaymentID", "payment_id", "paymentId"
            ]);

            const loanIdValue = getPaymentValue(payment, [
                "LoanID", "loan_id", "loanId"
            ]);

            const paymentDate = getPaymentValue(payment, [
                "PaymentDate", "payment_date", "paymentDate"
            ]);

            const amount = getPaymentValue(payment, [
                "Amount", "amount"
            ]);

            const mode = getPaymentValue(payment, [
                "PaymentMode", "payment_mode", "paymentMode"
            ]);

            const reference = getPaymentValue(payment, [
                "ReferenceNumber", "reference_number", "referenceNumber"
            ]);

            return `
                <tr>
                    <td>${escapePaymentHTML(paymentId)}</td>
                    <td>${escapePaymentHTML(loanIdValue)}</td>
                    <td>${escapePaymentHTML(String(paymentDate).slice(0, 10))}</td>
                    <td>${escapePaymentHTML(formatPaymentAmount(amount))}</td>
                    <td>${escapePaymentHTML(mode)}</td>
                    <td>${escapePaymentHTML(reference || "—")}</td>
                </tr>
            `;
        }).join("");

        showPaymentMessage(
            "paymentHistoryMessage",
            `Loaded ${payments.length} payment(s) for Loan ID ${loanId}.`
        );
    } catch (error) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6">Unable to load payment history.</td>
            </tr>
        `;

        showPaymentMessage(
            "paymentHistoryMessage",
            error.message || "Failed to load payments.",
            false
        );
    }
}

if (loanPaymentForm) {
    const dateInput = document.getElementById("paymentDate");

    function setPaymentDateToToday() {
        if (!dateInput) return;

        const today = new Date();

        dateInput.value = new Date(
            today.getTime() - today.getTimezoneOffset() * 60000
        ).toISOString().slice(0, 10);
    }

    if (dateInput && !dateInput.value) {
        setPaymentDateToToday();
    }

    loanPaymentForm.addEventListener("submit", async event => {
        event.preventDefault();

        const loanId = document.getElementById("paymentLoanId").value.trim();
        const amount = Number(
            document.getElementById("paymentAmount").value
        );
        const paymentDate = document.getElementById("paymentDate").value;
        const paymentMode = document.getElementById("paymentMode").value;

        if (
            !loanId ||
            !Number.isInteger(Number(loanId)) ||
            Number(loanId) < 1
        ) {
            showPaymentMessage(
                "paymentFormMessage",
                "Enter a valid loan ID.",
                false
            );
            return;
        }

        if (!Number.isFinite(amount) || amount <= 0) {
            showPaymentMessage(
                "paymentFormMessage",
                "Payment amount must be greater than zero.",
                false
            );
            return;
        }

        if (!paymentDate || !paymentMode) {
            showPaymentMessage(
                "paymentFormMessage",
                "Please complete the required payment fields.",
                false
            );
            return;
        }

        const submitButton = loanPaymentForm.querySelector(
            'button[type="submit"]'
        );

        try {
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = "Recording...";
            }

            const result = await apiRequest(
                `/api/loans/${encodeURIComponent(loanId)}/payments`,
                {
                    method: "POST",
                    body: JSON.stringify({
                        amount,
                        payment_date: paymentDate,
                        payment_mode: paymentMode
                    })
                }
            );

            const referenceNumber =
                result.reference_number || result.ReferenceNumber;

            showPaymentMessage(
                "paymentFormMessage",
                `${result.message || "Payment recorded successfully."}` +
                (referenceNumber ? ` Reference: ${referenceNumber}` : "")
            );

            const historyLoanId = document.getElementById("historyLoanId");

            if (historyLoanId) {
                historyLoanId.value = loanId;
            }

            resetForm(loanPaymentForm);
            setPaymentDateToToday();

            await loadLoanPayments(loanId);
        } catch (error) {
            showPaymentMessage(
                "paymentFormMessage",
                error.message || "Failed to record the payment.",
                false
            );
        } finally {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = "Record Payment";
            }
        }
    });
}

if (paymentHistoryForm) {
    paymentHistoryForm.addEventListener("submit", async event => {
        event.preventDefault();

        const loanId = document.getElementById("historyLoanId").value.trim();

        if (
            !loanId ||
            !Number.isInteger(Number(loanId)) ||
            Number(loanId) < 1
        ) {
            showPaymentMessage(
                "paymentHistoryMessage",
                "Enter a valid loan ID.",
                false
            );
            return;
        }

        await loadLoanPayments(loanId);
    });
}


/* ==========================================
   ADVANCED SQL: BRANCH ACCOUNT SUMMARY VIEW
   ========================================== */

async function loadBranchAccountSummary() {
    const table = document.getElementById("branchSummaryTable");
    const message = document.getElementById("branchSummaryMessage");

    if (!table) return;

    table.innerHTML = `<tr><td colspan="4">Loading...</td></tr>`;

    try {
        const result = await apiRequest("/api/branch-account-summary");
        const branches = result.branch_account_summary ?? [];

        if (!Array.isArray(branches) || branches.length === 0) {
            table.innerHTML =
                `<tr><td colspan="4">No branch records found.</td></tr>`;
            return;
        }

        table.innerHTML = branches.map(branch => `
            <tr>
                <td>${escapeLoanHTML(branch.BranchID)}</td>
                <td>${escapeLoanHTML(branch.BranchName)}</td>
                <td>${escapeLoanHTML(branch.TotalAccounts)}</td>
                <td>₹${formatLoanAmount(branch.TotalBalance)}</td>
            </tr>
        `).join("");

        if (message) message.hidden = true;
    } catch (error) {
        table.innerHTML =
            `<tr><td colspan="4">Could not load branch summary.</td></tr>`;

        if (message) {
            message.textContent = error.message;
            message.className = "message error";
            message.hidden = false;
        }

        console.error("Branch summary error:", error);
    }
}

const refreshBranchButton =
    document.getElementById("refreshBranchSummary");

if (refreshBranchButton) {
    refreshBranchButton.addEventListener(
        "click",
        loadBranchAccountSummary
    );
}

loadBranchAccountSummary();


/* ==========================================
   ADVANCED SQL: CUSTOMER ACCOUNTS PROCEDURE
   AND TOTAL BALANCE FUNCTION
   ========================================== */

const customerLookupForm =
    document.getElementById("customerAccountLookupForm");

if (customerLookupForm) {
    customerLookupForm.addEventListener("submit", async event => {
        event.preventDefault();

        const customerId = Number(
            document.getElementById("lookupCustomerId").value
        );

        const table = document.getElementById("customerAccountsTable");
        const message = document.getElementById("customerLookupMessage");
        const totalContainer =
            document.getElementById("customerTotalBalance");
        const totalValue =
            document.getElementById("customerTotalBalanceValue");
        const button = customerLookupForm.querySelector(
            'button[type="submit"]'
        );

        if (!Number.isInteger(customerId) || customerId <= 0) {
            if (message) {
                message.textContent = "Enter a valid Customer ID.";
                message.className = "message error";
                message.hidden = false;
            }
            return;
        }

        if (message) message.hidden = true;
        if (totalContainer) totalContainer.hidden = true;

        table.innerHTML =
            `<tr><td colspan="6">Loading customer accounts...</td></tr>`;

        if (button) button.disabled = true;

        try {
            // Stored procedure: GetCustomerAccounts
            const result = await apiRequest(
                `/api/customers/${customerId}/accounts`
            );

            const accounts = Array.isArray(result)
                ? result
                : result.accounts ??
                  result.customer_accounts ??
                  result.data ??
                  [];

            if (!Array.isArray(accounts)) {
                throw new Error("Unexpected customer account response.");
            }

            if (accounts.length === 0) {
                table.innerHTML =
                    `<tr><td colspan="6">No linked accounts found.</td></tr>`;
            } else {
                table.innerHTML = accounts.map(account => `
                    <tr>
                        <td>${escapeLoanHTML(account.CustomerID ?? account.customer_id)}</td>
                        <td>${escapeLoanHTML(account.First_Name ?? account.First_name ?? account.first_name)}</td>
                        <td>${escapeLoanHTML(account.Last_Name ?? account.Last_name ?? account.last_name)}</td>
                        <td>${escapeLoanHTML(account.AccountNumber ?? account.account_number)}</td>
                        <td>${escapeLoanHTML(account.AccountType ?? account.account_type)}</td>
                        <td>₹${formatLoanAmount(account.Balance ?? account.balance)}</td>
                    </tr>
                `).join("");
            }

            // Function: GetCustomerTotalBalance
            const balanceResult = await apiRequest(
                `/api/customers/${customerId}/total-balance`
            );

            const balance =
                balanceResult.TotalBalance ??
                balanceResult.total_balance ??
                balanceResult.totalBalance;

            if (balance === undefined || balance === null) {
                throw new Error("Total balance was not returned by Flask.");
            }

            if (totalValue) {
                totalValue.textContent = `₹${formatLoanAmount(balance)}`;
            }

            if (totalContainer) totalContainer.hidden = false;

            if (message) {
                message.textContent =
                    `Customer ${customerId}: ${accounts.length} account(s) found.`;
                message.className = "message success";
                message.hidden = false;
            }
        } catch (error) {
            table.innerHTML =
                `<tr><td colspan="6">Could not load customer details.</td></tr>`;

            if (message) {
                message.textContent = error.message;
                message.className = "message error";
                message.hidden = false;
            }

            console.error("Customer lookup error:", error);
        } finally {
            if (button) button.disabled = false;
        }
    });
}
