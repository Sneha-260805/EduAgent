# EduAgent

EduAgent is an adaptive AI tutor for AI/ML learning. It is designed as a complete academic showcase project, not just a simple chatbot. The app combines authentication, difficulty classification, topic detection, example retrieval, tutor generation, follow-up evaluation, learner memory, progress charts, and a polished dark Gradio dashboard.

The main goal is to demonstrate a full learning loop:

1. A learner asks an AI/ML question.
2. EduAgent predicts the learner's difficulty level.
3. EduAgent detects the topic and retrieves relevant dataset examples.
4. The Tutor Agent explains the concept at the right level.
5. The Evaluator Agent asks a follow-up question.
6. The learner answers the follow-up.
7. The Memory Agent updates mastery, weak areas, topic history, and recommendations.
8. The dashboard updates the learner profile and charts.

---

## Key Features

- Login, signup, logout, and authenticated learner sessions
- Per-user learner profile persistence with SQLite
- Difficulty classification into beginner, intermediate, and advanced levels
- Topic detection from learner questions
- Dataset-backed example retrieval from `eduagent_dataset.csv`
- Groq-powered Tutor Agent for level-aware explanations
- Evaluator Agent for follow-up questions and understanding checks
- Shared LLM client with timeout, retry, and fallback behavior
- Pydantic-validated evaluator output parsing
- Memory Agent for learner state, weak areas, mastery, and recommendations
- Dark theme Gradio UI designed for a project demo or professor presentation
- Two-column workspace with a chat area and organized learner dashboard
- Tabbed dashboard sections to avoid clutter
- Matplotlib progress charts with dark theme styling
- System Insights / Research panel for showing internal AI pipeline signals

---

## Recent Reliability Improvements

Several earlier prototype weaknesses have been addressed directly:

- The classifier no longer uses broad hardcoded difficulty override lists after prediction. It uses the trained model result, a narrow beginner-intent calibration for definition/simple-explanation questions, and a low-confidence fallback to `intermediate`.
- Topic detection and example retrieval now reuse cached TF-IDF indexes instead of fitting a new vectorizer from scratch on every query.
- Tutor and evaluator Groq calls now go through a shared LLM client with timeout, retries, logging, and graceful fallback text.
- Evaluator JSON is validated with Pydantic before it updates learner memory.
- Mastery scoring constants are named and documented as heuristics.
- MongoDB placeholder code and `pymongo` dependency were removed because the active project uses SQLite.
- A lightweight qualitative evaluation script was added for comparing tutor behavior across beginner, advanced, and memory-influenced cases.

Important honesty note: retrieval is currently cached TF-IDF example retrieval, not a dense-vector FAISS/Chroma RAG pipeline. The project should be presented as retrieval-assisted adaptive tutoring. A semantic vector store remains a strong future upgrade.

---

## Current UI

EduAgent uses a dark, presentation-ready Gradio interface.

### Login Page

The login page includes:

- A dark academic showcase hero section
- Login and signup tabs
- Clean authentication card
- Project capability highlights
- Consistent typography, spacing, and dark theme styling

### Chat Page

The chat page is organized into two main columns.

Left column:

- Tutor conversation
- Main question input
- Ask EduAgent button
- Clear Chat button

Right column:

- A tabbed learner dashboard that keeps the page organized
- Important learner state first
- Research/debug information separated from learner-facing information

Dashboard tabs:

- `Overview`
  - Detected level
  - Detected topic
  - Confidence scores
  - Learner memory / progress summary

- `Evaluate`
  - Follow-up question
  - Learner follow-up answer input
  - Evaluate Follow-up button
  - Evaluation result

- `Progress`
  - Mastery by Topic chart
  - Topic Revisit Count chart
  - Weak Concept Count by Topic chart

- `Research`
  - System Insights / Admin Panel
  - Retrieved Examples
  - Internal signals useful for demos and explainability

---

## System Insights

System Insights is meant for demo, research, and professor-facing explanation. It is not required for normal learners, but it helps show that EduAgent is more than a chat interface.

It displays internal pipeline values such as:

- Predicted level
- Confidence scores
- Detected topic
- Memory hint used by the Tutor Agent
- Evaluator strategy hint
- Last evaluation summary
- Last evaluation JSON
- Retrieved examples from the dataset

This panel is placed under the `Research` dashboard tab so it stays available for presentations without cluttering the main learner experience.

---

## Charts

EduAgent includes three progress charts using Matplotlib and `gr.Plot`.

### Mastery by Topic

Shows the learner's current mastery score for each topic. Mastery changes after follow-up evaluation.

### Topic Revisit Count

Shows how many times the learner has asked about or revisited each topic.

### Weak Concept Count by Topic

Shows how many weak concepts are tracked under each topic.

If a chart has no data yet, EduAgent shows a clean dark placeholder instead of an empty or broken plot.

---

## Architecture

```text
EduAgent/
  gradio_app.py
  app/
    main.py
    ui.py
  agents/
    llm_client.py
    tutor_agent.py
    evaluator_agent.py
    memory_agent.py
  ml/
    classifier.py
    topic_detector.py
    retriever.py
    prompts.py
  auth/
    auth_service.py
    password_utils.py
  db/
    sqlite_store.py
    profile_repository.py
  config/
    settings.py
  evaluate_pipeline_quality.py
  eduagent_dataset.csv
  difficulty_classifier/
  requirements.txt
```

---

## File Responsibilities

### `gradio_app.py`

The app launcher.

- Imports `create_app()` from `app/main.py`
- Imports custom CSS from `app/ui.py`
- Launches the Gradio app with the dark theme styling

### `app/ui.py`

The UI layer.

- Defines the custom dark CSS
- Builds the login/signup page
- Builds the two-column chat workspace
- Organizes the learner dashboard into tabs
- Defines UI components for:
  - chat
  - learner snapshot
  - follow-up evaluation
  - profile display
  - charts
  - system insights
  - retrieved examples

This file focuses on layout and presentation. It does not contain the tutoring backend logic.

### `app/main.py`

The orchestration and Gradio callback layer.

Responsibilities:

- Initializes the database
- Handles signup, login, and logout callbacks
- Handles main learner questions
- Calls the Tutor Agent
- Calls the Evaluator Agent
- Updates learner memory
- Formats profile display
- Formats evaluation display
- Builds progress charts
- Builds System Insights markdown
- Wires backend outputs into the UI components

### `agents/llm_client.py`

Shared LLM client wrapper.

Responsibilities:

- Calls Groq chat completions
- Applies timeout configuration
- Retries transient failures
- Logs failures
- Returns fallback text when configured
- Prevents temporary LLM/API failures from crashing the UI

### `agents/tutor_agent.py`

The Tutor Agent.

Responsibilities:

- Predicts the difficulty level for the learner question
- Detects the topic
- Retrieves relevant examples
- Reads memory hints from the learner profile
- Reads evaluator strategy hints from the most recent evaluation
- Builds the tutor prompt
- Calls Groq through the shared retry/fallback LLM client

The Tutor Agent adapts its explanation style based on:

- predicted level
- detected topic
- prior topic history
- mastery score
- weak concepts
- last evaluation result

### `agents/evaluator_agent.py`

The Evaluator Agent.

Responsibilities:

- Generates one follow-up question after the tutor answer
- Evaluates the learner's response to the follow-up
- Validates evaluator JSON with Pydantic before returning it to the memory update flow
- Returns structured evaluation data:
  - `understanding_level`
  - `weak_concepts`
  - `feedback`
  - `recommended_action`

Expected understanding levels:

- `good`
- `partial`
- `poor`

Expected recommended actions:

- `advance`
- `re-explain`
- `give easier example`
- `give more practice`

### `agents/memory_agent.py`

The Memory Agent.

Responsibilities:

- Normalizes learner profile shape
- Tracks sessions and questions asked
- Tracks topics seen
- Tracks topic revisit counts
- Tracks weak areas
- Tracks mastery scores
- Tracks recommended next topics
- Stores the last evaluation
- Builds tutor memory hints
- Builds evaluator strategy hints
- Uses documented heuristic mastery constants for prototype scoring

This is the part that makes EduAgent adaptive across turns and sessions.

### `ml/classifier.py`

Difficulty classification layer.

Responsibilities:

- Loads the trained classifier from `difficulty_classifier/`
- Predicts the learner question level
- Returns confidence scores
- Applies a narrow beginner-intent calibration for definition/simple-explanation prompts
- Falls back to `intermediate` when classifier confidence is low

The classifier does not use broad keyword-based difficulty overrides after prediction. The remaining calibration is intentionally narrow and documented so prompts like "what is a large language model?" are treated as beginner questions unless the learner asks for advanced analysis.

### `ml/topic_detector.py`

Topic detection layer.

Responsibilities:

- Cleans and normalizes question text
- Builds and reuses a cached TF-IDF topic index
- Compares learner questions with dataset topics
- Returns the most relevant topic

### `ml/retriever.py`

Dataset retrieval layer.

Responsibilities:

- Loads `eduagent_dataset.csv`
- Filters by predicted level and detected topic
- Builds and reuses cached TF-IDF retrieval indexes by level/topic
- Ranks examples by relevance
- Returns examples used as supporting context for the tutor

This is lexical retrieval, not dense semantic retrieval. It is intentionally documented that way.

### `auth/auth_service.py`

Authentication service layer.

Responsibilities:

- Handles signup
- Handles login
- Supports email/username based login flow
- Wraps user payloads for Gradio callbacks

### `auth/password_utils.py`

Password utility layer.

Responsibilities:

- Hashes passwords
- Verifies passwords securely

### `db/sqlite_store.py`

SQLite setup layer.

Responsibilities:

- Opens database connections
- Initializes `users` table
- Initializes `profiles` table
- Adds compatibility columns when missing

### `db/profile_repository.py`

Persistence repository layer.

Responsibilities:

- Creates users
- Looks up users
- Creates profiles if missing
- Loads learner profiles
- Saves learner profiles
- Safely serializes/deserializes JSON profile fields

### `evaluate_pipeline_quality.py`

Lightweight qualitative evaluation harness.

Responsibilities:

- Runs selected learner scenarios through the tutor pipeline
- Records predicted level, confidence, detected topic, retrieved examples, and tutor answer
- Writes JSONL output for manual comparison
- Helps evaluate whether the tutor changes behavior across beginner, advanced, and memory-influenced cases

---

## Learner Profile Data

Each learner profile stores:

- `sessions`
- `questions_asked`
- `last_level`
- `topics_seen`
- `level_history`
- `topic_counts`
- `weak_areas`
- `mastery`
- `used_explanations`
- `recommended_next_topics`
- `last_evaluation`

This profile is persisted per user and loaded again after login.

---

## End-to-End Runtime Flow

### 1. Authentication

The user signs up or logs in. EduAgent loads or creates a learner profile.

### 2. Question Asking

The learner asks an AI/ML question in the chat input.

### 3. Classification

The classifier predicts the learner level:

- beginner
- intermediate
- advanced

It also returns confidence scores.

### 4. Topic Detection

EduAgent detects the topic from the learner question.

### 5. Retrieval

Relevant examples are retrieved from `eduagent_dataset.csv`.

### 6. Tutoring

The Tutor Agent builds a prompt using:

- learner question
- predicted level
- detected topic
- retrieved examples
- memory hint
- evaluator strategy hint

The generated answer is shown in the chat.

### 7. Follow-up Question

The Evaluator Agent generates a short conceptual follow-up question.

### 8. Evaluation

The learner answers the follow-up. The Evaluator Agent scores the response and returns feedback.

### 9. Memory Update

The Memory Agent updates:

- topic counts
- weak concepts
- mastery score
- recommendations
- last evaluation

### 10. Dashboard Update

The UI refreshes:

- learner snapshot
- learner memory / progress
- evaluation result
- charts
- system insights

---

## Dataset Requirements

EduAgent expects `eduagent_dataset.csv` in the project root.

Required columns:

```text
question
answer
level
topic
```

Example row structure:

```csv
question,answer,level,topic
"What is supervised learning?","Supervised learning is...",beginner,Machine Learning
```

The retrieval pipeline uses this dataset to find relevant examples for the tutor prompt.

---

## Model Requirements

EduAgent expects the trained difficulty classifier artifacts in:

```text
difficulty_classifier/
```

Typical files include:

```text
config.json
model.safetensors
tokenizer_config.json
special_tokens_map.json
vocab.txt
```

---

## Environment Variables

Create a `.env` file in the project root:

```text
GROQ_API_KEY=your_groq_api_key_here
MODEL_NAME=your_groq_model_name_here
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
```

Only `GROQ_API_KEY` is required. `MODEL_NAME`, `LLM_TIMEOUT_SECONDS`, and `LLM_MAX_RETRIES` are optional overrides.

You can also set the API key in PowerShell:

```powershell
$env:GROQ_API_KEY="your_groq_api_key_here"
```

---

## Setup

### 1. Clone

```powershell
git clone https://github.com/Sneha-260805/EduAgent.git
cd EduAgent
```

### 2. Create Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

If you prefer manual installation:

```powershell
pip install pandas numpy scikit-learn transformers datasets torch gradio groq matplotlib seaborn wordcloud python-dotenv passlib pydantic
```

### 4. Configure Environment

Create `.env` and add your Groq API key.

```text
GROQ_API_KEY=your_groq_api_key_here
```

### 5. Run the App

```powershell
python .\gradio_app.py
```

Open the local URL printed by Gradio. It is usually:

```text
http://127.0.0.1:7860
```

---

## Validation

Run a syntax/build check:

```powershell
python -c "from app.main import create_app; app = create_app(); print('app build ok')"
```

Optional checks:

```powershell
python .\test_classifier.py
python .\pipeline_test.py
```

Run a qualitative LLM pipeline evaluation:

```powershell
python .\evaluate_pipeline_quality.py
```

This writes JSONL records to `evaluation_runs/pipeline_eval.jsonl`. Review the output manually to compare whether the answer style changes across beginner, advanced, and memory-influenced cases.

---

## Common Issues

### Missing `GROQ_API_KEY`

Make sure `.env` exists or set the variable in the current shell.

### Dataset Not Found

Make sure `eduagent_dataset.csv` is in the project root.

### Classifier Files Not Found

Make sure the `difficulty_classifier/` folder exists and contains the trained model/tokenizer artifacts.

### Empty Charts

This is normal for a new learner profile. Charts populate after questions and follow-up evaluations.

### No Follow-up Context

Ask a main question first, then answer the generated follow-up question in the evaluation tab.

### Login or Profile Issues

Restart the app so `init_db()` runs and initializes the required SQLite tables.

---

## Project Strengths

- Demonstrates a complete adaptive learning loop
- Has real learner memory instead of stateless chat
- Includes both tutor and evaluator behavior
- Uses cached dataset retrieval for supporting examples
- Provides visual progress tracking
- Shows internal system intelligence for academic evaluation
- Keeps the UI organized with learner-facing and research-facing panels separated
- Includes retry/fallback handling for LLM calls
- Validates evaluator JSON before updating learner memory

---

## Current Limitations

- Retrieval is cached TF-IDF example retrieval, not dense-vector FAISS/Chroma retrieval.
- Mastery is a documented heuristic score, not a validated pedagogical model.
- The qualitative evaluation script helps compare outputs, but it is not a full automated LLM evaluation benchmark.
- The Gradio UI is polished for a demo, but a production product would likely use a custom frontend.

---

## Future Improvements

Possible next steps:

- Add richer mastery scoring over time
- Replace heuristic mastery with a formal learner model such as Bayesian Knowledge Tracing
- Replace TF-IDF retrieval with a semantic vector store such as FAISS or ChromaDB
- Add per-topic learning paths
- Add exportable learner reports
- Add instructor/admin analytics
- Add better topic taxonomy
- Add evaluation history charts
- Add automated LLM response quality evaluation
- Add a custom frontend for even more polished production UI
- Add unit tests for profile update logic and callback return contracts

---

## Tech Stack

- Python
- Gradio
- Groq API
- SQLite
- Matplotlib
- Pandas
- Scikit-learn
- Transformers
- PyTorch
- Passlib
- Pydantic

---

## Summary

EduAgent is an adaptive AI/ML tutor prototype with a complete learning loop:

```text
Question -> Classification -> Topic Detection -> Retrieval -> Tutor Answer -> Follow-up -> Evaluation -> Memory Update -> Dashboard Update
```

It is built to be understandable, demo-ready, and academically presentable while preserving a modular backend architecture.
