# Aviator Backend - Quick Reference

## 🚀 Running the Application

### Start Backend Server
```bash
cd aviatorbackend
source venv/bin/activate
python -m uvicorn main:app --reload
```
**Available at:** http://localhost:8000

### Start Frontend Server
```bash
cd aviatorfrontend
npm install
npm run dev
```
**Available at:** http://localhost:5174

---

## ✅ Running Tests

### All Tests
```bash
pytest test_full_app.py -v
```

### Specific Test Class
```bash
pytest test_full_app.py::TestAuthentication -v
pytest test_full_app.py::TestBetting -v
pytest test_full_app.py::TestMpesaWallet -v
```

### With Coverage
```bash
pytest test_full_app.py --cov=services --cov-report=html
```

### Test Runner Script
```bash
bash run_tests.sh
```

---

## 📊 Test Statistics

- **Total Tests:** 22
- **Passing:** 22 (100%)
- **Duration:** ~13 seconds
- **Coverage:** Authentication, Wallet, Betting, Game Loop, M-Pesa, Admin

---

## 🔑 Key API Endpoints

### Authentication
- `POST /auth/register` - User registration (phone + password)
- `POST /auth/login` - User login (returns JWT token)

### Wallet
- `GET /wallet/balance` - Get current balance (auth required)
- `POST /wallet/deposit/stk` - Initiate M-Pesa deposit
- `POST /wallet/withdraw/mpesa` - Withdraw via M-Pesa
- `POST /mpesa/stk/callback` - Handle M-Pesa callbacks

### Aviator Game
- `GET /aviator/round` - Get current game round
- `POST /aviator/bet` - Place a bet
- `POST /aviator/cashout` - Cash out from active bet

### Admin
- `POST /admin/login` - Admin login
- `GET /admin/protected` - Protected admin endpoint

---

## 📁 Project Structure

```
aviatorbackend/
├── main.py                    # FastAPI app & endpoints
├── auth.py                    # Auth models
├── database.py               # SQLAlchemy config
├── jwt_utils.py              # JWT handling
├── dependencies.py           # Auth dependencies
├── requirements.txt          # Python dependencies
├── test_full_app.py          # 22 test cases
├── run_tests.sh              # Test runner script
├── TESTING.md                # Testing guide
├── TEST_RESULTS.md           # This test summary
│
└── services/
    ├── auth_service.py       # Registration & login
    ├── user_service.py       # User queries
    ├── wallet_service.py     # Wallet operations
    ├── bet_service.py        # Bet placement
    ├── aviator_service.py    # Game loop & rounds
    ├── multiplier_service.py # Crash multiplier logic
    └── mpesa_service_mock.py # Mock M-Pesa (safe testing)
```

---

## 🔐 Authentication

**Type:** JWT (JSON Web Tokens)  
**Claims:** `sub` (phone number)  
**Duration:** 24 hours

**Header Format:**
```
Authorization: Bearer <token>
```

**Test Credentials:**
```
Phone: 254712345678
Password: testpass123
```

---

## 💰 Transaction Types

| Type | Description |
|------|-------------|
| deposit | Money in from M-Pesa |
| withdraw | Money out via M-Pesa |
| bet | Wager on Aviator round |
| win | Successful bet payout |
| bonus | Admin bonus credit |
| refund | Bet refund |

---

## 🎮 Game Flow

1. User registers/logs in
2. User funds wallet via M-Pesa
3. Round opens (5 second betting window)
4. User places bet (amount deducted immediately)
5. Plane climbs (multiplier increases 0.05s)
6. User can:
   - **Cash out** at any time (win = bet × multiplier)
   - **Hold** until crash (lose entire bet)
7. Round crashes at random point
8. Next round begins

---

## 🧪 Test Database

**Reset between tests:** Automatic  
**Cleanup:** All tables cleared after each test  
**Isolation:** Each test has fresh database state  

**Tables Used:**
- users
- wallets
- transactions
- game_rounds
- bets
- admin_settings

---

## 🐛 Common Issues & Solutions

### Connection Refused (Database)
```
Error: connection to server at "localhost" failed
```
**Solution:** Ensure PostgreSQL is running
```bash
sudo systemctl start postgresql
```

### Pytest Not Found
```
Error: No module named pytest
```
**Solution:** Install testing dependencies
```bash
pip install pytest httpx
```

### Venv Python Not Found
```
Error: python3: bad interpreter: No such file
```
**Solution:** Recreate virtual environment
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📝 Environment Variables

**Required (.env file):**
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aviator_db
```

**Optional:**
```env
MOCK_MPESA=true              # Use mock M-Pesa (default: true)
MPESA_CONSUMER_KEY=...       # Real M-Pesa (when MOCK_MPESA=false)
MPESA_CONSUMER_SECRET=...    # Real M-Pesa (when MOCK_MPESA=false)
MPESA_PASSKEY=...            # Real M-Pesa (when MOCK_MPESA=false)
```

---

## 🚨 Important Notes

- ✅ All 22 tests passing
- ✅ Database constraints validated
- ✅ M-Pesa mocked for safe testing
- ✅ Transaction atomicity enforced
- ✅ Concurrent operations tested
- ⚠️ Error handlers need HTTP exception mapping (currently raising raw exceptions)

---

## 📞 Next Actions

1. **Verify Backend:** `pytest test_full_app.py -v`
2. **Check Frontend:** Visit http://localhost:5174
3. **Test Login:** Register → Login → Check balance
4. **Test Betting:** Fund wallet → Wait for open round → Place bet
5. **Check M-Pesa:** Review mock responses in test output

---

**Last Updated:** January 27, 2026  
**Test Status:** ✅ All Passing (22/22)  
**Ready for:** Frontend integration & browser testing
