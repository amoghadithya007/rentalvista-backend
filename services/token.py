import jwt
import datetime
from os import environ

def encode_jwt(user_id: str) -> bytes:
    """
    Generates the JWT
    :params 
        1. user_id: string
    :return: bytes
    """
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7, seconds=5),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload,
            environ.get('SECRET_KEY'),
            algorithm='HS256'
        )
    except Exception as e:
        return e

def decode_jwt(auth_token: str) -> str:
    """
    Decodes the JWT
    :param 
        1. auth_token: string
    :return: integer|string
    """
    try:
        payload = jwt.decode(auth_token, environ.get('SECRET_KEY'))
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'

