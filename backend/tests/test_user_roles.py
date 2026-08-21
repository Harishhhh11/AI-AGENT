"""Regression tests for organization-scoped user role management."""


def test_role_assignment_rejects_cross_organization_role():
    """The service must never assign another tenant's role."""
    from app.services.user_service import UserService

    class FakeRepository:
        def get_by_id_in_organization(self, user_id, organization_id):
            return object()

        def get_role_in_organization(self, role_id, organization_id):
            return None

    service = object.__new__(UserService)
    service.repository = FakeRepository()

    try:
        service.assign_role(1, 10, 99)
    except ValueError as exc:
        assert str(exc) == "Role not found in this organization."
    else:
        raise AssertionError("Cross-organization role assignment was allowed.")


def test_role_removal_rejects_cross_organization_role():
    """Role removal must also be organization-scoped."""
    from app.services.user_service import UserService

    class FakeRepository:
        def get_by_id_in_organization(self, user_id, organization_id):
            return object()

        def get_role_in_organization(self, role_id, organization_id):
            return None

    service = object.__new__(UserService)
    service.repository = FakeRepository()

    try:
        service.remove_role(1, 10, 99)
    except ValueError as exc:
        assert str(exc) == "Role not found in this organization."
    else:
        raise AssertionError("Cross-organization role removal was allowed.")
