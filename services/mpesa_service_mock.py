"""
Mock M-Pesa Service for Testing
Replaces real M-Pesa calls with predictable mock responses
"""

import os
from datetime import datetime

# Use mock mode if environment variable is set
USE_MOCK_MPESA = os.getenv("MOCK_MPESA", "true").lower() == "true"


def get_access_token():
    """Mock or real access token"""
    if USE_MOCK_MPESA:
        return "mock_token_12345"
    
    import base64
    import requests
    
    CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY", "")
    CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET", "")
    MPESA_BASE_URL = "https://sandbox.safaricom.co.ke"
    
    if not CONSUMER_KEY or not CONSUMER_SECRET:
        return "mock_token_12345"
    
    auth = base64.b64encode(
        f"{CONSUMER_KEY}:{CONSUMER_SECRET}".encode()
    ).decode()
    
    headers = {"Authorization": f"Basic {auth}"}
    try:
        response = requests.get(
            f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials",
            headers=headers,
            timeout=5
        )
        return response.json().get("access_token", "mock_token_12345")
    except Exception as e:
        print(f"Failed to get real token: {e}. Using mock.")
        return "mock_token_12345"


def stk_push(phone: str, amount: float, reference: str):
    """
    Mock or real STK Push (deposit)
    Returns mock response if MOCK_MPESA is enabled
    """
    if USE_MOCK_MPESA:
        return {
            "ResponseCode": "0",
            "ResponseDescription": "Success. Request accepted for processing",
            "MerchantRequestID": f"mock_{reference}",
            "CheckoutRequestID": f"ws_CO_DMZ_{reference}",
            "CustomerMessage": "Success. Request accepted for processing"
        }
    
    import base64
    import requests
    
    BUSINESS_SHORT_CODE = os.getenv("MPESA_BUSINESS_SHORT_CODE", "")
    PASSKEY = os.getenv("MPESA_PASSKEY", "")
    STK_CALLBACK_URL = os.getenv("MPESA_STK_CALLBACK_URL", "https://localhost/mpesa/stk/callback")
    MPESA_BASE_URL = "https://sandbox.safaricom.co.ke"
    
    if not BUSINESS_SHORT_CODE or not PASSKEY:
        return {"error": "M-Pesa credentials not configured"}
    
    token = get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    password = base64.b64encode(
        f"{BUSINESS_SHORT_CODE}{PASSKEY}{timestamp}".encode()
    ).decode()
    
    payload = {
        "BusinessShortCode": BUSINESS_SHORT_CODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": BUSINESS_SHORT_CODE,
        "PhoneNumber": phone,
        "CallBackURL": STK_CALLBACK_URL,
        "AccountReference": reference,
        "TransactionDesc": "Wallet Deposit"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers=headers,
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def b2c_withdraw(phone: str, amount: float):
    """
    Mock or real B2C Withdraw (withdrawal)
    Returns mock response if MOCK_MPESA is enabled
    """
    if USE_MOCK_MPESA:
        return {
            "Result": {
                "ResultType": 0,
                "ResultCode": 0,
                "ResultDesc": "Success. Request accepted for processing",
                "ConversationID": f"mock_conv_{phone}",
                "OriginatorConversationID": f"mock_orig_{phone}",
                "OriginatorThirdPartyReferenceID": None
            }
        }
    
    import requests
    
    BUSINESS_SHORT_CODE = os.getenv("MPESA_BUSINESS_SHORT_CODE", "")
    INITIATOR_NAME = os.getenv("MPESA_INITIATOR_NAME", "")
    SECURITY_CREDENTIAL = os.getenv("MPESA_SECURITY_CREDENTIAL", "")
    B2C_TIMEOUT_URL = os.getenv("MPESA_B2C_TIMEOUT_URL", "https://localhost/mpesa/b2c/timeout")
    B2C_RESULT_URL = os.getenv("MPESA_B2C_RESULT_URL", "https://localhost/mpesa/b2c/result")
    MPESA_BASE_URL = "https://sandbox.safaricom.co.ke"
    
    if not BUSINESS_SHORT_CODE or not INITIATOR_NAME or not SECURITY_CREDENTIAL:
        return {"error": "M-Pesa credentials not configured"}
    
    token = get_access_token()
    
    payload = {
        "InitiatorName": INITIATOR_NAME,
        "SecurityCredential": SECURITY_CREDENTIAL,
        "CommandID": "BusinessPayment",
        "Amount": int(amount),
        "PartyA": BUSINESS_SHORT_CODE,
        "PartyB": phone,
        "Remarks": "Wallet Withdrawal",
        "QueueTimeOutURL": B2C_TIMEOUT_URL,
        "ResultURL": B2C_RESULT_URL,
        "Occasion": "withdraw"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{MPESA_BASE_URL}/mpesa/b2c/v1/paymentrequest",
            json=payload,
            headers=headers,
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}
