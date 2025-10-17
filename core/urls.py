# core/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("tours/", views.tour_grid, name="tour_grid"),

    # 1) Modal POST -> Order create (değişmedi)
    path("tours/booking/", views.tour_booking, name="tour_booking"),

    # 2) GÜVENLİ (UUID) detay/flow
    path("tours/booking/p/<uuid:public_id>/", views.tour_booking_detail_public, name="tour_booking_detail_public"),
    path("tours/booking/p/<uuid:public_id>/traveler/", views.save_travelers_public, name="save_travelers_public"),
    path('tours/booking/p/<uuid:public_id>/success/', views.order_success_public, name='order_success_public'),

    # İstersen: eski int ID rotalarını kapat ya da 404/redirect yap
    # path("tours/booking/<int:order_id>/", views.legacy_booking_redirect, name="tour_booking_detail"),
    # path("tours/booking/<int:order_id>/traveler/", views.legacy_booking_redirect, name="save_travelers"),
    # path('tours/booking/<int:order_id>/success/', views.legacy_booking_redirect, name='order_success'),

    path("tours/<slug:slug>/", views.tour_detail, name="tour_detail"),
    path("about/", views.about, name="about"),
    path("services/", views.services, name="services"),
    path("faqs/", views.faqs, name="faqs"),
    path("booking-confirmation/", views.booking_confirmation, name="booking_confirmation"),
    path("sign-in/", views.sign_in, name="sign_in"),
    path("sign-up/", views.sign_up, name="sign_up"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
