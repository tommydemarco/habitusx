from django.contrib import messages
from django.utils import timezone
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from datetime import timedelta
from .models import Habit, CheckOff
from django.views import View
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q


class HabitsListView(LoginRequiredMixin, ListView):
    model = Habit
    template_name = "habit-list.html"
    context_object_name = "habits"
    ordering = ["-date_created"]

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            today = timezone.now().date()
            monday = today - timedelta(days=today.weekday())
            two_mondays_ago = today - timedelta(days=today.weekday() + 7)
            context["monday"] = monday
            context["two_mondays_ago"] = two_mondays_ago
            for habit in context['habits']:
                latest_checkoff = habit.checkoffs.order_by('-date_added').first()
                habit.latest_checkoff = latest_checkoff 
            return context

class FilteredHabitListView(LoginRequiredMixin, ListView):
    model = Habit
    template_name = "habit-list.html"
    context_object_name = "habits"

    def get_queryset(self):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        day_before_yesterday = yesterday - timedelta(days=1)

        monday = today - timedelta(days=today.weekday())
        two_mondays_ago = today - timedelta(days=today.weekday() + 7)

        checked_off_status = self.kwargs.get("checkedoffstatus")
        occurrence = self.kwargs.get("occurrence")

        daily_habits = Habit.objects.filter(occurrence__daily_rate=1, user=self.request.user)
        weekly_habits = Habit.objects.filter(occurrence__daily_rate=7, user=self.request.user)

        if occurrence == "daily": 
            habits_checked = daily_habits.filter(
                Q(checkoffs__date_added__gt=today),
            ).distinct()
            habits_unchecked = daily_habits.filter(
                (Q(date_created__date=today) & Q(checkoffs__isnull=True)) |
                Q(checkoffs__date_added__lt=day_before_yesterday)
            ).distinct()
            habits_broken = daily_habits.filter(
                checkoffs__date_added__lt=yesterday, 
            ).distinct()
            habits_any_status = daily_habits
        elif occurrence == "weekly":
            habits_checked = weekly_habits.filter(
                checkoffs__date_added__range=(monday, today), 
            ).distinct()
            habits_unchecked = weekly_habits.filter(
                ((Q(date_created__date__gte=monday) & Q(checkoffs__isnull=True))) |
                (Q(checkoffs__date_added__lte=two_mondays_ago) & ~Q(checkoffs__date_added__range=(monday, today)))
            ).distinct()
            habits_broken = weekly_habits.filter(
                Q(checkoffs__date_added__lt=monday)
            ).distinct()
            habits_any_status = weekly_habits
        elif occurrence == "any-occurrence": 
            habits_checked = daily_habits.filter(
                Q(checkoffs__date_added__gt=today),
            ).distinct() | weekly_habits.filter(
                checkoffs__date_added__range=(monday, today), 
            ).distinct()
            habits_unchecked = daily_habits.filter(
                (Q(date_created__date=today) & Q(checkoffs__isnull=True)) |
                Q(checkoffs__date_added__lt=day_before_yesterday)
            ).distinct() | weekly_habits.filter(
                ((Q(date_created__date__gte=monday) & Q(checkoffs__isnull=True))) |
                (Q(checkoffs__date_added__lte=two_mondays_ago) & ~Q(checkoffs__date_added__range=(monday, today)))
            ).distinct()
            habits_broken = daily_habits.filter(
                checkoffs__date_added__lt=yesterday, 
            ).distinct() | weekly_habits.filter(
                Q(checkoffs__date_added__lt=monday)
            ).distinct()
            habits_any_status = daily_habits | weekly_habits
        else: raise Http404('Occurrence 404')

        if checked_off_status == "checked": return habits_checked
        elif checked_off_status == "unchecked": return habits_unchecked
        elif checked_off_status == "streak-broken": return habits_broken
        elif checked_off_status == "any-status": return habits_any_status
        else: raise Http404(checked_off_status)

    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            today = timezone.now().date()
            monday = today - timedelta(days=today.weekday())
            two_mondays_ago = today - timedelta(days=today.weekday() + 7)
            context["monday"] = monday
            context["two_mondays_ago"] = two_mondays_ago
            for habit in context['habits']:
                latest_checkoff = habit.checkoffs.order_by('-date_added').first()
                habit.latest_checkoff = latest_checkoff 
            return context


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
    
class HabitDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        habit = get_object_or_404(Habit, pk=pk)
        
        if habit.user == request.user:
            habit.delete()

        messages.success(self.request, 'The habit was successfully deleted')
        return redirect('/') 
    
class CheckoffCreateView(LoginRequiredMixin, View):
   def post(self, request, pk):
        habit = get_object_or_404(Habit, pk=pk)

        if not habit:
            messages.error(self.request, 'There was an error in checking off the habit. PLease try again')
            return redirect('/') 
        
        CheckOff.objects.create(
            habit=habit,
            date_added=timezone.now()
        )

        messages.error(self.request, 'The habit was checked off successfully')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))