from django.test import TestCase
from django.contrib.auth.models import User
from .models import Habit, CheckOff, OccurrenceRate
from datetime import date
from django.urls import reverse

class BaseTestSetup(TestCase):
    
    def setUp(self):
        # ======= setup users
        self.user1 = User.objects.create_user(username="John", password="password1")
        self.user2 = User.objects.create_user(username="Jane", password="password2")

        # ======= setup occurrences
        self.dalyOccurrence = OccurrenceRate.objects.create(description="Daily", daily_rate=1)
        self.weeklyOccurrence = OccurrenceRate.objects.create(description="Weekly", daily_rate=7)

        # ======= setup habits
        self.habit1John = Habit.objects.create(description="John Habit 1", user=self.user1, date_created=date(2024, 9, 15), occurrence=self.dalyOccurrence)
        self.habit2John = Habit.objects.create(description="John Habit 2", user=self.user1, date_created=date(2024, 9, 16), occurrence=self.weeklyOccurrence)
        self.habit3John = Habit.objects.create(description="John Habit 3", user=self.user1, date_created=date(2024, 9, 17), occurrence=self.dalyOccurrence)
        
        self.habit1Jane = Habit.objects.create(description="Jane Habit 1", user=self.user2, date_created=date(2024, 9, 15), occurrence=self.weeklyOccurrence)
        self.habit2Jane = Habit.objects.create(description="Jane Habit 2", user=self.user2, date_created=date(2024, 9, 16), occurrence=self.dalyOccurrence)

        # ======= setup checkoffs
        # ========================= john
        CheckOff.objects.create(habit=self.habit1John, date_added=date(2024, 9, 15))
        CheckOff.objects.create(habit=self.habit1John, date_added=date(2024, 9, 16))
        CheckOff.objects.create(habit=self.habit1John, date_added=date(2024, 9, 17))

        CheckOff.objects.create(habit=self.habit2John, date_added=date(2024, 9, 17))
        CheckOff.objects.create(habit=self.habit2John, date_added=date(2024, 9, 24))

        CheckOff.objects.create(habit=self.habit3John, date_added=date(2024, 9, 17))
        CheckOff.objects.create(habit=self.habit3John, date_added=date(2024, 9, 18))

        # ========================= jane
        CheckOff.objects.create(habit=self.habit1Jane, date_added=date(2024, 9, 15))
        CheckOff.objects.create(habit=self.habit1Jane, date_added=date(2024, 9, 16))
        CheckOff.objects.create(habit=self.habit1Jane, date_added=date(2024, 9, 20))
        CheckOff.objects.create(habit=self.habit1Jane, date_added=date(2024, 9, 21))
        CheckOff.objects.create(habit=self.habit1Jane, date_added=date(2024, 9, 22))

        CheckOff.objects.create(habit=self.habit2Jane, date_added=date(2024, 9, 17))
        CheckOff.objects.create(habit=self.habit2Jane, date_added=date(2024, 9, 25))


class AnalyticsViewTest(BaseTestSetup):

    def test_analytics_view_status_code(self):
        self.client.login(username="John", password="password1")
        response = self.client.get(reverse("analytics"))
        self.assertEqual(response.status_code, 200)
        
    def test_analytics_view_template_used(self):
        self.client.login(username="John", password="password1")
        response = self.client.get(reverse("analytics"))
        self.assertTemplateUsed(response, "analytics.html")

    def test_analytics_view_context(self):
        self.client.login(username="John", password="password1")
        response = self.client.get(reverse("analytics"))
        habits_list = response.context["habits_list"]
        
        self.assertEqual(len(habits_list), 3)
        
        self.assertEqual(habits_list[0]["habit"].description, "John Habit 1")
        self.assertEqual(habits_list[0]["consecutive_count"], 3)
        self.assertEqual(habits_list[0]["is_streak_active"], False)

        self.assertEqual(habits_list[1]["habit"].description, "John Habit 2")
        self.assertEqual(habits_list[1]["consecutive_count"], 2)
        self.assertEqual(habits_list[1]["is_streak_active"], False)

        
class HomeViewTest(BaseTestSetup):

    def test_home_view_status_code(self):
        self.client.login(username="Jane", password="password2")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_home_view_context(self):
        self.client.login(username="Jane", password="password2")
        response = self.client.get(reverse("home"))
        habits = response.context["habits"]

        self.assertEqual(len(habits), 2)
        
        self.assertEqual(habits[0].description, "Jane Habit 1")
        self.assertEqual(habits[0].occurrence.description, "Weekly")
        self.assertEqual(habits[1].description, "Jane Habit 2")
        self.assertEqual(habits[1].occurrence.description, "Daily")


class FilteredViewTest(BaseTestSetup):

    def test_filtered_view_status_code(self):
        self.client.login(username="Jane", password="password2")
        response = self.client.get(reverse("filtered", kwargs={"occurrence" : "daily", "checkedoffstatus": "streak-broken"}))
        self.assertEqual(response.status_code, 200)

    def test_filtered_view_context(self):
        self.client.login(username="Jane", password="password2")
        response = self.client.get(reverse("filtered", kwargs={"occurrence" : "daily", "checkedoffstatus": "streak-broken"}))
        habits = response.context["habits"]

        self.assertEqual(len(habits), 1)
        
        self.assertEqual(habits[0].description, "Jane Habit 2")
        self.assertEqual(habits[0].occurrence.description, "Daily")

class CreateHabitViewTest(BaseTestSetup):

    def test_habit_create_view(self):
        self.client.login(username="John", password="password1")
        response = self.client.post(reverse("add-new-habit"), {
            "description": "New Habit",
            "occurrence": self.dalyOccurrence.id
        })
        
        self.assertEqual(response.status_code, 302) 
        self.assertEqual(Habit.objects.count(), 6) 
        self.assertEqual(Habit.objects.last().description, "New Habit") 


class HabitDeleteViewTest(BaseTestSetup):

    def test_delete_habit_view(self):
        self.client.login(username="John", password="password1")
        habit_id = Habit.objects.first().id
        response = self.client.post(reverse("delete-habit", kwargs={"pk": habit_id}))
        self.assertFalse(Habit.objects.filter(id=habit_id).exists())
        self.assertRedirects(response, reverse("home"))


class HabitCheckoffViewTest(BaseTestSetup):

    def test_habit_checkoff_view(self):
        
        self.assertEqual(CheckOff.objects.count(), 14) 
        
        self.client.login(username="John", password="password1")
        habit_to_checkoff_id = Habit.objects.filter(user=self.user1).first().id
        response = self.client.post(reverse("checkoff-habit", kwargs={"pk": habit_to_checkoff_id}))
        
        self.assertEqual(response.status_code, 302) 
        self.assertEqual(CheckOff.objects.count(), 15)