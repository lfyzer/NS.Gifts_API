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