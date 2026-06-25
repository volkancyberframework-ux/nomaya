from django.shortcuts import redirect


class ForcePasswordChangeMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        user = request.user

        if (
            user.is_authenticated
            and hasattr(user, "nomaya_profile")
            and user.nomaya_profile.force_password_change
        ):

            allowed = [
                "/sign-in/",
                "/update-forced-password/",
                "/logout/",
                "/admin/logout/",
                "/static/",
                "/media/",
            ]

            if not any(
                request.path.startswith(x)
                for x in allowed
            ):
                return redirect("sign_in")

        return self.get_response(request)
