import subprocess
import sys
import shlex
import os
import re
from .llm_handler import DeepSeekLLMHandler
import click

class ErrorInterceptor:
    def __init__(self):
        self.llm_handler = DeepSeekLLMHandler()
    
    def run_command(self, command):
        try:
            # Normalize command input
            if isinstance(command, str):
                cmd_str = command
                cmd_parts = shlex.split(command)
            else:
                cmd_str = ' '.join(command)
                cmd_parts = command
            
            # Execute command through shell to get native errors
            result = subprocess.run(
                cmd_str,
                shell=True,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Successful command execution
            if result.returncode == 0:
                print(result.stdout)
                return result
            
            # Show original error exactly as terminal would
            print(f"\n\033[91mCOMMAND ERROR:\033[0m")
            print(result.stderr.strip() or f"Command failed with exit code {result.returncode}")
            
            # Display error detection
            print("\n\033[91m🔴 ERROR DETECTED 🔴\033[0m")
            print(f"Command: {cmd_str}")
            print(f"Exit Code: {result.returncode}")
            
            # Get structured solution
            solution = self.llm_handler.get_error_solution(result.stderr)
            return self._process_solution(solution, cmd_parts)
            
        except Exception as e:
            print(f"\n\033[91mExecution Error: {e}\033[0m")
            return None

    def _process_solution(self, solution, cmd_parts):
        """Common solution processing logic"""
        # Parse solution components
        solution_data = {
            'cause': self._extract_section(solution, 'Cause'),
            'explanation': self._extract_section(solution, 'Explanation'),
            'command': self._extract_section(solution, 'Command'),
            'prevention': self._extract_section(solution, 'Prevention')
        }

        # Display analysis
        print("\n\033[93m📖 Error Analysis:\033[0m")
        print(f"\033[91mCause:\033[0m {solution_data.get('cause', 'Unknown')}")
        print(f"\033[94mTechnical Note:\033[0m {solution_data.get('explanation', '')}")
        
        if solution_data.get('prevention'):
            print(f"\n\033[96m🔒 Prevention Tip:\033[0m {solution_data.get('prevention')}")

        # Handle command suggestion
        corrective_command = solution_data.get('command')
        
        if corrective_command:
            # Clean command from formatting
            corrective_command = corrective_command.strip('`').strip()
            if click.confirm(f"\n\033[92m🚀 Suggested fix: {corrective_command}\nRun this command? (Y/n)\033[0m"):
                self._execute_corrective_command(corrective_command)
        else:
            print("\n\033[93m⚠️  Additional suggestions:\033[0m")
            print(solution)

    def _extract_section(self, solution, section_name):
        """Extract specific section from structured response"""
        match = re.search(fr"{section_name}:\s*(.+?)(?=\n\w+:|$)", solution, re.DOTALL)
        return match.group(1).strip() if match else None

    def _execute_corrective_command(self, command):
        """Execute the corrective command and show results"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"\n\033[92m✅ Command executed successfully:\033[0m")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"\n\033[91m❌ Corrective command failed:\033[0m")
            print(e.stderr)
        except Exception as e:
            print(f"\n\033[91m⚠️  Unexpected error: {str(e)}\033[0m")

def main():
    if len(sys.argv) < 2:
        print("Usage: error-assist <shell_command>")
        sys.exit(1)
    
    command = sys.argv[1:]
    interceptor = ErrorInterceptor()
    interceptor.run_command(command)

if __name__ == "__main__":
    main()