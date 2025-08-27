# main.py
import os
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from src.models import Tasks, UserInDB

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

# Создаем "базу данных" в памяти в виде списка объектов Tasks
tasks_db: list[Tasks] = []


@app.post("/tasks/", response_model=Tasks, status_code=201)
async def create_task(new_task: Tasks) -> Tasks:
    """
    Создает новую задачу и добавляет ее в "базу данных".

    FastAPI автоматически проверит данные в запросе
    согласно Pydantic-модели Tasks и сгенерирует UUID
    и timestamp, если они не предоставлены.
    """
    tasks_db.append(new_task)
    return new_task


@app.get("/tasks/", response_model=list[Tasks])
async def read_all_tasks() -> list[Tasks]:
    """
    Возвращает полный список всех задач.
    """
    return tasks_db


@app.get("/tasks/{task_id}", response_model=Tasks)
async def read_task(task_id: UUID) -> Tasks:
    """
    Возвращает одну задачу по её UUID.
    """
    # Ищем задачу по uuid в списке
    for task in tasks_db:
        if task.uuid == task_id:
            return task
    # Если задача не найдена, возвращаем HTTP-ошибку 404
    raise HTTPException(status_code=404, detail="Задача не найдена")


@app.put("/tasks/{task_id}", response_model=Tasks)
async def update_task(task_id: UUID, update_task: Tasks) -> Tasks:
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
async def delete_task(task_id: UUID) -> None:
    """
    Удаляет задачу по ее UUID.
    """
    # Ищем задачу по uuid и удаляем её
    for index, task in enumerate(tasks_db):
        if task.uuid == task_id:
            tasks_db.pop(index)
            # Возвращаем пустой ответ с кодом 204 No Content
            return
    # Если задача не найдена, возвращаем HTTP-ошибку 404
    raise HTTPException(status_code=404, detail="Task not found")
