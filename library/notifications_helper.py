from django.db.models import Q
from .models import Notification, NotificationRead


def create_broadcast_notification(notification_type, title, message, category="General", link=""):
    """
    Creates a system-wide broadcast notification for all library users.
    Types: book_added, journal_added, newspaper_added, announcement_added, general
    """
    try:
        return Notification.objects.create(
            user=None,  # Null indicates broadcast to all students & faculty
            notification_type=notification_type,
            title=title,
            message=message,
            category=category,
            link=link
        )
    except Exception as e:
        print(f"[Notification] Error creating broadcast notification: {e}")
        return None


def create_personal_notification(user, notification_type, title, message, category="Alert", link=""):
    """
    Creates a direct notification for a specific user (e.g., reservation ready, loan due).
    """
    if not user:
        return None
    try:
        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            category=category,
            link=link,
            is_read=False
        )
    except Exception as e:
        print(f"[Notification] Error creating personal notification: {e}")
        return None


def get_user_notifications_payload(request, limit=25):
    """
    Retrieves personal + broadcast notifications for the current user/session
    with unread counts and read receipts.
    """
    if not request.user.is_authenticated:
        # Guests see latest broadcast notifications
        broadcasts = Notification.objects.filter(user=None).order_by("-created_at")[:limit]
        items = []
        for n in broadcasts:
            items.append({
                "id": n.id,
                "type": n.notification_type,
                "title": n.title,
                "message": n.message,
                "category": n.category,
                "link": n.link or "/#books-section",
                "created_at": n.created_at.strftime("%b %d, %I:%M %p"),
                "is_read": False,
                "is_personal": False,
            })
        return {
            "unread_count": len(items),
            "notifications": items
        }

    # Authenticated user: personal + broadcasts
    notifs = Notification.objects.filter(
        Q(user=request.user) | Q(user=None)
    ).order_by("-created_at")[:limit]

    read_broadcast_ids = set(
        NotificationRead.objects.filter(user=request.user).values_list("notification_id", flat=True)
    )

    items = []
    unread_count = 0
    for n in notifs:
        if n.user is not None:
            is_read = n.is_read
            is_personal = True
        else:
            is_read = n.id in read_broadcast_ids
            is_personal = False

        if not is_read:
            unread_count += 1

        items.append({
            "id": n.id,
            "type": n.notification_type,
            "title": n.title,
            "message": n.message,
            "category": n.category,
            "link": n.link or "/#books-section",
            "created_at": n.created_at.strftime("%b %d, %I:%M %p"),
            "is_read": is_read,
            "is_personal": is_personal,
        })

    return {
        "unread_count": unread_count,
        "notifications": items
    }


def mark_notification_as_read(user, notification_id):
    """
    Marks a specific notification as read for the user.
    """
    try:
        notif = Notification.objects.get(id=notification_id)
        if notif.user is not None:
            if notif.user == user:
                notif.is_read = True
                notif.save(update_fields=["is_read"])
                return True
        elif user and user.is_authenticated:
            NotificationRead.objects.get_or_create(user=user, notification=notif)
            return True
    except Notification.DoesNotExist:
        pass
    return False


def mark_all_notifications_as_read(user):
    """
    Marks all notifications (personal + unread broadcasts) as read for the user.
    """
    if not user or not user.is_authenticated:
        return False

    # Mark personal
    Notification.objects.filter(user=user, is_read=False).update(is_read=True)

    # Mark broadcasts
    broadcasts = Notification.objects.filter(user=None)
    existing_read = set(NotificationRead.objects.filter(user=user).values_list("notification_id", flat=True))
    to_create = []
    for b in broadcasts:
        if b.id not in existing_read:
            to_create.append(NotificationRead(user=user, notification=b))

    if to_create:
        NotificationRead.objects.bulk_create(to_create, ignore_conflicts=True)

    return True
