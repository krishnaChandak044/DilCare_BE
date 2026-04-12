import os
import sys
import django

sys.path.append('/Users/LENOVO/Desktop/DilCare_BE/DilCare_BE')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ai.providers import chat

try:
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "hi"}
    ]
    from ai.providers import _chat_gemini
    res = _chat_gemini(messages)
    print("SUCCESS:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
