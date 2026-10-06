import os
import json
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
st.set_page_config(page_title="AI Study Planner", layout="wide")

def get_client():
    key = os.getenv("GROQ_API_KEY")
    if not key or key == "your_groq_api_key_here":
        return None
    return Groq(api_key=key)

def build_prompt(subjects, days, hours, difficulty, notes):
    subject_text = "\n".join(
        f"- {x['subject']}: {x['topics']}" for x in subjects
    )
    return f"""
You are an AI Study Planner Agent.
Create a realistic college study plan.

Subjects and topics:
{subject_text}

Available study hours per day: {hours}
Plan duration: {days} days
Difficulty: {difficulty}
Extra notes: {notes or "None"}

Rules:
- Prioritize difficult and important topics.
- Keep the workload realistic.
- Include revision.
- Do not overload a day.
- Return ONLY valid JSON.

JSON format:
{{
  "overview": "short explanation",
  "days": [
    {{
      "day": 1,
      "focus": "main focus",
      "tasks": [
        {{
          "subject": "subject",
          "topic": "topic",
          "activity": "what to do",
          "minutes": 60
        }}
      ],
      "revision": "revision activity"
    }}
  ],
  "tips": ["tip 1", "tip 2", "tip 3"]
}}
"""

def generate_plan(subjects, days, hours, difficulty, notes):
    client = get_client()
    if client is None:
        raise ValueError("GROQ_API_KEY is missing in .env")

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You create practical student study plans and always return valid JSON."},
            {"role": "user", "content": build_prompt(subjects, days, hours, difficulty, notes)}
        ],
        temperature=0.3,
    )
    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

def to_markdown(plan):
    lines = ["# AI Study Plan", "", plan.get("overview", ""), ""]
    for day in plan.get("days", []):
        lines.append(f"## Day {day.get('day')}: {day.get('focus', '')}")
        for task in day.get("tasks", []):
            lines.append(
                f"- **{task.get('subject')}** - {task.get('topic')} - "
                f"{task.get('activity')} ({task.get('minutes')} min)"
            )
        if day.get("revision"):
            lines.append(f"- **Revision:** {day.get('revision')}")
        lines.append("")
    if plan.get("tips"):
        lines.append("## Tips")
        lines += [f"- {x}" for x in plan["tips"]]
    return "\n".join(lines)

st.title("AI Study Planner")
st.write("Create a practical day-wise study plan using a Groq-powered AI agent.")

with st.sidebar:
    st.header("Planner Settings")
    days = st.slider("Plan duration (days)", 1, 14, 7)
    hours = st.slider("Available study hours per day", 1, 10, 3)
    difficulty = st.selectbox("Overall difficulty", ["Easy", "Medium", "Hard"], index=1)

if "subjects" not in st.session_state:
    st.session_state.subjects = [{"subject": "", "topics": ""}]

st.subheader("Subjects and Topics")
for i, item in enumerate(st.session_state.subjects):
    c1, c2 = st.columns([1, 2])
    with c1:
        item["subject"] = st.text_input(
            f"Subject {i+1}", item["subject"], key=f"subject_{i}",
            placeholder="e.g. Python"
        )
    with c2:
        item["topics"] = st.text_input(
            f"Topics {i+1}", item["topics"], key=f"topics_{i}",
            placeholder="e.g. Functions, OOP, File Handling"
        )

if st.button("Add another subject"):
    st.session_state.subjects.append({"subject": "", "topics": ""})
    st.rerun()

notes = st.text_area(
    "Extra information",
    placeholder="Example: I have an exam next week and struggle with OOP."
)

if st.button("Generate Study Plan", type="primary"):
    valid = [
        x for x in st.session_state.subjects
        if x["subject"].strip() and x["topics"].strip()
    ]
    if not valid:
        st.error("Please enter at least one subject and its topics.")
    else:
        with st.spinner("AI agent is creating your study plan..."):
            try:
                st.session_state.plan = generate_plan(
                    valid, days, hours, difficulty, notes
                )
                st.session_state.completed = {}
                st.session_state.valid_subjects = valid
            except json.JSONDecodeError:
                st.error("The AI returned an invalid plan format. Please try again.")
            except Exception as e:
                st.error(f"Could not generate the plan: {e}")

if "plan" in st.session_state:
    plan = st.session_state.plan
    st.divider()
    st.subheader("Your Study Plan")
    st.write(plan.get("overview", ""))

    total = 0
    done = 0

    for day in plan.get("days", []):
        st.markdown(f"### Day {day.get('day')} - {day.get('focus', '')}")
        for idx, task in enumerate(day.get("tasks", [])):
            total += 1
            task_id = f"{day.get('day')}_{idx}"
            checked = st.checkbox(
                f"{task.get('subject')} | {task.get('topic')} | "
                f"{task.get('activity')} ({task.get('minutes')} min)",
                value=st.session_state.completed.get(task_id, False),
                key=f"check_{task_id}"
            )
            st.session_state.completed[task_id] = checked
            if checked:
                done += 1
        if day.get("revision"):
            st.caption(f"Revision: {day.get('revision')}")

    if total:
        st.progress(done / total)
        st.write(f"Progress: {done}/{total} tasks completed")

    if plan.get("tips"):
        st.subheader("Study Tips")
        for tip in plan["tips"]:
            st.write(f"- {tip}")

    st.download_button(
        "Download Plan",
        data=to_markdown(plan),
        file_name="study_plan.md",
        mime="text/markdown"
    )

    st.divider()
    st.subheader("Need a revised plan?")
    new_hours = st.slider("New daily study hours", 1, 10, hours, key="new_hours")
    new_note = st.text_input(
        "What changed?",
        placeholder="Example: I have less time on weekdays."
    )

    if st.button("Regenerate Plan"):
        with st.spinner("AI agent is revising the plan..."):
            try:
                revised_notes = f"{notes}\nNew situation: {new_note}"
                st.session_state.plan = generate_plan(
                    st.session_state.valid_subjects,
                    days,
                    new_hours,
                    difficulty,
                    revised_notes
                )
                st.session_state.completed = {}
                st.rerun()
            except Exception as e:
                st.error(f"Could not revise the plan: {e}")
