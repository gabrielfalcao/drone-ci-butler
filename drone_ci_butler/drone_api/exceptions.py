from requests import Response


class ClientError(Exception):
    def __init__(self, response: Response, message: str):
        self.response = response
        message = message or f"{response.status_code}: {response.text}"
        super().__init__(f"{response.request.url} -> {message}")


class APIException(ClientError):
    def __init__(self, response: Response):
        self.response = response
        super().__init__(response, f"{(response.text or '').strip()}")


class NotFound(APIException):
    def __init__(self, response: Response):
        super().__init__(response)


def invalid_response(response: Response):
    if response.status_code == 404:
        return NotFound(response)

    return APIException(response)
