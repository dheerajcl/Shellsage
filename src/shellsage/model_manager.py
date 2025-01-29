import os
import yaml
import requests
from pathlib import Path
from openai import OpenAI
import inquirer

class ModelManager:
    CONFIG_PATH = Path.home() / ".shellsage/config.yaml"
    
    def __init__(self):
        self.config = self._load_config()
        self.client = None
        self._init_client()
        
    def _load_config(self):
        """Load or create configuration with defaults"""
        default_config = {
            'mode': 'local',
            'local': {
                'provider': 'ollama',
                'model': 'llama3:8b-instruct-q4_1'
            },
            'api': {
                'provider': 'groq',
                'key': os.getenv('GROQ_API_KEY', ''),
                'model': 'llama3-8b-8192'
            }
        }
        
        try:
            self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            if self.CONFIG_PATH.exists():
                with open(self.CONFIG_PATH) as f:
                    return {**default_config, **yaml.safe_load(f)}
            return default_config
        except Exception as e:
            print(f"Config error: {e}")
            return default_config

    def _init_client(self):
        """Initialize active client based on config"""
        if self.config['mode'] == 'api':
            self.client = OpenAI(
                api_key=self.config['api']['key'],
                base_url="https://api.groq.com/openai/v1"
            )
        else:
            self.client = None  # Local handled separately

    def switch_mode(self, new_mode):
        """Change operation mode"""
        self.config['mode'] = new_mode
        self._save_config()
        self._init_client()

    def get_ollama_models(self):
        """List installed Ollama models"""
        try:
            response = requests.get("http://localhost:11434/api/tags")
            return [m['name'] for m in response.json().get('models', [])]
        except requests.ConnectionError:
            return []

    def interactive_setup(self):
        """Guide user through configuration"""
        questions = [
            inquirer.List('mode',
                message="Select operation mode:",
                choices=['local', 'api'],
                default=self.config['mode']
            ),
            inquirer.List('local_provider',
                message="Choose local provider:",
                choices=['ollama', 'huggingface'],
                default=self.config['local']['provider'],
                ignore=lambda x: x['mode'] != 'local'
            ),
            inquirer.List('ollama_model',
                message="Select Ollama model:",
                choices=self.get_ollama_models(),
                default=self.config['local']['model'],
                ignore=lambda x: x['local_provider'] != 'ollama'
            ),
            inquirer.Text('api_key',
                message="Enter Groq API key:",
                default=self.config['api']['key'],
                ignore=lambda x: x['mode'] != 'api'
            )
        ]
        
        answers = inquirer.prompt(questions)
        self._update_config(answers)
        self._init_client()

    def _update_config(self, answers):
        """Update configuration from answers"""
        self.config.update({
            'mode': answers['mode'],
            'local': {
                'provider': answers.get('local_provider', 'ollama'),
                'model': answers.get('ollama_model', 'llama3:8b-instruct-q4_1')
            },
            'api': {
                'key': answers.get('api_key', ''),
                'model': 'llama3-8b-8192'
            }
        })
        self._save_config()

    def _save_config(self):
        """Save configuration to file"""
        with open(self.CONFIG_PATH, 'w') as f:
            yaml.dump(self.config, f)

    def generate(self, prompt, max_tokens=512):
        """Unified generation interface"""
        if self.config['mode'] == 'api':
            return self._api_generate(prompt, max_tokens)
        return self._local_generate(prompt)

    def _api_generate(self, prompt, max_tokens):
        """Generate using Groq API"""
        response = self.client.chat.completions.create(
            model=self.config['api']['model'],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    def _local_generate(self, prompt):
        """Generate using local provider"""
        if self.config['local']['provider'] == 'ollama':
            return self._ollama_generate(prompt)
        return self._hf_generate(prompt)

    def _ollama_generate(self, prompt):
        """Generate using Ollama API with streaming support"""
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.config['local']['model'],
                    "prompt": prompt,
                    "stream": False,  # Force non-streaming
                    "options": {
                        "temperature": 0.1,
                        "stop": ["\n\n"]  # Prevent endless generation
                    }
                },
                # timeout=30  # Add timeout
            )
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            raise RuntimeError(f"Ollama error: {str(e)}")
    
    def _hf_generate(self, prompt):
        """Generate using HuggingFace model"""
        from ctransformers import AutoModelForCausalLM
        
        try:
            model = AutoModelForCausalLM.from_pretrained(
                model_path=self.config['local']['model'],
                model_type='llama'
            )
            return model(prompt)
        except Exception as e:
            raise RuntimeError(f"HuggingFace error: {str(e)}")