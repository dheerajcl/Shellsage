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

    # Update _build_prompt in DeepSeekLLMHandler
    def _build_prompt(self, context):
        # Extract files mentioned in error if any
        error_files = []
        if context.get('error_output'):
            # Simple regex to find file paths in error messages
            file_matches = re.findall(r'\'(.*?)\'|\"(.*?)\"|\b([\/\w\.-]+\.\w+)\b', context.get('error_output', ''))
            for match in file_matches:
                for group in match:
                    if group and os.path.exists(group) and os.path.isfile(group):
                        error_files.append(group)

        # Gather command-specific context details
        specialized_context = ""
        if context.get('git_status'):
            specialized_context += f"\n**Git Status**: {context['git_status'][:200]}"
        if context.get('docker_containers'):
            specialized_context += f"\n**Docker Containers**: {', '.join(context['docker_containers'][:3])}"
        if context.get('failed_services'):
            specialized_context += f"\n**Failed Services**: {', '.join(context['failed_services'])}"

        # File content context
        file_context = ""
        if context.get('file_context', {}).get('file_contents'):
            for file, content in context['file_context']['file_contents'].items():
                if len(content) > 300:
                    content = content[:300] + "..."
                file_context += f"\n**File {file}**: ```\n{content}\n```"

        # Build the enhanced prompt
        prompt = f"""**[Terminal Context Analysis]**
    **System Environment**: {context.get('env_vars', {}).get('SHELL', 'Unknown')} on {context.get('os', 'Linux')}
    **Working Directory**: {context['cwd']} ({len(context.get('file_context', {}).get('files', []))} files)
    **Recent Commands**: {', '.join(context.get('history', [])[-3:])}
    **Failed Command**: `{context['command']}`
    **Error Message**: {context['error_output']}
    **Exit Code**: {context['exit_code']}
    **Referenced Files**: {', '.join(error_files) if error_files else 'None detected'}
    **Man Page Excerpt**: {context.get('man_excerpt', 'N/A')}
    {specialized_context}
    {file_context}

    **Required Analysis Format:**
    <think>
    Step 1: Identify the exact error message and command that failed
    Step 2: Analyze why the command failed (syntax, missing files, permissions, etc.)
    Step 3: Find the correct command or fix based on context
    Step 4: Consider any potential risks
    </think>

    Root Cause: <1-line diagnosis>
    Fix: `[executable command]`
    Technical Explanation: <specific system-level reason>
    Potential Risks: <if any>
    Prevention Tip: <actionable advice>"""

        return prompt

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