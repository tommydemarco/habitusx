from django.contrib import admin
from .models import Habit, OccurrenceRate, CheckOff

admin.site.register(Habit)
admin.site.register(OccurrenceRate)
admin.site.register(CheckOff)