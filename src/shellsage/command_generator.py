import os
import re
from .model_manager import ModelManager


class CommandGenerator:
    def __init__(self):
        self.manager = ModelManager()
    
    def generate_commands(self, query, context=None):
        try:
            prompt = self._build_prompt(query, context)
            response = self.manager.generate(prompt)
            
            # Check if response contains thinking tokens
            has_thinking = '<think>' in response and '</think>' in response
            
            if has_thinking:
                thoughts = []
                remaining_response = response
                while '<think>' in remaining_response and '</think>' in remaining_response:
                    think_start = remaining_response.find('<think>') + len('<think>')
                    think_end = remaining_response.find('</think>')
                    if think_start > -1 and think_end > -1:
                        thought = remaining_response[think_start:think_end].strip()
                        thoughts.append(thought)
                        remaining_response = remaining_response[think_end + len('</think>'):]
                
                final_response = remaining_response.strip()
                return self._format_thinking_response(thoughts, final_response)
            else:
                return self._parse_response(response)
                
        except Exception as e:
            return [{
                'type': 'warning',
                'content': f"Error: {str(e)}"
            }, {
                'type': 'command',
                'content': None,
                'details': None
            }]

    def _build_prompt(self, query, context):
        # Determine the primary context based on the query and environment
        system_context = f"""SYSTEM: You are a Linux terminal expert. Generate exactly ONE command or command sequence.
Primary focus is on system-level operations (package management, system updates, file operations).
Only consider Git operations if the query explicitly mentions Git/repository operations.
    
USER QUERY: {query}
    
RESPONSE FORMAT:
🧠 Analysis: [1-line explanation]
🛠️ Command: ```[executable command(s)]```
📝 Details: [technical specifics]
⚠️ Warning: [if dangerous]

CURRENT CONTEXT:
- OS: {context.get('os', 'Linux')}
- Directory: {context.get('cwd', 'Unknown')}
{f'- Git repo: Yes (only relevant for Git-specific queries)' if context.get('git') else ''}

PRIORITY ORDER:
1. System-level operations (apt, dnf, pacman, etc.)
2. File system operations
3. Repository operations (only if explicitly requested)

EXAMPLES:
Query: "update packages"
🧠 Analysis: Update system packages using the appropriate package manager
🛠️ Command: ```sudo apt update && sudo apt upgrade -y```
📝 Details: Updates package lists and upgrades all installed packages
⚠️ Warning: System may require restart after certain updates

Query: "update git repo"
🧠 Analysis: Update local Git repository with remote changes
🛠️ Command: ```git pull origin main```
📝 Details: Fetches and merges changes from the remote repository
⚠️ Warning: Ensure working directory is clean before updating
"""
        return system_context

    
    def _format_thinking_response(self, thoughts, final_response):
        results = []
        
        # Add thinking process to results
        for thought in thoughts:
            results.append({
                'type': 'thinking',
                'content': thought
            })
        
        # Parse the final response
        components = self._parse_response(final_response)
        
        # Clean up any duplicate sections caused by thinking process
        seen_types = set()
        cleaned_components = []
        
        for comp in components:
            if comp['type'] not in seen_types and comp['content']:
                seen_types.add(comp['type'])
                # Remove any duplicate content within the same component
                if isinstance(comp['content'], str):
                    comp['content'] = '\n'.join(dict.fromkeys(comp['content'].split('\n')))
                cleaned_components.append(comp)
        
        results.extend(cleaned_components)
        return results
    
    
    def _parse_response(self, response):
        # Clean up response by removing any remaining XML-like tags
        cleaned = re.sub(r'<[^>]+>', '', response)
        
        components = {
            'analysis': None,
            'command': None,
            'details': None,
            'warning': None
        }
        
        markers = {
            'analysis': ['🧠', 'Analysis:'],
            'command': ['🛠️', 'Command:'],
            'details': ['📝', 'Details:'],
            'warning': ['⚠️', 'Warning:']
        }
        
        lines = cleaned.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            for section, section_markers in markers.items():
                if any(marker in line for marker in section_markers):
                    current_section = section
                    for marker in section_markers:
                        line = line.replace(marker, '').strip()
                    components[section] = line
                    break
            
            if current_section and not any(
                marker in line for markers_list in markers.values() 
                for marker in markers_list
            ):
                if components[current_section]:
                    components[current_section] += '\n' + line
                else:
                    components[current_section] = line
        
        return [{
            'type': key,
            'content': value.strip() if value else None
        } for key, value in components.items()]