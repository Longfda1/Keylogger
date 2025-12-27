from cryptography.fernet import Fernet

def create_key_pair():
    key = Fernet.generate_key()
    with open("client_key.key", "wb") as f:
        f.write(key)
    print("✅ Key pair generated!")
    print("👉 Copy 'client_key.key' to Server-Project and rename to 'server_key.key'")

if __name__ == '__main__':
    create_key_pair()
