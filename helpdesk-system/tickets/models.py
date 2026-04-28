from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class HelpdeskUser(AbstractUser):
    ROLE_ENDUSER = 'enduser'
    ROLE_TECHNICIAN = 'technician'
    ROLE_ADMIN = 'administrator'

    ROLE_CHOICES = [
        (ROLE_ENDUSER, 'End User'),
        (ROLE_TECHNICIAN, 'Technician'),
        (ROLE_ADMIN, 'Administrator'),
    ]

    department = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_ENDUSER)

    def is_technician(self):
        return self.role == self.ROLE_TECHNICIAN

    def is_administrator(self):
        return self.role == self.ROLE_ADMIN


class Ticket(models.Model):
    STATUS_OPEN = 'open'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_PENDING = 'pending'
    STATUS_RESOLVED = 'resolved'
    STATUS_CLOSED = 'closed'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED, 'Closed'),
    ]

    CATEGORY_NETWORK = 'network'
    CATEGORY_POWER = 'power'
    CATEGORY_PRINTER = 'printer'
    CATEGORY_SOFTWARE = 'software'
    CATEGORY_EMAIL = 'email'
    CATEGORY_SLOW = 'slow'
    CATEGORY_PASSWORD = 'password'
    CATEGORY_HARDWARE = 'hardware'
    CATEGORY_INTERNET = 'internet'
    CATEGORY_SECURITY = 'security'

    CATEGORY_CHOICES = [
        (CATEGORY_NETWORK, 'Network / Wi-Fi Problem'),
        (CATEGORY_POWER, 'Computer Not Turning On'),
        (CATEGORY_PRINTER, 'Printer Issue'),
        (CATEGORY_SOFTWARE, 'Software Installation'),
        (CATEGORY_EMAIL, 'Email Problem'),
        (CATEGORY_SLOW, 'Slow Computer'),
        (CATEGORY_PASSWORD, 'Password Reset'),
        (CATEGORY_HARDWARE, 'Hardware Failure'),
        (CATEGORY_INTERNET, 'Internet Connectivity'),
        (CATEGORY_SECURITY, 'Security / Virus Issue'),
    ]

    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_URGENT = 'urgent'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_URGENT, 'Urgent'),
    ]

    ticket_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(HelpdeskUser, on_delete=models.CASCADE, related_name='tickets')
    user_name = models.CharField(max_length=150)
    department = models.CharField(max_length=100)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    assigned_to = models.ForeignKey(
        HelpdeskUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        limit_choices_to={'role': HelpdeskUser.ROLE_TECHNICIAN},
    )
    created_date = models.DateTimeField(default=timezone.now)
    resolved_date = models.DateTimeField(null=True, blank=True)
    screenshot = models.FileField(upload_to='screenshots/', null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f"Ticket #{self.ticket_id}: {self.get_category_display()}"

    def is_resolved(self):
        return self.status == self.STATUS_RESOLVED

    def resolution_time_minutes(self):
        if self.resolved_date:
            return int((self.resolved_date - self.created_date).total_seconds() / 60)
        return None
