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
@click.argument('query', nargs=-1, required=True)
@click.option('--execute', is_flag=True, help='Execute commands with confirmation')
def ask(query, execute):
    """Generate and execute commands with safety checks"""
    generator = CommandGenerator()
    context = {
        'os': subprocess.run('uname -s', shell=True, capture_output=True, text=True).stdout.strip(),
        'cwd': os.getcwd(),
        'git': os.path.exists('.git')
    }
    
    results = generator.generate_commands(' '.join(query), context)
    
    click.echo("\n\033[94m=== COMMAND ANALYSIS ===\033[0m")
    for item in results:
        if item['type'] == 'warning' and item['content']:
            click.echo(f"\n\033[91m⚠️ WARNING: {item['content']}\033[0m")
        elif item['type'] == 'analysis' and item['content']:
            click.echo(f"\n\033[96m🧠 ANALYSIS: {item['content']}\033[0m")
    
    command_item = next((i for i in results if i['type'] == 'command'), None)
    
    if command_item and command_item['content']:
        click.echo(f"\n\033[92m🛠️ COMMAND: {command_item['content']}\033[0m")
        if command_item['details']:
            click.echo(f"\033[93m📝 DETAILS: {command_item['details']}\033[0m")
        
        if execute:
            if click.confirm("\n\033[95m🚀 Execute this command? (Y/n)\033[0m"):
                # Allow full terminal interaction
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