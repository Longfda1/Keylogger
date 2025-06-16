from cryptography.fernet import Fernet


def create_key_pair():
    key = Fernet.generate_key()

    # Lưu key cho client
    with open("sever_key.key", "wb") as f:
        f.write(key)

    print("✅ Key pair generated!")
    print("👉 Copy 'sever_key.key' to Server-Project and rename to 'server_key.key'")


if __name__ == '__main__':
    create_key_pair()