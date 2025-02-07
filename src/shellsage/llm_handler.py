import os
import re
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
        return f"""**[Terminal Context Analysis]**
**System Environment**: {context.get('env_vars', {}).get('SHELL')} on {context.get('os', 'Linux')}
**Working Directory**: {context['cwd']} ({len(context.get('file_context', {}).get('files', []))} files)
**Recent Processes**: {', '.join(context.get('process_tree', [])[-3:])}
**Network State**: {context.get('network_state', ['Unknown'])[0]}
**Command History**: {', '.join(context.get('history', [])[-5:])}

**Failed Command**: {context['command']}
**Error Message**: {context['error_output']}
**Exit Code**: {context['exit_code']}
**Man Page Excerpt**: {context.get('man_excerpt', '')}

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
        # Detect reasoning model response
        is_reasoning_model = any(x in self.manager.local_model.lower() 
                               for x in ['deepseek', 'r1', 'think', 'expert'])
        
        if is_reasoning_model and '</think>' in raw:
            # Extract all thinking blocks and final response
            thoughts = []
            remaining = raw
            while '<think>' in remaining and '</think>' in remaining:
                think_start = remaining.find('<think>') + len('<think>')
                think_end = remaining.find('</think>')
                if think_start > -1 and think_end > -1:
                    thoughts.append(remaining[think_start:think_end].strip())
                    remaining = remaining[think_end + len('</think>'):]
            raw = remaining.strip()

        # Existing cleaning logic
        cleaned = re.sub(r'\n+', '\n', raw)
        cleaned = re.sub(r'(\d\.\s|\*\*)', '', cleaned)
        
        return re.sub(
            r'(Root Cause|Fix|Technical Explanation|Potential Risks|Prevention Tip):?',
            lambda m: f"🔍 {m.group(1)}:" if m.group(1) == "Root Cause" else 
                     f"🛠️ {m.group(1)}:" if m.group(1) == "Fix" else
                     f"📚 {m.group(1)}:" if m.group(1) == "Technical Explanation" else
                     f"⚠️ {m.group(1)}:" if m.group(1) == "Potential Risks" else
                     f"🔒 {m.group(1)}:",
            cleaned
        )