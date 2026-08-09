from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model

from .models import Task


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
    fields = ["name", "description", "deadline", "status", "priority"]
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


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
        return context


class FriendProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "tasks/user_profile.html"
    context_object_name = "profile_user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["tasks"] = Task.objects.filter(
            owner=self.object
        )

        return context
    

class RegisterView(TemplateView):
    template_name = "registration/register.html"
