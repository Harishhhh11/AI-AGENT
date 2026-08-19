from app.exceptions.base import AppException


class OrganizationNotFoundException(AppException):

    def __init__(self):
        super().__init__(
            message="Organization not found.",
            status_code=404,
        )


class OrganizationAlreadyExistsException(AppException):

    def __init__(self, field: str):

        super().__init__(
            message=f"Organization with this {field} already exists.",
            status_code=409,
        )