import subprocess
import sys
import os
import re
import yaml
import click
from collections import deque
from .llm_handler import DeepSeekLLMHandler

class ErrorInterceptor:
    def __init__(self):
        self.llm_handler = DeepSeekLLMHandler()
        self.command_history = deque(maxlen=10)  # Store last 10 commands
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
        self.last_command = command
        self.command_history.append(command)
        result = subprocess.CompletedProcess(
            args=command,
            returncode=exit_code,
            stdout='',
            stderr=self._get_native_error(command)
        )
        self._handle_error(result)

    def _handle_error(self, result):
        """Process and analyze command errors"""
        # Get relevant files from command history
        relevant_files = self._get_relevant_files_from_history()
        
        error_context = {
            'command': self.last_command,
            'error_output': self._get_full_error_output(result),
            'cwd': os.getcwd(),
            'exit_code': result.returncode,
            'history': list(self.command_history),
            'relevant_files': relevant_files,
            **self._get_additional_context()
        }

        # Enhanced context for file operations
        parts = self.last_command.split()
        if len(parts) > 0:
            base_cmd = parts[0]
            error_context['man_excerpt'] = self._get_man_page(base_cmd)

        if os.getenv('SHELLSAGE_DEBUG'):
            print("\n\033[90m[DEBUG] Error Context:")
            print(yaml.dump(error_context, allow_unicode=True) + "\033[0m")

        print("\n\033[90m🔎 Analyzing error...\033[0m")
        solution = self.llm_handler.get_error_solution(error_context)

        if solution:
            self._show_analysis(solution, error_context)
        else:
            print("\n\033[91mError: Could not get analysis\033[0m")

    def _get_relevant_files_from_history(self):
        """Extract recently referenced files from command history"""
        files = []
        for cmd in reversed(list(self.command_history)[:-1]):  # Exclude current command
            parts = cmd.split()
            if parts and parts[0] in ['touch', 'mkdir', 'cp', 'mv', 'vim', 'nano']:
                # Get the last argument as it's typically the file
                files.append(parts[-1])
                if len(files) >= 3:  # Limit to last 3 files
                    break
        return files

    def _get_man_page(self, command):
        """Get relevant sections from man page"""
        try:
            result = subprocess.run(
                f'man {command} 2>/dev/null | col -b',
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                content = result.stdout
                
                # Extract relevant sections
                sections = []
                current_section = None
                for line in content.split('\n'):
                    if line.upper() in ['NAME', 'SYNOPSIS', 'DESCRIPTION']:
                        current_section = line
                        sections.append(line)
                    elif current_section and line.startswith(' '):
                        sections.append(line.strip())
                    if len(sections) > 10:  # Limit size
                        break
                        
                return '\n'.join(sections)
            return "No manual entry available"
        except Exception:
            return "Error retrieving manual page"

    def _get_full_error_output(self, result):
        """Combine stderr/stdout and sanitize"""
        error_output = ''
        if hasattr(result, 'stderr') and result.stderr:
            error_output += result.stderr if isinstance(result.stderr, str) else result.stderr.decode()
        if hasattr(result, 'stdout') and result.stdout:
            error_output += '\n' + (result.stdout if isinstance(result.stdout, str) else result.stdout.decode())
        
        return re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', error_output).strip()

    def _show_analysis(self, solution, context):
        """Display analysis with command context and full man page"""
        components = {
            'cause': re.search(r'🔍 Root Cause: (.+?)(?=\n🛠️|\n📚|\n⚠️|\n🔒|$)', solution, re.DOTALL),
            'fix': re.search(r'🛠️ Fix: `(.+?)`', solution),
            'explanation': re.search(r'📚 Technical Explanation: (.+?)(?=\n⚠️|\n🔒|$)', solution, re.DOTALL),
            'risk': re.search(r'⚠️ Potential Risks: (.+?)(?=\n🔒|$)', solution, re.DOTALL),
            'prevention': re.search(r'🔒 Prevention Tip: (.+?)(?=\n|$)', solution, re.DOTALL)
        }

        print("\n\033[94m=== ERROR ANALYSIS ===\033[0m")
        
        # Show command history context
        if context['history']:
            print(f"\n\033[90m[Context] Recent Commands:")
            for cmd in context['history'][-3:]:
                print(f"  {cmd}\033[0m")
        
        # Show relevant files from history if any
        if context.get('relevant_files'):
            print(f"\n\033[90m[Context] Recently Used Files:")
            for file in context['relevant_files']:
                print(f"  {file}\033[0m")

        # Show analysis components
        self._print_component(components['cause'], '\033[91m', "ROOT CAUSE")
        self._print_component(components['explanation'], '\033[93m', "TECHNICAL DETAILS")
        self._print_component(components['risk'], '\033[33m', "POTENTIAL RISKS")

        # Show complete man page excerpt
        if context.get('man_excerpt'):
            print(f"\n\033[90m[Manual Excerpt]")
            print(f"{context['man_excerpt']}\033[0m")

        if components['fix']:
            self._prompt_fix(components['fix'].group(1), context['relevant_files'])

    def _print_component(self, match, color, label):
        """Enhanced component display"""
        if match:
            cleaned = match.group(1).replace('\n', ' ').strip()
            print(f"{color}▸ {label}:\n   {cleaned}\033[0m")

    def _prompt_fix(self, command, relevant_files):
        """Smart fix suggestion using context"""
        clean_cmd = re.sub(r'^\s*\[.*?\]\s*', '', command).strip()
        
        # If the command contains 'filename' or similar placeholder and we have relevant files
        if ('filename' in clean_cmd.lower() or 'file' in clean_cmd.lower()) and relevant_files:
            clean_cmd = clean_cmd.replace('filename', relevant_files[0])
            clean_cmd = clean_cmd.replace('file', relevant_files[0])
            
        if click.confirm(f"\n\033[95m🚀 Run fix command: '{clean_cmd}'? (Y/n)\033[0m"):
            subprocess.run(
                clean_cmd,
                shell=True,
                check=False,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr
            )

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

    def _get_additional_context(self):
        """Gather additional context for error analysis"""
        context = {}
        
        # Git context
        if self.last_command.startswith('git '):
            try:
                git_status = subprocess.run(
                    'git status --porcelain',
                    shell=True,
                    capture_output=True,
                    text=True
                )
                context['git_status'] = git_status.stdout
                context['git_remotes'] = subprocess.run(
                    'git remote -v',
                    shell=True,
                    capture_output=True,
                    text=True
                ).stdout
            except:
                pass
            
        return context