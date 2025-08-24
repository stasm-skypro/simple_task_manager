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
