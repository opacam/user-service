from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    """Given a password, returns a hashed password."""
    return pwd_context.hash(password)
