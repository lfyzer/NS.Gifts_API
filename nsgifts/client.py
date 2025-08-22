import asyncio
import logging
import time
import uuid

from typing import Any, Dict, Optional, Union

import aiohttp
from aiohttp import ClientConnectionError, ClientResponseError, ClientTimeout

from .errors import (
    APIError,
    APIConnectionError,
    APITimeoutError,
    APIAuthenticationError,
    APIServerError,
    APIClientError,
)
from .models import (
    Region,
    UserLoginSchema,
    UserSchema,
    CategoryRequest,
    CreateOrder,
    PayOrder,
    SteamRubCalculate,
    SteamGiftOrderCalculate,
    SteamGiftOrder,
    SteamPackageRequest,
)
from .api_endpoints import API_ENDPOINTS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class NSGiftsClient:
    """Client for interacting with the NS Gifts API.

    This client handles authentication, token management, and API requests to the
    NS Gifts service. It supports automatic token refresh, retry logic for
    transient errors, and server error detection with a cooldown.

    Attributes:
        base_url (str): The base URL for the API.
        max_retries (int): Maximum number of retry attempts for failed requests.
        request_timeout (int): Timeout in seconds for API requests.
        server_error_cooldown (int): Cooldown in seconds after detecting a server
            error.
        token_refresh_buffer (int): Time buffer in seconds before token expiry to
            trigger refresh.
        token (Optional[str]): The current JWT token.
        token_expiry (int): Unix timestamp when the token expires.
        email (Optional[str]): User's email for authentication.
        password (Optional[str]): User's password for authentication.
        session (Optional[aiohttp.ClientSession]): The aiohttp ClientSession for making requests.
    """

    def __init__(
        self,
        base_url: str = "https://api.ns.gifts",
        max_retries: int = 3,
        request_timeout: int = 30,
        server_error_cooldown: int = 300,
        token_refresh_buffer: int = 300,
    ):
        """Initializes the NSGiftsClient.

        Args:
            base_url (str): The base URL for the API.
            max_retries (int): Maximum retry attempts.
            request_timeout (int): Request timeout in seconds.
            server_error_cooldown (int): Cooldown after server error.
            token_refresh_buffer (int): Buffer before token expiry for refresh.
        """
        self.base_url = base_url
        self._max_retries = max_retries
        self._request_timeout = request_timeout
        self._server_error_cooldown = server_error_cooldown
        self._token_refresh_buffer = token_refresh_buffer
        self.token: Optional[str] = None
        self.token_expiry: int = 0
        self.email: Optional[str] = None
        self.password: Optional[str] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self._token_lock = asyncio.Lock()
        self._session_lock = asyncio.Lock()
        self._server_error_detected = False
        self._server_error_timestamp = 0

    async def __aenter__(self):
        """Enters the async context manager."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exits the async context manager, closing the session."""
        await self.close()

    async def close(self):
        """Closes the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    def _get_headers(self) -> Dict[str, str]:
        """Gets the HTTP headers for API requests.

        Returns:
            Dict[str, str]: Dictionary of headers, including Authorization if token is set.
        """
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _ensure_session(self):
        """Ensures an active aiohttp session exists."""
        if not self.session or self.session.closed:
            async with self._session_lock:
                if not self.session or self.session.closed:
                    self.session = aiohttp.ClientSession(
                        raise_for_status=True,
                    )
                    logger.debug("Created new HTTP session")

    async def _ensure_valid_token(self):
        """Ensures the token is valid, refreshing if necessary.

        Raises:
            APIAuthenticationError: If refresh fails or credentials missing.
        """
        current_time = int(time.time())
        if not self.token or (
            self.token_expiry - current_time < self._token_refresh_buffer
        ):
            async with self._token_lock:
                # Re-check inside the lock to prevent a race condition
                current_time = int(time.time())
                if not self.token or (
                    self.token_expiry - current_time
                    < self._token_refresh_buffer
                ):
                    if not self.email or not self.password:
                        raise APIAuthenticationError(
                            "Token expired, but credentials are not set for "
                            "refresh. Call login() first."
                        )
                    await self._request_with_retries(
                        "POST",
                        API_ENDPOINTS["login"],
                        json_data={
                            "email": self.email,
                            "password": self.password,
                        },
                        is_auth_request=True,
                    )
                    logger.info("Token refreshed successfully")

    async def _request_with_retries(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        is_auth_request: bool = False,
    ) -> Dict[str, Any]:
        """Performs a request with retry and error handling logic.

        This is a centralized method to handle common request patterns.
        It handles connection errors, timeouts, and server errors with a
        backoff strategy.

        Args:
            method (str): HTTP method (e.g., 'POST').
            endpoint (str): API endpoint path.
            json_data (Optional[Dict]): Optional JSON payload.
            is_auth_request (bool): True if this is an authentication request.

        Returns:
            Dict[str, Any]: Response JSON as a dictionary.

        Raises:
            APIConnectionError: If connection fails.
            APITimeoutError: If timeout.
            APIServerError: If server error.
            APIAuthenticationError: If login fails.
            APIClientError: If client error occurs (4xx responses).
        """
        url = f"{self.base_url}{endpoint}"
        last_error = None
        await self._ensure_session()

        for attempt in range(self._max_retries):
            if (
                self._server_error_detected
                and not self._is_cooldown_expired()
                and not is_auth_request
            ):
                cooldown_remaining = (
                    self._server_error_timestamp
                    + self._server_error_cooldown
                    - int(time.time())
                )
                raise APIServerError(
                    f"API server error detected. Avoiding requests for "
                    f"{cooldown_remaining} more seconds."
                )

            try:
                async with self.session.request(
                    method,
                    url,
                    json=json_data,
                    headers=self._get_headers(),
                    timeout=self._request_timeout,
                ) as response:
                    result = await response.json()

                    if (
                        endpoint == API_ENDPOINTS["login"]
                        or endpoint == API_ENDPOINTS["signup"]
                    ):
                        self.token = result.get("access_token")
                        self.token_expiry = result.get(
                            "valid_thru", int(time.time()) + 5400
                        )

                    return result

            except ClientResponseError as e:
                last_error = e
                if 400 <= e.status < 500:
                    if e.status == 401 and not is_auth_request:
                        logger.warning(
                            "Received 401 Unauthorized. Attempting token "
                            "refresh..."
                        )
                        try:
                            await self._ensure_valid_token()
                            # Retry the request with the new token
                            continue
                        except APIAuthenticationError:
                            # Refresh failed, so the original 401 is a
                            # permanent issue
                            raise APIAuthenticationError(
                                "Authentication failed after token refresh."
                            ) from e
                    else:
                        raise APIClientError(
                            f"Client error at {url}: {e.status} {e.message}"
                        ) from e
                else:  # 500+
                    self._server_error_detected = True
                    self._server_error_timestamp = int(time.time())
                    raise APIServerError(
                        f"Server error at {url}: {e.status} {e.message}"
                    ) from e
            except (ClientConnectionError, ClientTimeout) as e:
                last_error = e
                error_type = (
                    "Connection error"
                    if isinstance(e, ClientConnectionError)
                    else "Request timeout"
                )
                logger.warning(
                    f"{error_type} on attempt {attempt + 1}/"
                    f"{self._max_retries} for {url}: {e}"
                )

                if attempt < self._max_retries - 1:
                    wait_time = 1 * (2**attempt)
                    await asyncio.sleep(wait_time)
                else:
                    ErrorClass = (
                        APIConnectionError
                        if isinstance(e, ClientConnectionError)
                        else APITimeoutError
                    )
                    raise ErrorClass(
                        f"{error_type} after {self._max_retries} attempts."
                    ) from last_error

        raise APIError("Request failed after all retries.") from last_error

    def _is_cooldown_expired(self) -> bool:
        """Checks if the server error cooldown has expired."""
        current_time = int(time.time())
        return (
            self._server_error_timestamp + self._server_error_cooldown
        ) <= current_time

    def is_server_error_detected(self) -> bool:
        """Checks if a server error is currently detected.

        Returns:
            True if server error detected and cooldown active, else False.
        """
        if self._server_error_detected and self._is_cooldown_expired():
            self._server_error_detected = False
        return self._server_error_detected

    def reset_server_error_state(self) -> None:
        """Resets the server error detection state."""
        self._server_error_detected = False
        self._server_error_timestamp = 0
        logger.info("Server error state has been manually reset")

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Logs in the user and retrieves a JWT token.

        Args:
            email (str): User's email/username.
            password (str): User's password.

        Returns:
            Response dictionary with token.

        Raises:
            APIAuthenticationError: If login fails.
            APIServerError: If server error.
            APIConnectionError: If connection fails.
            APITimeoutError: If timeout.
        """
        self.email = email
        self.password = password
        data = UserLoginSchema(email=email, password=password).model_dump()
        return await self._request_with_retries(
            "POST", API_ENDPOINTS["login"], data, is_auth_request=True
        )

    async def signup(
        self, email: str, role: str, bybit_deposit: str = "0"
    ) -> Dict[str, Any]:
        """Signs up a new user.

        Args:
            email (str): User's email/username.
            role (str): User's role.
            bybit_deposit (str): Bybit deposit (default "0").

        Returns:
            Response dictionary with token.

        Raises:
            APIError: If signup fails.
            APIServerError: If server error.
            APIConnectionError: If connection fails.
            APITimeoutError: If timeout.
        """
        self.email = email
        data = UserSchema(
            email=email, role=role, bybit_deposit=bybit_deposit
        ).model_dump()
        return await self._request_with_retries(
            "POST", API_ENDPOINTS["signup"], data, is_auth_request=True
        )

    async def get_all_services(self) -> Dict[str, Any]:
        """Gets all available services.

        Returns:
            Dictionary of services.
        """
        return await self._make_authenticated_request(
            "POST", API_ENDPOINTS["get_all_services"]
        )

    async def get_categories(self) -> Dict[str, Any]:
        """Gets service categories.

        Returns:
            Dictionary of categories.
        """
        return await self._make_authenticated_request(
            "POST", API_ENDPOINTS["get_categories"]
        )

    async def get_services_by_category(self, category_id: int) -> Dict[str, Any]:
        """Gets services by category ID.

        Args:
            category_id: ID of the category.

        Returns:
            Dictionary of services in the category.
        """
        data = CategoryRequest(category_id=category_id).model_dump()
        return await self._make_authenticated_request(
            "POST", API_ENDPOINTS["get_services_by_category"], json_data=data
        )

    async def create_order(
        self,
        service_id: int,
        quantity: float,
        custom_id: Optional[str] = None,
        data: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates a new order.

        Args:
            service_id (int): ID of the service.
            quantity (float): Quantity to order.
            custom_id (Optional[str]): Optional custom ID (auto-generated if None).
            data (Optional[str]): Optional additional data.

        Returns:
            Order creation response.
        """
        if not custom_id:
            custom_id = str(uuid.uuid4())

        order_data = CreateOrder(
            service_id=service_id,
            quantity=quantity,
            custom_id=custom_id,
            data=data,
        ).model_dump(exclude_none=True)

        return await self._make_authenticated_request(
            "POST", API_ENDPOINTS["create_order"], json_data=order_data
        )

    async def pay_order(self, custom_id: str) -> Dict[str, Any]:
        """Pays for an order.

        Args:
            custom_id (str): Custom ID of the order.

        Returns:
            Payment response.
        """
        data = PayOrder(custom_id=custom_id).model_dump()
        return await self._make_authenticated_request(
            "POST", API_ENDPOINTS["pay_order"], json_data=data
        )

    async def check_balance(self) -> Dict[str, Any]:
        """Checks the user's balance.

        Returns:
            Balance information.
        """
        return await self._make_authenticated_request(
            "POST", API_ENDPOINTS["check_balance"]
        )

    async def calculate_steam_amount(self, amount: int) -> Dict[str, Any]:
        """Calculates Steam amount.

        Args:
            amount (int): Amount in RUB.

        Returns:
            Calculation result.
        """
        data = SteamRubCalculate(amount=amount).model_dump()
        return await self._make_authenticated_request(
            "POST", API_ENDPOINTS["calculate_steam_amount"], json_data=data
        )

    async def get_steam_currency_rate(self) -> Dict[str, Any]:
        """Gets current Steam currency rate.

        Returns:
            Dict[str, Any]: Currency rate information.
        """
        return await self._make_authenticated_request(
            "POST", API_ENDPOINTS["get_steam_currency_rate"]
        )

    async def get_user_info(self) -> Dict[str, Any]:
        """Gets user information.

        Returns:
            Dict[str, Any]: User info dictionary.
        """
        return await self._make_authenticated_request(
            "POST", API_ENDPOINTS["get_user_info"]
        )

    async def calculate_steam_gift(
        self, sub_id: int, region: Union[Region, str]
    ) -> Dict[str, Any]:
        """Calculates Steam gift order.

        Args:
            sub_id (int): Steam sub ID.
            region (Union[Region, str]): Region (RU, KZ, UA).

        Returns:
            Dict[str, Any]: Calculation result.
        """
        data = SteamGiftOrderCalculate(
            sub_id=sub_id, region=region
        ).model_dump()
        return await self._make_authenticated_request(
            "POST", API_ENDPOINTS["calculate_steam_gift"], json_data=data
        )

    async def create_steam_gift_order(
        self,
        friend_link: str,
        sub_id: int,
        region: Union[Region, str],
        gift_name: Optional[str] = None,
        gift_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates a Steam gift order.

        Args:
            friend_link (str): Friend's Steam link.
            sub_id (int): Steam sub ID.
            region (Union[Region, str]): Region (RU, KZ, UA).
            gift_name (Optional[str]): Optional gift name.
            gift_description (Optional[str]): Optional gift description.

        Returns:
            Dict[str, Any]: Order creation response.
        """
        data = SteamGiftOrder(
            friend_link=friend_link,
            sub_id=sub_id,
            region=region,
            gift_name=gift_name,
            gift_description=gift_description,
        ).model_dump(by_alias=True, exclude_none=True)

        return await self._make_authenticated_request(
            "POST",
            API_ENDPOINTS["create_steam_gift_order"],
            json_data=data,
        )

    async def pay_steam_gift_order(self, custom_id: str) -> Dict[str, Any]:
        """Pays for a Steam gift order.

        Args:
            custom_id (str): Custom ID of the order.

        Returns:
            Dict[str, Any]: Payment response.
        """
        data = PayOrder(custom_id=custom_id).model_dump()
        return await self._make_authenticated_request(
            "POST", API_ENDPOINTS["pay_steam_gift_order"], json_data=data
        )

    async def get_order_info(self, custom_id: str) -> Dict[str, Any]:
        """Gets order information.

        Args:
            custom_id (int): Custom ID of the order.

        Returns:
            Dict[str, Any]: Order details.
        """
        data = PayOrder(custom_id=custom_id).model_dump()
        return await self._make_authenticated_request(
            "POST", API_ENDPOINTS["get_order_info"], json_data=data
        )

    async def get_steam_package_price(self, package_id: int) -> Dict[str, Any]:
        """Gets Steam package prices for regions.

        Args:
            package_id (int): Steam package ID.

        Returns:
            Dict[str, Any]: Price information.
        """
        data = SteamPackageRequest(package_id=package_id).model_dump()
        return await self._make_authenticated_request(
            "POST", API_ENDPOINTS["get_steam_package_price"], json_data=data
        )

    async def add_ip_to_whitelist(self, ip: str) -> Dict[str, Any]:
        """Adds an IP to the whitelist.

        Args:
            ip (str): IP address to add.

        Returns:
            Dict[str, Any]: Response dictionary.
        """
        return await self._make_authenticated_request(
            "POST", API_ENDPOINTS["add_ip_to_whitelist"], json_data={"ip": ip}
        )

    async def remove_ip_from_whitelist(self, ip: str) -> Dict[str, Any]:
        """Removes an IP from the whitelist.

        Args:
            ip (str): IP address to remove.

        Returns:
            Dict[str, Any]: Response dictionary.
        """
        return await self._make_authenticated_request(
            "POST",
            API_ENDPOINTS["remove_ip_from_whitelist"],
            json_data={"ip": ip},
        )

    async def list_whitelist_ips(self) -> Dict[str, Any]:
        """Lists whitelisted IPs.

        Returns:
            Dict[str, Any]: List of IPs.
        """
        return await self._make_authenticated_request(
            "POST", API_ENDPOINTS["list_whitelist_ips"]
        )

    async def _make_authenticated_request(
        self, method: str, endpoint: str, json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Makes an authenticated request, ensuring a valid token exists.

        Args:
            method (str): HTTP method (e.g., 'POST').
            endpoint (str): API endpoint path.
            json_data (Optional[Dict]): Optional JSON payload.

        Returns:
            Response JSON as a dictionary.

        Raises:
            APIAuthenticationError: If not authenticated or login failed.
            APIError: For other client or server errors.
        """
        if not self.token and not (self.email and self.password):
            raise APIAuthenticationError(
                "Authentication required. Call login() or signup() first."
            )
        await self._ensure_valid_token()
        return await self._request_with_retries(method, endpoint, json_data)