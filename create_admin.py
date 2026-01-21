from argon2 import PasswordHasher

ph = PasswordHasher()

password = "admin123"   # temporary password
hashed = ph.hash(password)

print("Hashed password:")
print(hashed)
