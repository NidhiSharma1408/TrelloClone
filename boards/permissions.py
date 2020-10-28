from rest_framework.permissions import BasePermission

class IsMemberOrAllowed(BasePermission):
    def has_object_permission(self, request, view, obj):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return bool(request.user and (request.user.profile in obj.members.all() or not obj.is_private))

class IsMember(BasePermission):
    def has_object_permission(self,request,view,obj):
        print(view)
        return bool(request.user and request.user.profile in obj.members.all())

class IsAdminOfBoard(BasePermission):
    def has_object_permission(self,request,view,obj):
        return bool(request.user and request.user.profile in obj.admins.all())

class IsAllowedInBoard(BasePermission):
    def has_object_permission(self,request,view,obj):
        return bool(request.user and (request.user.profile in obj.team.members.all() or request.user.profile in obj.guests.all()))
