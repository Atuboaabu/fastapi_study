from security import hash_password, verify_password

def test_hash_password_does_not_store_plaintext():
    password = "password123"

    hashed = hash_password(password)

    assert password != hashed

def test_same_password_produces_different_hashes():
    password = "password123"

    hashed1 = hash_password(password)

    hashed2 = hash_password(password)

    assert hashed1 != hashed2

def test_verify_password():
    password = "password123"

    hashed = hash_password(password)

    assert verify_password(password, hashed) == True

    assert verify_password("wrong_password", hashed) == False