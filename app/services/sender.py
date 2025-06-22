from openai import OpenAI
from ..core.config import get_settings

st = get_settings()
client = OpenAI(api_key=st.openai_api_key)

def ask_llm(prompt: str) -> str:
    """Gerçek GPT cevabı almak istersen bu fonksiyonu kullan."""
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system",
             "content": "You are an expert evaluator of R&D centre activity reports."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()
