import hmac
import hashlib
import secrets
import math

HOUSE_EDGE = 0.01  # 1%

def generate_server_seed():
    return secrets.token_hex(32)

def generate_client_seed():
    return secrets.token_hex(16)

def calculate_crash_point(server_seed, client_seed, nonce):
    message = f"{client_seed}:{nonce}".encode()
    key = server_seed.encode()

    h = hmac.new(key, message, hashlib.sha256).hexdigest()
    h_int = int(h[:13], 16)

    crash = (2**52 / (h_int + 1)) * (1 - HOUSE_EDGE)
    return round(max(1.0, crash), 2)