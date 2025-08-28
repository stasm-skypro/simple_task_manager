# main.py
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.models import Task, Token, TokenData, User, UserInDB

# Инициализируем FastAPI приложение
app = FastAPI()

# ------------------------------------------------------------
# JWT-аутентификация
# ------------------------------------------------------------

# Для реального проекта серктеный ключ долджен быть в переменных окружения
SECRET_KEY = os.getenv("SECRET_KEY", "123456789")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Контекст для хэшированнвх паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Схема для аутентийикации по OAuth2 с паролем
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Создаём "базу данных" в памяти в виде списка объектов User
user_db = [
    UserInDB(
        id=1,
        username="admin",
        password=pwd_context.hash("strong_admin_password"),
    ),
    UserInDB(
        id=2,
        username="user",
        password=pwd_context.hash("strong_user_password"),
    ),
]

# Создаем "базу данных" в памяти в виде списка объектов Task
tasks_db: list[Task] = [
    Task(
        uuid="3fa85f64-5717-4562-b3fc-2c963f66afa6",
        name="Дописать тестовое задание",
        description="Дописать аутентификацию",
        created_at="2025-08-27T18:33:18.086Z",
        in_work=False,
        is_finished=True,
        owner=1,
    ),
    Task(
        uuid="5fa15f67-3784-4662-b3fc-6c653f69afa2",
        name="Дописать README",
        description="Дописать в README примеры JSON-ответов аутентификации",
        created_at="2025-08-26T18:33:18.086Z",
        in_work=True,
        is_finished=False,
        owner=2,
    ),
]

# -----------------
# Функции аутентификации
# -----------------


def get_user(db: list[UserInDB], username: str | None) -> UserInDB | None:
    """
    Ищет пользователя по user_id в базе данных.
    """
    if username is not None:
        for user in db:
            if user.username == username:
                return user
    return None


def authenticate_user(db: list[UserInDB], username: str, password: str) -> UserInDB | None:
    """
    Проверяет имя пользователя и пароль.
    """
    user = get_user(db, username)
    if not user:
        return None
    if not pwd_context.verify(password, user.password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Создает JWT-токен.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt


# -----------------
# Зависимости
# -----------------


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """
    Получает текущего пользователя из токена.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Невозможно проверить учётные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(user_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    # Возвращаем упрощенную модель пользователя без пароля
    return User(id=user.id, username=user.username, hashed_password=user.password)


# -----------------
# Эндпоинты аутентификации
# -----------------


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """
    Получает JWT-токен.
    """
    user = authenticate_user(user_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="Bearer")


# -----------------
# Эндпоинты задач
# -----------------


@app.post("/tasks/", response_model=Task, status_code=201)
async def create_task(new_task: Task) -> Task:
    """
    Создает новую задачу и добавляет ее в "базу данных".

    FastAPI автоматически проверит данные в запросе
    согласно Pydantic-модели Task и сгенерирует UUID
    и timestamp, если они не предоставлены.
    """
    tasks_db.append(new_task)
    return new_task


@app.get("/tasks/", response_model=list[Task])
async def read_all_() -> list[Task]:
    """
    Возвращает полный список всех задач.
    """
    return tasks_db


@app.get("/tasks/{task_id}", response_model=Task)
async def read_task(task_id: UUID) -> Task:
    """
    Возвращает одну задачу по её UUID.
    """
    # Ищем задачу по uuid в списке
    for task in tasks_db:
        if task.uuid == task_id:
            return task
    # Если задача не найдена, возвращаем HTTP-ошибку 404
    raise HTTPException(status_code=404, detail="Задача не найдена")


@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: UUID, update_task: Task) -> Task:
    """
    Обновляет существующую задачу по ее UUID.

    Получаем UUID из пути и новые данные для задачи из тела запроса.
    """
    # Ищем задачу по uuid и обновляем её данные
    for index, task in enumerate(tasks_db):
        if task.uuid == task_id:
            # обновляем задачу в списке
            tasks_db[index] = update_task
            return update_task
    # Если задача не найдена, возвращаем HTTP-ошибку 404
    raise HTTPException(status_code=404, detail="Задача не найдена")


@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: UUID, current_user: Annotated[User, Depends(get_current_user)]) -> None:
    """
    Удаляет задачу по ее UUID. Доступ толькот для владельца.
    """
    # Ищем задачу по uuid и удаляем её
    for index, task in enumerate(tasks_db):
        if task.uuid == task_id:
            # Теперь проверяем,является ли текущий пользователь владельцем задачи.
            if current_user.id != task.owner:
                raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения операции")
            tasks_db.pop(index)
            # Возвращаем пустой ответ с кодом 204 No Content
            return
    # Если задача не найдена, возвращаем HTTP-ошибку 404
    raise HTTPException(status_code=404, detail="Задача не найдена")
