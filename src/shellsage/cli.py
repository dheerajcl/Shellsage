import sys
import click
import os
import subprocess
import inquirer
from .error_interceptor import ErrorInterceptor
from .command_generator import CommandGenerator
from .model_manager import ModelManager, PROVIDERS
from .helpers import update_env_file, update_env_variable
from dotenv import load_dotenv
import re

@click.group()
def cli():
    """Terminal Assistant - Error Analysis & Command Generation"""

@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument('command', nargs=-1)
@click.option('--analyze', is_flag=True, hidden=True)
@click.option('--exit-code', type=int, hidden=True)
def run(command, analyze, exit_code):
    """Execute command with error analysis"""
    interceptor = ErrorInterceptor()
    if analyze:
        interceptor.auto_analyze(' '.join(command), exit_code)
    else:
        interceptor.run_command(command)

# cli.py - update the ask command

@cli.command()
@click.argument('query', nargs=-1, required=True)
@click.option('--execute', is_flag=True, help='Execute commands with safety checks')
def ask(query, execute):
    """Generate and execute commands with safety checks"""
    generator = CommandGenerator()
    interceptor = ErrorInterceptor()

    # Add distro detection at the top of the ask command
    try:
        with open('/etc/os-release') as f:
            dist_info = {k.lower(): v.strip('"') for k,v in 
                        [line.split('=') for line in f if '=' in line]}
        dist_name = dist_info.get('pretty_name', 'Linux')
    except FileNotFoundError:
        import platform
        dist_name = f"{platform.system()} {platform.release()}"

    context = {
        'os': dist_name,
        'cwd': os.getcwd(),
        'git': os.path.exists('.git'),
        'history': interceptor.command_history
    }
    
    results = generator.generate_commands(' '.join(query), context)
    
    click.echo("\n\033[94m=== COMMAND ANALYSIS ===\033[0m")
    
    # Display thinking process first if present
    thinking_items = [item for item in results if item['type'] == 'thinking']
    if thinking_items:
        click.echo("\n\033[95m=== THINKING PROCESS ===\033[0m")
        for item in thinking_items:
            click.echo(f"\n\033[95m💭 {item['content']}\033[0m")
    
    # Display other components
    command_item = next((i for i in results if i['type'] == 'command' and i['content']), None)
    
    for item in results:
        if item['type'] == 'warning' and item['content']:
            click.echo(f"\n\033[91m⚠️ WARNING: {item['content']}\033[0m")
        elif item['type'] == 'analysis' and item['content']:
            click.echo(f"\n\033[96m🧠 ANALYSIS: {item['content']}\033[0m")
    
    if command_item and command_item['content']:
        click.echo(f"\n\033[92m🛠️ COMMAND: {command_item['content']}\033[0m")
        details_item = next((i for i in results if i['type'] == 'details'), None)
        if details_item and details_item['content']:
            click.echo(f"\033[93m📝 DETAILS: {details_item['content']}\033[0m")
        
        if execute:
            if click.confirm("\n\033[95m🚀 Execute this command? (Y/n)\033[0m"):
                subprocess.run(
                    command_item['content'],
                    shell=True,
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                    stderr=sys.stderr
                )
    else:
        click.echo("\n\033[91mNo valid command generated\033[0m")

@cli.command()
def install():
    """Install automatic error handling"""
    hook = r"""
shell_sage_prompt() {
    local EXIT=$?
    local CMD=$(fc -ln -1 | awk '{$1=$1}1' | sed 's/\\/\\\\/g')
    [ $EXIT -ne 0 ] && shellsage run --analyze "$CMD" --exit-code $EXIT
    history -s "$CMD"  # Force into session history
}
PROMPT_COMMAND="shell_sage_prompt"
"""
    click.echo("# Add this to your shell config:")
    click.echo(hook)
    click.echo("\n# Then run: source ~/.bashrc")

@cli.command()
def setup():
    """Interactive configuration setup"""
    if not os.path.exists('.env'):
        click.echo("❌ Missing .env file - clone the repository properly")
        return

    # Mode selection
    mode_q = inquirer.List(
        'mode',
        message="Select operation mode:",
        choices=['local', 'api'],
        default=os.getenv('MODE', 'local')
    )
    answers = inquirer.prompt([mode_q])
    mode = answers['mode']
    
    if mode == 'local':
        # Create/update .env with all providers
        env_lines = [
            f"# Shell Sage Configuration\n",
            f"ACTIVE_API_PROVIDER=groq\n"
        ]
        for provider in PROVIDERS:
            env_lines.append(f"{provider.upper()}_API_KEY=\n")
        
        if not os.path.exists('.env'):
            with open('.env', 'w') as f:
                f.writelines(env_lines)
        
        # API provider selection
        provider_q = inquirer.List(
            'provider',
            message="Select API Provider:",
            choices=list(PROVIDERS.keys())
        )
        answers = inquirer.prompt([provider_q])
        provider = answers['provider']
        
        # Read directly from .env file instead of os.getenv
        with open('.env') as f:
            env_content = f.read()
        existing_key = re.search(f"{provider.upper()}_API_KEY=(.*)", env_content)
        if not existing_key or not existing_key.group(1).strip():
            key_q = inquirer.Text(
                'key',
                message=f"Enter {provider} API key:"
            )
            key_answers = inquirer.prompt([key_q])
            # Update .env without duplicates
            update_env_file(provider, key_answers['key'])
            load_dotenv(override=True)  # Now using the correct import
        
        # Model selection
        models = PROVIDERS[provider]['models']
        model_q = inquirer.List(
            'model',
            message=f"Select {provider} model:",
            choices=models
        )
        model_answers = inquirer.prompt([model_q])
        
        # Update active provider using helper
        update_env_variable('ACTIVE_API_PROVIDER', provider)
        
        click.echo("✅ API configuration updated!")
    elif mode == 'api':
        # Update provider FIRST before checking key
        update_env_variable('ACTIVE_API_PROVIDER', provider)
        load_dotenv(override=True)
        
        # Now check key in updated environment
        key = os.getenv(f"{provider.upper()}_API_KEY")
        if not key:
            key_q = inquirer.Text(
                'key',
                message=f"Enter {provider} API key:"
            )
            key_answers = inquirer.prompt([key_q])
            # Update .env
            update_env_variable(f"{provider.upper()}_API_KEY", key_answers['key'])

        # Model selection
        models = PROVIDERS[provider]['models']
        if not model:
            model_q = inquirer.List(
                'model',
                message=f"Select {provider} model:",
                choices=models
            )
            model = inquirer.prompt([model_q])['model']
        
        # Update config
        manager = ModelManager()
        update_env_variable('API_MODEL', model)
        manager.switch_mode('api', model_name=model)
        click.echo(f"✅ Switched to API mode using {provider}/{model}")
        
    else:
        current_mode = manager.config['mode']
        click.echo(f"Current mode: {current_mode}")
        if current_mode == 'local':
            click.echo(f"Local model: {manager.config['local']['model']}")
        else:
            provider = os.getenv('ACTIVE_API_PROVIDER', 'groq')
            click.echo(f"API Provider: {provider}")

@cli.command()
@click.option('--mode', type=click.Choice(['local', 'api']))
@click.option('--provider', type=click.Choice(list(PROVIDERS.keys())))
@click.option('--model', help="Specify model name")
def config(mode, provider, model):
    """Configure operation mode and models"""
    manager = ModelManager()
    
    if mode == 'local':
        models = manager.get_ollama_models()
        question = [
            inquirer.List('model',
                message="Select local model:",
                choices=models,
                default=os.getenv('LOCAL_MODEL')
            )
        ]
        answers = inquirer.prompt(question)
        update_env_variable('LOCAL_MODEL', answers['model'])
        update_env_variable('MODE', 'local')
        click.echo(f"✅ Switched to local mode using {answers['model']}")
            
    elif mode == 'api':
        if not provider:
            # Interactive provider selection
            provider_q = inquirer.List(
                'provider',
                message="Select API Provider:",
                choices=list(PROVIDERS.keys())
            )
            provider = inquirer.prompt([provider_q])['provider']
        
        # Update provider FIRST before checking key
        update_env_variable('ACTIVE_API_PROVIDER', provider)
        load_dotenv(override=True)
        
        # Now check key in updated environment
        key = os.getenv(f"{provider.upper()}_API_KEY")
        if not key:
            key_q = inquirer.Text(
                'key',
                message=f"Enter {provider} API key:"
            )
            key_answers = inquirer.prompt([key_q])
            # Update .env
            update_env_variable(f"{provider.upper()}_API_KEY", key_answers['key'])

        # Model selection
        models = PROVIDERS[provider]['models']
        if not model:
            model_q = inquirer.List(
                'model',
                message=f"Select {provider} model:",
                choices=models
            )
            model = inquirer.prompt([model_q])['model']
        
        # Update config
        manager.switch_mode('api', model_name=model)
        click.echo(f"✅ Switched to API mode using {provider}/{model}")
        
    else:
        current_mode = manager.config['mode']
        click.echo(f"Current mode: {current_mode}")
        if current_mode == 'local':
            click.echo(f"Local model: {manager.config['local']['model']}")
        else:
            provider = os.getenv('ACTIVE_API_PROVIDER', 'groq')
            click.echo(f"API Provider: {provider}")

@cli.command()
@click.option('--provider', type=click.Choice(['ollama', 'huggingface']))
def models(provider):
    """Manage local models"""
    manager = ModelManager()
    
    if provider:
        manager.config['local']['provider'] = provider
        manager._save_config()
    
    click.echo(f"Local provider: {manager.config['local']['provider']}")
    
    if manager.config['local']['provider'] == 'ollama':
        models = manager.get_ollama_models()
        click.echo("\nInstalled Ollama models:")
    else:
        models = manager._get_hf_models()
        click.echo("\nInstalled HuggingFace models:")
        
    for model in models:
        click.echo(f"- {model}")    


if __name__ == "__main__":
    cli()