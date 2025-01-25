import os
from openai import OpenAI

class DeepSeekLLMHandler:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('HYPERBOLIC_API_KEY')
        if not self.api_key:
            raise ValueError("HYPERBOLIC_API_KEY environment variable required")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.hyperbolic.xyz/v1"
        )

    def get_error_solution(self, error_output):
        try:
            chat_completion = self.client.chat.completions.create(
                model="Qwen/Qwen2.5-Coder-32B-Instruct",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a UNIX terminal expert. For command errors:
                    1. Identify if it's a typo, missing package, or execution error
                    2. For typos: suggest correct command
                    3. For missing packages: suggest install command
                    4. Format response as:
                    Cause: [1-sentence cause]
                    Explanation: [technical details]
                    Command: `[correct command]`
                    Prevention: [prevention tip]"""
                    },
                    {
                        "role": "user",
                        "content": f"Error output:\n{error_output}"
                    }
                ],
                temperature=0.2,
                max_tokens=200
            )

            return chat_completion.choices[0].message.content
        
        except Exception as e:
            return f"API Error: {str(e)}"