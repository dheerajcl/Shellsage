import sys
import click
from .error_interceptor import ErrorInterceptor

@click.group()
def cli():
    """Error Assistant - Automatic Terminal Problem Solver"""

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
def install():
    """Install automatic error handling"""
    hook = r"""
error_assist_prompt() {
    local EXIT=$?
    [ $EXIT -eq 0 ] && return
    local CMD=$(history 1 | sed 's/^ *[0-9]\+ *//;s/\\/\\\\/g')
    error-assist run --analyze "$CMD" --exit-code $EXIT
}
PROMPT_COMMAND="error_assist_prompt"
"""
    click.echo("# Add this to your shell config:")
    click.echo(hook)
    click.echo("\n# Then run: source ~/.bashrc")

if __name__ == "__main__":
    cli()