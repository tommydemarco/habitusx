from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class OccurrenceRate(models.Model):
    description = models.TextField(max_length=200)
    daily_rate = models.IntegerField()

    def __str__(self):
            return '%s' % (self.description)


class Habit(models.Model):
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    occurrence = models.ForeignKey(OccurrenceRate, related_name="occurrence", on_delete=models.CASCADE)
    date_created = models.DateTimeField(default=timezone.now)


class CheckOff(models.Model):
    habit = models.ForeignKey(Habit, related_name="checkoffs", on_delete=models.CASCADE)
    date_added = models.DateTimeField(default=timezone.now)
    
