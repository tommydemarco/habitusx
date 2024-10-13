from django.urls import path
from .views import  HabitsListView, HabitCreateView, FilteredHabitListView, HabitDeleteView, CheckoffCreateView

urlpatterns = [
    path('', HabitsListView.as_view(), name='home'),
    path('/add-new-habit', HabitCreateView.as_view(), name='add-new-habit'),
    path('filter/<occurrence>/<checkedoffstatus>/', FilteredHabitListView.as_view(), name='filtered'),
    path('/delete-habit/<int:pk>/', HabitDeleteView.as_view(), name='delete-habit'),
    path('/checkoff-habit/<int:pk>/', CheckoffCreateView.as_view(), name='checkoff-habit'),
]
