"""
models.py — Database Models
============================
Defines the database structure for the AI Study Planner app.

MODELS:
  1. StudyHistory — Stores each user's study plan session
"""

from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


class StudyHistory(models.Model):
    """
    Stores a record every time a user generates a study plan.
    
    Fields:
      user      → Which user made this request (linked to Django's built-in User)
      mood      → The mood the user selected
      hours     → How many hours available
      focus     → Focus level (1–10)
      intensity → AI-predicted intensity (Light/Moderate/Intense)
      date      → When the plan was generated
    
    VIVA TIP:
      This is a ForeignKey relationship — one user can have MANY study history
      records, but each history record belongs to exactly ONE user.
    """
    
    # Mood choices for the dropdown
    MOOD_CHOICES = [
        ('Happy', '😊 Happy'),
        ('Sad', '😢 Sad'),
        ('Stressed', '😤 Stressed'),
        ('Energetic', '⚡ Energetic'),
        ('Tired', '😴 Tired'),
    ]
    
    # Intensity choices (AI output)
    INTENSITY_CHOICES = [
        ('Light', 'Light'),
        ('Moderate', 'Moderate'),
        ('Intense', 'Intense'),
    ]
    
    # ForeignKey: Each history record is linked to a user
    # on_delete=CASCADE means if user is deleted, their history is deleted too
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='study_histories'
    )
    
    mood = models.CharField(
        max_length=20,
        choices=MOOD_CHOICES,
        help_text="User's mood when generating the plan"
    )
    
    hours = models.IntegerField(
        help_text="Available study hours (1–8)"
    )
    
    focus = models.IntegerField(
        help_text="Self-rated focus level (1–10)"
    )
    
    intensity = models.CharField(
        max_length=20,
        choices=INTENSITY_CHOICES,
        help_text="AI-predicted study intensity"
    )
    
    # auto_now_add=True automatically sets date to now when record is created
    date = models.DateTimeField(
        auto_now_add=True,
        help_text="When the plan was generated"
    )
    
    class Meta:
        # Order by newest first
        ordering = ['-date']
        verbose_name = 'Study History'
        verbose_name_plural = 'Study Histories'
    
    def __str__(self):
        """String representation — shown in Django admin panel"""
        return f"{self.user.username} | {self.mood} | {self.intensity} | {self.date.strftime('%Y-%m-%d')}"
    
    def get_mood_emoji(self):
        """Returns emoji for the mood"""
        emojis = {
            'Happy': '😊',
            'Sad': '😢',
            'Stressed': '😤',
            'Energetic': '⚡',
            'Tired': '😴',
        }
        return emojis.get(self.mood, '😐')
    
    def get_intensity_color(self):
        """Returns CSS color class for intensity badge"""
        colors = {
            'Light': 'badge-light-intensity',
            'Moderate': 'badge-moderate-intensity',
            'Intense': 'badge-intense-intensity',
        }
        return colors.get(self.intensity, '')



class Subject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    color = models.CharField(max_length=7, default='#2563eb', validators=[RegexValidator(r'^#[0-9a-fA-F]{6}$')])
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user','name'],name='unique_user_subject')]
    def __str__(self): return self.name

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject,on_delete=models.CASCADE,related_name='tasks')
    title = models.CharField(max_length=160)
    due_date = models.DateField(null=True,blank=True)
    estimated_minutes = models.PositiveIntegerField(default=60, validators=[MinValueValidator(5), MaxValueValidator(1440)])
    difficulty = models.PositiveSmallIntegerField(choices=[(1,'Easy'),(2,'Medium'),(3,'Hard')],default=2)
    priority = models.PositiveSmallIntegerField(choices=[(1,'Low'),(2,'Normal'),(3,'High')],default=2)
    completed = models.BooleanField(default=False)
    def __str__(self): return self.title

class StudyPlan(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='plans')
    title = models.CharField(max_length=120)
    mood = models.CharField(max_length=20,choices=StudyHistory.MOOD_CHOICES)
    focus = models.PositiveSmallIntegerField()
    minutes = models.PositiveIntegerField()
    intensity = models.CharField(max_length=20,choices=StudyHistory.INTENSITY_CHOICES)
    explanation = models.TextField()
    archived = models.BooleanField(default=False)
    starts_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-created_at']

class StudyBlock(models.Model):
    plan = models.ForeignKey(StudyPlan,on_delete=models.CASCADE,related_name='blocks')
    task = models.ForeignKey(Task,on_delete=models.SET_NULL,null=True,blank=True)
    title = models.CharField(max_length=180)
    kind = models.CharField(max_length=10,choices=[('study','Study'),('break','Break')])
    position = models.PositiveIntegerField()
    minutes = models.PositiveIntegerField()
    starts_at = models.DateTimeField()
    completed = models.BooleanField(default=False)
    class Meta:
        ordering=['position']
        constraints=[models.UniqueConstraint(fields=['plan','position'],name='unique_plan_position')]
