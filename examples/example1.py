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
