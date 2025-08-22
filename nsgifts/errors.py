class APIError(Exception):
    """Base exception for API client errors.
    
    This serves as the base class for all exceptions that may occur when interacting 
    with the API. All specific API error types inherit from this class.
    """


class APIConnectionError(APIError):
    """Raised for network connection errors.
    
    This exception occurs when there are issues with the network connection, such as:
    - Unable to establish a connection to the server
    - Connection interrupted during a request
    - DNS resolution problems
    - Socket errors
    - Proxy connection failures
    
    This typically indicates issues with the client's network, internet service provider,
    or intermediate network infrastructure rather than problems with the API server itself.
    """


class APITimeoutError(APIError):
    """Raised when an API request times out.
    
    This exception occurs when an API request does not receive a response within
    the established timeout period. Timeouts may happen due to:
    - High network latency
    - Server overload leading to slow response times
    - Long-running operations on the server side
    - Network congestion
    
    Increasing the client's timeout settings might help in some cases, but
    persistent timeouts could indicate server-side performance issues.
    """


class APIAuthenticationError(APIError):
    """Raised for authentication or token refresh errors.
    
    This exception occurs when there are problems with authentication, such as:
    - Invalid credentials (incorrect username/password)
    - Expired access token
    - Failed token refresh attempts
    - Access denied to requested resource (401 Unauthorized)
    - Revoked or invalid API keys
    - Account restrictions or suspensions
    
    This typically requires user intervention to provide correct credentials
    or resolve account-related issues.
    """


class APIServerError(APIError):
    """Raised when the API returns a 5xx error.
    
    This exception occurs when there are problems on the server side (status codes 500-599), such as:
    - 500 Internal Server Error: Unexpected condition on the server
    - 502 Bad Gateway: Invalid response from an upstream server
    - 503 Service Unavailable: Server is temporarily unavailable (maintenance or overload)
    - 504 Gateway Timeout: Upstream server failed to respond in time
    - 507 Insufficient Storage: Server storage limit reached
    
    These errors are generally temporary and not caused by the client request.
    Implementing retry logic with exponential backoff is recommended for handling these errors.
    """


class APIClientError(APIError):
    """Raised when the API returns a 4xx error.
    
    This exception occurs when there are errors related to the client request (status codes 400-499), such as:
    - 400 Bad Request: The request was malformed or contained invalid parameters
    - 403 Forbidden: The client lacks necessary permissions for the requested resource
    - 404 Not Found: The requested resource does not exist
    - 409 Conflict: The request conflicts with the current state of the server
    - 422 Unprocessable Entity: The server understands the content type but cannot process the request
    - 429 Too Many Requests: The client has sent too many requests in a given time period
    
    These errors typically require modifying the request parameters or addressing
    permission issues before retrying the request.
    """