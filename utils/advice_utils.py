import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from ai.model import interpret_message


# =========================================================
# FINANCIAL ADVICE
# =========================================================
def give_financial_advice(query, context=""):

    try:

        final_prompt = f"""
You are a smart financial assistant.

User financial context:
{context}

User query:
{query}

Give:
- practical advice
- concise explanations
- conversational responses
- avoid robotic tone
- avoid excessive emojis
"""

        response = interpret_message(final_prompt)

        return response

    except Exception as e:

        print("ADVICE ERROR:", e)

        return (
            "I couldn't generate financial advice properly right now."
        )