from .models import Order, ActivityProgress


def user_miles(request):
    total_miles = 0

    if request.user.is_authenticated and request.user.email:
        orders = Order.objects.filter(email__iexact=request.user.email)

        progresses = ActivityProgress.objects.filter(
            order__in=orders,
            status=ActivityProgress.Status.COMPLETED
        ).select_related("day_activity__activity")

        for p in progresses:
            total_miles += p.day_activity.activity.miles_reward or 0

    return {
        "user_total_miles": total_miles
    }
