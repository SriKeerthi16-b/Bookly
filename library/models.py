from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.title

    def active_borrow_record(self):
        return self.borrowrecord_set.filter(status__in=["issued", "overdue"]).order_by("-issue_date").first()

    def queue_count(self):
        return self.bookreservation_set.filter(status="waiting").count()


class Journal(models.Model):
    name = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200, blank=True)
    volume = models.CharField(max_length=50, blank=True)
    issue = models.CharField(max_length=50, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=100, blank=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Newspaper(models.Model):
    name = models.CharField(max_length=200)
    language = models.CharField(max_length=100, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    copies = models.PositiveIntegerField(default=1)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Computer(models.Model):
    STATUS_CHOICES = (
        ("working", "Working / Vacant"),
        ("in_use", "In Use"),
        ("maintenance", "Maintenance"),
    )

    system_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="working")
    location = models.CharField(max_length=100, default="Computer Library")
    notes = models.CharField(max_length=255, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.system_number


class Profile(models.Model):
    ROLE_CHOICES = (
        ("student", "Student"),
        ("librarian", "Librarian"),
        ("faculty", "Faculty"),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    member_id = models.CharField(max_length=50, blank=True, default="")
    department = models.CharField(max_length=100, blank=True, default="")
    phone_number = models.CharField(max_length=20, blank=True, default="")

    def __str__(self):
        return f"{self.user.username} ({self.role.capitalize()})"

    @property
    def max_borrow_limit(self):
        if self.role == "faculty":
            return 6
        elif self.role == "librarian":
            return 10
        return 3

    @property
    def standard_loan_days(self):
        if self.role == "faculty":
            return 30
        return 14


class BorrowRecord(models.Model):
    STATUS_CHOICES = (
        ("issued", "Issued / Active"),
        ("returned", "Returned"),
        ("overdue", "Overdue"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="borrow_records")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrow_records")
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="issued")
    fine_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.status})"

    def is_overdue(self):
        if self.status == "returned":
            return False
        return timezone.localdate() > self.due_date

    def days_remaining(self):
        today = timezone.localdate()
        diff = (self.due_date - today).days
        return diff

    def check_and_update_overdue(self):
        if self.status == "issued" and self.is_overdue():
            self.status = "overdue"
            overdue_days = (timezone.localdate() - self.due_date).days
            self.fine_amount = max(0, overdue_days * 5.00)  # Rs. 5 per overdue day
            self.save(update_fields=["status", "fine_amount"])


class BookReservation(models.Model):
    STATUS_CHOICES = (
        ("waiting", "In Queue"),
        ("notified", "Available for Pickup"),
        ("fulfilled", "Fulfilled"),
        ("cancelled", "Cancelled"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reservations")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reservations")
    reserved_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="waiting")

    def __str__(self):
        return f"{self.user.username} waiting for {self.book.title}"

    def get_queue_position(self):
        if self.status != "waiting":
            return 0
        earlier = BookReservation.objects.filter(
            book=self.book,
            status="waiting",
            reserved_at__lte=self.reserved_at
        ).count()
        return earlier


class LibraryVisit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="visits")
    date = models.DateField(auto_now_add=True)
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=(("checked_in", "Checked In"), ("checked_out", "Checked Out")), default="checked_in")

    def __str__(self):
        return f"{self.user.username} on {self.date} ({self.status})"


class Announcement(models.Model):
    CATEGORY_CHOICES = (
        ("general", "General"),
        ("exam", "Exam Hours"),
        ("new_arrivals", "New Arrivals"),
        ("maintenance", "Maintenance"),
        ("event", "Library Event"),
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="general")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

