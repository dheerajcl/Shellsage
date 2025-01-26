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
                    "content": f"""Generate terminal commands for user queries. Follow these rules:
                    
1. For multi-step operations, list all required commands in order
2. Include necessary checks/pre-requisites
3. Format response as:
🛠️ Step 1: `command1`
📝 Explanation: Brief description
🛠️ Step 2: `command2`
📝 Explanation: Brief description

Example for "push code to github":
🛠️ Step 1: `git status`
📝 Explanation: Check current repository status
🛠️ Step 2: `git add .`
📝 Explanation: Stage all changes
🛠️ Step 3: `git commit -m "Commit message"`
📝 Explanation: Create commit with message
🛠️ Step 4: `git push origin main`
📝 Explanation: Push to remote repository

Current Context: {context or 'No additional context'}"""
                }, {
                    "role": "user",
                    "content": query
                }],
                temperature=0.1,
                max_tokens=500
            )
            return self._parse_response(response.choices[0].message.content)
        
        except Exception as e:
            return [f"API Error: {str(e)}"]

    def _parse_response(self, response):
        steps = []
        pattern = r'🛠️ Step \d+: `(.+?)`\n📝 Explanation: (.+?)(?=\n🛠️|$)'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for match in matches:
            steps.append({
                'command': match[0].strip(),
                'explanation': match[1].strip()
            })
        return steps