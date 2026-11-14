from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import StudyHistory, Subject, Task

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

class PlanForm(forms.Form):
    title = forms.CharField(max_length=120, initial='My study plan')
    mood = forms.ChoiceField(choices=StudyHistory.MOOD_CHOICES, widget=forms.RadioSelect)
    minutes = forms.IntegerField(min_value=15, max_value=480, initial=120, label='Available minutes')
    focus = forms.IntegerField(min_value=1, max_value=10, initial=6, widget=forms.NumberInput(attrs={'type':'range','min':1,'max':10}))
    start = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type':'datetime-local'}), label='Start time')
    intensity = forms.ChoiceField(choices=[('auto','Recommend for me')]+StudyHistory.INTENSITY_CHOICES)

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ('name','color')
        widgets = {'color':forms.TextInput(attrs={'type':'color'})}

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('title','subject','due_date','estimated_minutes','difficulty','priority')
        widgets = {'due_date':forms.DateInput(attrs={'type':'date'})}
    def __init__(self,*args,user,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['subject'].queryset = Subject.objects.filter(user=user)
