# EduAgent

EduAgent is an adaptive AI tutor for AI/ML learning. It combines:

- difficulty classification (`beginner`, `intermediate`, `advanced`)
- topic detection + example retrieval from a dataset
- tutor answer generation via Groq
- evaluator-generated follow-up questions
- learner memory/profile tracking for personalization
- Gradio UI with login/signup and per-user progress

The codebase is modularized, with `gradio_app.py` kept as the compatibility launcher.

## Project Essence

EduAgent aims to make explanations adapt to each learner:

1. Understand learner intent and difficulty level.
2. Ground responses with topic-matched examples from your dataset.
3. Generate a tutor answer with level-appropriate depth.
4. Ask a follow-up to check understanding.
5. Update learner memory (topic counts, weak areas, mastery, recommendations).
6. Use that memory in later prompts so repeated topics are handled better.

---

## Current Architecture

```text
EduAgent/
  gradio_app.py                  # Launcher/entrypoint
  app/
    main.py                      # Orchestration, callbacks, flow wiring
    ui.py                        # Gradio UI builders (legacy + evaluation-capable)
  agents/
    tutor_agent.py               # Tutor LLM answer pipeline
    evaluator_agent.py           # Follow-up question + learner response evaluation
    memory_agent.py              # Profile normalization, updates, memory hints
  ml/
    classifier.py                # DistilBERT level prediction
    topic_detector.py            # Topic detection from question + dataset
    retriever.py                 # Example retrieval and scoring
    prompts.py                   # Prompt templates (if used by older flow)
  auth/
    password_utils.py            # Password hash/verify
    auth_service.py              # Signup/login services and wrappers
  db/
    sqlite_store.py              # SQLite connection and DB/table initialization
    profile_repository.py        # User/profile persistence and schema-compatible access
    mongo_store.py               # Placeholder for Mongo store integration
  config/
    settings.py                  # Env/config constants
```

---

## File Responsibilities (Detailed)

### `gradio_app.py`
- Imports `create_app()` from `app/main.py`
- Launches Gradio app

### `app/main.py`
- Main callback orchestration for:
  - signup/login/logout
  - tutor question handling
  - follow-up evaluation handling
  - chat reset
- Creates compatibility wrappers so the legacy UI layout remains usable
- Calls `init_db()` during app creation so required tables exist before login

### `app/ui.py`
- `build_demo(...)`: legacy two-column UI flow (login/signup + chatbot panel)
- `build_ui(...)`: newer evaluator-explicit flow
- Currently supports follow-up evaluation input in the legacy path via callback wiring

### `agents/tutor_agent.py`
- `generate_tutor_response(user_question, profile)`:
  - predicts level via classifier
  - detects topic via topic detector
  - retrieves examples from dataset
  - builds memory hint from profile
  - sends combined prompt to Groq and returns final answer

### `agents/evaluator_agent.py`
- `generate_followup_question(...)`: generates one conceptual understanding-check question
- `evaluate_followup_response(...)`: evaluates learner follow-up reply and returns structured JSON:
  - `understanding_level`
  - `weak_concepts`
  - `feedback`
  - `recommended_action`

### `agents/memory_agent.py`
- `ensure_profile_structure(...)`: normalizes old/new profile shapes and ensures all keys exist
- `update_profile_after_question(...)`: updates question count, topics, level history
- `update_profile_after_evaluation(...)`: updates mastery, weak areas, and recommendations
- `build_memory_hint(...)`: creates personalization hint for tutor prompt

### `ml/classifier.py`
- Loads DistilBERT classifier from `difficulty_classifier/`
- Predicts level + confidence scores with heuristic guardrails

### `ml/topic_detector.py`
- Text cleaning
- Topic similarity scoring to detect most relevant topic for current learner question

### `ml/retriever.py`
- Loads dataset from `eduagent_dataset.csv`
- Filters by level/topic and ranks examples using similarity + complexity penalty

### `auth/password_utils.py`
- Secure password hashing
- Password verification

### `auth/auth_service.py`
- Signup and login service layer
- Backward-compatible wrappers used by app callbacks (`signup_user`, `login_user`)
- Converts auth result into UI-friendly user payload

### `db/sqlite_store.py`
- Opens SQLite connection
- Creates `users` and `profiles` tables when missing (`init_db()`)

### `db/profile_repository.py`
- Profile CRUD (`load_profile`, `save_profile`, `create_profile_if_missing`)
- User lookup/creation helpers used by auth
- Supports compatibility across older/newer SQLite user table column shapes

---

## End-to-End Runtime Flow

1. User logs in.
2. App loads profile from SQLite and normalizes it.
3. User asks question.
4. Tutor agent returns answer + detected level/topic + examples.
5. Memory agent updates profile after question.
6. Evaluator agent generates follow-up question.
7. User replies to follow-up.
8. Evaluator agent scores understanding.
9. Memory agent updates mastery/weak areas/recommendations.

---

## Setup

### Prerequisites
- Python 3.10+ (3.13 also works)
- Git
- Groq API key

### Clone
```powershell
git clone https://github.com/Sneha-260805/EduAgent.git
cd EduAgent
```

### Virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Install dependencies
```powershell
pip install --upgrade pip
pip install pandas numpy scikit-learn transformers datasets torch gradio groq python-dotenv matplotlib seaborn wordcloud
```

### Configure environment
Create `.env` in project root:
```text
GROQ_API_KEY=your_groq_api_key_here
```

Or set in current terminal:
```powershell
$env:GROQ_API_KEY="your_groq_api_key_here"
```

---

## Model and Dataset Requirements

Required at runtime:
- `difficulty_classifier/` (DistilBERT artifacts)
- `eduagent_dataset.csv` with columns:
  - `question`
  - `answer`
  - `level`
  - `topic`

Not committed by design:
- `eduagent_dataset.csv`
- `eduagent_training_ready.csv`
- `difficulty_classifier/`
- `logs/`, `results/`, `__pycache__/`

---

## Run

```powershell
python .\gradio_app.py
```

Open the local URL shown in terminal (usually `http://127.0.0.1:7860` or `7861`).

---

## Validation / Dev Checks

```powershell
python -m compileall config auth db ml agents app gradio_app.py
```

Optional checks:
```powershell
python .\test_classifier.py
python .\pipeline_test.py
```

---

## Common Issues and Fixes

- **`GROQ_API_KEY` missing**
  - Ensure `.env` exists or set the env variable in current shell.

- **`no such table: profiles`**
  - `init_db()` must run before login. Restart app with:
    - `python .\gradio_app.py`

- **`no such column: id` (or other users column mismatch)**
  - Caused by old/new SQLite schema differences; repository/auth layer now includes compatibility logic.

- **Follow-up response drifts off-topic**
  - Ensure you answer in the dedicated follow-up evaluation field/button path so evaluator uses stored follow-up context.

- **Gradio warning about theme/css in `Blocks(...)`**
  - Warning is non-blocking; app still runs. (Gradio v6 moved these params to `launch()`.)

---

## Optional Scripts

```powershell
python .\analyze_dataset.py
python .\prepare_training_dataset.py
python .\train_classifier.py
python .\eduagent_full.py
python .\example_retriever.py
```

