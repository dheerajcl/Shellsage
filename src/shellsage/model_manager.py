from .helpers import update_env_variable
import os
import yaml
import requests
from pathlib import Path
from openai import OpenAI
import inquirer
from anthropic import Anthropic
from dotenv import load_dotenv


# Define providers at module level
PROVIDERS = {
    'groq': {
        'client': OpenAI,
        'base_url': 'https://api.groq.com/openai/v1',
        'models': ['llama-3.1-8b-instant', 'deepseek-r1-distill-llama-70b', 'gemma2-9b-it', 'llama-3.3-70b-versatile', 'llama3-70b-8192', 'llama3-8b-8192', 'mixtral-8x7b-32768']
    },
    'openai': {
        'client': OpenAI,
        'base_url': 'https://api.openai.com/v1',
        'models': ['gpt-4o', 'chatgpt-4o-latest', 'o1', 'o1-mini', 'o1-preview', 'gpt-4o-2024-08-06', 'gpt-4o-mini-2024-07-18', 'gpt-4-turbo', 'gpt-3.5-turbo']
    },
    'anthropic': {
        'client': Anthropic,
        'models': ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229']
    },
    'fireworks': {
        'client': OpenAI,
        'base_url': 'https://api.fireworks.ai/inference/v1',
        'models': ['accounts/fireworks/models/llama-v3p1-405b-instruct', 'accounts/fireworks/models/deepseek-v3', 'accounts/fireworks/models/llama-v3p1-8b-instruct', 'accounts/fireworks/models/llama-v3p3-70b-instruct']
    },
    'openrouter': {
        'client': OpenAI,
        'base_url': 'https://openrouter.ai/api/v1',
        'models': ['deepseek/deepseek-r1-distill-llama-70b:free', 'deepseek/deepseek-r1-distill-qwen-32b', 'mistralai/mistral-small-24b-instruct-2501', 'openai/gpt-3.5-turbo-instruct', 'microsoft/phi-4', 'google/gemini-2.0-flash-thinking-exp:free', 'google/gemini-2.0-pro-exp-02-05:free', 'deepseek/deepseek-r1:free', 'qwen/qwen-vl-plus:free']
    },
    'deepseek': {
        'client': OpenAI,
        'base_url': 'https://api.deepseek.com/v1',
        'models': ['deepseek-chat']
    }
}

class ModelManager:
    PROVIDERS = PROVIDERS  # Add this line to expose the module-level PROVIDERS
    
    def __init__(self):
        load_dotenv(override=True)
        self.mode = os.getenv('MODE', 'local')
        self.local_model = os.getenv('LOCAL_MODEL', 'llama3:8b-instruct-q4_1')
        self.client = None
        self._init_client()
        
    def _init_client(self):
        """Initialize active client based on config"""
        if self.mode == 'api':
            provider = os.getenv('ACTIVE_API_PROVIDER', 'groq')
            api_key = os.environ.get(f"{provider.upper()}_API_KEY")
            
            if not api_key:
                raise ValueError(f"API key for {provider} not set. Run 'shellsage setup'")

            if self.PROVIDERS[provider]['client'] == OpenAI:
                self.client = OpenAI(
                    api_key=api_key,
                    base_url=self.PROVIDERS[provider].get('base_url')
                )
            # Special case for Anthropic
            elif provider == 'anthropic':
                self.client = Anthropic(api_key=api_key)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        else:
            # Initialize local client if needed
            self.client = "ollama"  # Just a flag for local mode

    def switch_mode(self, new_mode, model_name=None):
        """Change mode with optional model selection"""
        update_env_variable('MODE', new_mode)
        
        if new_mode == 'local' and model_name:
            update_env_variable('LOCAL_MODEL', model_name)
        elif new_mode == 'api' and model_name:
            provider = next(p for p in self.PROVIDERS if model_name in self.PROVIDERS[p]['models'])
            update_env_variable('ACTIVE_API_PROVIDER', provider)
            update_env_variable('API_MODEL', model_name)
            
        load_dotenv(override=True)
        self._init_client()

    def get_ollama_models(self):
        """List installed Ollama models"""
        try:
            ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
            response = requests.get(f"{ollama_host}/api/tags")
            return [m['name'] for m in response.json().get('models', [])]
        except requests.ConnectionError:
            return []

    def interactive_setup(self):
        """Guide user through configuration"""
        questions = [
            inquirer.List('mode',
                message="Select operation mode:",
                choices=['local', 'api'],
                default=self.mode
            ),
            inquirer.List('local_model',
                message="Select local model:",
                choices=self.get_ollama_models(),
                default=self.local_model
            ),
            inquirer.Text('api_key',
                message="Enter Groq API key:",
                default=os.getenv(f"GROQ_API_KEY", ''),
                ignore=lambda x: x['mode'] != 'api'
            )
        ]
        
        answers = inquirer.prompt(questions)
        self._update_config(answers)
        self._init_client()

    def _update_config(self, answers):
        """Update configuration from answers"""
        self.mode = answers['mode']
        self.local_model = answers['local_model']
        os.environ["ACTIVE_API_PROVIDER"] = "groq" if self.mode == 'api' else ""  # Fixed provider assignment
        os.environ["GROQ_API_KEY"] = answers['api_key']
        load_dotenv(override=True)

    def list_local_models(self):
        """Get all available local models"""
        models = []
        if self.mode == 'local':
            models = self.get_ollama_models()
        return models
    
    def generate(self, prompt, max_tokens=512):
        """Unified generation interface"""
        try:
            if self.mode == 'api':
                return self._api_generate(prompt, max_tokens)
            return self._local_generate(prompt)
        except Exception as e:
            raise RuntimeError(f"Generation failed: {str(e)}")

    def _api_generate(self, prompt, max_tokens):
        """Generate using selected API provider"""
        provider = os.getenv('ACTIVE_API_PROVIDER', 'groq')
        model = os.getenv('API_MODEL')  # New environment variable
        
        try:
            if self.PROVIDERS[provider]['client'] == OpenAI:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            elif provider == 'anthropic':
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"API Error ({provider}): {str(e)}")

    def _local_generate(self, prompt):
        """Generate using local provider"""
        if self.mode == 'local':
            return self._ollama_generate(prompt)
        return self._hf_generate(prompt)

    # model_manager.py

    def _ollama_generate(self, prompt):
        try:
            ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
            # Detect if it's a reasoning model based on model name
            is_reasoning_model = any(x in self.local_model.lower() for x in ['deepseek', 'r1', 'think', 'expert'])

            options = {
                "temperature": 0.1,
                "num_predict": 200048
            }

            # Only set stop tokens for non-reasoning models
            if not is_reasoning_model:
                options["stop"] = ["\n\n\n", "USER QUERY:"]

            response = requests.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": self.local_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": options
                }
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
                model_path=self.local_model,
                model_type='llama'
            )
            return model(prompt)
        except Exception as e:
            raise RuntimeError(f"HuggingFace error: {str(e)}")