
from ai.model import query_llm

class RAGPipeline:
    """Simple pipeline to handle general finance questions."""
    def query(self, user_query):
        prompt = (f"User asked: {user_query}\n"
                  "Provide a clear, short, accurate answer about finance or investments.")
        return query_llm(prompt)
