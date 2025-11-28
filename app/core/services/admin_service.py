from app.infrastructure.database.models.admin import Admin
from app.core.repositories.admin_repository import AdminRepository


class AdminService:
    def __init__(self, repository: AdminRepository):
        self.repository = repository
