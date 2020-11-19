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
def is_allowed_to_watch_or_star(request,board):
    if board.preference.permission_level == models.Preference.permission.public:
            return True
    elif board.preference.permission_level == models.Preference.permission.team_members:
        if request.user.profile in board.team.members.all():
            return True
    elif request.user.profile in board.members.all():
        return True
    else:
        return False