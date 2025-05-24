from typing import Dict, List, Optional
import re


def extract_procedures_from_script(script: str) -> List[str]:
    """Extract procedure names from a generated script."""
    # Pattern to match procedure calls
    proc_pattern = r'\bEXEC\s+(?:\[\w+\]\.)?\[?\w+\]?\s*\[?\w+\]?\b'
    
    # Find all matches
    matches = re.finditer(proc_pattern, script, re.IGNORECASE)
    
    # Extract and clean procedure names
    proc_names = []
    for match in matches:
        proc = match.group(0)
        # Remove EXEC and brackets
        proc = proc.replace('EXEC', '').strip()
        proc = proc.replace('[', '').replace(']', '').strip()
        # Split schema and procedure name
        if '.' in proc:
            proc = proc.split('.')[-1]  # Take just the procedure name
        proc_names.append(proc)
    
    return list(set(proc_names))  # Remove duplicates


def extract_parameters_from_procedure_call(call: str) -> List[str]:
    """Extract parameter names from a procedure call."""
    # Pattern to match parameter assignments
    param_pattern = r'\s*@\w+\s*=\s*'
    
    # Find all matches
    matches = re.finditer(param_pattern, call, re.IGNORECASE)
    
    # Extract parameter names
    params = []
    for match in matches:
        param = match.group(0)
        # Extract just the parameter name
        param = param.strip()
        param = param.split('=')[0].strip()
        param = param.lstrip('@')
        params.append(param)
    
    return params


def categorize_script_complexity(script: str) -> str:
    """Categorize script complexity based on various factors."""
    complexity = 1  # Base complexity
    
    # Count number of procedure calls
    proc_calls = len(extract_procedures_from_script(script))
    complexity += min(proc_calls - 1, 2)  # Max +2 for multiple procedures
    
    # Check for conditional logic
    if re.search(r'\bIF\b|\bCASE\b', script, re.IGNORECASE):
        complexity += 1
    
    # Check for loops
    if re.search(r'\bWHILE\b|\bFOR\b', script, re.IGNORECASE):
        complexity += 1
    
    # Check for transactions
    if re.search(r'\bBEGIN\s+TRAN\b|\bCOMMIT\b|\bROLLBACK\b', script, re.IGNORECASE):
        complexity += 1
    
    # Check for error handling
    if re.search(r'\bTRY\b|\bCATCH\b|\bTHROW\b', script, re.IGNORECASE):
        complexity += 1
    
    # Map complexity to categories
    if complexity <= 2:
        return "simple"
    elif complexity <= 4:
        return "medium"
    else:
        return "complex"
