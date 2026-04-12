import google.generativeai as genai
import os
genai.configure(api_key=os.environ.get("AI_API_KEY", "AIzaSyBilLL3BnPFmVQTBKlXNIOs_OX3zlT7oHM"))

for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(m.name)
