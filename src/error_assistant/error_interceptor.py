import subprocess
import sys
import os
import re
import click
from collections import deque
from .llm_handler import DeepSeekLLMHandler

class ErrorInterceptor:
    def __init__(self):
        self.llm_handler = DeepSeekLLMHandler()
        self.command_history = deque(maxlen=3)
        self.last_command = ""

    def run_command(self, command):
        """Execute command with error interception"""
        try:
            full_cmd = ' '.join(command)
            self.last_command = full_cmd
            self.command_history.append(full_cmd)
            
            # Execute with live terminal interaction
            result = subprocess.run(
                full_cmd,
                shell=True,
                check=False,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
            
            if result.returncode != 0:
                self._handle_error(result)
            
            sys.exit(result.returncode)
            
        except Exception as e:
            print(f"\n\033[91mExecution Error: {e}\033[0m")
            sys.exit(1)

    def auto_analyze(self, command, exit_code):
        """Automatically analyze failed commands from shell hook"""
        result = subprocess.CompletedProcess(
            args=command,
            returncode=exit_code,
            stdout='',
            stderr=self._get_native_error(command)
        )
        self._handle_error(result)

    def _handle_error(self, result):
        """Process and analyze command errors"""
        error_context = {
            'command': self.last_command,
            'command_history': list(self.command_history)[:-1],
            'error_output': self._get_full_error_output(result),
            'cwd': os.getcwd(),
            'exit_code': result.returncode,
            'env': os.environ.copy(),
            'additional_context': self._get_additional_context()
        }
        
        print("\n\033[90m🔎 Analyzing error...\033[0m")
        solution = self.llm_handler.get_error_solution(error_context)
        
        if solution:
            self._show_analysis(solution)
        else:
            print("\n\033[91mError: Could not get analysis. Please check your API key and connection.\033[0m")

    def _get_full_error_output(self, result):
        """Combine stderr/stdout and sanitize"""
        error_output = (result.stderr + '\n' + result.stdout).strip()
        # Remove ANSI escape codes
        return re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', error_output)
    


    def _get_additional_context(self):
        """Gather additional context for error analysis"""
        context = ""
        
        # Git context
        if self.last_command.startswith('git '):
            try:
                git_status = subprocess.run(
                    'git status --porcelain',
                    shell=True,
                    capture_output=True,
                    text=True
                )
                context += f"\nGit Status:\n{git_status.stdout}"
                
                git_remote = subprocess.run(
                    'git remote -v',
                    shell=True,
                    capture_output=True,
                    text=True
                )
                context += f"\nGit Remotes:\n{git_remote.stdout}"
            except:
                pass
        
        # Docker context
        if 'docker' in self.last_command:
            try:
                docker_ps = subprocess.run(
                    'docker ps -a',
                    shell=True,
                    capture_output=True,
                    text=True
                )
                context += f"\nDocker Containers:\n{docker_ps.stdout}"
            except:
                pass
        
        return context

    def _show_analysis(self, solution):
        """Display error analysis with improved command extraction"""
        # Improved regex for command extraction
        fix_match = re.search(r'🛠️ Fix: `([^`]+)`', solution)
        components = {
            'cause': re.search(r'🔍 Cause: (.+)', solution),
            'fix': fix_match.group(1) if fix_match else None,
            'explanation': re.search(r'📚 Explanation: (.+)', solution),
            'warning': re.search(r'⚠️ Warning: (.+)', solution),
            'prevention': re.search(r'🔒 Prevention: (.+)', solution)
        }

        print("\n\033[94m=== ERROR ANALYSIS ===\033[0m")
        self._print_component(components['cause'], '\033[91m', "Cause")
        self._print_component(components['explanation'], '\033[93m', "Explanation")
        self._print_component(components['warning'], '\033[91m', "Warning")
        self._print_component(components['prevention'], '\033[92m', "Prevention")

        if components['fix']:
            self._prompt_fix(components['fix'])

    def _print_component(self, match, color, label):
        """Improved component printing"""
        if match:
            print(f"{color}● {label}: {match.group(1).strip()}\033[0m")

    def _prompt_fix(self, command):
        """Sanitize and execute command"""
        # Clean command from LLM artifacts
        clean_cmd = re.sub(r'^\s*\[.*?\]\s*', '', command).strip()
        if click.confirm(f"\n\033[95m🚀 Run fix command: '{clean_cmd}'? (Y/n)\033[0m"):
            self._execute_command(clean_cmd)

    def _execute_command(self, command):
        """Execute with full terminal passthrough"""
        try:
            # Directly pass through stdin/stdout/stderr
            subprocess.run(
                command,
                shell=True,
                check=False,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
        except Exception as e:
            print(f"\n\033[91mExecution failed: {str(e)}\033[0m")

    def _get_native_error(self, command):
        """Get error output directly from command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
            return result.stderr.strip()
        except Exception:
            return "Command execution failed"