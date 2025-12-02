from src.schemas.schemas import TelegramUser, TelegramMessage
from src.tests.conftest import client

def test_health(client):
    telegram_user = TelegramUser(
        user_id=123456789,
        first_name="alex",
        last_name="test",
        username="ksairos",
        chat_id=123456789
    )

    message = TelegramMessage(
        user=telegram_user,
        user_prompt="Hello, how are you?"
    )

    response = client.post("/invoke", json=message.model_dump())
    assert response.status_code == 200