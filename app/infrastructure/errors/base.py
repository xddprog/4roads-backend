from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"

    def __init__(self, detail: str | None = None):
        super().__init__(
            status_code=self.status_code,
            detail=detail or self.detail
        )


class InternalServerError(HTTPException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Internal server error"

    def __init__(self, detail: str | None = None):
        super().__init__(
            status_code=self.status_code,
            detail=detail or self.detail
        )