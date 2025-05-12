from django.contrib.auth.hashers import PBKDF2PasswordHasher

class CustomPBKDF2Hasher(PBKDF2PasswordHasher):
    algorithm = "pbkdf2_sha256_custom"
    iterations = 50000

# https://docs.djangoproject.com/en/5.1/topics/auth/passwords/