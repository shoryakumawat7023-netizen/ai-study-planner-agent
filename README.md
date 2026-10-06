# AI Study Planner Agent

A simple college hackathon prototype using Groq and Llama 3.3 70B Versatile.

## Features
- Add subjects and topics
- Set daily study hours
- Set plan duration and difficulty
- Generate a day-wise study plan
- Task checklist and progress
- Regenerate the plan when constraints change
- Download the plan as Markdown
- API key stored in `.env`

## Setup

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Put your Groq key in `.env`:

```text
GROQ_API_KEY=your_actual_key
```

Run:

```powershell
streamlit run app.py
```

## Agentic workflow
1. Student provides subjects, topics, time and constraints.
2. The app builds a structured request.
3. Groq LLM reasons about priorities and available time.
4. The response is converted into a structured plan.
5. The student can track tasks and regenerate the plan when constraints change.

## Hackathon demo
Enter 2-3 subjects, generate a 7-day plan, mark tasks complete, change available time, and regenerate the plan.
