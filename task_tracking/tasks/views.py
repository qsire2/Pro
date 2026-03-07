from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from tasks import models
from django.views.generic import ListView, DetailView, CreateView, View, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import TaskForm, TaskFilterForm, CommentForm
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

from .mixins import UserIsOwnerMixin



class TaskListView(ListView):
    model = models.Task
    context_object_name = "tasks"
    template_name = "tasks/templates/task_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get("status", "")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = TaskFilterForm(self.request.GET)
        return context


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = models.Task
    context_object_name = "task"
    template_name = "tasks/templates/task_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = CommentForm()
        return context

    def post(self, request, *args, **kwargs):
        comment_form = CommentForm(request.POST, request.FILES)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.task = self.get_object()
            comment.save()
            return redirect("tasks:task-detail", pk=comment.task.pk)


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = models.Task
    form_class = TaskForm
    template_name = "tasks/templates/task_form.html"
    success_url = reverse_lazy("tasks:task-list")

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = models.Task
    form_class = TaskForm
    template_name = "tasks/templates/task_update_form.html"
    success_url = reverse_lazy("tasks:task-list")


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = models.Task
    template_name = "tasks/templates/task_delete_confirmation.html"
    success_url = reverse_lazy("tasks:task-list")


class TaskCompleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        task = get_object_or_404(models.Task, pk=pk)
        task.completed = True
        task.save()
        return redirect("tasks:task-detail", pk=pk)


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = models.Comment
    form_class = CommentForm
    template_name = "tasks/templates/edit_comment.html"

    def get_success_url(self):
        return self.object.task.get_absolute_url()


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = models.Comment
    template_name = "tasks/templates/delete_comment.html"

    def get_success_url(self):
        return self.object.task.get_absolute_url()


class CommentLikeToggle(LoginRequiredMixin, View):
    def get(self, request, pk):
        comment = get_object_or_404(models.Comment, pk=pk)

        if request.user in comment.likes.all():
            comment.likes.remove(request.user)
        else:
            comment.likes.add(request.user)

        return redirect(request.META.get("HTTP_REFERER"))


class CustomLoginView(LoginView):
    template_name = "tasks/templates/login.html"


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("tasks:login")


class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = "tasks/templates/register.html"
    success_url = reverse_lazy("tasks:login")