from django.contrib import admin
from .models import StudyHistory,Subject,Task,StudyPlan,StudyBlock
admin.site.register([StudyHistory,Subject,Task,StudyPlan,StudyBlock])
