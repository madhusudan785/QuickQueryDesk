import pytest
from datetime import timedelta
import jwt
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.config import get_settings

settings = get_settings()

def test_password_hashing():
    """Test that a password can be hashed and verified correctly."""
    password = "secure_password123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_jwt_token_generation_and_decoding():
    """Test JWT creation and decoding."""
    data = {"sub": "12345", "role": "agent"}
    token = create_access_token(data=data, expires_delta=timedelta(minutes=15))
    
    decoded = decode_access_token(token)
    assert decoded["sub"] == "12345"
    assert decoded["role"] == "agent"
    assert "exp" in decoded


def test_jwt_token_expired():
    """Test that an expired token raises an exception."""
    data = {"sub": "12345", "role": "agent"}
    # Create a token that expired 1 minute ago
    token = create_access_token(data=data, expires_delta=timedelta(minutes=-1))
    
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)
