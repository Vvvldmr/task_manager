from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import TemplateView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model, login

from .models import Task, Comment, Friendship, FriendRequest
from .forms import TaskForm


User = get_user_model()


class IndexView(TemplateView):
    template_name = "tasks/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            context["tasks"] = Task.objects.filter(
                owner=self.request.user
            )

        return context


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    template_name = "tasks/task_create.html"
    form_class = TaskForm
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comments"] = self.object.comments.all()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        text = request.POST.get("text", "").strip()

        if text:
            Comment.objects.create(task=self.object, author=request.user, text=text)

        return redirect("task_detail", pk=self.object.pk)


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    template_name = "tasks/task_edit.html"
    form_class = TaskForm

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)

    def get_success_url(self):
        return reverse_lazy("task_detail", kwargs={"pk": self.object.pk})


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = "tasks/task_confirm_delete.html"
    success_url = reverse_lazy("index")

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)


class UserLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("index")


class MyProfileView(LoginRequiredMixin, TemplateView):
    template_name = "tasks/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_user"] = self.request.user
        context["tasks"] = Task.objects.filter(owner=self.request.user)

        context["friends"] = User.objects.filter(
            friendships_as_friend__user=self.request.user
        )

        context["incoming_requests"] = FriendRequest.objects.filter(
            to_user=self.request.user
        )

        return context


class FriendProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "tasks/user_profile.html"
    context_object_name = "profile_user"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object == request.user:
            return redirect("profile")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        is_friend = Friendship.objects.filter(
            user=self.request.user, friend=self.object
        ).exists()

        context["is_friend"] = is_friend
        context["tasks"] = Task.objects.filter(owner=self.object) if is_friend else None

        context["request_sent"] = FriendRequest.objects.filter(
            from_user=self.request.user, to_user=self.object
        ).exists()

        context["request_received"] = FriendRequest.objects.filter(
            from_user=self.object, to_user=self.request.user
        ).exists()

        return context


class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


@login_required
@require_POST
def send_friend_request(request, pk):
    to_user = get_object_or_404(User, pk=pk)

    already_friends = Friendship.objects.filter(user=request.user, friend=to_user).exists()

    if to_user != request.user and not already_friends:
        FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)

    return redirect("friend_profile", pk=pk)


@login_required
@require_POST
def accept_friend_request(request, pk):
    from_user = get_object_or_404(User, pk=pk)
    deleted, _ = FriendRequest.objects.filter(from_user=from_user, to_user=request.user).delete()

    if deleted:
        Friendship.objects.get_or_create(user=request.user, friend=from_user)
        Friendship.objects.get_or_create(user=from_user, friend=request.user)

    return redirect("profile")


@login_required
@require_POST
def decline_friend_request(request, pk):
    from_user = get_object_or_404(User, pk=pk)
    FriendRequest.objects.filter(from_user=from_user, to_user=request.user).delete()
    return redirect("profile")
