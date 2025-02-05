import os
import re
from .model_manager import ModelManager

class CommandGenerator:
    def __init__(self):
        self.manager = ModelManager()
    
    def generate_commands(self, query, context=None):
        try:
            prompt = self._build_prompt(query, context)
            response = self.manager.generate(prompt)
            return self._parse_response(response)
        except Exception as e:
            return [{
                'type': 'warning',
                'content': f"Error: {str(e)}"
            }, {
                'type': 'command',
                'content': None,
                'details': None
            }]

    def _build_prompt(self, query, context):
        return f"""SYSTEM: You are a Linux terminal expert. Generate exactly ONE command.
    
    USER QUERY: {query}
    
    RESPONSE FORMAT:
    🧠 Analysis: [1-line explanation]
    🛠️ Command: ```[executable command(s)]```
    📝 Details: [technical specifics]
    ⚠️ Warning: [if dangerous]
    
    EXAMPLE MULTI-COMMAND RESPONSE:
    🧠 Analysis: Set up new Git repository and push
    🛠️ Command: ```
    git init
    git add .
    git commit -m "Initial commit"
    git remote add origin https://github.com/user/repo.git
    git push -u origin main
    ```
    📝 Details: Full repository initialization and first push
    ⚠️ Warning: Verify remote URL before pushing
    
    CURRENT CONTEXT:
    - OS: {context.get('os', 'Linux')}
    - Directory: {context.get('cwd', 'Unknown')}
    - Git repo: {'Yes' if context.get('git') else 'No'}"""

    def _parse_response(self, response):
    # Handle JSON artifacts from streaming
        cleaned = response.replace('\n', ' ').replace('  ', ' ')

        # More robust pattern matching
        components = {
            'analysis': re.search(r'🧠 Analysis: (.+?)(?=🛠️ Command|⚠️ Warning|$)', cleaned),
            'warning': re.search(r'⚠️ Warning: (.+?)(?=🛠️ Command|📝 Details|$)', cleaned),
            'command': re.search(r'🛠️ Command: ```(.*?)```', cleaned, re.DOTALL),
            'details': re.search(r'📝 Details: (.+?)(?=⚠️ Warning|$)', cleaned)
        }

        # Fallback pattern for malformed responses
        if not components['command']:
            command_match = re.search(r'(sudo [\w-]+|apt|dnf|brew|yum|pacman) [\w &|$-]+', cleaned)
            if command_match:
                components['command'] = command_match

        return [{
            'type': 'analysis',
            'content': components['analysis'].group(1).strip() if components['analysis'] else None
        }, {
            'type': 'warning', 
            'content': components['warning'].group(1).strip() if components['warning'] else None
        }, {
            'type': 'command',
            'content': components['command'].group(1).strip() if components['command'] else None,
            'details': components['details'].group(1).strip() if components['details'] else None
        }]