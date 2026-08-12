from django.urls import path
from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("profile/", views.MyProfileView.as_view(), name="profile"),
    path("friends/<int:pk>/", views.FriendProfileView.as_view(), name="friend_profile"),
    path("friends/<int:pk>/request/", views.send_friend_request, name="send_friend_request"),
    path("friends/<int:pk>/accept/", views.accept_friend_request, name="accept_friend_request"),
    path("friends/<int:pk>/decline/", views.decline_friend_request, name="decline_friend_request"),
    path("tasks/create/", views.TaskCreateView.as_view(), name="task_create"),
    path("tasks/<int:pk>/", views.TaskDetailView.as_view(), name="task_detail"),
    path("tasks/<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task_edit"),
    path("tasks/<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task_delete"),
    path("tasks/<int:pk>/status/", views.change_task_status, name="task_status_update"),
]