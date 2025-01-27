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
            # Truncate long errors but keep critical parts
            error_output = self._sanitize_error_output(error_context['error_output'])
            command_history = "\n".join([f"{i+1}. {cmd}" for i, cmd in enumerate(error_context.get('command_history', []))])
            
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{
                    "role": "system",
                    "content": f"""Analyze terminal errors with technical precision. Focus on:

- Exit code {error_context['exit_code']} patterns
- Permission issues (sudo vs user permissions)
- Path/directory context: {error_context['cwd']}
- Command sequence history:
{command_history}

Error Output Analysis:
{error_output}

Response MUST:
1. Identify PRIMARY error cause (file, permission, syntax, etc)
2. Provide EXACT fix command WITHOUT any commentary in backticks
Example: 🛠️ Fix: `fastfetch`
3. Explain technical root cause
4. Suggest prevention strategy
5. Flag any destructive operations (rm, format, etc)

Structure response STRICTLY as:
🔍 Cause: <1-line summary>
🛠️ Fix: `[command]` (required)
📚 Explanation: <technical details>
⚠️ Warning: <if destructive>
🔒 Prevention: <actionable advice>"""
                }, {
                    "role": "user",
                    "content": "Diagnose this error with maximum technical accuracy:"
                }],
                temperature=0.1,
                max_tokens=1024  # Increased for detailed analysis
            )
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Error analysis failed: {str(e)}"

    def _sanitize_error_output(self, error):
        # Keep first 500 chars and last 500 chars for critical info
        if len(error) > 1000:
            return f"{error[:500]}\n[...truncated...]\n{error[-500:]}"
        return error