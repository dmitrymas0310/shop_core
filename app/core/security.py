from passlib.context import CryptContext

#Контекст для работы с паролями
pwd_context = CryptContext(
    schemes=["bcrypt"],      #алгоритм хэширования
    deprecated="auto",       #старые алгоритмы будут помечены как устаревшие
)

#Преобразование обычного пароля в безопасный хэш для хранения в БД
def hash_password(password: str) -> str: 
    return pwd_context.hash(password)

#Проверка - подходит ли введенный пароль к хэшу из БД
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
