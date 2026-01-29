# Full Application Testing Guide

## Overview
Complete testing suite for Aviator game backend + frontend with M-Pesa integration.

---

## Quick Start Testing

### 1. **Backend Unit & Integration Tests**

```bash
# Install test dependencies (if not already installed)
cd ~/Desktop/Aviator/aviatorbackend
pip install pytest pytest-cov httpx

# Run all tests
pytest test_full_app.py -v

# Run specific test class
pytest test_full_app.py::TestAuthentication -v

# Run with coverage report
pytest test_full_app.py --cov=services --cov-report=html

# Run tests in watch mode (requires pytest-watch)
pip install pytest-watch
ptw test_full_app.py
```

### 2. **Manual API Testing with cURL**

#### Register New User
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"phone":"254712345678","password":"testpass123"}'
```

#### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"254712345678","password":"testpass123"}'

# Save the token from response: TOKEN="eyJhbGc..."
```

#### Get Current Round
```bash
curl http://localhost:8000/aviator/round
```

#### Get Wallet Balance (Authenticated)
```bash
curl http://localhost:8000/wallet/balance \
  -H "Authorization: Bearer TOKEN"
```

#### Place a Bet (Authenticated)
```bash
curl -X POST http://localhost:8000/aviator/bet \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"amount":1000,"auto_cashout":2.5}'
```

#### Test STK Push (M-Pesa Deposit) - Uses Mock
```bash
curl -X POST http://localhost:8000/wallet/deposit/stk \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"amount":1000}'
```

#### Test B2C Withdrawal - Uses Mock
```bash
curl -X POST http://localhost:8000/wallet/withdraw/mpesa \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"amount":500}'
```

---

## Testing Scenarios

### Scenario 1: User Registration & Login
```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"phone":"254787654321","password":"mypass123"}'
# Response: {"success": true, "message": "User registered successfully"}

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"254787654321","password":"mypass123"}'
# Response: {"success": true, "access_token": "...", "user": {...}}
```

### Scenario 2: Wallet & Betting
```bash
# Get initial balance
TOKEN="<token_from_login>"
curl http://localhost:8000/wallet/balance -H "Authorization: Bearer $TOKEN"
# Response: {"balance": 0}

# Fund wallet via SQL (simulating M-Pesa deposit)
# In PostgreSQL: INSERT INTO transactions (...); 
# UPDATE wallets SET balance = balance + 5000 WHERE user_id = 1;

# Place bet
curl -X POST http://localhost:8000/aviator/bet \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"amount":1000,"auto_cashout":3.5}'
# Response: {"success": true}

# Check updated balance
curl http://localhost:8000/wallet/balance -H "Authorization: Bearer $TOKEN"
# Response: {"balance": 4000}  (5000 - 1000 bet)
```

### Scenario 3: M-Pesa Integration (Mock)
```bash
# By default, M-Pesa calls return mock responses
# No real money is transferred

# Test STK Push (deposit)
curl -X POST http://localhost:8000/wallet/deposit/stk \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"amount":1000}'
# Response (Mock): {
#   "ResponseCode": "0",
#   "ResponseDescription": "Success. Request accepted for processing",
#   "MerchantRequestID": "mock_...",
#   "CheckoutRequestID": "ws_CO_DMZ_..."
# }

# Simulate M-Pesa callback
curl -X POST http://localhost:8000/mpesa/stk/callback \
  -H "Content-Type: application/json" \
  -d '{
    "Body": {
      "stkCallback": {
        "ResultCode": 0,
        "ResultDesc": "Success",
        "CallbackMetadata": {
          "Item": [
            {"Name": "Amount", "Value": 1000},
            {"Name": "AccountReference", "Value": "stk_1_1000"}
          ]
        }
      }
    }
  }'
# Response: {"ResultCode": 0}
```

---

## Frontend Testing

### Test in Browser
1. Open http://localhost:5174
2. Register with phone: `254712345678`, password: `test123`
3. Click "Register"
4. Login with same credentials
5. Watch the plane animate during game rounds
6. Try placing bets (if wallet is funded)
7. Test logout

### Frontend E2E Tests (Optional)
```bash
# Install Cypress or Playwright
cd ~/Desktop/Aviator/aviatorfrontend
npm install cypress --save-dev

# Run tests
npx cypress open
```

---

## Environment Configuration

### For Real M-Pesa Integration (Production)

Create `.env` file in `/home/lwk/Desktop/Aviator/aviatorbackend/`:

```bash
# M-Pesa Credentials
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_BUSINESS_SHORT_CODE=your_paybill_number
MPESA_PASSKEY=your_passkey
MPESA_INITIATOR_NAME=initiator_name
MPESA_SECURITY_CREDENTIAL=encrypted_credential

# Callbacks (must be publicly accessible)
MPESA_STK_CALLBACK_URL=https://yourdomain.com/mpesa/stk/callback
MPESA_B2C_TIMEOUT_URL=https://yourdomain.com/mpesa/b2c/timeout
MPESA_B2C_RESULT_URL=https://yourdomain.com/mpesa/b2c/result

# Use real M-Pesa (not mock)
MOCK_MPESA=false

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aviator_db
```

### For Testing (Current Setup - Uses Mock M-Pesa)

```bash
# Mock is enabled by default
MOCK_MPESA=true
```

---

## Test Database

### Reset Database for Fresh Tests
```bash
cd ~/Desktop/Aviator/aviatorbackend

# Drop and recreate (WARNING: deletes all data)
python3 << 'EOF'
from sqlalchemy import text
from database import engine

with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS bets CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS transactions CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS wallets CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS admins CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS settings CASCADE"))
    conn.commit()

print("Database reset complete")
EOF

# Reload schema
python3 test_db.py
```

---

## Common Issues & Fixes

### Issue: `net::ERR_FAILED 200` CORS Error
**Fix**: Already applied! CORS now includes port 5174
```python
# In main.py, CORS middleware includes:
allow_origins=[
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    ...
]
```

### Issue: Tests Fail with `psycopg2.errors.ForeignKeyViolation`
**Fix**: Auto-teardown deletes records in correct order:
```python
# In test_full_app.py fixtures:
def setup_teardown():
    # Delete in order of dependencies
    conn.execute(text("DELETE FROM bets"))
    conn.execute(text("DELETE FROM transactions"))
    conn.execute(text("DELETE FROM wallets"))
    conn.execute(text("DELETE FROM users"))
```

### Issue: M-Pesa Callback Fails
**Fix**: Callback endpoint always returns 200 to M-Pesa
```python
@app.post("/mpesa/stk/callback")
def stk_callback(payload: dict):
    try:
        # Process callback
        ...
    except Exception as e:
        print(f"Callback error: {e}")
    return {"ResultCode": 0}  # Always success to M-Pesa
```

---

## Test Coverage Report

Run with coverage:
```bash
pytest test_full_app.py --cov=services --cov-report=term-missing

# Generate HTML report
pytest test_full_app.py --cov=services --cov-report=html
# Open htmlcov/index.html in browser
```

---

## CI/CD Integration (GitHub Actions)

Create `.github/workflows/test.yml`:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: aviator_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt pytest pytest-cov
      - run: pytest test_full_app.py --cov
```

---

## Quick Reference: Test Commands

```bash
# Run all tests
pytest test_full_app.py -v

# Run specific test
pytest test_full_app.py::TestAuthentication::test_register_success -v

# Run with print statements visible
pytest test_full_app.py -v -s

# Run only fast tests
pytest test_full_app.py -v -m "not slow"

# Stop after first failure
pytest test_full_app.py -x

# Run last failed tests
pytest test_full_app.py --lf

# Generate coverage
pytest test_full_app.py --cov=services --cov-report=html

# Parallel testing (faster)
pip install pytest-xdist
pytest test_full_app.py -n auto
```

---

## Next Steps

1. **Run basic tests**: `pytest test_full_app.py -v`
2. **Test in browser**: Visit http://localhost:5174
3. **Test auth flow**: Register → Login → Place bet
4. **Test M-Pesa**: Test deposit/withdraw (mock responses)
5. **Load testing**: Use Apache Bench or k6 for stress testing
6. **Real M-Pesa**: Configure credentials and set `MOCK_MPESA=false`

---

## Support

For issues:
- Check test output for specific assertion failures
- Review logs in backend console
- Check browser DevTools network tab for API responses
- Run individual test for debugging: `pytest test_full_app.py::TestClassName::test_method -vvs`
