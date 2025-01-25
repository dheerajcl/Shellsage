import subprocess
import sys
import shlex
import os
import re
import click
from .llm_handler import DeepSeekLLMHandler

class ErrorInterceptor:
    def __init__(self):
        self.llm_handler = DeepSeekLLMHandler()
        self.last_command = ""

    def run_command(self, command):
        try:
            self.last_command = ' '.join(command)
            # Increase buffer size for large outputs
            result = subprocess.run(
                self.last_command,
                shell=True,
                capture_output=True,
                text=True,
                bufsize=1024 * 1024  # 1MB buffer
            )
            
            if result.returncode != 0:
                self._handle_error(result)
            
            sys.exit(result.returncode)
            
        except Exception as e:
            print(f"\n\033[91mExecution Error: {e}\033[0m")
            sys.exit(1)

    def auto_analyze(self, command, exit_code):
        result = subprocess.CompletedProcess(
            args=command,
            returncode=exit_code,
            stdout='',
            stderr=self._get_native_error(command)
        )
        self._handle_error(result)

    def _handle_error(self, result):
        # Get git status if it's a git command
        git_context = ''
        if self.last_command.startswith('git '):
            try:
                git_status = subprocess.run(
                    'git status --porcelain',
                    shell=True,
                    capture_output=True,
                    text=True
                )
                git_context = f"\nGit Status:\n{git_status.stdout}"
            except:
                pass
            
        error_context = {
            'command': self.last_command,
            'error_output': (result.stderr + '\n' + result.stdout).strip() if result.stdout else result.stderr,
            'cwd': os.getcwd(),
            'exit_code': result.returncode,
            'additional_context': git_context
        }
        
        print("\n\033[90m🔎 Analyzing error...\033[0m")
        solution = self.llm_handler.get_error_solution(error_context)

        if solution:
            self._show_analysis(solution)
        else:
            print("\n\033[91mError: Could not get analysis. Please check your API key and connection.\033[0m")
        

    def _show_analysis(self, solution):
        components = {
            'cause': re.search(r'🔍 Cause: (.+)', solution),
            'fix': re.search(r'🛠️ Fix: `(.+?)`', solution),
            'explanation': re.search(r'📚 Explanation: (.+)', solution),
            'prevention': re.search(r'🔒 Prevention: (.+)', solution)
        }

        print("\n\033[94m=== ERROR ANALYSIS ===\033[0m")
        self._print_component(components['cause'], '\033[91m')
        self._print_component(components['explanation'], '\033[93m')
        self._print_component(components['prevention'], '\033[92m')

        if components['fix']:
            self._prompt_fix(components['fix'].group(1))

    def _print_component(self, match, color):
        if match:
            print(f"{color}{match.group(0)}\033[0m")

    def _prompt_fix(self, command):
        if click.confirm(f"\n\033[95m🚀 Run fix command: {command}? (Y/n)\033[0m"):
            self._execute_command(command)

    def _execute_command(self, command):
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
            print("\n\033[92m=== COMMAND OUTPUT ===\033[0m")
            print(result.stdout if result.stdout else "(No output)")
            if result.stderr:
                print(f"\n\033[91m=== ERRORS ===\033[0m\n{result.stderr}")
                
        except Exception as e:
            print(f"\n\033[91mEXECUTION FAILED: {str(e)}\033[0m")

    def _get_native_error(self, command):
        try:
            # Special handling for git commands
            if command.startswith('git '):
                # Get both stderr and stdout for git commands as git uses both
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    env={'LANG': 'en_US.UTF-8', 'GIT_TERMINAL_PROMPT': '0'}
                )
                # Combine stdout and stderr for git commands as git uses both
                error_output = result.stdout + '\n' + result.stderr if result.stdout else result.stderr
                return error_output.strip()

            # Normal command handling
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
            return result.stderr.strip()
        except Exception:
            return "Command execution failed"