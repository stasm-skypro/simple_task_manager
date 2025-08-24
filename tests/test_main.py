# test_main.py
# from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

# Импортируем экземпляр приложения и "базу данных"
from src.main import app, tasks_db

# Создаем тестовый клиент
client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_db_before_test():
    """Фикстура для очистки "базы данных" перед каждым тестом."""
    tasks_db.clear()
    yield
    tasks_db.clear()


def test_create_task():
    """Тест создания новой задачи."""
    # Тело запроса для новой задачи
    new_task_payload = {
        "name": "Новая задача",
        "description": "Описание новой задачи",
        "in_work": False,
        "is_finished": False,
    }

    # Отправляем POST-запрос на эндпоинт создания задачи
    response = client.post("/tasks/", json=new_task_payload)

    # Проверяем, что ответ имеет статус 201 Created
    assert response.status_code == 201

    # Получаем данные из ответа
    data = response.json()

    # Проверяем, что данные в ответе соответствуют отправленным
    assert data["name"] == "Новая задача"
    assert data["description"] == "Описание новой задачи"
    assert data["in_work"] is False
    assert data["is_finished"] is False

    # Проверяем, что были сгенерированы uuid и created_at
    assert "uuid" in data
    assert "created_at" in data

    # Проверяем, что задача добавилась в "базу данных"
    assert len(tasks_db) == 1
    assert str(tasks_db[0].uuid) == data["uuid"]
