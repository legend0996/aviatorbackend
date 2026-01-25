import base64
import requests
from datetime import datetime


MPESA_BASE_URL = "https://sandbox.safaricom.co.ke"

CONSUMER_KEY = "<CONSUMER_KEY>"
CONSUMER_SECRET = "<CONSUMER_SECRET>"
BUSINESS_SHORT_CODE = "<PAYBILL>"
PASSKEY = "<PASSKEY>"

STK_CALLBACK_URL = "https://my-domain.com/mpesa/stk/callback"
B2C_TIMEOUT_URL = "https://my-domain.com/mpesa/b2c/timeout"
B2C_RESULT_URL = "https://my-domain.com/mpesa/b2c/result"


def get_access_token():
    auth = base64.b64encode(
        f"{CONSUMER_KEY}:{CONSUMER_SECRET}".encode()
    ).decode()

    headers = {"Authorization": f"Basic {auth}"}
    response = requests.get(
        f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials",
        headers=headers
    )

    return response.json()["access_token"]


# -------------------
# STK PUSH (DEPOSIT)
# -------------------
def stk_push(phone: str, amount: float, reference: str):
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

    response = requests.post(
        f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers=headers
    )

    return response.json()


# -------------------
# B2C WITHDRAW
# -------------------
def b2c_withdraw(phone: str, amount: float):
    token = get_access_token()

    payload = {
        "InitiatorName": "<INITIATOR_NAME>",
        "SecurityCredential": "<SECURITY_CREDENTIAL>",
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

    response = requests.post(
        f"{MPESA_BASE_URL}/mpesa/b2c/v1/paymentrequest",
        json=payload,
        headers=headers
    )

    return response.json()
