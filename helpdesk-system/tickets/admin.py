from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import HelpdeskUser, Ticket


@admin.register(HelpdeskUser)
class HelpdeskUserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Helpdesk Profile', {'fields': ('role', 'department')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'is_staff')
    list_filter = ('role', 'department', 'is_staff')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'user_name', 'category', 'priority', 'status', 'assigned_to', 'created_date')
    list_filter = ('status', 'category', 'priority', 'assigned_to')
    search_fields = ('user_name', 'description', 'department')
    raw_id_fields = ('user', 'assigned_to')
