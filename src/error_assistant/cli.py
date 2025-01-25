import sys
import click
from .error_interceptor import ErrorInterceptor

@click.command()
@click.argument('command', nargs=-1, required=True)
def main(command):
    """
    Error Assistant CLI Tool
    
    Intercept and resolve errors for shell commands
    """
    # Convert command tuple to list
    full_command = list(command)
    
    # Initialize interceptor
    interceptor = ErrorInterceptor()
    interceptor.run_command(full_command)

if __name__ == "__main__":
    main()