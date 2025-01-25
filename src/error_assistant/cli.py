import sys
import click
import os
import subprocess
from .error_interceptor import ErrorInterceptor
from .command_generator import CommandGenerator

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

@cli.command()
@click.argument('query', nargs=-1, required=True)  # Changed to required
@click.option('--execute', is_flag=True, help='Execute commands automatically')
def ask(query, execute):
    """Generate commands from natural language queries"""
    generator = CommandGenerator()
    context = {
        'os': subprocess.run('uname -s', shell=True, capture_output=True, text=True).stdout.strip(),
        'git_initialized': os.path.exists('.git')
    }
    
    steps = generator.generate_commands(' '.join(query), context)
    
    if not steps:
        click.echo("No valid commands generated")
        return

    click.echo("\n\033[94m=== GENERATED COMMANDS ===\033[0m")
    for idx, step in enumerate(steps, 1):
        click.echo(f"\n\033[93mStep {idx}:\033[0m {step['explanation']}")
        click.echo(f"\033[92mCommand:\033[0m {step['command']}")
        
        if execute and click.confirm(f"Run this command? (Y/n)"):
            subprocess.run(step['command'], shell=True)

@cli.command()
def install():
    """Install automatic error handling"""
    hook = r"""
shell_sage_prompt() {
    local EXIT=$?
    [ $EXIT -eq 0 ] && return
    local CMD=$(fc -ln -1 | sed 's/^[[:space:]]*//;s/\\/\\\\/g')
    shellsage run --analyze "$CMD" --exit-code $EXIT
}
PROMPT_COMMAND="shell_sage_prompt"
"""
    click.echo("# Add this to your shell config:")
    click.echo(hook)
    click.echo("\n# Then run: source ~/.bashrc")

if __name__ == "__main__":
    cli()