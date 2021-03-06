from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import GuestEmail,EmailActivation
from .forms import UserAdminChangeForm,UserAdminCreationForm

User = get_user_model()

class UserAdmin(BaseUserAdmin):

    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
        
    def has_view_or_change_permission(self, request, obj=None):
        return request.user.is_superuser

    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'admin','staff')
    list_filter = ('admin','staff','is_active')
    fieldsets = (
        (None, {'fields': ('email','full_name','password')}),
        #('Personal info', {'fields': ()}),
        ('Permissions', {'fields': ('admin','staff','is_active')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

class EmailActivationAdmin(admin.ModelAdmin):
    search_fields = ['email']
    class Meta:
        model = EmailActivation

admin.site.register(GuestEmail)
admin.site.register(User,UserAdmin)
admin.site.register(EmailActivation,EmailActivationAdmin)
admin.site.unregister(Group)
