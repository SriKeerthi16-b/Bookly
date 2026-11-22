from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from .models import (
    Book, Journal, Newspaper, Computer, Profile,
    BorrowRecord, BookReservation, LibraryVisit, Announcement,
    Notification, NotificationRead
)
from .notifications_helper import (
    create_broadcast_notification,
    create_personal_notification,
    get_user_notifications_payload,
    mark_notification_as_read,
    mark_all_notifications_as_read
)

LIBRARIAN_SECRET_CODE = "BOOKLY-ADMIN-2026"



def get_user_profile(user):
    if not user.is_authenticated:
        return None
    return getattr(user, "profile", None)


# -------------------------------------------------------------------
# Role Gateway & Dedicated Authentication
# -------------------------------------------------------------------

def auth_gateway(request):
    """Hub for choosing role to login or register."""
    if request.user.is_authenticated:
        profile = get_user_profile(request.user)
        if profile and profile.role == "librarian":
            return redirect("librarian_dashboard")
        elif profile and profile.role == "faculty":
            return redirect("faculty_dashboard")
        return redirect("student_dashboard")
    return render(request, "auth/role_gateway.html")


def student_login(request):
    if request.user.is_authenticated:
        return redirect("student_dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            profile = get_user_profile(user)
            if profile and profile.role == "student":
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect("student_dashboard")
            elif not profile:
                # auto-create student profile if missing
                Profile.objects.create(user=user, role="student")
                login(request, user)
                return redirect("student_dashboard")
            else:
                messages.error(request, f"This account is registered as {profile.role.title()}. Please login via the {profile.role.title()} portal.")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "auth/student_login.html")


def student_register(request):
    if request.user.is_authenticated:
        return redirect("student_dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        member_id = request.POST.get("member_id", "").strip()
        department = request.POST.get("department", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, "auth/student_register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "A user with that username already exists.")
            return render(request, "auth/student_register.html")

        user = User.objects.create_user(username=username, password=password)
        Profile.objects.create(
            user=user,
            role="student",
            member_id=member_id,
            department=department,
            phone_number=phone_number
        )
        login(request, user)
        messages.success(request, f"Student account created! Welcome to Bookly, {username}.")
        return redirect("student_dashboard")

    return render(request, "auth/student_register.html")


def faculty_login(request):
    if request.user.is_authenticated:
        return redirect("faculty_dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            profile = get_user_profile(user)
            if profile and profile.role == "faculty":
                login(request, user)
                messages.success(request, f"Welcome back, Professor {user.username}!")
                return redirect("faculty_dashboard")
            else:
                role_name = profile.role.title() if profile else "Student"
                messages.error(request, f"This account is registered as {role_name}. Please login via the {role_name} portal.")
        else:
            messages.error(request, "Invalid faculty credentials.")
    return render(request, "auth/faculty_login.html")


def faculty_register(request):
    if request.user.is_authenticated:
        return redirect("faculty_dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        member_id = request.POST.get("member_id", "").strip()
        department = request.POST.get("department", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, "auth/faculty_register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already in use.")
            return render(request, "auth/faculty_register.html")

        user = User.objects.create_user(username=username, password=password)
        Profile.objects.create(
            user=user,
            role="faculty",
            member_id=member_id,
            department=department,
            phone_number=phone_number
        )
        login(request, user)
        messages.success(request, f"Faculty profile registered for {username}.")
        return redirect("faculty_dashboard")

    return render(request, "auth/faculty_register.html")


def librarian_login(request):
    if request.user.is_authenticated:
        profile = get_user_profile(request.user)
        if profile and profile.role == "librarian":
            return redirect("librarian_dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            profile = get_user_profile(user)
            if profile and profile.role == "librarian":
                login(request, user)
                messages.success(request, f"Librarian Control Center active for {user.username}.")
                return redirect("librarian_dashboard")
            else:
                messages.error(request, "Unauthorized. This account does not have Librarian credentials.")
        else:
            messages.error(request, "Invalid librarian username or password.")
    return render(request, "auth/librarian_login.html")


def librarian_register(request):
    if request.user.is_authenticated:
        return redirect("librarian_dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        member_id = request.POST.get("member_id", "").strip()
        staff_code = request.POST.get("staff_code", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()

        if staff_code != LIBRARIAN_SECRET_CODE:
            messages.error(request, f"Invalid Librarian Security Passcode. Authorization denied.")
            return render(request, "auth/librarian_register.html", {"secret_hint": LIBRARIAN_SECRET_CODE})

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, "auth/librarian_register.html", {"secret_hint": LIBRARIAN_SECRET_CODE})

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "auth/librarian_register.html", {"secret_hint": LIBRARIAN_SECRET_CODE})

        user = User.objects.create_user(username=username, password=password, is_staff=True)
        Profile.objects.create(
            user=user,
            role="librarian",
            member_id=member_id or "LIB-STAFF",
            department="Library Administration",
            phone_number=phone_number
        )
        login(request, user)
        messages.success(request, f"Librarian staff profile created for {username}.")
        return redirect("librarian_dashboard")

    return render(request, "auth/librarian_register.html", {"secret_hint": LIBRARIAN_SECRET_CODE})


def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("auth_gateway")


# -------------------------------------------------------------------
# Dashboards & Catalog Hub
# -------------------------------------------------------------------

def home(request):
    """
    Application Entry Point:
    - If unauthenticated, displays the Role Gateway / Registration & Login portal first.
    - If authenticated, automatically routes to the user's specific dashboard.
    """
    if not request.user.is_authenticated:
        return render(request, "auth/role_gateway.html")

    profile = get_user_profile(request.user)
    if profile:
        if profile.role == "librarian":
            return redirect("librarian_dashboard")
        elif profile.role == "faculty":
            return redirect("faculty_dashboard")
        elif profile.role == "student":
            return redirect("student_dashboard")
    return render(request, "auth/role_gateway.html")


def catalog_view(request):
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()

    books = Book.objects.all().order_by("-id")
    if q:
        books = books.filter(
            Q(title__icontains=q) |
            Q(author__icontains=q) |
            Q(isbn__icontains=q) |
            Q(category__icontains=q)
        )
    if category:
        books = books.filter(category__iexact=category)

    journals = Journal.objects.all().order_by("-id")
    newspapers = Newspaper.objects.all().order_by("-id")
    computers = Computer.objects.all().order_by("system_number")
    announcements = Announcement.objects.filter(is_active=True)[:5]

    # Categories list for filter tags
    categories = Book.objects.values_list("category", flat=True).distinct()

    # User-specific data
    user_borrowed = []
    user_reservations = []
    current_visit = None
    if request.user.is_authenticated:
        # update overdue records
        for rec in BorrowRecord.objects.filter(user=request.user, status="issued"):
            rec.check_and_update_overdue()
        user_borrowed = BorrowRecord.objects.filter(user=request.user, status__in=["issued", "overdue"]).order_by("-issue_date")
        user_reservations = BookReservation.objects.filter(user=request.user, status__in=["waiting", "notified"]).order_by("-reserved_at")
        current_visit = LibraryVisit.objects.filter(user=request.user, date=timezone.localdate(), status="checked_in").last()

    return render(request, "index.html", {
        "books": books,
        "journals": journals,
        "newspapers": newspapers,
        "computers": computers,
        "announcements": announcements,
        "categories": categories,
        "search_query": q,
        "selected_category": category,
        "computer_total": computers.count(),
        "computer_working": computers.filter(status="working").count(),
        "computer_in_use": computers.filter(status="in_use").count(),
        "computer_maintenance": computers.filter(status="maintenance").count(),
        "user_borrowed": user_borrowed,
        "user_reservations": user_reservations,
        "current_visit": current_visit,
        "notifications_data": get_user_notifications_payload(request),
    })



def student_dashboard(request):
    if not request.user.is_authenticated:
        return redirect("student_login")
    profile = get_user_profile(request.user)
    if profile and profile.role != "student":
        if profile.role == "librarian":
            return redirect("librarian_dashboard")
        return redirect("faculty_dashboard")

    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()

    books = Book.objects.all().order_by("-id")
    if q:
        books = books.filter(
            Q(title__icontains=q) |
            Q(author__icontains=q) |
            Q(isbn__icontains=q) |
            Q(category__icontains=q)
        )
    if category:
        books = books.filter(category__iexact=category)

    # Check and update overdue statuses for the user
    for rec in BorrowRecord.objects.filter(user=request.user, status="issued"):
        rec.check_and_update_overdue()

    user_borrowed = BorrowRecord.objects.filter(user=request.user, status__in=["issued", "overdue"]).order_by("-issue_date")
    user_reservations = BookReservation.objects.filter(user=request.user, status__in=["waiting", "notified"]).order_by("-reserved_at")
    borrow_history = BorrowRecord.objects.filter(user=request.user, status="returned").order_by("-return_date")[:5]
    current_visit = LibraryVisit.objects.filter(user=request.user, date=timezone.localdate(), status="checked_in").last()

    journals = Journal.objects.all().order_by("-id")
    newspapers = Newspaper.objects.all().order_by("-id")
    computers = Computer.objects.all().order_by("system_number")
    announcements = Announcement.objects.filter(is_active=True)[:5]
    categories = Book.objects.values_list("category", flat=True).distinct()

    return render(request, "student_dashboard.html", {
        "books": books,
        "journals": journals,
        "newspapers": newspapers,
        "computers": computers,
        "announcements": announcements,
        "categories": categories,
        "search_query": q,
        "selected_category": category,
        "user_borrowed": user_borrowed,
        "user_reservations": user_reservations,
        "borrow_history": borrow_history,
        "current_visit": current_visit,
        "profile": profile,
        "max_limit": profile.max_borrow_limit if profile else 3,
        "active_borrow_count": user_borrowed.count(),
        "computer_total": computers.count(),
        "computer_working": computers.filter(status="working").count(),
        "computer_in_use": computers.filter(status="in_use").count(),
        "computer_maintenance": computers.filter(status="maintenance").count(),
        "notifications_data": get_user_notifications_payload(request),
    })


def faculty_dashboard(request):
    if not request.user.is_authenticated:
        return redirect("faculty_login")
    profile = get_user_profile(request.user)
    if profile and profile.role != "faculty":
        if profile.role == "librarian":
            return redirect("librarian_dashboard")
        return redirect("student_dashboard")

    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()

    books = Book.objects.all().order_by("-id")
    if q:
        books = books.filter(
            Q(title__icontains=q) |
            Q(author__icontains=q) |
            Q(isbn__icontains=q) |
            Q(category__icontains=q)
        )
    if category:
        books = books.filter(category__iexact=category)

    for rec in BorrowRecord.objects.filter(user=request.user, status="issued"):
        rec.check_and_update_overdue()

    user_borrowed = BorrowRecord.objects.filter(user=request.user, status__in=["issued", "overdue"]).order_by("-issue_date")
    user_reservations = BookReservation.objects.filter(user=request.user, status__in=["waiting", "notified"]).order_by("-reserved_at")
    current_visit = LibraryVisit.objects.filter(user=request.user, date=timezone.localdate(), status="checked_in").last()

    journals = Journal.objects.all().order_by("-id")
    newspapers = Newspaper.objects.all().order_by("-id")
    computers = Computer.objects.all().order_by("system_number")
    announcements = Announcement.objects.filter(is_active=True)[:5]
    categories = Book.objects.values_list("category", flat=True).distinct()

    return render(request, "faculty_dashboard.html", {
        "books": books,
        "journals": journals,
        "newspapers": newspapers,
        "computers": computers,
        "announcements": announcements,
        "categories": categories,
        "search_query": q,
        "selected_category": category,
        "user_borrowed": user_borrowed,
        "user_reservations": user_reservations,
        "current_visit": current_visit,
        "profile": profile,
        "max_limit": profile.max_borrow_limit if profile else 6,
        "active_borrow_count": user_borrowed.count(),
        "computer_working": computers.filter(status="working").count(),
        "computer_in_use": computers.filter(status="in_use").count(),
        "computer_maintenance": computers.filter(status="maintenance").count(),
        "notifications_data": get_user_notifications_payload(request),
    })


def librarian_dashboard(request):
    if not request.user.is_authenticated:
        return redirect("librarian_login")
    profile = get_user_profile(request.user)
    if not profile or profile.role != "librarian":
        messages.error(request, "Access restricted to Library Staff.")
        return redirect("home")

    # Update overdue records across all users
    for rec in BorrowRecord.objects.filter(status="issued"):
        rec.check_and_update_overdue()

    books = Book.objects.all().order_by("-id")
    journals = Journal.objects.all().order_by("-id")
    newspapers = Newspaper.objects.all().order_by("-id")
    computers = Computer.objects.all().order_by("system_number")
    announcements = Announcement.objects.all().order_by("-created_at")

    active_issues = BorrowRecord.objects.filter(status__in=["issued", "overdue"]).order_by("-issue_date")
    returned_issues = BorrowRecord.objects.filter(status="returned").order_by("-return_date")[:10]
    active_reservations = BookReservation.objects.filter(status__in=["waiting", "notified"]).order_by("-reserved_at")
    today_visits = LibraryVisit.objects.filter(date=timezone.localdate()).order_by("-entry_time")

    return render(request, "librarian_dashboard.html", {
        "books": books,
        "journals": journals,
        "newspapers": newspapers,
        "computers": computers,
        "announcements": announcements,
        "active_issues": active_issues,
        "returned_issues": returned_issues,
        "active_reservations": active_reservations,
        "today_visits": today_visits,
        "available_books": books.filter(available=True).count(),
        "borrowed_books": books.filter(available=False).count(),
        "journal_count": journals.count(),
        "newspaper_count": newspapers.count(),
        "computer_total": computers.count(),
        "computer_working": computers.filter(status="working").count(),
        "computer_in_use": computers.filter(status="in_use").count(),
        "computer_maintenance": computers.filter(status="maintenance").count(),
        "total_visits_today": today_visits.count(),
        "currently_inside": today_visits.filter(status="checked_in").count(),
        "notifications_data": get_user_notifications_payload(request),
    })


# -------------------------------------------------------------------
# Resource CRUD for Librarian (Books, Journals, Newspapers, Computers)
# -------------------------------------------------------------------

def add_book(request):
    if not request.user.is_authenticated or getattr(request.user.profile, "role", "") != "librarian":
        return redirect("home")
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        author = request.POST.get("author", "").strip()
        category = request.POST.get("category", "").strip()
        isbn = request.POST.get("isbn", "").strip()
        description = request.POST.get("description", "").strip()

        if title and author and category and isbn:
            if Book.objects.filter(isbn=isbn).exists():
                messages.error(request, f"A book with ISBN {isbn} already exists.")
            else:
                book = Book.objects.create(
                    title=title, author=author, category=category,
                    isbn=isbn, description=description
                )
                create_broadcast_notification(
                    notification_type="book_added",
                    title=f"📚 New Book Arrival: {book.title}",
                    message=f"'{book.title}' by {book.author} has arrived in the {book.category} section. Available to borrow now!",
                    category=book.category or "Book",
                    link="/#books-section"
                )
                messages.success(request, f'Book "{title}" added to library inventory.')
        else:
            messages.error(request, "Please fill in all required fields.")
    return redirect("librarian_dashboard")


def edit_book(request, book_id):
    if not request.user.is_authenticated or getattr(request.user.profile, "role", "") != "librarian":
        return redirect("home")
    book = get_object_or_404(Book, id=book_id)
    if request.method == "POST":
        book.title = request.POST.get("title", book.title).strip()
        book.author = request.POST.get("author", book.author).strip()
        book.category = request.POST.get("category", book.category).strip()
        new_isbn = request.POST.get("isbn", book.isbn).strip()
        if new_isbn != book.isbn and Book.objects.filter(isbn=new_isbn).exists():
            messages.error(request, "ISBN already exists on another book.")
        else:
            book.isbn = new_isbn
            book.description = request.POST.get("description", book.description).strip()
            book.available = "available" in request.POST
            book.save()
            messages.success(request, f'Book "{book.title}" updated successfully.')
    return redirect("librarian_dashboard")


def delete_book(request, book_id):
    if not request.user.is_authenticated or getattr(request.user.profile, "role", "") != "librarian":
        return redirect("home")
    book = get_object_or_404(Book, id=book_id)
    title = book.title
    book.delete()
    messages.success(request, f'Book "{title}" was removed from the collection.')
    return redirect("librarian_dashboard")


def add_journal(request):
    if not request.user.is_authenticated or getattr(request.user.profile, "role", "") != "librarian":
        return redirect("home")
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        publisher = request.POST.get("publisher", "").strip()
        volume = request.POST.get("volume", "").strip()
        issue = request.POST.get("issue", "").strip()
        publication_date = request.POST.get("publication_date") or None
        category = request.POST.get("category", "").strip()

        if name:
            journal = Journal.objects.create(
                name=name, publisher=publisher, volume=volume,
                issue=issue, publication_date=publication_date, category=category
            )
            create_broadcast_notification(
                notification_type="journal_added",
                title=f"📖 New Journal Added: {journal.name}",
                message=f"Volume {journal.volume or '1'} Issue {journal.issue or 'Current'} published by {journal.publisher or 'Academic Press'} ({journal.category}) is now in research archives.",
                category=journal.category or "Journal",
                link="/#journals-section"
            )
            messages.success(request, f'Journal "{name}" added.')
    return redirect("librarian_dashboard")


def edit_journal(request, journal_id):
    if not request.user.is_authenticated or getattr(request.user.profile, "role", "") != "librarian":
        return redirect("home")
    journal = get_object_or_404(Journal, id=journal_id)
    if request.method == "POST":
        journal.name = request.POST.get("name", journal.name).strip()
        journal.publisher = request.POST.get("publisher", journal.publisher).strip()
        journal.volume = request.POST.get("volume", journal.volume).strip()
        journal.issue = request.POST.get("issue", journal.issue).strip()
        pub_date = request.POST.get("publication_date")
        if pub_date:
            journal.publication_date = pub_date
        journal.category = request.POST.get("category", journal.category).strip()
        journal.available = "available" in request.POST
        journal.save()
        messages.success(request, f'Journal "{journal.name}" updated.')
    return redirect("librarian_dashboard")


def delete_journal(request, journal_id):
    if not request.user.is_authenticated or getattr(request.user.profile, "role", "") != "librarian":
        return redirect("home")
    journal = get_object_or_404(Journal, id=journal_id)
    name = journal.name
    journal.delete()
    messages.success(request, f'Journal "{name}" deleted.')
    return redirect("librarian_dashboard")


def add_newspaper(request):
    if not request.user.is_authenticated or getattr(request.user.profile, "role", "") != "librarian":
        return redirect("home")
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        language = request.POST.get("language", "").strip()
        publication_date = request.POST.get("publication_date") or None
        copies = request.POST.get("copies") or 1

        if name:
            newspaper = Newspaper.objects.create(
                name=name, language=language,
                publication_date=publication_date, copies=copies
            )
            create_broadcast_notification(
                notification_type="newspaper_added",
                title=f"📰 Today's Newspaper Available: {newspaper.name}",
                message=f"{newspaper.name} ({newspaper.language}) with {newspaper.copies} copies is available in the periodical reading section.",
                category="Newspaper",
                link="/#newspapers-section"
            )
            messages.success(request, f'Newspaper "{name}" added.')
    return redirect("librarian_dashboard")


def edit_newspaper(request, newspaper_id):
    if not request.user.is_authenticated or getattr(request.user.profile, "role", "") != "librarian":
        return redirect("home")
    newspaper = get_object_or_404(Newspaper, id=newspaper_id)
    if request.method == "POST":
        newspaper.name = request.POST.get("name", newspaper.name).strip()
        newspaper.language = request.POST.get("language", newspaper.language).strip()
        pub_date = request.POST.get("publication_date")
        if pub_date:
            newspaper.publication_date = pub_date
        newspaper.copies = int(request.POST.get("copies", newspaper.copies))
        newspaper.available = "available" in request.POST
        newspaper.save()
        messages.success(request, f'Newspaper "{newspaper.name}" updated.')
    return redirect("librarian_dashboard")


def delete_newspaper(request, newspaper_id):
    if not request.user.is_authenticated or getattr(request.user.profile, "role", "") != "librarian":
        return redirect("home")
    newspaper = get_object_or_404(Newspaper, id=newspaper_id)
    name = newspaper.name
    newspaper.delete()
    messages.success(request, f'Newspaper "{name}" deleted.')
    return redirect("librarian_dashboard")


def add_computer(request):
    if not request.user.is_authenticated or getattr(request.user.profile, "role", "") != "librarian":
        return redirect("home")
    if request.method == "POST":
        system_number = request.POST.get("system_number", "").strip()
        status = request.POST.get("status", "working")
        location = request.POST.get("location", "Computer Library").strip()
        notes = request.POST.get("notes", "").strip()

        if system_number:
            if Computer.objects.filter(system_number=system_number).exists():
                messages.error(request, f"Computer system {system_number} already exists.")
            else:
                Computer.objects.create(
                    system_number=system_number,
                    status=status,
                    location=location or "Computer Library",
                    notes=notes
                )
                messages.success(request, f"Workstation {system_number} added.")
    return redirect("librarian_dashboard")


def edit_computer(request, computer_id):
    if not request.user.is_authenticated or getattr(request.user.profile, "role", "") != "librarian":
        return redirect("home")
    computer = get_object_or_404(Computer, id=computer_id)
    if request.method == "POST":
        computer.system_number = request.POST.get("system_number", computer.system_number).strip()
        computer.status = request.POST.get("status", computer.status)
        computer.location = request.POST.get("location", computer.location).strip()
        computer.notes = request.POST.get("notes", "").strip()
        computer.save()
        messages.success(request, f"Workstation {computer.system_number} updated.")
    return redirect("librarian_dashboard")


def toggle_computer_status(request, computer_id):
    if not request.user.is_authenticated or getattr(request.user.profile, "role", "") != "librarian":
        return redirect("home")
    computer = get_object_or_404(Computer, id=computer_id)
    cycle = {"working": "in_use", "in_use": "maintenance", "maintenance": "working"}
    computer.status = cycle.get(computer.status, "working")
    computer.save(update_fields=["status"])
    messages.success(request, f"{computer.system_number} status set to {computer.get_status_display()}.")
    return redirect("librarian_dashboard")


def delete_computer(request, computer_id):
    if not request.user.is_authenticated or getattr(request.user.profile, "role", "") != "librarian":
        return redirect("home")
    computer = get_object_or_404(Computer, id=computer_id)
    sys_num = computer.system_number
    computer.delete()
    messages.success(request, f"Workstation {sys_num} deleted.")
    return redirect("librarian_dashboard")


# -------------------------------------------------------------------
# Announcements Studio
# -------------------------------------------------------------------

def add_announcement(request):
    if not request.user.is_authenticated or getattr(request.user.profile, "role", "") != "librarian":
        return redirect("home")
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        category = request.POST.get("category", "general")

        if title and content:
            announcement = Announcement.objects.create(
                title=title, content=content, category=category,
                author=request.user
            )
            create_broadcast_notification(
                notification_type="announcement_added",
                title=f"📢 Library Notice: {announcement.title}",
                message=announcement.content,
                category=announcement.get_category_display() if hasattr(announcement, 'get_category_display') else "Announcement",
                link="/#announcements-sec"
            )
            messages.success(request, f'Announcement "{title}" published to library bulletin.')
        else:
            messages.error(request, "Announcement title and content cannot be empty.")
    return redirect("librarian_dashboard")


def edit_announcement(request, announcement_id):
    if not request.user.is_authenticated or getattr(request.user.profile, "role", "") != "librarian":
        return redirect("home")
    announcement = get_object_or_404(Announcement, id=announcement_id)
    if request.method == "POST":
        announcement.title = request.POST.get("title", announcement.title).strip()
        announcement.content = request.POST.get("content", announcement.content).strip()
        announcement.category = request.POST.get("category", announcement.category)
        announcement.is_active = "is_active" in request.POST
        announcement.save()
        messages.success(request, f'Announcement "{announcement.title}" updated.')
    return redirect("librarian_dashboard")


def delete_announcement(request, announcement_id):
    if not request.user.is_authenticated or getattr(request.user.profile, "role", "") != "librarian":
        return redirect("home")
    announcement = get_object_or_404(Announcement, id=announcement_id)
    announcement.delete()
    messages.success(request, "Announcement deleted.")
    return redirect("librarian_dashboard")


# -------------------------------------------------------------------
# Borrowing, Returns, Queue, & Gate Attendance
# -------------------------------------------------------------------

def borrow_book(request, book_id):
    if not request.user.is_authenticated:
        messages.error(request, "Please sign in to borrow books.")
        return redirect("auth_gateway")

    book = get_object_or_404(Book, id=book_id)
    profile = get_user_profile(request.user)
    max_limit = profile.max_borrow_limit if profile else 3
    active_count = BorrowRecord.objects.filter(user=request.user, status__in=["issued", "overdue"]).count()

    if active_count >= max_limit:
        messages.error(request, f"You have reached your maximum borrow limit ({max_limit} books). Please return a book first.")
        return redirect(request.META.get("HTTP_REFERER", "home"))

    if not book.available:
        messages.warning(request, f'"{book.title}" is currently borrowed. You can join the reservation queue instead.')
        return redirect(request.META.get("HTTP_REFERER", "home"))

    loan_days = profile.standard_loan_days if profile else 14
    due_date = timezone.localdate() + timedelta(days=loan_days)

    BorrowRecord.objects.create(
        user=request.user,
        book=book,
        due_date=due_date,
        status="issued"
    )
    book.available = False
    book.save(update_fields=["available"])

    # If this user had a reservation for this book, fulfill it
    BookReservation.objects.filter(user=request.user, book=book, status__in=["waiting", "notified"]).update(status="fulfilled")

    messages.success(request, f'Successfully borrowed "{book.title}"! Return due date: {due_date.strftime("%d %b %Y")} ({loan_days} days).')
    return redirect(request.META.get("HTTP_REFERER", "home"))


def return_book(request, record_id):
    if not request.user.is_authenticated:
        return redirect("auth_gateway")

    record = get_object_or_404(BorrowRecord, id=record_id)
    profile = get_user_profile(request.user)

    # Allow return if user is librarian OR user is the borrower
    if profile.role != "librarian" and record.user != request.user:
        messages.error(request, "Unauthorized return action.")
        return redirect("home")

    record.return_date = timezone.localdate()
    record.status = "returned"
    if record.is_overdue():
        overdue_days = (timezone.localdate() - record.due_date).days
        record.fine_amount = max(0, overdue_days * 5.00)
    record.save()

    book = record.book
    book.available = True
    book.save(update_fields=["available"])

    # Check if someone is in queue for this book
    next_reservation = BookReservation.objects.filter(book=book, status="waiting").order_by("reserved_at").first()
    if next_reservation:
        next_reservation.status = "notified"
        next_reservation.save(update_fields=["status"])
        create_personal_notification(
            user=next_reservation.user,
            notification_type="reservation_ready",
            title=f"🎉 Reserved Book Ready: {book.title}",
            message=f"Great news! Your waitlisted book '{book.title}' is returned and held for you at the circulation desk.",
            category="Waitlist Ready",
            link="/student/#reserved-sec"
        )
        messages.info(request, f'Book returned. Reader {next_reservation.user.username} has been notified from the queue!')
    else:
        messages.success(request, f'"{book.title}" has been returned to the shelves.')

    return redirect(request.META.get("HTTP_REFERER", "home"))


def reserve_book(request, book_id):
    if not request.user.is_authenticated:
        messages.error(request, "Please login to reserve books in queue.")
        return redirect("auth_gateway")

    book = get_object_or_404(Book, id=book_id)

    # Check if already borrowed by this user
    if BorrowRecord.objects.filter(user=request.user, book=book, status__in=["issued", "overdue"]).exists():
        messages.warning(request, "You already have this book borrowed!")
        return redirect(request.META.get("HTTP_REFERER", "home"))

    # Check if already in queue
    if BookReservation.objects.filter(user=request.user, book=book, status__in=["waiting", "notified"]).exists():
        messages.warning(request, f'You are already in the queue for "{book.title}".')
        return redirect(request.META.get("HTTP_REFERER", "home"))

    reservation = BookReservation.objects.create(
        user=request.user,
        book=book,
        status="waiting"
    )
    pos = reservation.get_queue_position()
    messages.success(request, f'Added to queue for "{book.title}". You are #{pos} in line.')
    return redirect(request.META.get("HTTP_REFERER", "home"))


def cancel_reservation(request, reservation_id):
    if not request.user.is_authenticated:
        return redirect("auth_gateway")
    reservation = get_object_or_404(BookReservation, id=reservation_id)
    profile = get_user_profile(request.user)
    if profile.role != "librarian" and reservation.user != request.user:
        messages.error(request, "Unauthorized.")
        return redirect("home")

    reservation.status = "cancelled"
    reservation.save(update_fields=["status"])
    messages.info(request, f'Reservation for "{reservation.book.title}" cancelled.')
    return redirect(request.META.get("HTTP_REFERER", "home"))


def toggle_visit(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please login to log library visit.")
        return redirect("auth_gateway")

    today = timezone.localdate()
    open_visit = LibraryVisit.objects.filter(user=request.user, date=today, status="checked_in").last()

    if open_visit:
        open_visit.exit_time = timezone.now()
        open_visit.status = "checked_out"
        open_visit.save(update_fields=["exit_time", "status"])
        messages.success(request, f"Checked out of the Library at {timezone.localtime(open_visit.exit_time).strftime('%I:%M %p')}. Have a good day!")
    else:
        new_visit = LibraryVisit.objects.create(
            user=request.user,
            date=today,
            status="checked_in"
        )
        messages.success(request, f"Checked in to the Library at {timezone.localtime(new_visit.entry_time).strftime('%I:%M %p')}. Welcome!")

    return redirect(request.META.get("HTTP_REFERER", "home"))


# -------------------------------------------------------------------
# Notification Endpoints
# -------------------------------------------------------------------

def get_notifications_api(request):
    """Returns unread notifications and list for current user."""
    payload = get_user_notifications_payload(request)
    return JsonResponse(payload)


def mark_notification_read_view(request, notification_id):
    """Marks a single notification as read."""
    success = mark_notification_as_read(request.user, notification_id)
    return JsonResponse({"success": success})


def mark_all_notifications_read_view(request):
    """Marks all notifications as read."""
    success = mark_all_notifications_as_read(request.user)
    return JsonResponse({"success": success})


# -------------------------------------------------------------------
# PWA Root Handlers (Manifest & Service Worker)
# -------------------------------------------------------------------

def pwa_manifest_view(request):
    import os
    from django.conf import settings
    from django.http import HttpResponse
    manifest_path = os.path.join(settings.BASE_DIR, "static", "manifest.json")
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HttpResponse(content, content_type="application/manifest+json")
    except Exception as e:
        return HttpResponse("{}", content_type="application/manifest+json")


def pwa_sw_view(request):
    import os
    from django.conf import settings
    from django.http import HttpResponse
    sw_path = os.path.join(settings.BASE_DIR, "static", "js", "sw.js")
    try:
        with open(sw_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HttpResponse(content, content_type="application/javascript; charset=utf-8")
    except Exception as e:
        return HttpResponse("// SW load error", content_type="application/javascript; charset=utf-8")


