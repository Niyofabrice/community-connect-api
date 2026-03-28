from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrStaff(BasePermission):
    """
    Staff/Admin: Can do anything
    Citizens: Can only view/edit/delete their own reports
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.role in ['STAFF', 'ADMIN']:
            return True
        
        is_owner = obj.user == request.user
        
        # Prevent Citizens from deleting reports that aren't PENDING
        if request.method == 'DELETE' and obj.status != 'PENDING':
            return False
            
        return is_owner