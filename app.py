import streamlit as st
import ollama
import re

# ---------------- PAGE ----------------
st.set_page_config(page_title="CareerPilot AI", layout="wide")
st.title("🚀 CareerPilot AI")
st.caption("Intelligent Learning & Career Assistant")

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_topic" not in st.session_state:
    st.session_state.last_topic = None

if "last_entity" not in st.session_state:
    st.session_state.last_entity = None

# ---------------- MODE ----------------
mode = st.selectbox(
    "🎯 Choose Mode",
    ["General", "Career", "Coding", "Logistics", "Interview"]
)

# ---------------- INPUT GATE ----------------
def input_gate(prompt):
    if prompt.count("?") > 1:
        return "reject", "Ask one clear question."
    return "ok", None

# ---------------- INTENT ----------------
def detect_intent(prompt):
    p = prompt.lower()

    if any(x in p for x in ["plan", "trip", "itinerary"]):
        return "plan"
    elif any(x in p for x in ["compare", "vs", "difference"]):
        return "comparison"
    elif any(x in p for x in ["why", "how", "explain", "journey"]):
        return "explanation"
    else:
        return "general"

# ---------------- TOPIC ----------------
def detect_topic(prompt):
    p = prompt.lower()

    if any(x in p for x in ["business", "profit", "company"]):
        return "business"
    elif any(x in p for x in ["trip", "travel", "place", "city", "country"]):
        return "travel"
    elif any(x in p for x in ["college", "university", "placement"]):
        return "education"
    elif any(x in p for x in ["code", "python", "error"]):
        return "coding"
    else:
        return "general"

# ---------------- ENTITY MEMORY ----------------
def extract_entity(prompt):
    words = prompt.split()
    if len(words) <= 3:
        return prompt.strip()
    return None

# ---------------- SYSTEM PROMPT ----------------
def build_system_prompt(mode, intent, entity):
    return f"""
You are a sharp, high-thinking assistant.

MODE: {mode}
INTENT: {intent}
CONTEXT ENTITY: {entity}

THINKING RULES:
- Start with a strong insight (not definition)
- Use real-world explanation
- Avoid generic lines
- No fluff

STRUCTURE:
1. CORE INSIGHT
2. WHY IT WORKS
3. REAL EXAMPLE
4. JUDGMENT

FOLLOW-UP RULE (CRITICAL):
- Generate exactly 3 follow-up questions
- They must be based on the user's question
- They must feel like curiosity hooks
- Avoid generic ones like "example", "uses", "mistakes"
- Make them slightly sharp and thought-provoking

FORMAT:
👉 Choose next:
1. ...
2. ...
3. ...
"""

# ---------------- OUTPUT CLEAN ----------------
def output_gate(text, mode):

    text = re.sub(r"as an ai|language model", "", text, flags=re.I)

    weak_words = ["maybe", "probably", "generally", "in conclusion"]
    for w in weak_words:
        text = re.sub(w, "", text, flags=re.I)

    if mode == "Interview":
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        text = "\n".join(lines[:5])

    return text.strip()

# ---------------- DISPLAY ----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---------------- INPUT ----------------
prompt = st.chat_input("Ask anything...")

# ---------------- CLEAR ----------------
if st.button("🧹 Clear Chat"):
    st.session_state.messages = []
    st.session_state.last_topic = None
    st.session_state.last_entity = None
    st.rerun()

# ---------------- MAIN ----------------
if prompt:

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    # GREETING FIX
    if prompt.lower().strip() in ["hi", "hello", "hey", "hii"]:
        output = "Hey 👋 What do you want to explore today?"

        with st.chat_message("assistant"):
            st.write(output)

        st.session_state.messages.append(
            {"role": "assistant", "content": output}
        )
        st.stop()

    status, message = input_gate(prompt)

    if status != "ok":
        with st.chat_message("assistant"):
            st.write(message)

        st.session_state.messages.append(
            {"role": "assistant", "content": message}
        )
        st.stop()

    intent = detect_intent(prompt)
    topic = detect_topic(prompt)

    entity = extract_entity(prompt)
    if entity:
        st.session_state.last_entity = entity
    else:
        entity = st.session_state.last_entity

    st.write(f"🧠 Intent: {intent} | Topic: {topic} | Context: {entity}")

    system_prompt = build_system_prompt(mode, intent, entity)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(st.session_state.messages)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                res = ollama.chat(
                    model="mistral",
                    messages=messages,
                    stream=True,
                    options={"temperature": 0.3}
                )

                output = ""
                placeholder = st.empty()

                for chunk in res:
                    output += chunk["message"]["content"]
                    placeholder.write(output)

                output = output_gate(output, mode)

                # 🔥 REMOVE DUPLICATE FOLLOW-UPS
                parts = output.split("👉 Choose next:")
                if len(parts) > 2:
                    output = parts[0] + "👉 Choose next:" + parts[-1]

                placeholder.write(output)

            except Exception as e:
                output = f"❌ Error: {str(e)}\n👉 Run: ollama pull mistral"
                st.write(output)

    st.session_state.messages.append(
        {"role": "assistant", "content": output}
    )