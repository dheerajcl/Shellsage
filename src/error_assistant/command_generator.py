import os
import re
import click
from openai import OpenAI

class CommandGenerator:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1"
        )
    
    def generate_commands(self, query, context=None):
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{
                    "role": "system",
                    "content": f"""Generate terminal commands with precision:

1. STRICT requirement analysis before suggesting commands
2. SINGLE command if sufficient, MULTI-STEP only when necessary
3. Include safety checks and confirmation prompts
4. Add WARNINGS for destructive operations
5. Consider OS: {context.get('os', 'Linux')}
6. Current directory: {context.get('cwd', 'Unknown')}

Response format:
🧠 Analysis: <brief needs assessment>
⚠️ Warning: <if dangerous>
🛠️ Command: `[command]`
📝 Details: <parameters explanation>
🔍 Check: <verification step>"""
                }, {
                    "role": "user",
                    "content": query
                }],
                temperature=0.1,
                max_tokens=700
            )
            return self._parse_response(response.choices[0].message.content)
        
        except Exception as e:
            return [{
            'type': 'warning',
            'content': f"API Error: {str(e)}"
            }, {
                'type': 'command',
                'content': None,
                'details': None
            }]

    def _parse_response(self, response):
        # Improved pattern matching for different components
        components = {
            'analysis': re.search(r'🧠 Analysis: (.+)', response),
            'warning': re.search(r'⚠️ Warning: (.+)', response),
            'command': re.search(r'🛠️ Command: `(.+?)`', response),
            'details': re.search(r'📝 Details: (.+)', response),
            'check': re.search(r'🔍 Check: (.+)', response)
        }
        
        return [{
            'type': 'analysis',
            'content': components['analysis'].group(1) if components['analysis'] else None
        }, {
            'type': 'warning',
            'content': components['warning'].group(1) if components['warning'] else None
        }, {
            'type': 'command',
            'content': components['command'].group(1) if components['command'] else None,
            'details': components['details'].group(1) if components['details'] else None
        }, {
            'type': 'check',
            'content': components['check'].group(1) if components['check'] else None
        }]