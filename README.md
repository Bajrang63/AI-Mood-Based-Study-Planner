# Studyspace · AI Mood-Based Study Planner

A Django study workspace with blue-and-white light mode and black-and-blue dark mode. Organize subjects and deadlines, generate task-based schedules, and track your progress.

## Features

- Account registration with Django password validation; login, CSRF-protected actions, and POST logout.
- Responsive dashboard, persistent theme preference, keyboard focus states, reduced-motion support, and printable plans.
- Subjects, editable tasks, priorities, difficulty, deadlines, and task completion.
- Study plans with mood/focus inputs, 15–480 available minutes, local start time, and intensity override.
- Deadline-first task allocation with priority and difficulty tie-breakers. Minutes already allocated to other plans are reserved, preventing duplicate allocation.
- Saved study/break blocks, per-block completion, one-click replanning of unfinished time, plan history pagination, and separate plan/history CSV exports.
- Wall-clock focus timer with pause/reset and accurate background-tab countdown. Timer state itself resets on navigation/reload; completion is saved separately.
- Dashboard totals based on recorded block completion. Marking a task done is separate from marking a scheduled block complete.
- Earlier StudyHistory records remain available after migration.

## Local setup (Python 3.12)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Set environment variables in your shell. `.env.example` documents them; this app does not automatically load `.env` files.

```bash
# macOS/Linux
export DEBUG=true
export SECRET_KEY='replace-with-your-own-long-random-development-key'
python manage.py migrate
python manage.py runserver
```

PowerShell: `$env:DEBUG="true"` and `$env:SECRET_KEY="your-development-key"` before the Python commands. Open http://127.0.0.1:8000.

## Recommendation model

The default recommendation uses transparent mood/focus rules. The optional Decision Tree learns labels generated from synthetic scoring rules; it is a prototype and is not evidence that a schedule improves learning. No clinical mood assessment is performed. Users can override intensity.

```bash
python manage.py train_study_model
```

Training is explicit and never runs during application import. The model is loaded once per process. Restart workers after retraining. Generate the model with the installed dependency versions; the old scikit-learn 1.3 pickle is removed to avoid compatibility problems. Do not load model files from untrusted sources.

## Architecture

- `planner/forms.py`: typed, server-side input and ownership validation.
- `planner/services.py`: task allocation and complete plan creation.
- `planner/models.py`: Subject, Task, StudyPlan, StudyBlock, and legacy StudyHistory.
- `planner/views.py`: user-scoped pages, completion actions, exports, authentication.
- `planner/ml_model.py`: optional model training and recommendation rules.
- `planner/templates/` and `planner/static/`: Django templates, CSS tokens, theme and timer controls; no frontend framework required.

## Validation

```bash
python manage.py test
node tests/ui.test.cjs
python manage.py makemigrations --check --dry-run
python manage.py collectstatic --noinput
```

GitHub Actions runs these checks on pushes and pull requests. The DOM-contract test checks theme/menu controls and timer behavior without a rendering engine. Tests cover duration and continuity, task allocation, invalid input, ownership, CSRF, password validation, saved plans, exports, and preservation of legacy history.

## Deployment

Set `DEBUG=false`, a stable random `SECRET_KEY`, `ALLOWED_HOSTS`, and HTTPS `CSRF_TRUSTED_ORIGINS`. Choose `TIME_ZONE` (default Asia/Kolkata). Enable `TRUST_PROXY_SSL=true` only behind a proxy that strips untrusted forwarding headers. Run migrations, collect static files, then `gunicorn study_planner.wsgi:application`.

SQLite is the development default. Use persistent database storage; configure PostgreSQL and a shared cache for a multi-worker production deployment. The current login throttle uses Django's cache and is per process with the default local-memory backend. HTTPS and secure cookies are enabled when DEBUG is false. Check deployment settings with `python manage.py check --deploy`.

## Current limits and next steps

- Plans are saved, but individual scheduled blocks cannot yet be moved or resized. Edit tasks to influence future plans.
- Notification delivery, quizzes, and external calendar sync are not implemented.
- Use “Replan unfinished time” to archive a plan and allocate its remaining time from now. Completed blocks remain in the original plan; unfinished reservations are released.
- Completion records user confirmation, not verified time spent. No study-effectiveness claim is made.
