import json
import os
import re
from datetime import datetime

def save_json_file(filename, data):
    """Save data to JSON file with proper formatting."""
    # Create directory if it doesn't exist
    dir_path = os.path.dirname(filename)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, default=str, ensure_ascii=False)
        print(f"  ✓ Saved: {filename}")
        return True
    except Exception as e:
        print(f"  ✗ Error saving {filename}: {e}")
        return False

def load_json_file(filename):
    """Load data from JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"  ⚠ File not found: {filename}")
        return None
    except Exception as e:
        print(f"  ✗ Error loading {filename}: {e}")
        return None

def clean_sql_text(sql_text):
    """Clean SQL text by removing comments and extra whitespace."""
    if not sql_text:
        return ""
    
    # Remove block comments
    sql_text = re.sub(r'/\*.*?\*/', '', sql_text, flags=re.DOTALL)
    
    # Remove line comments
    lines = sql_text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Simple line comment removal
        comment_pos = line.find('--')
        if comment_pos >= 0:
            cleaned_lines.append(line[:comment_pos].rstrip())
        else:
            cleaned_lines.append(line)
    
    # Join and normalize whitespace
    cleaned = '\n'.join(cleaned_lines)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\s*\n\s*', '\n', cleaned)
    
    return cleaned.strip()

def generate_sample_value(param_name, param_type):
    """Generate sample values for parameters based on name and type."""
    param_name_lower = param_name.lower() if param_name else ''
    param_type_lower = param_type.lower() if param_type else ''
    
    # ID parameters
    if 'id' in param_name_lower:
        if 'user_id' in param_name_lower:
            return "1001"
        elif 'card_id' in param_name_lower:
            return "2001" 
        else:
            return "123"
    
    # Boolean parameters
    if param_type_lower == 'bit' or 'is_' in param_name_lower:
        return "1"
    
    # Date parameters
    if 'date' in param_name_lower or 'datetime' in param_type_lower:
        return "GETDATE()"
    
    # Numeric parameters
    if any(t in param_type_lower for t in ['int', 'decimal', 'numeric', 'float', 'money']):
        return "100"
    
    # String parameters
    if 'name' in param_name_lower:
        return "N'Sample Name'"
    elif 'description' in param_name_lower:
        return "N'Sample Description'"
    elif 'email' in param_name_lower:
        return "N'user@example.com'"
    else:
        return "N'Sample Value'"
