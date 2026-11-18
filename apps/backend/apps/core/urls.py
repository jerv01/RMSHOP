from django.urls import path

from .views import HealthView, ScheduledTasksView

urlpatterns = [
    path("health", HealthView.as_view(), name="health"),
    path(
        "internal/run-scheduled-tasks",
        ScheduledTasksView.as_view(),
        name="run-scheduled-tasks",
    ),
]
