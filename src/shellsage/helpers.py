from pathlib import Path

def update_env_file(provider, key):
    """Update provider key in .env without duplicates"""
    env_path = Path('.env')
    
    if not env_path.exists():
        env_path.touch()
        
    lines = env_path.read_text().splitlines()
    key_line = f"{provider.upper()}_API_KEY={key}"
    
    # Remove existing entries
    new_lines = [line for line in lines if not line.startswith(f"{provider.upper()}_API_KEY=")]
    
    # Add new key at the end
    new_lines.append(key_line)
    
    # Write back to file
    env_path.write_text("\n".join(new_lines))

def update_env_variable(variable, value):
    """Update any .env variable without duplicates"""
    env_path = Path('.env')
    
    if not env_path.exists():
        env_path.touch()
        
    lines = env_path.read_text().splitlines()
    
    # Remove existing entries
    new_lines = [line for line in lines if not line.startswith(f"{variable}=")]
    
    # Add new value
    new_lines.append(f"{variable}={value}")
    
    # Write back to file
    env_path.write_text("\n".join(new_lines))