# test_main.py
from uuid import uuid4

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


def test_read_all_tasks_empty_list():
    """Тест получения списка задач, когда он пуст."""
    response = client.get("/tasks/")

    assert response.status_code == 200
    assert response.json() == []


def test_read_all_tasks():
    """Тест получения списка задач, когда в нем есть данные."""
    # Создаем несколько задач для теста
    client.post(
        "/tasks/",
        json={
            "name": "Задача 1",
            "description": "Описание 1",
            "in_work": True,
            "is_finished": False,
        },
    )
    client.post(
        "/tasks/",
        json={
            "name": "Задача 2",
            "description": "Описание 2",
            "in_work": False,
            "is_finished": False,
        },
    )

    response = client.get("/tasks/")

    assert response.status_code == 200

    # Проверяем, что в ответе две задачи
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Задача 1"
    assert data[1]["name"] == "Задача 2"


def test_read_task_success():
    """Тест получения одной задачи по UUID (успешный сценарий)."""
    # Создаем задачу, чтобы получить ее uuid
    create_response = client.post(
        "/tasks/",
        json={
            "name": "Задача для чтения",
            "description": "Описание",
            "in_work": False,
            "is_finished": False,
        },
    )
    task_uuid = create_response.json()["uuid"]

    # Получаем задачу по uuid
    response = client.get(f"/tasks/{task_uuid}")

    assert response.status_code == 200
    data = response.json()

    # Проверяем, что получена нужная задача
    assert data["name"] == "Задача для чтения"
    assert data["uuid"] == task_uuid


def test_read_task_not_found():
    """Тест получения задачи, которой не существует (сценарий ошибки)."""
    # Используем uuid4 для генерации UUID, которого нет в "базе данных"
    non_existent_uuid = str(uuid4())

    response = client.get(f"/tasks/{non_existent_uuid}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Задача не найдена"


def test_update_task_success():
    """Тест обновления задачи (успешный сценарий)."""
    # Создаем задачу для обновления
    create_response = client.post(
        "/tasks/",
        json={"name": "Старая задача", "description": "Старое описание", "in_work": False, "is_finished": False},
    )
    task_uuid = create_response.json()["uuid"]

    # Новые данные для обновления
    updated_payload = {
        "uuid": task_uuid,
        "name": "Обновленная задача",
        "description": "Обновленное описание",
        "in_work": True,
        "is_finished": False,
    }

    response = client.put(f"/tasks/{task_uuid}", json=updated_payload)

    assert response.status_code == 200
    data = response.json()

    # Проверяем, что данные были обновлены
    assert data["name"] == "Обновленная задача"
    assert data["description"] == "Обновленное описание"
