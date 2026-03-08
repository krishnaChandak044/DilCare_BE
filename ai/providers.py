"""
AI — Provider abstraction layer.
Supports Groq, Gemini and Ollama.
Configure via django settings (or env vars).

Settings:
    AI_PROVIDER = "groq" | "gemini" | "ollama"
    AI_API_KEY  = "<your-api-key>"        # not needed for ollama
    AI_MODEL    = "<model-name>"          # optional override
    OLLAMA_BASE_URL = "http://localhost:11434"   # only for ollama
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# ─── DilCare system prompt ────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are DilCare AI Health Assistant — a friendly, knowledgeable and empathetic health companion built for Indian users.

Your guidelines:
1. **Scope**: Answer questions about general health, heart health, fitness, nutrition, medicines, ayurveda, yoga, mental wellness, and healthy lifestyle habits.
2. **Tone**: Warm, supportive, conversational. Use simple language. You can occasionally use Hindi/Hinglish words (e.g., Namaste, Aapka swasthya) when natural.
3. **Safety**: Always remind users that you are NOT a doctor. For serious symptoms, emergencies, or specific medical diagnoses, advise them to consult a healthcare professional immediately.
4. **Indian context**: Be aware of Indian dietary habits, common diseases (diabetes, heart disease, hypertension), Indian home remedies, Ayurveda, Yoga practices, and government health schemes.
5. **Conciseness**: Keep replies under 200 words unless the user asks for detailed information. Use bullet points and emojis for readability.
6. **Medicines**: You can provide general information about common medicines but NEVER prescribe. Always say "please consult your doctor before starting/stopping any medicine."
7. **Wellness tips**: Proactively suggest small actionable tips — drinking warm water, walking 30 min, pranayama, turmeric milk, etc.
8. **Privacy**: Never ask for or store personal health records in conversation. To track health data, guide users to use the DilCare app features (water tracker, medicine reminder, BMI calculator, step tracker, etc.)."""


# ─── Provider dispatch ────────────────────────────────────────────────────────

def get_provider():
    """Return the configured provider name (lowercase)."""
    return getattr(settings, "AI_PROVIDER", "groq").lower()


def get_api_key():
    return getattr(settings, "AI_API_KEY", "")


def get_model():
    provider = get_provider()
    default_models = {
        "groq": "llama-3.3-70b-versatile",
        "gemini": "gemini-2.0-flash",
        "ollama": "llama3.2",
    }
    return getattr(settings, "AI_MODEL", default_models.get(provider, ""))


# ─── Chat function ────────────────────────────────────────────────────────────

def chat(messages: list[dict]) -> dict:
    """
    Send a conversation to the configured AI provider.

    Args:
        messages: list of {"role": "system"|"user"|"assistant", "content": str}

    Returns:
        {"content": str, "model": str, "tokens": int|None}
    """
    provider = get_provider()
    logger.info("AI chat via %s (model=%s)", provider, get_model())

    if provider == "groq":
        return _chat_groq(messages)
    elif provider == "gemini":
        return _chat_gemini(messages)
    elif provider == "ollama":
        return _chat_ollama(messages)
    else:
        raise ValueError(f"Unknown AI provider: {provider}")


# ─── Groq ─────────────────────────────────────────────────────────────────────

def _chat_groq(messages: list[dict]) -> dict:
    from groq import Groq

    client = Groq(api_key=get_api_key())
    model = get_model()

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )
    choice = response.choices[0]
    return {
        "content": choice.message.content,
        "model": model,
        "tokens": getattr(response.usage, "total_tokens", None),
    }


# ─── Google Gemini ────────────────────────────────────────────────────────────

def _chat_gemini(messages: list[dict]) -> dict:
    import google.generativeai as genai

    genai.configure(api_key=get_api_key())
    model_name = get_model()
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=next(
            (m["content"] for m in messages if m["role"] == "system"), SYSTEM_PROMPT
        ),
    )

    # Convert to Gemini format (system handled above)
    history = []
    for m in messages:
        if m["role"] == "system":
            continue
        role = "user" if m["role"] == "user" else "model"
        history.append({"role": role, "parts": [m["content"]]})

    # Last message is the new user turn
    chat_session = model.start_chat(history=history[:-1])
    response = chat_session.send_message(history[-1]["parts"][0])

    return {
        "content": response.text,
        "model": model_name,
        "tokens": None,
    }


# ─── Ollama (local) ──────────────────────────────────────────────────────────

def _chat_ollama(messages: list[dict]) -> dict:
    import httpx

    base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
    model = get_model()

    resp = httpx.post(
        f"{base_url}/api/chat",
        json={"model": model, "messages": messages, "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()

    return {
        "content": data["message"]["content"],
        "model": model,
        "tokens": data.get("eval_count"),
    }
