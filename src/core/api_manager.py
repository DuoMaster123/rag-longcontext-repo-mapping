import time
import os

class APIKeyManager:
    def __init__(self, api_keys: list):
        self.api_keys = [key for key in api_keys if key and key.strip()]
        if not self.api_keys:
            raise ValueError("[ERROR] No API keys configured.")
        self.current_index = 0

    def get_key(self) -> str:
        return self.api_keys[self.current_index]

    def rotate(self):
        old_index = self.current_index
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        print(f"[WARN] Rate limit encountered. Rotating from Key #{old_index + 1} to Key #{self.current_index + 1}.")

    def execute_with_retry(self, api_call_function, *args, **kwargs):
        max_retries = len(self.api_keys) * 2
        attempts = 0
        
        while attempts < max_retries:
            try:
                current_key = self.get_key()
                return api_call_function(api_key=current_key, *args, **kwargs)
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "rate limit" in error_msg or "quota" in error_msg:
                    attempts += 1
                    self.rotate()
                    time.sleep(2)
                else:
                    print(f"[ERROR] Critical API failure: {e}")
                    break
                    
        raise Exception("[FATAL] All API keys exhausted due to rate limits.")