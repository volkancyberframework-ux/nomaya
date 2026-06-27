# core/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    #path("tours/", views.tour_grid, name="tour_grid"),

    # 1) Modal POST -> Order create (değişmedi)
    #path("tours/booking/", views.tour_booking, name="tour_booking"),
    path(
    "audio/<str:tracking_code>/<int:day_activity_id>/<str:audio_type>/",
    views.secure_audio_stream,
    name="secure_audio_stream"
    ),

    # 2) GÜVENLİ (UUID) detay/flow
    #path("tours/booking/p/<uuid:public_id>/", views.tour_booking_detail_public, name="tour_booking_detail_public"),
    #path("tours/booking/p/<uuid:public_id>/traveler/", views.save_travelers_public, name="save_travelers_public"),
    #path('tours/booking/p/<uuid:public_id>/success/', views.order_success_public, name='order_success_public'),

    # İstersen: eski int ID rotalarını kapat ya da 404/redirect yap
    # path("tours/booking/<int:order_id>/", views.legacy_booking_redirect, name="tour_booking_detail"),
    # path("tours/booking/<int:order_id>/traveler/", views.legacy_booking_redirect, name="save_travelers"),
    # path('tours/booking/<int:order_id>/success/', views.legacy_booking_redirect, name='order_success'),
    path("api/today-plan/<str:code>/", views.today_plan, name="today_plan"),
    path("api/activity-progress/", views.update_activity_progress, name="update_activity_progress"),
    #path("tours/<slug:slug>/", views.tour_detail, name="tour_detail"),
    path("about/", views.about, name="about"),
    #path("nomayaasistan/", views.nomaya_asistan, name="nomaya_asistan"),
    path("services/", views.services, name="services"),
    path("faqs/", views.faqs, name="faqs"),
    path("booking-confirmation/", views.booking_confirmation, name="booking_confirmation"),
    path("sign-in/", views.sign_in, name="sign_in"),
    path("sign-up/", views.sign_up, name="sign_up"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("api/order-itinerary/<str:code>/", views.order_itinerary, name="order_itinerary"),
    path("orders/<int:order_id>/accept-link/", views.accept_link_payment, name="accept_link_payment"),
    path(
    "orders/<int:order_id>/request-miles-payment/",
    views.request_miles_payment,
    name="request_miles_payment",
    ),
    path(
    "orders/<int:order_id>/request-bank-transfer/",
    views.request_bank_transfer,
    name="request_bank_transfer"
    ),
    path("api/verify-code/", views.verify_tracking_code, name="verify_tracking_code"),
    path("geo/", views.geo, name="geo"),
    path("api/update-location/", views.update_location, name="update_location"),
    path("live-map/", views.live_map, name="live_map"),
    path("api/live-locations/", views.live_locations_api, name="live_locations_api"),

    path(
        "orders/<uuid:public_id>/stripe/",
        views.stripe_checkout_order,
        name="stripe_checkout_order"
    ),

    path(
        "sen-gez-diye/",
        views.order_customized,
        name="order_customized"
    ),

    path(
        "sen-gez-diye/<uuid:public_id>/",
        views.order_customized_detail,
        name="order_customized_detail"
    ),

    path(
        "sen-gez-diye/<uuid:public_id>/pay/",
        views.order_customized_pay,
        name="order_customized_pay"
    ),
    path(
    "update-forced-password/",
    views.update_forced_password,
    name="update_forced_password"
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
