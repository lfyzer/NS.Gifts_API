nsgifts
A modern, async Python client for NS.Gifts API (unofficial).

Features
🚀 Fully Async: Built with asyncio and aiohttp for high performance.

🔄 Auto Token Management: Automatically handles token refresh to keep your session active.

🛡️ Robust Error Handling: Provides detailed and specific exception classes for different types of errors.

⏱️ Retry Mechanism: Implements an intelligent retry logic with exponential backoff for transient errors.

🧩 Pydantic Models: Uses Pydantic for type-safe data validation and clear schemas.

🎮 Steam Gift Support: Complete implementation of all Steam gift-related API functionality.

Installation
You can install the library using pip:

pip install nsgifts

Quick Start
Here's a simple example of how to log in and get user information.

import asyncio
from nsgifts import NSGiftsClient, APIError

credentials = [
    "your_email@example.com",
    "your_password"
]

async def main(credentials):
    """Main function demonstrating client usage."""
    try:
        async with NSGiftsClient() as client:
            login_result = await client.login(credentials[0], credentials[1])
            print(f"Logged in, token valid until: {login_result['valid_thru']}")
            
            user_info = await client.get_user_info()
            print(f"User Info: {user_info}")

    except APIError as e:
        print(f"An API error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main(credentials))

Examples
Below are more detailed examples for different use cases. You can find these in the examples/ directory of the repository.

1. Checking Your Balance
This example shows how to log in and check your current balance.

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
    your_email = "your_email@example.com"
    your_password = "your_password"
    asyncio.run(check_user_balance(your_email, your_password))

2. Getting All Services
This script fetches and prints all available services from the API.

import asyncio
from nsgifts import NSGiftsClient

async def get_services(email, password):
    async with NSGiftsClient() as client:
        await client.login(email, password)
        services_data = await client.get_all_services()
        
        print("Available Services:")
        for category in services_data.get('categories', []):
            print(f"Category ID: {category['id']}, Name: {category['name']}")
        
        print("\nAll services data retrieved successfully.")

if __name__ == "__main__":
    your_email = "your_email@example.com"
    your_password = "your_password"
    asyncio.run(get_services(your_email, your_password))

3. Creating and Paying for an Order
This example demonstrates the full flow of creating a new order and then paying for it. It uses uuid to generate a unique custom_id for the order.

import asyncio
import uuid
from nsgifts import NSGiftsClient

async def create_and_pay_order(email, password, service_id, quantity):
    async with NSGiftsClient() as client:
        await client.login(email, password)

        # 1. Create the order
        custom_order_id = str(uuid.uuid4())
        print(f"Creating order with custom ID: {custom_order_id}")
        order_creation_response = await client.create_order(
            service_id=service_id,
            quantity=quantity,
            custom_id=custom_order_id
        )
        print("Order Creation Response:", order_creation_response)

        # 2. Pay for the order
        payment_response = await client.pay_order(custom_id=custom_order_id)
        print("Payment Response:", payment_response)

if __name__ == "__main__":
    your_email = "your_email@example.com"
    your_password = "your_password"
    
    # Example order details:
    service_to_buy = 123  # Replace with a real service ID
    quantity_to_buy = 1.0
    
    asyncio.run(create_and_pay_order(your_email, your_password, service_to_buy, quantity_to_buy))

Error Handling
The client is designed to handle various API errors gracefully. You can catch specific exceptions to handle different failure scenarios:

APIConnectionError: For network connectivity issues.

APITimeoutError: When a request exceeds the timeout.

APIAuthenticationError: For login failures, invalid tokens, or unauthorized access.

APIClientError: For client-side errors like a bad request (4xx).

APIServerError: For server-side issues (5xx).

APIError: The base class for all client-related exceptions.

Here's an example of how to handle different errors:

import asyncio
from nsgifts import (
    NSGiftsClient,
    APIAuthenticationError,
    APITimeoutError,
    APIClientError,
)

async def handle_errors():
    async with NSGiftsClient() as client:
        try:
            # Example that might cause an authentication error
            await client.login("wrong_email@example.com", "wrong_password")
            
        except APIAuthenticationError as e:
            print(f"Authentication failed: {e}")
        except APIClientError as e:
            print(f"Client error occurred: {e}")
        except APITimeoutError as e:
            print(f"Request timed out: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(handle_errors())
