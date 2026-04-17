# EduAgent

EduAgent is an adaptive AI tutor for AI/ML questions. It predicts user difficulty level (beginner/intermediate/advanced), retrieves relevant examples, and generates responses using Groq LLMs.

## What Is Included In This Repo

- Source code (`*.py`)
- Visualization outputs (`graph*.png`)
- Project config (`.gitignore`)

## What Is Not Included (Generated / Large Files)

These are intentionally excluded from git and must be generated locally:

- `eduagent_dataset.csv`
- `eduagent_training_ready.csv`
- `difficulty_classifier/`
- `logs/`
- `results/`
- `__pycache__/`

## Prerequisites

- Python 3.10+ (3.13 works with current code)
- Git
- Groq API key

## 1) Clone And Enter Project

```powershell
git clone https://github.com/Sneha-260805/EduAgent.git
cd EduAgent
```

## 2) Create Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 3) Install Dependencies

```powershell
pip install --upgrade pip
pip install pandas numpy scikit-learn transformers datasets torch gradio groq matplotlib seaborn wordcloud
```

## 4) Set Environment Variable

Set your Groq key before running tutor/app scripts:

```powershell
$env:GROQ_API_KEY="your_groq_api_key_here"
```

Optional (current terminal session):

```powershell
echo $env:GROQ_API_KEY
```

## 5) Download Pretrained Classifier (Recommended)

If you only want to run the app (without retraining), download the pretrained model zip:

- [difficulty_classifier.zip (Google Drive)](https://drive.google.com/file/d/1T75e4DaAuqyEhAnKc0wX2NpSI3jGpvhQ/view?usp=sharing)

Then extract it in the project root so this path exists:

- `./difficulty_classifier/`

After extraction, you can run the app directly:

```powershell
python .\gradio_app.py
```

## 6) Add Dataset File (Only Needed For Retraining)

Place your dataset at:

- `eduagent_dataset.csv`

Expected columns include:

- `question`
- `answer`
- `level`
- `topic`

## 7) Prepare Training Dataset

```powershell
python .\prepare_training_dataset.py
```

This generates:

- `eduagent_training_ready.csv`

## 8) Train Difficulty Classifier

```powershell
python .\train_classifier.py
```

This generates:

- `difficulty_classifier/`
- `logs/`
- `results/`

## 9) Run The Gradio App

```powershell
python .\gradio_app.py
```

Open the local URL shown in terminal (usually `http://127.0.0.1:7860`).

## Optional Scripts

- Analyze dataset:

```powershell
python .\analyze_dataset.py
```

- Run CLI tutor:

```powershell
python .\eduagent_full.py
```

## Common Issues

- **`GROQ_API_KEY` missing**  
  Set it again in the same terminal session before running scripts.

- **Transformer/TensorFlow Keras errors**  
  `train_classifier.py` already disables TensorFlow path via `USE_TF=0`.

- **Missing dataset/model files**  
  Ensure `eduagent_dataset.csv` exists, then run prepare + train steps above.

