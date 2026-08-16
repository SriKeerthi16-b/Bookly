from django.contrib import admin
from .models import (
    Book, Journal, Newspaper, Computer, Profile,
    BorrowRecord, BookReservation, LibraryVisit, Announcement
)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "isbn", "available", "created_at")
    search_fields = ("title", "author", "isbn", "category")
    list_filter = ("category", "available")


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ("name", "publisher", "volume", "issue", "publication_date", "available")
    search_fields = ("name", "publisher", "category")
    list_filter = ("category", "available")


@admin.register(Newspaper)
class NewspaperAdmin(admin.ModelAdmin):
    list_display = ("name", "language", "publication_date", "copies", "available")
    search_fields = ("name", "language")
    list_filter = ("language", "available")


@admin.register(Computer)
class ComputerAdmin(admin.ModelAdmin):
    list_display = ("system_number", "status", "location", "notes", "updated_at")
    search_fields = ("system_number", "location")
    list_filter = ("status", "location")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "member_id", "department", "phone_number")
    list_filter = ("role", "department")
    search_fields = ("user__username", "member_id", "department")


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "book", "issue_date", "due_date", "return_date", "status", "fine_amount")
    list_filter = ("status", "issue_date", "due_date")
    search_fields = ("user__username", "book__title", "book__isbn")


@admin.register(BookReservation)
class BookReservationAdmin(admin.ModelAdmin):
    list_display = ("user", "book", "reserved_at", "status")
    list_filter = ("status", "reserved_at")
    search_fields = ("user__username", "book__title")


@admin.register(LibraryVisit)
class LibraryVisitAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "entry_time", "exit_time", "status")
    list_filter = ("status", "date")
    search_fields = ("user__username",)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "created_at", "author", "is_active")
    list_filter = ("category", "is_active", "created_at")
    search_fields = ("title", "content")

