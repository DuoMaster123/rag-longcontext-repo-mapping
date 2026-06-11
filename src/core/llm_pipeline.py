import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from google.genai import types

# Append project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.core.api_manager import APIKeyManager

load_dotenv()

class AIEngine:
    def __init__(self):
        github_keys = [os.getenv("GITHUB_TOKEN_1"), os.getenv("GITHUB_TOKEN_2")]
        gemini_keys = [os.getenv("GEMINI_KEY_1"), os.getenv("GEMINI_KEY_2")]
        
        self.github_manager = APIKeyManager(github_keys)
        self.gemini_manager = APIKeyManager(gemini_keys)

    def _call_gpt4o_api(self, api_key: str, system_prompt: str, user_prompt: str) -> str:
        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=api_key
        )
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1, 
            max_tokens=4096
        )
        return response.choices[0].message.content

    def _call_gemini_api(self, api_key: str, system_prompt: str, user_prompt: str) -> str:
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.1,
                max_output_tokens=8192,
            )
        )
        return response.text

    def ask_gpt4o(self, system_prompt: str, user_prompt: str) -> str:
        print("[INFO] Sending request to GPT-4o (GitHub Models)...")
        return self.github_manager.execute_with_retry(
            self._call_gpt4o_api, 
            system_prompt=system_prompt, 
            user_prompt=user_prompt
        )

    def ask_gemini(self, system_prompt: str, user_prompt: str) -> str:
        print("[INFO] Sending request to Gemini 2.5 Flash...")
        return self.gemini_manager.execute_with_retry(
            self._call_gemini_api, 
            system_prompt=system_prompt, 
            user_prompt=user_prompt
        )

# Execution block for testing
if __name__ == "__main__":
    engine = AIEngine()
    
    sys_prompt = "You are a helpful coding assistant. Return output in JSON format."
    usr_prompt = "Return a JSON object with a greeting message."
    
    try:
        print("\n--- Testing GPT-4o Pipeline ---")
        gpt_res = engine.ask_gpt4o(sys_prompt, usr_prompt)
        print(gpt_res)
        
        print("\n--- Testing Gemini Pipeline ---")
        gemini_res = engine.ask_gemini(sys_prompt, usr_prompt)
        print(gemini_res)
        
    except Exception as e:
        print(f"[ERROR] Exception during test execution: {e}")