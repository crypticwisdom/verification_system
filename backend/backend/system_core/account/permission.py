from rest_framework.permissions import BasePermission
from account.models import User, UserRole, UserDetail


class IsSuperAdmin(BasePermission):
    """
    Allows access only to authenticated super admin users.
    """

    def has_permission(self, request, view):
        is_admin_user_type = request.user.userdetail.user_type == "platform"
        is_admin_user_role = request.user.userdetail.userrole.user_role == "super-admin"
        return bool(request.user.is_superuser and is_admin_user_role and is_admin_user_type)


class IsPartnerManager(BasePermission):
    """
    Allows access only to authenticated Partner Managers.
    """

    def has_permission(self, request, view):
        is_admin_user_type = request.user.userdetail.user_type == "platform"
        is_admin_user_role = request.user.userdetail.userrole.user_role == "partner-manager"
        return bool(is_admin_user_role and is_admin_user_type)


class IsIndividual(BasePermission):
    """
    Allows access only to authenticated Partner Managers.
    """

    def has_permission(self, request, view):
        is_admin_user_type = request.user.userdetail.user_type == "individual"
        is_admin_user_role = request.user.userdetail.userrole.user_role == "individual"
        return bool(is_admin_user_role and is_admin_user_type)


class IsAgency(BasePermission):
    """
    Allows access only to authenticated Agency.
    """

    def has_permission(self, request, view):
        is_admin_user_type = request.user.userdetail.user_type == "agency"
        is_admin_user_role = request.user.userdetail.userrole.user_role == "agency"
        return bool(is_admin_user_role and is_admin_user_type)


class IsSubAgency(BasePermission):
    """
    Allows access only to Sub-Agency.
    """

    def has_permission(self, request, view):
        is_admin_user_type = request.user.userdetail.user_type == "agency"
        is_admin_user_role = request.user.userdetail.userrole.user_role == "sub-agency"
        return bool(is_admin_user_role and is_admin_user_type)


class IsBusiness(BasePermission):
    """
    Allows access only to Business.
    """

    def has_permission(self, request, view):
        is_admin_user_type = request.user.userdetail.user_type == "corporate-business"
        is_admin_user_role = request.user.userdetail.userrole.user_role == "corporate-business"
        return bool(is_admin_user_role and is_admin_user_type)


class IsDeveloper(BasePermission):
    """
    Allows access only to developer users.
    """

    def has_permission(self, request, view):
        is_developer_user_type = request.user.userdetail.user_type == "developer"
        is_developer_user_role = request.user.userdetail.userrole.user_role == "developer"
        return bool(is_developer_user_type and is_developer_user_role)
