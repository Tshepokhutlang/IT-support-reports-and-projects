# IT Helpdesk Ticket Management System

A Django-based helpdesk ticket system for small businesses, schools, and organizations.

## Features
- End users can submit tickets, attach screenshots, and track status.
- Technicians can view assigned tickets, update status, and add notes.
- Administrators can manage users, assign tickets, and view support metrics.
- Dashboard shows ticket counts, average resolution time, and technician performance.

## Setup
1. Activate the workspace virtual environment:
   ```powershell
   .\.venv\Scripts\Activate
   ```
2. Run migrations:
   ```powershell
   .\.venv\Scripts\python.exe manage.py migrate
   ```
3. Create an admin user:
   ```powershell
   .\.venv\Scripts\python.exe manage.py createsuperuser
   ```
4. Start the development server:
   ```powershell
   .\.venv\Scripts\python.exe manage.py runserver
   ```

## Access
- Frontend: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Notes
- The project uses SQLite for local development.
- For production, configure a proper database and secure Django settings.
