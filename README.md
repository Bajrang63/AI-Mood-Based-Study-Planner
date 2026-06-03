# 🧠 AI Mood-Based Study Planner
### Final Year Project — Django + scikit-learn (Decision Tree)

---

## 📁 Project Structure

```
study_planner/
│
├── manage.py                    ← Django management commands
├── requirements.txt             ← Python dependencies
├── Procfile                     ← For Render/Railway deployment
├── runtime.txt                  ← Python version for deployment
│
├── study_planner/               ← Project config package
│   ├── __init__.py
│   ├── settings.py              ← Main Django settings
│   ├── production_settings.py   ← Production-only settings
│   ├── urls.py                  ← Root URL configuration
│   └── wsgi.py                  ← WSGI entry point
│
├── planner/                     ← Main application
│   ├── __init__.py
│   ├── models.py                ← Database models (StudyHistory)
│   ├── views.py                 ← View functions (controllers)
│   ├── urls.py                  ← App URL routing
│   ├── admin.py                 ← Django admin config
│   ├── ml_model.py              ← Decision Tree AI model
│   ├── study_model.pkl          ← Saved trained model (auto-generated)
│   │
│   ├── templates/               ← HTML templates
│   │   ├── base.html            ← Base layout (navbar, footer)
│   │   ├── index.html           ← Home / form page
│   │   ├── result.html          ← Study plan result page
│   │   ├── login.html           ← Login + Register page
│   │   └── history.html         ← Past sessions + charts
│   │
│   └── static/
│       ├── css/style.css        ← All styles
│       └── js/script.js         ← Frontend JavaScript
│
└── db.sqlite3                   ← SQLite database (auto-created)
```

---

## 🚀 LOCAL SETUP (Step-by-Step)

### Step 1 — Clone / Download the project
```bash
# If using git:
git clone <your-repo-url>
cd study_planner

# Or just navigate to the downloaded folder:
cd study_planner
```

### Step 2 — Create a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Set up the database
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 5 — Create an admin user (optional)
```bash
python manage.py createsuperuser
# Enter username, email, password when prompted
```

### Step 6 — Run the development server
```bash
python manage.py runserver
```

### Step 7 — Open in browser
```
http://127.0.0.1:8000/
```

> The AI model trains automatically on first run — no extra steps needed!

---

## 🌐 DEPLOYMENT GUIDE

### Option A — Deploy on Render (Free, Recommended)

1. Push your project to GitHub

2. Go to [render.com](https://render.com) → New → Web Service

3. Connect your GitHub repository

4. Set these values:
   - **Build Command:** `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput`
   - **Start Command:** `gunicorn study_planner.wsgi:application`

5. Add Environment Variables:
   - `SECRET_KEY` → any long random string
   - `DJANGO_SETTINGS_MODULE` → `study_planner.production_settings`
   - `ALLOWED_HOSTS` → `your-app-name.onrender.com`

6. Click **Deploy** — done! 🎉

---

### Option B — Deploy on Railway

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. Initialize and deploy:
   ```bash
   railway init
   railway up
   ```

3. Set environment variables in Railway dashboard (same as Render above)

---

### Option C — Deploy on PythonAnywhere (Free tier)

1. Sign up at [pythonanywhere.com](https://pythonanywhere.com)

2. Open a Bash console and run:
   ```bash
   git clone <your-repo-url>
   cd study_planner
   pip install --user -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic
   ```

3. Go to **Web** tab → Add a new web app → Manual config → Python 3.11

4. Set your **WSGI configuration file** to point to your project

5. In the WSGI file, add:
   ```python
   import sys
   import os
   sys.path.insert(0, '/home/<your-username>/study_planner')
   os.environ['DJANGO_SETTINGS_MODULE'] = 'study_planner.settings'
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

6. Reload the web app — done!

---

## 🧠 MODULE EXPLANATIONS (For Viva)

### 1. `ml_model.py` — The AI Brain
This is the core of the project. It:
- Generates synthetic training data based on expert study rules
- Trains a **Decision Tree Classifier** from scikit-learn
- Saves the trained model as `study_model.pkl` using `pickle`
- Provides a `predict_intensity()` function that views.py calls
- Generates time-blocked study schedules and personalized tips

**Why Decision Tree?**
- Easy to understand and explain
- No need for data normalization
- Visual and interpretable (you can draw it on a whiteboard)
- Works well for small, rule-based datasets

### 2. `models.py` — Database Blueprint
Defines the `StudyHistory` table in SQLite:
- `ForeignKey` to Django's built-in `User` model (one-to-many)
- Stores mood, hours, focus, intensity, and timestamp
- Django ORM converts Python code to SQL automatically

### 3. `views.py` — Request Handlers
Each function processes one URL:
- `@login_required` decorator protects pages from unauthenticated users
- `request.session` passes data between views without a database round-trip
- `authenticate()` and `login()` are Django's built-in auth functions

### 4. `urls.py` — URL Router
Maps URL strings to view functions.
- `path('', home_view, name='home')` — the name allows `{% url 'home' %}` in templates
- Django checks URLs from top to bottom and calls the first match

### 5. Templates (`index.html`, `result.html`, etc.)
Use **Django Template Language (DTL)**:
- `{{ variable }}` — outputs a value
- `{% for item in list %}` — loops
- `{% if condition %}` — conditionals
- `{% url 'name' %}` — generates URLs
- `{% extends 'base.html' %}` — template inheritance

### 6. `style.css` — Glassmorphism UI
- CSS custom properties (`--variable`) for consistent theming
- `backdrop-filter: blur()` for glass effect
- CSS Grid for responsive layouts
- `@keyframes` for smooth animations

### 7. `script.js` — Frontend Logic
- Updates sliders in real-time with `input` event
- Validates form before submission
- Renders Chart.js charts for mood history
- `IntersectionObserver` for scroll animations

---

## ❓ 10 IMPORTANT VIVA QUESTIONS & ANSWERS

---

**Q1: What is the core AI/ML algorithm used in this project?**

**A:** The project uses a **Decision Tree Classifier** from scikit-learn. It takes three inputs — mood (encoded as 0–4), available hours (1–8), and focus level (1–10) — and predicts one of three study intensity levels: Light, Moderate, or Intense. I chose Decision Tree because it's highly interpretable, doesn't require feature scaling, and works well for categorical + numerical mixed inputs.

---

**Q2: How does the Decision Tree make a prediction?**

**A:** A Decision Tree splits data at each node using a criterion called **Gini Impurity** — it finds the feature and threshold that best separates the classes. For example, it might first split on focus level (focus < 5 → Light path), then on hours. The tree keeps splitting until it reaches a leaf node, which gives the final prediction. My tree has `max_depth=5` to prevent overfitting.

---

**Q3: What is overfitting and how did you handle it?**

**A:** Overfitting is when a model memorizes the training data but fails on new data. I handled it by:
1. Setting `max_depth=5` to limit tree complexity
2. Using an 80/20 train-test split with `train_test_split()`
3. Evaluating accuracy on the unseen test set

---

**Q4: Why did you use synthetic data instead of real data?**

**A:** Collecting real-world labeled study data would require extensive user surveys and ethical approval, which is impractical for a college project. Instead, I applied expert knowledge about how mood, hours, and focus affect study productivity to create rule-based synthetic data. This approach simulates what a study counselor would recommend and still trains a meaningful model.

---

**Q5: Explain the Django MVT architecture.**

**A:**
- **Model (models.py):** Defines database structure — the `StudyHistory` model maps to a database table
- **View (views.py):** Contains business logic — processes requests, calls the ML model, and returns responses
- **Template (templates/):** HTML files that display data to the user

Django's `urls.py` routes incoming requests to the correct view, which retrieves data via the model and renders a template.

---

**Q6: What is a ForeignKey and why did you use it?**

**A:** A `ForeignKey` creates a many-to-one relationship between tables. In this project, `StudyHistory.user = ForeignKey(User)` means one User can have many StudyHistory records, but each StudyHistory belongs to exactly one User. When the user is deleted (`on_delete=CASCADE`), all their history is automatically removed too.

---

**Q7: How does user authentication work in your app?**

**A:** I used Django's built-in authentication system:
1. `authenticate(username, password)` — checks credentials against the database
2. `login(request, user)` — stores the user in the session cookie
3. `@login_required` decorator — redirects unauthenticated users to `/login/`
4. `logout(request)` — clears the session

Passwords are never stored in plain text — Django uses PBKDF2 hashing by default.

---

**Q8: What is `pickle` and why is it used?**

**A:** `pickle` is Python's built-in serialization library. It converts a Python object (the trained model) into bytes and saves it to a `.pkl` file. When the app starts, it loads this file instead of retraining the model from scratch on every request. This is crucial for performance — training takes seconds, but loading takes milliseconds.

---

**Q9: How does the study schedule get generated?**

**A:** The `generate_study_plan()` function in `ml_model.py` uses a Pomodoro-style approach based on the predicted intensity:
- **Light:** 25-minute study + 10-minute break
- **Moderate:** 45-minute study + 10-minute break
- **Intense:** 60-minute study + 5-minute break

It calculates time blocks within the available hours and returns a list of dictionaries, each representing a study or break block.

---

**Q10: How would you scale this app for 10,000 users?**

**A:** Several improvements for scale:
1. Switch from SQLite to PostgreSQL (handles concurrent writes)
2. Use Redis for session storage and caching
3. Deploy on a cloud platform (AWS/GCP) with auto-scaling
4. Add Celery for background tasks (e.g., weekly email summaries)
5. Serve static files via CDN (e.g., AWS CloudFront)
6. Use a more sophisticated ML model trained on real user data

---

## 💬 HOW TO EXPLAIN YOUR PROJECT CONFIDENTLY

**30-Second Elevator Pitch:**
> "I built an AI-powered web application using Django and scikit-learn that helps students optimize their study sessions. Users input their mood, available hours, and focus level. A Decision Tree classifier then predicts the optimal study intensity — Light, Moderate, or Intense — and generates a personalized time-blocked schedule. All sessions are saved to a database, so students can track their patterns over time through visual charts."

**Key Points to Emphasize:**
- ✅ Full-stack: Frontend (HTML/CSS/JS) + Backend (Django) + AI/ML (scikit-learn)
- ✅ Real database integration (SQLite with Django ORM)
- ✅ User authentication with session management
- ✅ Explainable AI — Decision Tree is interpretable
- ✅ Complete deployment-ready project

---

## 🛠 TECH STACK SUMMARY

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | HTML5, CSS3, JS | UI/UX |
| Backend | Django 4.2 | Web framework |
| AI/ML | scikit-learn | Decision Tree model |
| Database | SQLite | Data storage |
| Charts | Chart.js | Data visualization |
| Icons | Font Awesome | UI icons |
| Fonts | Google Fonts | Typography |
| Deployment | Render/Railway | Cloud hosting |

---

## 📝 LICENSE
This project is created for educational purposes as a Final Year Project.
