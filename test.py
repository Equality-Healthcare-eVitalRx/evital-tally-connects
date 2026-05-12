from cryptography.fernet import Fernet

# Generate a key
# key = Fernet.generate_key()
key = "kphEig0_Dtx3iq2-Ok19KP0MTtVnXxO0gMlJ4ggAzPE="
print("➡ test.py:5 key:", key)
cipher_suite = Fernet(key)

# Encrypt a message
message = b"Hello, this is a secret message."
# cipher_text = cipher_suite.encrypt(message)
# print(f"Encrypted: {cipher_text}")

# Decrypt the message
cipher_text = "gAAAAABnszjdZeoK1Spduczc5Mu0WiQViUq1KsTgrQxk022bk1FzH7KVAPL6vkGdvs-ScaOQ9AxUloZf1bEiiZE2LiB2Pt22D9SrvTK3mSbKZoiZisqLCv7oui0q4RQ-9GSiHMREvkUg"
plain_text = cipher_suite.decrypt(cipher_text)
print(f"Decrypted: {plain_text.decode()}")
