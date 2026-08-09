from django.urls import path
from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("profile/", views.MyProfileView.as_view(), name="profile"),
    path("friends/<int:pk>/", views.FriendProfileView.as_view(), name="friend_profile"),
    path("tasks/create/", views.TaskCreateView.as_view(), name="task_create"),
]