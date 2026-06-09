import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

try:
    print("Testing gemini-2.5-flash...")
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
    response = llm.invoke("Hello, are you online?")
    print("Success! Response:")
    print(response.content)
except Exception as e:
    print(f"Error: {e}")
