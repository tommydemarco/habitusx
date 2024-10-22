from django.contrib import messages
from django.utils import timezone
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from datetime import timedelta, date
from .models import Habit, CheckOff
from django.views import View
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotAllowed
from django.db.models import Q
from django.shortcuts import render

def get_week_monday_from_day(day):
    """
    A utility function that returns the monday of the week in which parameter day belongs to
    """
    return day - timedelta(days=day.weekday())


class HabitsListView(LoginRequiredMixin, ListView):
    """
    Displays a list of habit belonging to the user that requested the page, orered by the date in which they were created
    """
    
    model = Habit
    template_name = "habit-list.html"
    context_object_name = "habits"
    ordering = ["-date_created"]

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            today = timezone.now().date()
            yesterday = today - timedelta(days=1)
            last_monday = today - timedelta(days=today.weekday())
            two_mondays_ago = today - timedelta(days=today.weekday() + 7)
            context["yesterday"] = yesterday
            context["last_monday"] = last_monday
            context["two_mondays_ago"] = two_mondays_ago
            for habit in context['habits']:
                latest_checkoff = habit.checkoffs.order_by('-date_added').first()
                habit.latest_checkoff = latest_checkoff 
            return context


class FilteredHabitListView(LoginRequiredMixin, ListView):
    """
    Displays a list of habit belonging to the user that requested the page, filtered by occurrence and checked-off status
    """
    
    model = Habit
    template_name = "habit-list.html"
    context_object_name = "habits"

    def get_queryset(self):
        """
        Returns a list of habits filtered by occurrence and checked-off status based on the value of get parameters
        """
        
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
        """
        Enriches the contexts with variables that are useful to display elements in the view, 
        such as the values of yesyerday, last_monday, and two_mondays_ago
        """
        
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        last_monday = today - timedelta(days=today.weekday())
        two_mondays_ago = today - timedelta(days=today.weekday() + 7)
        yesterday = today - timedelta(days=1)
        context["yesterday"] = yesterday
        context["last_monday"] = last_monday
        context["two_mondays_ago"] = two_mondays_ago
        for habit in context['habits']:
            latest_checkoff = habit.checkoffs.order_by('-date_added').first()
            habit.latest_checkoff = latest_checkoff 
        return context


class HabitCreateView(LoginRequiredMixin, CreateView):
    """
    Creates a habit with description and occurrence values coming from the POST request, and assigns the
    user associated to the habit as the user that performed the request. 
    On success, it redirects to the home page and shows a success message to the user
    """
    
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
    """
    Deletes a habit if a habit with the requested primary key belonging to the user that requested the deletion is found.
    On success, it redirects to the home page and shows a success message to the user
    """
    
    def post(self, request, pk):
        habit = get_object_or_404(Habit, pk=pk)
        
        if habit.user == request.user:
            habit.delete()

        messages.success(self.request, 'The habit was successfully deleted')
        return redirect('/') 

       
class CheckoffCreateView(LoginRequiredMixin, View):
    """
    Creates a CheckOff entity associated to the habit that matches the primary key passed in the POST request.
    On success, it shows a success message to the user
    On error, it redirects to the home page and shows an error message to the user
    """
    
    def post(self, request, pk):
        habit = get_object_or_404(Habit, pk=pk)

        if not habit:
            messages.error(self.request, 'There was an error in checking off the habit. PLease try again')
            return redirect('/') 
        
        CheckOff.objects.create(
            habit=habit,
            date_added=timezone.now()
        )

        messages.success(self.request, 'The habit was checked off successfully')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

   
def analytics_function_based_list_view(request):
    """
    It returns a collection of habits which are enriched with the following information:
        - The last date in which they were checked off
        - The maximum number of consecutive checkoffs (streak), according to the specific habit's occurrence (daily or weekly)
        - If their maximum streak of checkoffs is currently active or has been broken

    In addition, the context provided to the view by this function also includes a collection of habits with the
    longest streak among all tracked habits
    """
    
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET']) 
    
    sort_order = request.GET.get('sort', 'asc')
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    habits = Habit.objects.all()
    habits_list = []

    for habit in habits:
        checkoffs = CheckOff.objects.filter(habit=habit).order_by('date_added')
        
        consecutive_count = 0
        is_streak_active = False
        
        if checkoffs.exists() and habit.occurrence.daily_rate == 1:
            consecutive_count = 1 
            last_date = checkoffs.first().date_added  
            
            for checkoff in checkoffs[1:]:
                if checkoff.date_added.date() == last_date.date() + timedelta(days=1):
                    consecutive_count += 1
                    last_date = checkoff.date_added
                else:
                    break
                
            most_recent_date = checkoffs.last().date_added
            
            if most_recent_date.date() == yesterday or most_recent_date.date() == today:
                is_streak_active = True

        elif checkoffs.exists() and habit.occurrence.daily_rate == 7:    
            consecutive_count = 1
            current_week_monday = get_week_monday_from_day(date.today())
            last_week_monday = current_week_monday - timedelta(weeks=1)
            last_week_monday_checkoff = get_week_monday_from_day(checkoffs.first().date_added)

            for checkoff in checkoffs[1:]:
                current_week_monday_checkoff = get_week_monday_from_day(checkoff.date_added)
                if current_week_monday_checkoff.date() == last_week_monday_checkoff.date() + timedelta(weeks=1):
                    consecutive_count += 1
                    last_week_monday_checkoff = current_week_monday_checkoff
                else:
                    break

            most_recent_date = checkoffs.last().date_added
            most_recent_monday = get_week_monday_from_day(most_recent_date)

            if most_recent_monday.date() == current_week_monday or most_recent_monday.date() == last_week_monday:
                is_streak_active = True
        
        habits_list.append({
            "habit": habit,
            "last_date": last_date,
            "consecutive_count": consecutive_count,
            "is_streak_active": is_streak_active, 
        })

    if sort_order == "asc":
        habits_list = sorted(habits_list, key=lambda x: x["consecutive_count"])
    elif sort_order == "desc":
        habits_list = sorted(habits_list, key=lambda x: x["consecutive_count"], reverse=True)

    longest_streak_habits = []
    if not habits_list:
        longest_streak_habits = []
    else: 
        highest_count = max(habit["consecutive_count"] for habit in habits_list)
        longest_streak_habits = [habit for habit in habits_list if habit["consecutive_count"] == highest_count]

    context = {
        "habits_list": habits_list,
        "longest_streak_habits": longest_streak_habits
    }

    return render(request, 'analytics.html', context)