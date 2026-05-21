import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

try:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
except Exception as e:
    print("⚠️ Groq client init failed:", e)
    client = None


def interpret_message(prompt: str, context: str = "") -> str:
    """
    Send message to LLaMA3 via Groq for financial interpretation.
    Includes context for smarter responses.
    """
    if not client:
        return "⚠️ AI service unavailable. Please check your Groq API key."

    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "llama3-70b-8192"),
            messages=[
                {"role": "system", "content": "You are a helpful financial assistant giving precise, empathetic financial guidance."},
                {"role": "user", "content": f"Context: {context}\nUser: {prompt}"}
            ],
            temperature=0.6
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ AI processing failed: {e}"
