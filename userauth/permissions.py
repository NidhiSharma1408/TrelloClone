from rest_framework import permissions

class IsLoggedInUserOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user or request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        return request.user and (obj == request.user or request.user.is_staff)

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_staff

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self,request,view,obj):
        return (request.user == obj) or (request.user.is_staff)