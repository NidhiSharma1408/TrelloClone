from rest_framework.permissions import BasePermission
from . import models
class IsMemberOrAllowed(BasePermission):
    def has_object_permission(self, request, view, obj):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return bool(request.user and (request.user.profile in obj.members.all() or not obj.is_private))

class IsMember(BasePermission):
    def has_object_permission(self,request,view,obj):
        return bool(request.user and (request.user.profile in obj.members.all()))

class IsBoardAdmin(BasePermission):
    def has_object_permission(self,request,view,obj):
        return bool(request.user and (request.user.profile in obj.admins.all()))

class IsAllowedToView(BasePermission):
    def has_object_permission(self,request,view,obj):
        if obj.preference.permission_level == models.Preference.permission.public:
            return True
        if obj.preference.permission_level == models.Preference.permission.team_members:
            if request.user.profile in obj.team.members.all():
                return True
            else:
                False
