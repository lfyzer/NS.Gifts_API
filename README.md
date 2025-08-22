# nsgifts (Unofficial NS.Gifts API Client)

Асинхронный Python-клиент для [NS.Gifts API](https://api.ns.gifts/docs).  
❗ Я не сотрудничаю и никак не связан с [NS.Gifts](https://ns.gifts/). Этот клиент написан исключительно для удобства работы с API.

---

## 🚀 Установка

```bash
pip install nsgifts
```

---

## 📌 Быстрый старт

```python
import asyncio
from nsgifts import NSGiftsClient

async def main():
    async with NSGiftsClient() as client:
        # Авторизация
        await client.login("your@email.com", "your_password")

        # Проверка баланса
        balance = await client.check_balance()
        print(balance)

        # Получение категорий
        categories = await client.get_categories()
        print(categories)

asyncio.run(main())
```

---

## 📂 Основные возможности

- 🔑 Авторизация и регистрация (`login`, `signup`)
- 💰 Проверка баланса (`check_balance`)
- 📦 Управление заказами (`create_order`, `pay_order`, `get_order_info`)
- 🎮 Steam API:
  - `calculate_steam_amount`
  - `get_steam_currency_rate`
  - `calculate_steam_gift`
  - `create_steam_gift_order`
  - `pay_steam_gift_order`
  - `get_steam_package_price`
- 🌐 Управление whitelist IP:
  - `add_ip_to_whitelist`
  - `remove_ip_from_whitelist`
  - `list_whitelist_ips`

---

## 📘 Примеры использования

📂 Файл: `examples/basic_usage.py`
## Получаем информацию о профиле
```python
import asyncio
from nsgifts import NSGiftsClient, APIError

async def main(email, password):
    """Main function demonstrating client usage."""
    try:
        async with NSGiftsClient() as client:
            login_result = await client.login(email, password)
            print(f"Logged in, token valid until: {login_result['valid_thru']}")
            
            user_info = await client.get_user_info()
            print(f"User Info: {user_info}")

    except APIError as e:
        print(f"An API error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    email = "your_email@example.com" # email or nickname
    password = "your_password"
    asyncio.run(main(email, password))

```

📂 Файл: `examples/example2.py`
## Получаем баланс
```python
import asyncio
from nsgifts import NSGiftsClient, APIAuthenticationError

async def check_user_balance(email, password):
    try:
        async with NSGiftsClient() as client:
            await client.login(email, password)
            balance_info = await client.check_balance()
            print(f"Current Balance: {balance_info}")
    except APIAuthenticationError:
        print("Authentication failed. Please check your credentials.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    email = "your_email@example.com" # email or nickname
    password = "your_password"
    asyncio.run(check_user_balance(email, password))
```
---

## ⚠️ Отказ от ответственности (Disclaimer)

- Это **неофициальная библиотека**. Данный клиент не является официальным продуктом NS.Gifts.
- Я **не сотрудничаю** с NS.Gifts и не имею отношения к их сервису или компании.
- Автор **не несет ответственности** за любые проблемы, убытки или ущерб, возникшие в результате использования данной библиотеки.
- Библиотека может перестать работать в любой момент из-за изменений в API NS.Gifts.
- Данная библиотека предоставляется "КАК ЕСТЬ", без каких-либо гарантий, явных или подразумеваемых.
- Используйте на свой страх и риск.

---

## 📜 Лицензия

[MIT](LICENSE)
