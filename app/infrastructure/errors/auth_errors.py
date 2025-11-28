from fastapi import HTTPException, status


class InvalidCredentials(HTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Incorrect login or password"

    def __init__(self):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AccessDenied(HTTPException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Access denied"
    
    def __init__(self):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail,
        )