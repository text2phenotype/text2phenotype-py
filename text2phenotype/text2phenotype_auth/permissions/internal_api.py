from rest_framework.exceptions import (
    NotAuthenticated,
    PermissionDenied,
)
from rest_framework.permissions import BasePermission

from text2phenotype.constants.environment import Environment


class InternalApiPermission(BasePermission):
    def has_permission(self, request, view):
        if not Environment.INTERNAL_COMMUNICATION_API_KEY.value:
            raise NotAuthenticated('Internal API is not allowed for this environment')

        api_key = request.META.get('HTTP_X_API_KEY')
        if not api_key:
            raise NotAuthenticated('"X-Api-Key" HTTP header is not passed or empty')

        if api_key != Environment.INTERNAL_COMMUNICATION_API_KEY.value:
            raise PermissionDenied('Invalid Api Key')

        return True
