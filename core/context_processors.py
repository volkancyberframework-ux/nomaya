from .models import UserProfile


def user_miles(request):
    total_miles = 0

    if request.user.is_authenticated:
        profile = getattr(request.user, "nomaya_profile", None)

        if profile:
            total_miles = profile.miles or 0

    return {
        "user_total_miles": total_miles
    }
