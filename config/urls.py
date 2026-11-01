from django.contrib import admin
from django.urls import path
from library import views
from library import api

urlpatterns = [
    path("admin/", admin.site.urls),

    # PWA Service Worker & Manifest
    path("manifest.json", views.pwa_manifest_view, name="pwa_manifest"),
    path("sw.js", views.pwa_sw_view, name="pwa_sw"),

    # Gateways & Main
    path("", views.home, name="home"),
    path("auth/", views.auth_gateway, name="auth_gateway"),
    path("login/", views.auth_gateway, name="login"),
    path("register/", views.auth_gateway, name="register"),
    path("logout/", views.user_logout, name="logout"),

    # Dedicated Role Authentication
    path("auth/student/login/", views.student_login, name="student_login"),
    path("auth/student/register/", views.student_register, name="student_register"),
    path("auth/faculty/login/", views.faculty_login, name="faculty_login"),
    path("auth/faculty/register/", views.faculty_register, name="faculty_register"),
    path("auth/librarian/login/", views.librarian_login, name="librarian_login"),
    path("auth/librarian/register/", views.librarian_register, name="librarian_register"),

    # Dashboards
    path("student/", views.student_dashboard, name="student_dashboard"),
    path("faculty/", views.faculty_dashboard, name="faculty_dashboard"),
    path("librarian/", views.librarian_dashboard, name="librarian_dashboard"),

    # Resource CRUD - Books
    path("books/add/", views.add_book, name="add_book"),
    path("books/<int:book_id>/edit/", views.edit_book, name="edit_book"),
    path("books/<int:book_id>/delete/", views.delete_book, name="delete_book"),
    path("books/<int:book_id>/borrow/", views.borrow_book, name="borrow_book"),
    path("books/<int:book_id>/reserve/", views.reserve_book, name="reserve_book"),

    # Resource CRUD - Journals
    path("journals/add/", views.add_journal, name="add_journal"),
    path("journals/<int:journal_id>/edit/", views.edit_journal, name="edit_journal"),
    path("journals/<int:journal_id>/delete/", views.delete_journal, name="delete_journal"),

    # Resource CRUD - Newspapers
    path("newspapers/add/", views.add_newspaper, name="add_newspaper"),
    path("newspapers/<int:newspaper_id>/edit/", views.edit_newspaper, name="edit_newspaper"),
    path("newspapers/<int:newspaper_id>/delete/", views.delete_newspaper, name="delete_newspaper"),

    # Resource CRUD - Computers
    path("computers/add/", views.add_computer, name="add_computer"),
    path("computers/<int:computer_id>/edit/", views.edit_computer, name="edit_computer"),
    path("computers/<int:computer_id>/toggle/", views.toggle_computer_status, name="toggle_computer_status"),
    path("computers/<int:computer_id>/delete/", views.delete_computer, name="delete_computer"),

    # Announcements
    path("announcements/add/", views.add_announcement, name="add_announcement"),
    path("announcements/<int:announcement_id>/edit/", views.edit_announcement, name="edit_announcement"),
    path("announcements/<int:announcement_id>/delete/", views.delete_announcement, name="delete_announcement"),

    # Circulation & Gate Attendance
    path("records/<int:record_id>/return/", views.return_book, name="return_book"),
    path("reservations/<int:reservation_id>/cancel/", views.cancel_reservation, name="cancel_reservation"),
    path("visit/toggle/", views.toggle_visit, name="toggle_visit"),

    # Real-Time Notifications
    path("notifications/api/", views.get_notifications_api, name="notifications_api"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read_view, name="mark_notification_read"),
    path("notifications/read-all/", views.mark_all_notifications_read_view, name="mark_all_notifications_read"),

    # Mobile REST API v1 Endpoints
    path("api/v1/catalog/", api.api_catalog, name="api_catalog"),
    path("api/v1/notifications/", api.api_notifications, name="api_notifications"),
    path("api/v1/notifications/<int:notification_id>/read/", api.api_mark_notification_read, name="api_mark_notification_read"),
    path("api/v1/notifications/read-all/", api.api_mark_all_read, name="api_mark_all_read"),
    path("api/v1/profile/", api.api_profile, name="api_profile"),
    path("api/v1/visits/toggle/", api.api_toggle_visit, name="api_toggle_visit"),
]


