import os
from openai import OpenAI

class DeepSeekLLMHandler:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable required")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1"
        )

    def get_error_solution(self, error_context):
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{
                    "role": "system",
                    "content": f"""Analyze terminal errors with MANDATORY format:

**Command**: {error_context['command']}
**Error**: {error_context['error_output']}
**CWD**: {error_context['cwd']}
**Exit Code**: {error_context['exit_code']}

Response MUST contain:
1. 🔍 Cause: <1-line diagnosis>
2. 🛠️ Fix: `[executable command]`
3. 📚 Explanation: <technical reason>
4. 🔒 Prevention: <actionable tip>

Examples:
For 'fastfetc' typo:
🔍 Cause: Typo in command name
🛠️ Fix: `fastfetch`
📚 Explanation: 'fastfetc' not found, correct command is 'fastfetch'
🔒 Prevention: Use 'apt list fastfetch' to verify installation

For permission denied:
🔍 Cause: Missing execute permissions
🛠️ Fix: `chmod +x script.sh`
📚 Explanation: File lacks executable permission (mode 755 required)
🔒 Prevention: Always check permissions with 'ls -l'"""
                }, {
                    "role": "user",
                    "content": "Provide analysis for this error:"
                }],
                temperature=0.1,
                max_tokens=512
            )
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Error analysis failed: {str(e)}"