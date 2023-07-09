from rest_framework import permissions
from django.db.models import Q
from app.models import *

class IsBuisnessMembers(permissions.BasePermission) :
    """
        Permission for membersof a company
    """
    def has_permission(self, request, view):
        return super().has_permission(request, view)
    
class IsPostOwner(permissions.BasePermission) :
    """
        Permission for members of a company
    """

    def has_permission(self, request, view):
        post = Post.objects.get(pk = int(request.data.get('post')))

        return request.user in post.company.users.all()
    
