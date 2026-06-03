"""
views.py — View Functions (Controllers)
========================================
Each function here handles one URL/page of the web app.

VIEWS:
  1. home_view       → Main form page (index.html)
  2. predict_view    → Handles form submission + AI prediction
  3. result_view     → Shows the study plan result
  4. history_view    → Shows user's past study plans
  5. download_csv    → Downloads plan as CSV
  6. login_view      → Login page
  7. register_view   → Register page
  8. logout_view     → Logs user out

FLOW:
  User fills form → predict_view → saves to DB → redirects to result_view
"""

import csv
import json
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Count

from .models import StudyHistory
from .ml_model import predict_intensity
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'study_planner.settings')
django.setup()


# -------------------------------------------------------
# 1. HOME VIEW — Main Form Page
# -------------------------------------------------------
@login_required  # User must be logged in to access
def home_view(request):
    """
    Renders the main form page where users enter:
    - Mood, Available Hours, Focus Level
    
    Also shows the last 5 study sessions for quick reference.
    """
    # Get last 5 history items for the sidebar
    recent_history = StudyHistory.objects.filter(
        user=request.user
    ).order_by('-date')[:5]
    
    context = {
        'user': request.user,
        'recent_history': recent_history,
        'page': 'home',
    }
    return render(request, 'index.html', context)


# -------------------------------------------------------
# 2. PREDICT VIEW — Processes Form + Runs AI Model
# -------------------------------------------------------
@login_required
def predict_view(request):
    """
    Handles the POST form submission from index.html.
    
    Steps:
      1. Extract form data (mood, hours, focus)
      2. Validate input
      3. Call AI model to predict intensity
      4. Save result to database (StudyHistory)
      5. Store result in session
      6. Redirect to result page
    """
    if request.method != 'POST':
        return redirect('home')
    
    # Step 1: Extract form data
    mood = request.POST.get('mood', 'Happy')
    try:
        hours = int(request.POST.get('hours', 4))
        focus = int(request.POST.get('focus', 5))
    except (ValueError, TypeError):
        messages.error(request, "Invalid input. Please enter valid numbers.")
        return redirect('home')
    
    # Step 2: Validate ranges
    hours = max(1, min(8, hours))    # Clamp to 1–8
    focus = max(1, min(10, focus))   # Clamp to 1–10
    
    valid_moods = ['Happy', 'Sad', 'Stressed', 'Energetic', 'Tired']
    if mood not in valid_moods:
        mood = 'Happy'
    
    # Step 3: Run AI prediction
    result = predict_intensity(mood, hours, focus)
    
    # Step 4: Save to database
    history_record = StudyHistory.objects.create(
        user=request.user,
        mood=mood,
        hours=hours,
        focus=focus,
        intensity=result['intensity'],
    )
    
    # Step 5: Store result in session (to pass to result page)
    request.session['last_result'] = {
        'intensity': result['intensity'],
        'confidence': result['confidence'],
        'mood': mood,
        'hours': hours,
        'focus': focus,
        'study_plan': result['study_plan'],
        'tips': result['tips'],
        'history_id': history_record.id,
    }
    
    # Step 6: Redirect to result page
    return redirect('result')


# -------------------------------------------------------
# 3. RESULT VIEW — Displays AI-Generated Study Plan
# -------------------------------------------------------
@login_required
def result_view(request):
    """
    Displays the generated study plan to the user.
    Reads result from session (set in predict_view).
    """
    result = request.session.get('last_result')
    
    if not result:
        messages.info(request, "Please generate a study plan first.")
        return redirect('home')
    
    # Add intensity-specific styling info
    intensity_config = {
        'Light': {
            'color': '#4ade80',
            'emoji': '🌿',
            'description': 'A gentle, relaxed study session. Perfect for review and light reading.',
            'badge_class': 'intensity-light',
        },
        'Moderate': {
            'color': '#f59e0b',
            'emoji': '⚡',
            'description': 'A balanced, focused session. Good for learning new concepts.',
            'badge_class': 'intensity-moderate',
        },
        'Intense': {
            'color': '#f43f5e',
            'emoji': '🔥',
            'description': 'A deep, challenging session. Best for complex problem-solving.',
            'badge_class': 'intensity-intense',
        },
    }
    
    config = intensity_config.get(result['intensity'], intensity_config['Moderate'])
    
    context = {
        'result': result,
        'config': config,
        'page': 'result',
    }
    return render(request, 'result.html', context)


# -------------------------------------------------------
# 4. HISTORY VIEW — Shows Past Study Plans
# -------------------------------------------------------
@login_required
def history_view(request):
    """
    Shows all of the user's past study plan sessions.
    """
    # All history for this user
    all_history = StudyHistory.objects.filter(user=request.user)
    
    # Mood distribution for chart (count of each mood)
    mood_counts = (
        all_history.values('mood')
        .annotate(count=Count('mood'))
        .order_by('mood')
    )

    # Intensity distribution
    intensity_counts = (
        all_history.values('intensity')
        .annotate(count=Count('intensity'))
        .order_by('intensity')
    )

    # Time series data for focus trend chart
    focus_dates = [h.date.strftime('%b %d') for h in all_history.order_by('date')]
    focus_values = [h.focus for h in all_history.order_by('date')]
    
    chart_labels = [item['mood'] for item in mood_counts]
    chart_data = [item['count'] for item in mood_counts]
    
    context = {
        'history': all_history,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'focus_dates': json.dumps(focus_dates),
        'focus_values': json.dumps(focus_values),
        'intensity_counts': intensity_counts,
        'total_sessions': all_history.count(),
        'page': 'history',
    }
    return render(request, 'history.html', context)


# -------------------------------------------------------
# 5. DOWNLOAD CSV VIEW — Exports Study Plan as CSV
# -------------------------------------------------------
@login_required
def download_csv(request):
    """
    Downloads the user's study history as a CSV file.
    Can also download just the last plan if history_id is provided.
    """
    # Create HTTP response with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="study_plan.csv"'
    
    writer = csv.writer(response)
    
    # CSV Header row
    writer.writerow(['Date', 'Mood', 'Hours', 'Focus Level', 'Study Intensity'])
    
    # Get user's history
    history = StudyHistory.objects.filter(user=request.user)
    
    # Write each row
    for record in history:
        writer.writerow([
            record.date.strftime('%Y-%m-%d %H:%M'),
            record.mood,
            record.hours,
            record.focus,
            record.intensity,
        ])
    
    return response


# -------------------------------------------------------
# 6. LOGIN VIEW
# -------------------------------------------------------
def login_view(request):
    """
    Handles both GET (show login form) and POST (process login).
    """
    # If user is already logged in, redirect to home
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}! 🎉")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    
    return render(request, 'login.html', {'page': 'login'})


# -------------------------------------------------------
# 7. REGISTER VIEW
# -------------------------------------------------------
def register_view(request):
    """
    Handles user registration.
    Creates a new User object and logs them in automatically.
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        # Validation
        if not username or not password1:
            messages.error(request, "Username and password are required.")
        elif password1 != password2:
            messages.error(request, "Passwords do not match.")
        elif len(password1) < 6:
            messages.error(request, "Password must be at least 6 characters.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken. Choose another.")
        else:
            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
            )
            # Auto-login after registration
            login(request, user)
            messages.success(request, f"Account created! Welcome, {username}! 🎉")
            return redirect('home')
    
    return render(request, 'login.html', {'page': 'register'})


# -------------------------------------------------------
# 8. LOGOUT VIEW
# -------------------------------------------------------
def logout_view(request):
    """Logs the user out and redirects to login page."""
    logout(request)
    messages.info(request, "You've been logged out. See you soon! 👋")
    return redirect('login')


# -------------------------------------------------------
# 9. CHART DATA API — Returns JSON for mood chart
# -------------------------------------------------------
@login_required
def chart_data_api(request):
    """
    API endpoint that returns mood history as JSON for Chart.js.
    Called by JavaScript on the history page.
    """
    history = StudyHistory.objects.filter(user=request.user).order_by('date')
    
    data = {
        'dates': [h.date.strftime('%b %d') for h in history],
        'moods': [h.mood for h in history],
        'intensities': [h.intensity for h in history],
        'focus': [h.focus for h in history],
        'hours': [h.hours for h in history],
    }
    
    return JsonResponse(data)
