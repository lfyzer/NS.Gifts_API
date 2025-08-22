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

## 📘 Пример использования

📂 Файл: `examples/basic_usage.py`

```python
import asyncio
from nsgifts import NSGiftsClient

async def main():
    async with NSGiftsClient() as client:
        await client.login("test@example.com", "password123")
        balance = await client.check_balance()
        print("Balance:", balance)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## ⚠️ Disclaimer

- Это **неофициальная библиотека**.
- Я **не сотрудничаю** с NS.Gifts и не имею отношения к их сервису.
- Используйте на свой страх и риск.

---

## 📜 Лицензия

[MIT](LICENSE)
