from django.urls import path
from .views import  HabitsListView, HabitCreateView, FilteredHabitListView

urlpatterns = [
    path('', HabitsListView.as_view(), name='home'),
    path('/add-new-habit', HabitCreateView.as_view(), name='add-new-habit'),
    path('filter/<occurrence>/<checkedoffstatus>/', FilteredHabitListView.as_view(), name='filtered'),
]
