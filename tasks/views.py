from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import TemplateView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model, login

from .models import Task, Comment, Friendship, FriendRequest, Status, Priority
from .forms import TaskForm


User = get_user_model()

TASKS_PER_PAGE = 10

SORT_OPTIONS = {
    "deadline": "deadline",
    "priority": "-priority",
    "created": "-created_at",
}


def filter_and_sort_tasks(request, queryset):
    """Применяет поиск, фильтры по статусу/приоритету/просрочке и сортировку
    из GET-параметров запроса к переданному queryset задач."""
    query = request.GET.get("q", "").strip()

    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    status = request.GET.get("status")
    if status in Status.values:
        queryset = queryset.filter(status=status)

    priority = request.GET.get("priority")
    if priority in [str(value) for value, _ in Priority.choices]:
        queryset = queryset.filter(priority=priority)

    if request.GET.get("overdue") == "1":
        queryset = queryset.filter(deadline__lt=timezone.now()).exclude(status=Status.DONE)

    sort = request.GET.get("sort")
    if sort in SORT_OPTIONS:
        queryset = queryset.order_by(SORT_OPTIONS[sort])

    return queryset


def paginate_tasks(request, queryset, context):
    """Разбивает queryset задач на страницы и добавляет в context объект
    страницы и строку GET-параметров (без page) для ссылок пагинации."""
    paginator = Paginator(queryset, TASKS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)

    context["tasks"] = page_obj
    context["page_obj"] = page_obj
    context["querystring"] = params.urlencode()

    return context


User = get_user_model()


class IndexView(TemplateView):
    template_name = "tasks/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            tasks = filter_and_sort_tasks(
                self.request, Task.objects.filter(owner=self.request.user)
            )
            context = paginate_tasks(self.request, tasks, context)

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

        tasks = filter_and_sort_tasks(
            self.request, Task.objects.filter(owner=self.request.user)
        )
        context = paginate_tasks(self.request, tasks, context)

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

        if is_friend:
            tasks = Task.objects.filter(owner=self.object)
            context = paginate_tasks(self.request, tasks, context)
        else:
            context["tasks"] = None

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


@login_required
@require_POST
def change_task_status(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    status = request.POST.get("status")

    is_valid_status = status in Status.values
    is_locked = task.status == Status.DONE and status != Status.DONE

    if is_valid_status and not is_locked:
        task.status = status
        task.save()

    next_url = request.POST.get("next")

    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}
    ):
        return redirect(next_url)

    return redirect("task_detail", pk=task.pk)
