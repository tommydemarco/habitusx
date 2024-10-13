from django.contrib import messages
from django.utils import timezone
from django.http import Http404
from datetime import timedelta
from .models import Habit
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin


class HabitsListView(LoginRequiredMixin, ListView):
    model = Habit
    template_name = "habit-list.html"
    context_object_name = "habits"
    ordering = ["-date_created"]

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)

class FilteredHabitListView(LoginRequiredMixin, ListView):
    model = Habit
    template_name = "habit-list.html"
    context_object_name = "habits"

    def get_queryset(self):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        checked_off_status = self.kwargs.get("checkedoffstatus")
        occurrence = self.kwargs.get("occurrence")

        daily_habits = Habit.objects.filter(occurrence__daily_rate=1, user=self.request.user)
        weekly_habits = Habit.objects.filter(occurrence__daily_rate=7, user=self.request.user)
        any_occurrence_habits = Habit.objects.filter(user=self.request.user)

        if occurrence == "daily": 
            habits_checked = daily_habits.filter(
                checkoffs__date_added=today, 
            ).distinct()
            habits_unchecked = daily_habits.filter(
                checkoffs__date_added=yesterday, 
            ).distinct()
            habits_broken = daily_habits.filter(
                checkoffs__date_added__gt=yesterday, 
            ).distinct()
            habits_any_status = daily_habits
        elif occurrence == "weekly":
            habits_checked = weekly_habits.filter(
                checkoffs__date_added__range=(today - timedelta(days=7), today), 
            ).distinct()
            habits_unchecked = weekly_habits.filter(
                checkoffs__date_added__range=(today - timedelta(days=14), today - timedelta(days=7)), 
            ).distinct()
            habits_broken = weekly_habits.filter(
                checkoffs__date_added__lt= today - timedelta(days=14), 
            ).distinct()
            habits_any_status = weekly_habits
        elif occurrence == "any-occurrence": 
            habits_checked = any_occurrence_habits.filter(
                checkoffs__date_added__range=(today - timedelta(days=7), today)
            ).distinct()
            habits_unchecked = any_occurrence_habits.filter(
                checkoffs__date_added__range=(today - timedelta(days=14), today - timedelta(days=7))
            ).distinct()
            habits_broken = any_occurrence_habits.filter(
                checkoffs__date_added__lt= today - timedelta(days=14)
            ).distinct()
            habits_any_status = any_occurrence_habits
        else: raise Http404('Occurrence 404')

        if checked_off_status == "checked": return habits_checked
        elif checked_off_status == "unchecked": return habits_unchecked
        elif checked_off_status == "broken": return habits_broken
        elif checked_off_status == "any-status": return habits_any_status
        else: raise Http404(checked_off_status)



class HabitCreateView(LoginRequiredMixin, CreateView):
    model = Habit
    template_name = "add-new-habit.html"
    fields = ['description', 'occurrence']

    def get_success_url(self):
        return "/"

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Nice! You created a new habit')
        return super().form_valid(form)
    