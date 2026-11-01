from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    Book, Journal, Newspaper, Computer, Profile,
    BorrowRecord, BookReservation, LibraryVisit, Announcement,
    Notification
)
from .notifications_helper import (
    get_user_notifications_payload,
    mark_notification_as_read,
    mark_all_notifications_as_read,
    create_broadcast_notification,
    create_personal_notification
)


def api_catalog(request):
    """Returns the full catalog overview in JSON format."""
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()

    books_qs = Book.objects.all().order_by("-id")
    if q:
        books_qs = books_qs.filter(
            Q(title__icontains=q) |
            Q(author__icontains=q) |
            Q(isbn__icontains=q) |
            Q(category__icontains=q)
        )
    if category:
        books_qs = books_qs.filter(category__iexact=category)

    books_data = [
        {
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "category": b.category,
            "isbn": b.isbn,
            "description": b.description,
            "available": b.available,
            "queue_count": b.queue_count(),
        }
        for b in books_qs
    ]

    journals_data = [
        {
            "id": j.id,
            "name": j.name,
            "publisher": j.publisher,
            "volume": j.volume,
            "issue": j.issue,
            "category": j.category,
            "available": j.available,
        }
        for j in Journal.objects.all().order_by("-id")
    ]

    newspapers_data = [
        {
            "id": n.id,
            "name": n.name,
            "language": n.language,
            "copies": n.copies,
            "available": n.available,
        }
        for n in Newspaper.objects.all().order_by("-id")
    ]

    computers_qs = Computer.objects.all().order_by("system_number")
    computers_data = [
        {
            "id": c.id,
            "system_number": c.system_number,
            "status": c.status,
            "status_display": c.get_status_display(),
            "location": c.location,
            "notes": c.notes,
        }
        for c in computers_qs
    ]

    announcements_data = [
        {
            "id": a.id,
            "title": a.title,
            "content": a.content,
            "category": a.category,
            "category_display": a.get_category_display(),
            "created_at": a.created_at.strftime("%b %d, %Y"),
        }
        for a in Announcement.objects.filter(is_active=True)[:10]
    ]

    categories = list(Book.objects.values_list("category", flat=True).distinct())

    return JsonResponse({
        "success": True,
        "books_count": len(books_data),
        "books": books_data,
        "journals": journals_data,
        "newspapers": newspapers_data,
        "computers": computers_data,
        "announcements": announcements_data,
        "categories": categories,
        "lab_summary": {
            "total": computers_qs.count(),
            "working": computers_qs.filter(status="working").count(),
            "in_use": computers_qs.filter(status="in_use").count(),
            "maintenance": computers_qs.filter(status="maintenance").count(),
        }
    })


def api_notifications(request):
    """Fetches user notifications & unread count."""
    payload = get_user_notifications_payload(request)
    return JsonResponse({
        "success": True,
        "unread_count": payload["unread_count"],
        "notifications": payload["notifications"]
    })


@require_http_methods(["POST"])
def api_mark_notification_read(request, notification_id):
    """Marks a single notification as read."""
    success = mark_notification_as_read(request.user, notification_id)
    return JsonResponse({"success": success})


@require_http_methods(["POST"])
def api_mark_all_read(request):
    """Marks all notifications as read for current user."""
    success = mark_all_notifications_as_read(request.user)
    return JsonResponse({"success": success})


def api_profile(request):
    """Returns active user profile, borrowed books, reservations, and gate pass status."""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "authenticated": False, "message": "Not authenticated"}, status=401)

    profile = getattr(request.user, "profile", None)

    for rec in BorrowRecord.objects.filter(user=request.user, status="issued"):
        rec.check_and_update_overdue()

    borrows = BorrowRecord.objects.filter(user=request.user, status__in=["issued", "overdue"]).order_by("-issue_date")
    borrows_data = [
        {
            "record_id": b.id,
            "book_id": b.book.id,
            "title": b.book.title,
            "author": b.book.author,
            "issue_date": b.issue_date.strftime("%b %d, %Y"),
            "due_date": b.due_date.strftime("%b %d, %Y"),
            "status": b.status,
            "days_remaining": b.days_remaining(),
            "fine_amount": float(b.fine_amount),
            "is_overdue": b.is_overdue(),
        }
        for b in borrows
    ]

    reservations = BookReservation.objects.filter(user=request.user, status__in=["waiting", "notified"]).order_by("-reserved_at")
    reservations_data = [
        {
            "reservation_id": r.id,
            "book_id": r.book.id,
            "title": r.book.title,
            "author": r.book.author,
            "status": r.status,
            "status_display": r.get_status_display(),
            "queue_position": r.get_queue_position(),
            "reserved_at": r.reserved_at.strftime("%b %d, %Y"),
        }
        for r in reservations
    ]

    current_visit = LibraryVisit.objects.filter(user=request.user, date=timezone.localdate(), status="checked_in").last()
    visit_data = {
        "is_checked_in": current_visit is not None,
        "entry_time": current_visit.entry_time.strftime("%I:%M %p") if current_visit else None,
    }

    return JsonResponse({
        "success": True,
        "authenticated": True,
        "user": {
            "username": request.user.username,
            "role": profile.role if profile else "student",
            "member_id": profile.member_id if profile else "",
            "department": profile.department if profile else "",
            "max_borrow_limit": profile.max_borrow_limit if profile else 3,
            "standard_loan_days": profile.standard_loan_days if profile else 14,
        },
        "active_borrows": borrows_data,
        "active_reservations": reservations_data,
        "gate_pass": visit_data,
    })


@require_http_methods(["POST"])
def api_toggle_visit(request):
    """1-click mobile gate pass check-in / check-out."""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Sign in required"}, status=401)

    today = timezone.localdate()
    current_visit = LibraryVisit.objects.filter(user=request.user, date=today, status="checked_in").last()

    if current_visit:
        current_visit.status = "checked_out"
        current_visit.exit_time = timezone.now()
        current_visit.save(update_fields=["status", "exit_time"])
        return JsonResponse({
            "success": True,
            "status": "checked_out",
            "message": f"Checked out successfully at {current_visit.exit_time.strftime('%I:%M %p')}."
        })
    else:
        new_visit = LibraryVisit.objects.create(
            user=request.user,
            date=today,
            entry_time=timezone.now(),
            status="checked_in"
        )
        return JsonResponse({
            "success": True,
            "status": "checked_in",
            "message": f"Checked in successfully at {new_visit.entry_time.strftime('%I:%M %p')}."
        })
