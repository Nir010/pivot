from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("services/", views.services, name="services"),
    path("team/", views.team, name="team"),
    path("notices/", views.notices_list, name="notices"),
    path("contact/", views.contact, name="contact"),
]
