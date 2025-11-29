from fastapi import HTTPException, status


class InvalidSitemapPassword(HTTPException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Invalid sitemap password"

    def __init__(self):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail
        )

