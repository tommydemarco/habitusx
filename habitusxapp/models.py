from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class OccurrenceRate(models.Model):
    """
    The OccurrenceRate model represent the occurrence of a task, represented via its daily_rate attribute. 
    Although any integer could be assigned to the daily_rate attribute, the application currently supports the value of 1 and 7
    (which represent daily and weekly habits)
    """
    
    description = models.TextField(max_length=200)
    daily_rate = models.IntegerField()

    def __str__(self):
            return '%s' % (self.description)


class Habit(models.Model):
    """
    The Habit model represent a habit of a given user. 
    Besides the self-explainatory description and date_created attributes, the occurrence attribute is of ForeignKey type
    and creates a reltion to the OccurrenceRate model. This defines the occurrence of the task.
    """
    
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    occurrence = models.ForeignKey(OccurrenceRate, related_name="occurrence", on_delete=models.CASCADE)
    date_created = models.DateTimeField(default=timezone.now)


class CheckOff(models.Model):
    """
    The CheckOff model represent a date and time when a given habit has been checked off.
    It is completely independent of the occurrence of the habit. Hence, the application logic needs to make sure that
    CheckOff entities are not inserted at a frequency that is not in line with the occurrence value of the habit.
    """
    
    habit = models.ForeignKey(Habit, related_name="checkoffs", on_delete=models.CASCADE)
    date_added = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return 'Habit %s (%s) checkoff date %s' % (self.habit.id, self.habit.occurrence.description, self.date_added.strftime("%d-%m-%Y"))
    
