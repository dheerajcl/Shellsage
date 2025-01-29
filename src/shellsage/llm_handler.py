import os
from .model_manager import ModelManager

class DeepSeekLLMHandler:
    def __init__(self):
        self.manager = ModelManager()
    
    def get_error_solution(self, error_context):
        prompt = self._build_prompt(error_context)
        try:
            response = self.manager.generate(prompt, max_tokens=1024)
            return self._format_response(response)
        except Exception as e:
            return f"Error: {str(e)}"

    def _build_prompt(self, context):
        return f"""**[Terminal Error Diagnosis]**
**Failed Command**: {context['command']}
**Error Message**: {context['error_output']}
**Working Directory**: {context['cwd']}
**Exit Code**: {context['exit_code']}

**Required Format (NO MARKDOWN, STRICT LINES):**
🔍 Root Cause: <1-line diagnosis>
🛠️ Fix: `[executable command]`
📚 Technical Explanation: <specific system-level reason>
⚠️ Potential Risks: <if any>
🔒 Prevention Tip: <actionable advice>

**Example:**
🔍 Root Cause: Typo in command name
🛠️ Fix: `whoami`
📚 Technical Explanation: 'whoam' not found in $PATH
⚠️ Potential Risks: None
🔒 Prevention Tip: Use tab-completion for command names"""

    def _format_response(self, raw):
        # Handle different numbering formats
        cleaned = raw.replace("1. ", "")\
                    .replace("2. ", "")\
                    .replace("3. ", "")\
                    .replace("4. ", "")\
                    .replace("5. ", "")\
                    .replace("**", "")

        # Ensure proper headers
        return cleaned.replace("Root Cause:", "🔍 Root Cause:")\
                     .replace("Fix:", "🛠️ Fix:")\
                     .replace("Technical Explanation:", "📚 Technical Explanation:")\
                     .replace("Potential Risks:", "⚠️ Potential Risks:")\
                     .replace("Prevention Tip:", "🔒 Prevention Tip:")