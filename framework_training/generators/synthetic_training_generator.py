from typing import Dict, List, Optional
from datetime import datetime

from .pattern_analyzer.pattern_extractor import analyze_script_patterns
from .pattern_analyzer.pattern_normalizer import normalize_patterns
from .example_generators.simple_generator import SimpleExampleGenerator
from .example_generators.validation_generator import ValidationExampleGenerator
from .example_generators.crud_generator import CRUDExampleGenerator
from .example_generators.error_generator import ErrorHandlingExampleGenerator
from .example_generators.multi_procedure_generator import MultiProcedureExampleGenerator
from .example_generators.advanced_generator import AdvancedExampleGenerator
from .curriculum.curriculum_generator import generate_comprehensive_training_curriculum
from .curriculum.assessment_generator import create_skill_assessments
from .utils.value_generator import generate_sample_value
from .utils.script_utils import extract_procedures_from_script
from .output.markdown_generator import MarkdownGenerator

# Add these new functions for synthetic training data generation

def analyze_script_patterns(action_scripts_corpus, framework_api_details, procedure_relationships=None):
    """
    Analyze existing scripts to extract patterns for synthetic generation.
    """
    patterns = {
        "common_structures": [],
        "parameter_usage_patterns": {},
        "error_handling_patterns": [],
        "conditional_logic_patterns": [],
        "variable_naming_conventions": {},
        "procedure_call_patterns": {},
        "script_complexity_distribution": {"simple": 0, "medium": 0, "complex": 0},
        "common_sql_constructs": set(),
        "business_logic_patterns": []
    }
    
    if not action_scripts_corpus or not framework_api_details:
        return patterns
    
    print("PATTERN_ANALYSIS: Analyzing existing scripts for synthesis patterns...")
    
    # Create procedure lookup map
    proc_map = {f"{obj['schema_name']}.{obj['object_name']}": obj 
                for obj in framework_api_details if obj.get('object_type_short') == 'P'}
    
    for script_info in action_scripts_corpus:
        sql_text = script_info.get('sql_source', '')
        if not sql_text:
            continue
            
        # Analyze script complexity
        complexity = categorize_script_complexity(sql_text)
        patterns["script_complexity_distribution"][complexity] += 1
        
        # Extract parameter usage patterns
        extract_parameter_patterns(sql_text, patterns, proc_map)
        
        # Extract structural patterns
        extract_structural_patterns(sql_text, patterns)
        
        # Extract error handling patterns
        extract_error_handling_patterns(sql_text, patterns)
        
        # Extract conditional logic patterns
        extract_conditional_patterns(sql_text, patterns)
        
        # Extract variable naming conventions
        extract_variable_naming_patterns(sql_text, patterns)
        
        # Extract business logic patterns
        extract_business_logic_patterns(sql_text, patterns, script_info)
    
    # Normalize and clean patterns
    normalize_patterns(patterns)
    
    print(f"PATTERN_ANALYSIS: Extracted {len(patterns['common_structures'])} structural patterns")
    print(f"PATTERN_ANALYSIS: Found {len(patterns['parameter_usage_patterns'])} parameter patterns")
    print(f"PATTERN_ANALYSIS: Complexity distribution: {patterns['script_complexity_distribution']}")
    
    return patterns

def categorize_script_complexity(sql_text):
    """Categorize script complexity based on various factors."""
    lines = len([line for line in sql_text.split('\n') if line.strip()])
    exec_count = len(re.findall(r'\bEXEC\b', sql_text, re.IGNORECASE))
    if_count = len(re.findall(r'\bIF\b', sql_text, re.IGNORECASE))
    try_count = len(re.findall(r'\bTRY\b', sql_text, re.IGNORECASE))
    
    complexity_score = lines + (exec_count * 2) + (if_count * 3) + (try_count * 4)
    
    if complexity_score < 15:
        return "simple"
    elif complexity_score < 50:
        return "medium"
    else:
        return "complex"

def extract_parameter_patterns(sql_text, patterns, proc_map):
    """Extract how parameters are typically used in procedure calls."""
    # Find EXEC statements with parameters
    exec_pattern = r'EXEC\s+(?:dbo\.)?(\w+)\s+(.*?)(?=;|\n|$|EXEC|IF|ELSE|END)'
    exec_matches = re.finditer(exec_pattern, sql_text, re.IGNORECASE | re.DOTALL)
    
    for match in exec_matches:
        proc_name = match.group(1)
        params_text = match.group(2).strip()
        
        # Find the procedure in our framework
        full_proc_name = next((name for name in proc_map.keys() 
                              if name.endswith(f'.{proc_name}')), None)
        
        if full_proc_name and params_text:
            if full_proc_name not in patterns["parameter_usage_patterns"]:
                patterns["parameter_usage_patterns"][full_proc_name] = []
            
            # Parse parameter usage
            param_usage = parse_parameter_usage(params_text, proc_map[full_proc_name])
            if param_usage:
                patterns["parameter_usage_patterns"][full_proc_name].append(param_usage)

def parse_parameter_usage(params_text, proc_obj):
    """Parse how parameters are passed to a procedure."""
    usage_pattern = {
        "positional_params": [],
        "named_params": {},
        "variable_usage": [],
        "literal_usage": [],
        "context_vars_used": []
    }
    
    # Simple parameter parsing (could be enhanced)
    param_parts = re.split(r',(?![^()]*\))', params_text)
    
    for part in param_parts:
        part = part.strip()
        if not part:
            continue
            
        # Check for named parameters
        named_match = re.match(r'@(\w+)\s*=\s*(.+)', part)
        if named_match:
            param_name = f"@{named_match.group(1)}"
            param_value = named_match.group(2).strip()
            usage_pattern["named_params"][param_name] = param_value
            
            # Categorize the value type
            if param_value.startswith('@'):
                usage_pattern["variable_usage"].append(param_value)
                if param_value in ['@card_id', '@user_id', '@id', '@ids']:
                    usage_pattern["context_vars_used"].append(param_value)
            elif param_value.startswith("'") or param_value.startswith("N'"):
                usage_pattern["literal_usage"].append(param_value)
        else:
            # Positional parameter
            usage_pattern["positional_params"].append(part)
    
    return usage_pattern if any(usage_pattern.values()) else None

def extract_structural_patterns(sql_text, patterns):
    """Extract common structural patterns from scripts."""
    # Common structural elements
    structures = []
    
    # TRY-CATCH blocks
    if re.search(r'BEGIN\s+TRY.*?BEGIN\s+CATCH', sql_text, re.IGNORECASE | re.DOTALL):
        structures.append("try_catch_error_handling")
    
    # IF-ELSE blocks
    if re.search(r'IF\s+.*?\s+BEGIN.*?END', sql_text, re.IGNORECASE | re.DOTALL):
        structures.append("conditional_branching")
    
    # Variable declarations at start
    if re.search(r'^\s*DECLARE\s+@', sql_text, re.IGNORECASE | re.MULTILINE):
        structures.append("variable_declaration_block")
    
    # Multiple EXEC calls
    exec_count = len(re.findall(r'\bEXEC\b', sql_text, re.IGNORECASE))
    if exec_count > 1:
        structures.append(f"multiple_procedure_calls_{min(exec_count, 5)}")
    
    # Parameter validation
    if re.search(r'IF\s+@\w+\s+IS\s+NULL', sql_text, re.IGNORECASE):
        structures.append("parameter_validation")
    
    # Result checking
    if re.search(r'IF\s+@@ROWCOUNT', sql_text, re.IGNORECASE):
        structures.append("rowcount_checking")
    
    patterns["common_structures"].extend(structures)

def extract_error_handling_patterns(sql_text, patterns):
    """Extract error handling patterns."""
    error_patterns = []
    
    # TRY-CATCH with specific error handling
    if re.search(r'CATCH.*?THROW', sql_text, re.IGNORECASE | re.DOTALL):
        error_patterns.append("try_catch_with_throw")
    
    # Custom error messages
    if re.search(r"RAISERROR\s*\(", sql_text, re.IGNORECASE):
        error_patterns.append("custom_error_messages")
    
    # Error logging
    if re.search(r'sp_sys_log|log_error', sql_text, re.IGNORECASE):
        error_patterns.append("error_logging")
    
    patterns["error_handling_patterns"].extend(error_patterns)

def extract_conditional_patterns(sql_text, patterns):
    """Extract conditional logic patterns."""
    conditional_patterns = []
    
    # Parameter existence checks
    if re.search(r'IF\s+@\w+\s+IS\s+NOT\s+NULL', sql_text, re.IGNORECASE):
        conditional_patterns.append("parameter_existence_check")
    
    # Permission checks
    if re.search(r'HasRole|CheckPermission', sql_text, re.IGNORECASE):
        conditional_patterns.append("permission_validation")
    
    # Data validation
    if re.search(r'IF\s+LEN\s*\(', sql_text, re.IGNORECASE):
        conditional_patterns.append("string_length_validation")
    
    patterns["conditional_logic_patterns"].extend(conditional_patterns)

def extract_variable_naming_patterns(sql_text, patterns):
    """Extract variable naming conventions."""
    variables = re.findall(r'@(\w+)', sql_text)
    
    for var in variables:
        # Categorize variable types
        if var.lower() in ['card_id', 'id', 'user_id', 'parent_id']:
            patterns["variable_naming_conventions"]["id_variables"] = patterns["variable_naming_conventions"].get("id_variables", [])
            patterns["variable_naming_conventions"]["id_variables"].append(f"@{var}")
        elif var.lower().endswith('_name'):
            patterns["variable_naming_conventions"]["name_variables"] = patterns["variable_naming_conventions"].get("name_variables", [])
            patterns["variable_naming_conventions"]["name_variables"].append(f"@{var}")
        elif var.lower().startswith('is_'):
            patterns["variable_naming_conventions"]["boolean_variables"] = patterns["variable_naming_conventions"].get("boolean_variables", [])
            patterns["variable_naming_conventions"]["boolean_variables"].append(f"@{var}")

def extract_business_logic_patterns(sql_text, patterns, script_info):
    """Extract business logic patterns and use cases."""
    logic_patterns = []
    
    # Determine business context from script name/content
    script_name = script_info.get('action_name', '').lower()
    
    if any(word in script_name for word in ['create', 'add', 'insert']):
        logic_patterns.append("creation_workflow")
    elif any(word in script_name for word in ['update', 'modify', 'edit']):
        logic_patterns.append("update_workflow")
    elif any(word in script_name for word in ['delete', 'remove']):
        logic_patterns.append("deletion_workflow")
    elif any(word in script_name for word in ['list', 'get', 'fetch', 'search']):
        logic_patterns.append("retrieval_workflow")
    
    # Look for validation patterns
    if re.search(r'sp_api_validate|IsEmpty|HasRole', sql_text, re.IGNORECASE):
        logic_patterns.append("validation_heavy")
    
    # Look for audit/logging patterns
    if re.search(r'sp_sys_log|audit|log_action', sql_text, re.IGNORECASE):
        logic_patterns.append("audit_enabled")

    patterns["business_logic_patterns"].extend(logic_patterns)

def normalize_patterns(patterns, procedure_relationships=None):
    """Clean and normalize extracted patterns."""
    # Remove duplicates and sort
    for key in patterns:
        if isinstance(patterns[key], list):
            # Handle lists of primitives
            try:
                patterns[key] = list(set(patterns[key]))
            except TypeError:
                # If list contains unhashable types, keep original
                pass
        elif isinstance(patterns[key], dict):
            # Handle nested dictionaries
            for subkey in patterns[key]:
                if isinstance(patterns[key][subkey], list):
                    try:
                        patterns[key][subkey] = list(set(patterns[key][subkey]))
                    except TypeError:
                        # If list contains unhashable types, keep original
                        pass
                elif isinstance(patterns[key][subkey], dict):
                    # Handle nested dictionaries
                    for subsubkey in patterns[key][subkey]:
                        if isinstance(patterns[key][subkey][subsubkey], list):
                            try:
                                patterns[key][subkey][subsubkey] = list(set(patterns[key][subkey][subsubkey]))
                            except TypeError:
                                # If list contains unhashable types, keep original
                                pass

def generate_all_training_materials(framework_api_details, script_patterns, relationships, args):
    """Generate all training materials in one coordinated effort."""
    # Generate comprehensive training materials
    print("\nFRAMEWORK_TRAINING: Generating comprehensive training materials...")
    
    # Get clusters of related procedures
    clusters = relationships.get("relationship_summary", {}).get("procedure_clusters", [])
    
    # Get common workflows
    workflows = relationships.get("common_workflows", [])
    
    # Get error patterns
    error_patterns = relationships.get("error_patterns", [])
    
    # Generate examples based on patterns and relationships
    examples = []
    
    # Generate simple examples
    print("  Generating simple examples...")
    examples.extend(generate_simple_examples(framework_api_details, script_patterns, args.get("num_examples", 10)))
    
    # Generate validation examples
    print("  Generating validation examples...")
    examples.extend(generate_validation_examples(framework_api_details, script_patterns, args.get("num_examples", 5)))
    
    # Generate CRUD examples
    print("  Generating CRUD examples...")
    examples.extend(generate_crud_examples(framework_api_details, script_patterns, args.get("num_examples", 5)))
    
    # Generate error handling examples
    print("  Generating error handling examples...")
    examples.extend(generate_error_handling_examples(framework_api_details, script_patterns, args.get("num_examples", 5)))
    
    # Generate multi-procedure examples using relationships
    print("  Generating multi-procedure examples...")
    if clusters:
        for cluster in clusters[:3]:  # Generate examples for top 3 clusters
            examples.extend(generate_multi_procedure_examples(
                framework_api_details,
                script_patterns,
                relationships,
                cluster,
                args.get("num_examples", 3)
            ))
    
    # Generate advanced examples
    print("  Generating advanced examples...")
    examples.extend(generate_advanced_examples(framework_api_details, script_patterns, relationships, args.get("num_examples", 5)))
    
    # Add metadata
    metadata = {
        "generation_date": datetime.now().isoformat(),
        "total_examples": len(examples),
        "example_types": {
            "simple": len([example for example in examples if example.get("example_type") == "simple_single_procedure"]),
            "validation": len([example for example in examples if example.get("example_type") == "validation_focused"]),
            "crud": len([example for example in examples if example.get("example_type", "").startswith("crud_")]),
            "error_handling": len([example for example in examples if example.get("example_type") == "error_handling_focused"]),
            "multi_procedure": len([example for example in examples if example.get("example_type") == "multi_procedure_workflow"]),
            "advanced": len([example for example in examples if example.get("example_type", "").startswith("advanced_")])
        },
        "patterns_used": {
            "procedure_clusters": len(clusters),
            "workflows": len(workflows),
            "error_patterns": len(error_patterns)
        }
    }
    
    return {"examples": examples, "metadata": metadata}

def generate_simple_examples(framework_api_details, script_patterns, count):
    """Generate simple examples for each procedure."""
    examples = []
    procedures = [obj for obj in framework_api_details if obj.get('object_type_short') == 'P']
    
    for i in range(count):
        if not procedures:
            break
            
        proc = random.choice(procedures)
        proc_name = f"{proc['schema_name']}.{proc['object_name']}"
        
        # Create a simple use case
        use_case = generate_use_case_description(proc)
        
        # Generate the script
        script = generate_simple_script(proc, script_patterns)
        
        examples.append({
            "example_type": "simple_single_procedure",
            "use_case": use_case,
            "procedures_used": [proc_name],
            "sql_script": script,
            "learning_objectives": [
                f"Learn basic usage of {proc['object_name']}",
                "Understand parameter passing",
                "See proper variable declaration"
            ],
            "complexity_level": "beginner",
            "estimated_lines": len(script.split('\n'))
        })
    
    return examples

def generate_validation_examples(framework_api_details, script_patterns, count):
    """Generate examples focused on validation patterns."""
    examples = []
    procedures = [obj for obj in framework_api_details if obj.get('object_type_short') == 'P']
    
    for i in range(count):
        if not procedures:
            break
            
        proc = random.choice(procedures)
        proc_name = f"{proc['schema_name']}.{proc['object_name']}"
        
        script = generate_validation_script(proc, script_patterns)
        
        examples.append({
            "example_type": "validation_focused",
            "use_case": f"Validate input parameters before calling {proc['object_name']} with proper error handling",
            "procedures_used": [proc_name],
            "sql_script": script,
            "learning_objectives": [
                "Learn parameter validation techniques",
                "Understand error handling patterns",
                "See defensive programming practices"
            ],
            "complexity_level": "intermediate",
            "estimated_lines": len(script.split('\n'))
        })
    
    return examples

def generate_crud_examples(framework_api_details, script_patterns, count):
    """Generate CRUD workflow examples."""
    examples = []
    
    crud_patterns = {
        "create": ["create", "add", "insert", "new"],
        "read": ["get", "fetch", "list", "search", "find"],
        "update": ["update", "modify", "edit", "change"],
        "delete": ["delete", "remove", "drop"]
    }
    
    for i in range(count):
        operation = random.choice(list(crud_patterns.keys()))
        keywords = crud_patterns[operation]
        
        # Find procedures that match this operation
        matching_procs = []
        for obj in framework_api_details:
            if obj.get('object_type_short') == 'P':
                proc_name = obj['object_name'].lower()
                if any(keyword in proc_name for keyword in keywords):
                    matching_procs.append(obj)
        
        if matching_procs:
            proc = random.choice(matching_procs)
            script = generate_crud_script(proc, operation, script_patterns)
            
            examples.append({
                "example_type": f"crud_{operation}",
                "use_case": f"Perform {operation} operation using {proc['object_name']} with proper workflow",
                "procedures_used": [f"{proc['schema_name']}.{proc['object_name']}"],
                "sql_script": script,
                "learning_objectives": [
                    f"Learn {operation.upper()} operation patterns",
                    "Understand workflow best practices",
                    "See real-world usage scenarios"
                ],
                "complexity_level": "intermediate",
                "estimated_lines": len(script.split('\n'))
            })
    
    return examples

def generate_error_handling_examples(framework_api_details, script_patterns, count):
    """Generate examples with robust error handling."""
    examples = []
    procedures = [obj for obj in framework_api_details if obj.get('object_type_short') == 'P']
    
    for i in range(count):
        if not procedures:
            break
            
        proc = random.choice(procedures)
        script = generate_error_handling_script(proc, script_patterns)
        
        examples.append({
            "example_type": "error_handling_focused",
            "use_case": f"Call {proc['object_name']} with comprehensive error handling and recovery",
            "procedures_used": [f"{proc['schema_name']}.{proc['object_name']}"],
            "sql_script": script,
            "learning_objectives": [
                "Learn TRY-CATCH error handling",
                "Understand error logging patterns",
                "See graceful error recovery"
            ],
            "complexity_level": "advanced",
            "estimated_lines": len(script.split('\n'))
        })
    
    return examples

def generate_multi_procedure_examples(framework_api_details, script_patterns, relationships, count):
    """Generate examples using multiple related procedures."""
    examples = []
    
    # Get procedure relationships
    proc_relationships = relationships.get("procedure_relationships", {})
    
    for i in range(count):
        # Pick a procedure with relationships
        proc_with_relations = [
            (proc_name, data) for proc_name, data in proc_relationships.items()
            if data.get("total_relationships", 0) > 0
        ]
        
        if not proc_with_relations:
            continue
            
        main_proc_name, main_proc_data = random.choice(proc_with_relations)
        related_procs = list(main_proc_data["related_procedures"].keys())
        
        # Select 1-3 related procedures
        selected_related = random.sample(related_procs, min(3, len(related_procs)))
        all_procs = [main_proc_name] + selected_related
        
        script = generate_multi_procedure_script(all_procs, framework_api_details, script_patterns)
        
        examples.append({
            "example_type": "multi_procedure_workflow",
            "use_case": f"Complex workflow using {len(all_procs)} related procedures for complete business process",
            "procedures_used": all_procs,
            "sql_script": script,
            "learning_objectives": [
                "Learn procedure orchestration",
                "Understand workflow patterns",
                "See procedure relationships in action"
            ],
            "complexity_level": "advanced",
            "estimated_lines": len(script.split('\n'))
        })
    
    return examples

def generate_advanced_examples(framework_api_details, script_patterns, relationships, count):
    """Generate advanced examples with complex business logic."""
    examples = []
    
    for i in range(count):
        # Create complex scenarios
        scenario_types = [
            "conditional_workflow",
            "batch_processing",
            "transaction_management",
            "dynamic_execution"
        ]
        
        scenario = random.choice(scenario_types)
        script = generate_advanced_scenario_script(scenario, framework_api_details, script_patterns)
        
        examples.append({
            "example_type": f"advanced_{scenario}",
            "use_case": f"Advanced {scenario.replace('_', ' ')} pattern with multiple procedures and complex logic",
            "procedures_used": extract_procedures_from_script(script),
            "sql_script": script,
            "learning_objectives": [
                f"Master {scenario.replace('_', ' ')} patterns",
                "Understand advanced TSQL techniques",
                "See enterprise-level implementations"
            ],
            "complexity_level": "expert",
            "estimated_lines": len(script.split('\n'))
        })
    
    return examples

def generate_use_case_description(proc):
    """Generate a realistic use case description for a procedure."""
    proc_name = proc['object_name'].lower()
    
    if 'create' in proc_name or 'add' in proc_name:
        return f"Create a new record using {proc['object_name']} with all required parameters"
    elif 'update' in proc_name or 'modify' in proc_name:
        return f"Update existing data using {proc['object_name']} with validation"
    elif 'delete' in proc_name or 'remove' in proc_name:
        return f"Safely delete data using {proc['object_name']} with proper checks"
    elif 'get' in proc_name or 'fetch' in proc_name or 'list' in proc_name:
        return f"Retrieve data using {proc['object_name']} with optional filtering"
    else:
        return f"Execute {proc['object_name']} for business operation"

def generate_simple_script(proc, patterns):
    """Generate a simple script for a single procedure."""
    script_lines = []
    
    # Add comment header
    script_lines.append(f"-- Simple usage example for {proc['object_name']}")
    script_lines.append("")
    
    # Declare variables based on parameters
    required_params = [p for p in proc.get('parameters', []) 
                      if not p.get('has_default', False) and p.get('name') != '[Return Value]']
    
    if required_params:
        script_lines.append("-- Declare required parameters")
        for param in required_params:
            param_name = param['name']
            param_type = param.get('type_from_sys', 'nvarchar(255)')
            sample_value = generate_sample_value(param_name, param_type)
            script_lines.append(f"DECLARE {param_name} {param_type} = {sample_value};")
        script_lines.append("")
    
    # Add the procedure call
    script_lines.append(f"-- Execute the procedure")
    exec_line = f"EXEC {proc['schema_name']}.{proc['object_name']}"
    
    if required_params:
        param_assignments = [f"{p['name']} = {p['name']}" for p in required_params]
        exec_line += " " + ", ".join(param_assignments)
    
    script_lines.append(exec_line + ";")
    
    return "\n".join(script_lines)

def generate_validation_script(proc, patterns):
    """Generate a script with validation patterns."""
    script_lines = []
    
    script_lines.append(f"-- Validation example for {proc['object_name']}")
    script_lines.append("")
    
    # Parameters
    params = [p for p in proc.get('parameters', []) if p.get('name') != '[Return Value]']
    required_params = [p for p in params if not p.get('has_default', False)]
    
    if params:
        script_lines.append("-- Declare and initialize parameters")
        for param in params:
            param_name = param['name']
            param_type = param.get('type_from_sys', 'nvarchar(255)')
            sample_value = generate_sample_value(param_name, param_type)
            script_lines.append(f"DECLARE {param_name} {param_type} = {sample_value};")
        script_lines.append("")
    
    # Add validation
    if required_params:
        script_lines.append("-- Validate required parameters")
        for param in required_params:
            param_name = param['name']
            script_lines.append(f"IF {param_name} IS NULL")
            script_lines.append("BEGIN")
            script_lines.append(f"    RAISERROR('Parameter {param_name} is required', 16, 1);")
            script_lines.append("    RETURN;")
            script_lines.append("END;")
        script_lines.append("")
    
    # Add TRY-CATCH
    script_lines.append("-- Execute with error handling")
    script_lines.append("BEGIN TRY")
    script_lines.append(f"    EXEC {proc['schema_name']}.{proc['object_name']}")
    
    if params:
        param_assignments = [f"{p['name']} = {p['name']}" for p in params[:3]]  # Limit for readability
        script_lines.append("        " + ", ".join(param_assignments) + ";")
    else:
        script_lines[-1] += ";"
    
    script_lines.append("END TRY")
    script_lines.append("BEGIN CATCH")
    script_lines.append("    PRINT 'Error occurred: ' + ERROR_MESSAGE();")
    script_lines.append("    THROW;")
    script_lines.append("END CATCH;")
    
    return "\n".join(script_lines)

def generate_crud_script(proc, operation, patterns):
    """Generate a CRUD-specific script."""
    script_lines = []
    
    script_lines.append(f"-- {operation.upper()} operation using {proc['object_name']}")
    script_lines.append("")
    
    # Add context variables commonly used in the framework
    script_lines.append("-- Common context variables")
    script_lines.append("DECLARE @user_id int = @user_id; -- From context")
    script_lines.append("DECLARE @card_id int = @card_id; -- From context")
    script_lines.append("")
    
    # Operation-specific logic
    if operation == "create":
        script_lines.extend(generate_create_pattern(proc))
    elif operation == "read":
        script_lines.extend(generate_read_pattern(proc))
    elif operation == "update":
        script_lines.extend(generate_update_pattern(proc))
    elif operation == "delete":
        script_lines.extend(generate_delete_pattern(proc))
    
    return "\n".join(script_lines)

def generate_create_pattern(proc):
    """Generate creation workflow pattern."""
    lines = []
    
    lines.append("-- Validation before creation")
    lines.append("IF @user_id IS NULL")
    lines.append("BEGIN")
    lines.append("    RAISERROR('User context required for creation', 16, 1);")
    lines.append("    RETURN;")
    lines.append("END;")
    lines.append("")
    
    lines.append("-- Create new record")
    lines.append("BEGIN TRY")
    lines.append(f"    EXEC {proc['schema_name']}.{proc['object_name']}")
    
    # Add sample parameters
    params = [p for p in proc.get('parameters', []) if p.get('name') != '[Return Value]']
    if params:
        sample_params = []
        for param in params[:4]:  # Limit for readability
            param_name = param['name']
            if 'user_id' in param_name.lower():
                sample_params.append(f"{param_name} = @user_id")
            elif 'id' in param_name.lower() and param_name != '@user_id':
                sample_params.append(f"{param_name} = @card_id")
            else:
                sample_value = generate_sample_value(param_name, param.get('type_from_sys', 'nvarchar(255)'))
                sample_params.append(f"{param_name} = {sample_value}")
        
        lines.append("        " + ", ".join(sample_params) + ";")
    else:
        lines[-1] += ";"
    
    lines.append("")
    lines.append("    PRINT 'Record created successfully';")
    lines.append("END TRY")
    lines.append("BEGIN CATCH")
    lines.append("    PRINT 'Creation failed: ' + ERROR_MESSAGE();")
    lines.append("    THROW;")
    lines.append("END CATCH;")
    
    return lines

def generate_read_pattern(proc):
    """Generate read/retrieval workflow pattern."""
    lines = []
    
    lines.append("-- Prepare search parameters")
    lines.append("DECLARE @search_criteria nvarchar(255) = 'example search';")
    lines.append("DECLARE @page_size int = 20;")
    lines.append("DECLARE @page_number int = 1;")
    lines.append("")
    
    lines.append("-- Execute search/retrieval")
    lines.append(f"EXEC {proc['schema_name']}.{proc['object_name']}")
    
    # Add sample parameters for search
    params = [p for p in proc.get('parameters', []) if p.get('name') != '[Return Value]']
    if params:
        sample_params = []
        for param in params[:3]:
            param_name = param['name']
            if 'search' in param_name.lower() or 'criteria' in param_name.lower():
                sample_params.append(f"{param_name} = @search_criteria")
            elif 'page' in param_name.lower() and 'size' in param_name.lower():
                sample_params.append(f"{param_name} = @page_size")
            elif 'page' in param_name.lower():
                sample_params.append(f"{param_name} = @page_number")
            elif 'user_id' in param_name.lower():
                sample_params.append(f"{param_name} = @user_id")
            else:
                sample_value = generate_sample_value(param_name, param.get('type_from_sys', 'nvarchar(255)'))
                sample_params.append(f"{param_name} = {sample_value}")
        
        lines.append("    " + ", ".join(sample_params) + ";")
    else:
        lines[-1] += ";"
    
    lines.append("")
    lines.append("-- Check if results were found")
    lines.append("IF @@ROWCOUNT > 0")
    lines.append("    PRINT 'Data retrieved successfully';")
    lines.append("ELSE")
    lines.append("    PRINT 'No data found matching criteria';")
    
    return lines

def generate_update_pattern(proc):
    """Generate update workflow pattern."""
    lines = []
    
    lines.append("-- Validate record exists and user has permission")
    lines.append("IF @card_id IS NULL")
    lines.append("BEGIN")
    lines.append("    RAISERROR('Record ID required for update', 16, 1);")
    lines.append("    RETURN;")
    lines.append("END;")
    lines.append("")
    
    lines.append("-- Check if record exists")
    lines.append("DECLARE @record_exists bit = 0;")
    lines.append("-- Add existence check logic here")
    lines.append("")
    
    lines.append("-- Perform update with optimistic concurrency")
    lines.append("BEGIN TRY")
    lines.append(f"    EXEC {proc['schema_name']}.{proc['object_name']}")
    
    # Add sample parameters for update
    params = [p for p in proc.get('parameters', []) if p.get('name') != '[Return Value]']
    if params:
        sample_params = []
        for param in params[:4]:
            param_name = param['name']
            if 'id' in param_name.lower():
                sample_params.append(f"{param_name} = @card_id")
            elif 'user_id' in param_name.lower():
                sample_params.append(f"{param_name} = @user_id")
            elif 'modified' in param_name.lower() or 'updated' in param_name.lower():
                sample_params.append(f"{param_name} = GETDATE()")
            else:
                sample_value = generate_sample_value(param_name, param.get('type_from_sys', 'nvarchar(255)'))
                sample_params.append(f"{param_name} = {sample_value}")
        
        lines.append("        " + ", ".join(sample_params) + ";")
    else:
        lines[-1] += ";"
    
    lines.append("")
    lines.append("    IF @@ROWCOUNT = 0")
    lines.append("        RAISERROR('No records were updated. Record may not exist or may have been modified by another user.', 16, 1);")
    lines.append("    ELSE")
    lines.append("        PRINT 'Record updated successfully';")
    lines.append("")
    lines.append("END TRY")
    lines.append("BEGIN CATCH")
    lines.append("    PRINT 'Update failed: ' + ERROR_MESSAGE();")
    lines.append("    THROW;")
    lines.append("END CATCH;")
    
    return lines

def generate_delete_pattern(proc):
    """Generate delete workflow pattern."""
    lines = []
    
    lines.append("-- Safety checks before deletion")
    lines.append("IF @card_id IS NULL")
    lines.append("BEGIN")
    lines.append("    RAISERROR('Record ID required for deletion', 16, 1);")
    lines.append("    RETURN;")
    lines.append("END;")
    lines.append("")
    
    lines.append("-- Check for dependencies")
    lines.append("DECLARE @has_dependencies bit = 0;")
    lines.append("-- Add dependency check logic here")
    lines.append("")
    lines.append("IF @has_dependencies = 1")
    lines.append("BEGIN")
    lines.append("    RAISERROR('Cannot delete record with existing dependencies', 16, 1);")
    lines.append("    RETURN;")
    lines.append("END;")
    lines.append("")
    
    lines.append("-- Perform soft delete (preferred) or hard delete")
    lines.append("BEGIN TRY")
    lines.append(f"    EXEC {proc['schema_name']}.{proc['object_name']}")
    lines.append("        @id = @card_id,")
    lines.append("        @deleted_by = @user_id;")
    lines.append("")
    lines.append("    IF @@ROWCOUNT = 0")
    lines.append("        PRINT 'No record found to delete';")
    lines.append("    ELSE")
    lines.append("        PRINT 'Record deleted successfully';")
    lines.append("")
    lines.append("END TRY")
    lines.append("BEGIN CATCH")
    lines.append("    PRINT 'Deletion failed: ' + ERROR_MESSAGE();")
    lines.append("    THROW;")
    lines.append("END CATCH;")
    
    return lines

def generate_error_handling_script(proc, patterns):
    """Generate comprehensive error handling script."""
    script_lines = []
    
    script_lines.append(f"-- Comprehensive error handling example for {proc['object_name']}")
    script_lines.append("")
    
    script_lines.append("-- Error handling variables")
    script_lines.append("DECLARE @error_number int;")
    script_lines.append("DECLARE @error_message nvarchar(4000);")
    script_lines.append("DECLARE @error_severity int;")
    script_lines.append("DECLARE @error_state int;")
    script_lines.append("")
    
    # Add procedure parameters
    params = [p for p in proc.get('parameters', []) if p.get('name') != '[Return Value]']
    if params:
        script_lines.append("-- Procedure parameters")
        for param in params[:3]:
            param_name = param['name']
            param_type = param.get('type_from_sys', 'nvarchar(255)')
            sample_value = generate_sample_value(param_name, param_type)
            script_lines.append(f"DECLARE {param_name} {param_type} = {sample_value};")
        script_lines.append("")
    
    script_lines.append("-- Main execution with comprehensive error handling")
    script_lines.append("BEGIN TRY")
    script_lines.append("    -- Pre-execution validation")
    script_lines.append("    IF @user_id IS NULL")
    script_lines.append("        THROW 50001, 'User context is required', 1;")
    script_lines.append("")
    script_lines.append("    -- Execute the procedure")
    script_lines.append(f"    EXEC {proc['schema_name']}.{proc['object_name']}")
    
    if params:
        param_assignments = [f"{p['name']} = {p['name']}" for p in params[:3]]
        script_lines.append("        " + ", ".join(param_assignments) + ";")
    else:
        script_lines[-1] += ";"
    
    script_lines.append("")
    script_lines.append("    -- Success handling")
    script_lines.append("    PRINT 'Operation completed successfully';")
    script_lines.append("")
    script_lines.append("END TRY")
    script_lines.append("BEGIN CATCH")
    script_lines.append("    -- Capture error details")
    script_lines.append("    SELECT")
    script_lines.append("        @error_number = ERROR_NUMBER(),")
    script_lines.append("        @error_message = ERROR_MESSAGE(),")
    script_lines.append("        @error_severity = ERROR_SEVERITY(),")
    script_lines.append("        @error_state = ERROR_STATE();")
    script_lines.append("")
    script_lines.append("    -- Log the error (if logging procedure exists)")
    script_lines.append("    -- EXEC sp_sys_log_error @error_message, @error_number;")
    script_lines.append("")
    script_lines.append("    -- Handle different types of errors")
    script_lines.append("    IF @error_number = 2 -- File not found")
    script_lines.append("        PRINT 'Resource not found: ' + @error_message;")
    script_lines.append("    ELSE IF @error_number BETWEEN 50000 AND 59999 -- Custom errors")
    script_lines.append("        PRINT 'Business logic error: ' + @error_message;")
    script_lines.append("    ELSE")
    script_lines.append("        PRINT 'System error occurred: ' + @error_message;")
    script_lines.append("")
    script_lines.append("    -- Re-throw the error for upstream handling")
    script_lines.append("    THROW;")
    script_lines.append("END CATCH;")
    
    return "\n".join(script_lines)

def generate_multi_procedure_script(proc_names, framework_api_details, patterns):
    """Generate script using multiple related procedures."""
    script_lines = []
    
    script_lines.append(f"-- Multi-procedure workflow using {len(proc_names)} related procedures")
    script_lines.append(f"-- Procedures: {', '.join([name.split('.')[-1] for name in proc_names])}")
    script_lines.append("")
    
    script_lines.append("-- Common context and workflow variables")
    script_lines.append("DECLARE @user_id int = @user_id; -- From context")
    script_lines.append("DECLARE @card_id int = @card_id; -- From context")
    script_lines.append("DECLARE @workflow_success bit = 1;")
    script_lines.append("DECLARE @step_result int;")
    script_lines.append("")
    
    script_lines.append("-- Begin transaction for data consistency")
    script_lines.append("BEGIN TRANSACTION;")
    script_lines.append("")
    script_lines.append("BEGIN TRY")
    
    # Generate calls for each procedure
    for i, proc_name in enumerate(proc_names[:4], 1):  # Limit to 4 for readability
        proc_obj = next(
            (obj for obj in framework_api_details 
             if f"{obj['schema_name']}.{obj['object_name']}" == proc_name),
            None
        )
        
        if proc_obj:
            script_lines.append("")
            script_lines.append(f"    -- Step {i}: {proc_obj['object_name']}")
            script_lines.append(f"    EXEC {proc_name}")
            
            # Add relevant parameters
            params = [p for p in proc_obj.get('parameters', []) if p.get('name') != '[Return Value]']
            if params:
                sample_params = []
                for param in params[:3]:
                    param_name = param['name']
                    if 'user_id' in param_name.lower():
                        sample_params.append(f"{param_name} = @user_id")
                    elif 'id' in param_name.lower() and 'user_id' not in param_name.lower():
                        sample_params.append(f"{param_name} = @card_id")
                    else:
                        sample_value = generate_sample_value(param_name, param.get('type_from_sys', 'nvarchar(255)'))
                        sample_params.append(f"{param_name} = {sample_value}")
                
                script_lines.append("        " + ", ".join(sample_params) + ";")
            else:
                script_lines[-1] += ";"
            
            script_lines.append(f"    ")
            script_lines.append(f"    -- Verify step {i} success")
            script_lines.append("    IF @@ROWCOUNT = 0")
            script_lines.append("    BEGIN")
            script_lines.append(f"        SET @workflow_success = 0;")
            script_lines.append(f"        RAISERROR('Step {i} failed - no rows affected', 16, 1);")
            script_lines.append("    END;")
    
    script_lines.append("")
    script_lines.append("    -- All steps completed successfully")
    script_lines.append("    COMMIT TRANSACTION;")
    script_lines.append("    PRINT 'Multi-procedure workflow completed successfully';")
    script_lines.append("")
    script_lines.append("END TRY")
    script_lines.append("BEGIN CATCH")
    script_lines.append("    -- Rollback on any error")
    script_lines.append("    IF @@TRANCOUNT > 0")
    script_lines.append("        ROLLBACK TRANSACTION;")
    script_lines.append("")
    script_lines.append("    PRINT 'Workflow failed: ' + ERROR_MESSAGE();")
    script_lines.append("    THROW;")
    script_lines.append("END CATCH;")
    
    return "\n".join(script_lines)

def generate_advanced_scenario_script(scenario, framework_api_details, patterns):
    """Generate advanced scenario scripts."""
    script_lines = []
    
    if scenario == "conditional_workflow":
        script_lines.extend(generate_conditional_workflow(framework_api_details))
    elif scenario == "batch_processing":
        script_lines.extend(generate_batch_processing(framework_api_details))
    elif scenario == "transaction_management":
        script_lines.extend(generate_transaction_management(framework_api_details))
    elif scenario == "dynamic_execution":
        script_lines.extend(generate_dynamic_execution(framework_api_details))
    
    return "\n".join(script_lines)

def generate_conditional_workflow(framework_api_details):
    """Generate conditional workflow pattern."""
    lines = []
    
    lines.append("-- Advanced conditional workflow with multiple decision points")
    lines.append("")
    lines.append("-- Workflow parameters")
    lines.append("DECLARE @user_role nvarchar(50) = 'Admin'; -- From user context")
    lines.append("DECLARE @operation_type nvarchar(50) = @operation_type;")
    lines.append("DECLARE @data_size int = 100;")
    lines.append("DECLARE @batch_mode bit = 0;")
    lines.append("")
    lines.append("-- Determine workflow path based on conditions")
    lines.append("IF @user_role = 'Admin' AND @data_size > 1000")
    lines.append("BEGIN")
    lines.append("    PRINT 'Admin bulk operation detected - using optimized path';")
    lines.append("    SET @batch_mode = 1;")
    lines.append("END")
    lines.append("ELSE IF @user_role IN ('Manager', 'Supervisor')")
    lines.append("BEGIN")
    lines.append("    PRINT 'Manager operation - standard validation path';")
    lines.append("    -- Add manager-specific validation")
    lines.append("END")
    lines.append("ELSE")
    lines.append("BEGIN")
    lines.append("    PRINT 'Standard user operation - full validation required';")
    lines.append("    -- Add comprehensive validation")
    lines.append("END;")
    lines.append("")
    lines.append("-- Execute based on determined path")
    lines.append("IF @batch_mode = 1")
    lines.append("BEGIN")
    lines.append("    -- Batch processing logic")
    lines.append("    PRINT 'Executing batch workflow';")
    lines.append("END")
    lines.append("ELSE")
    lines.append("BEGIN")
    lines.append("    -- Individual processing logic")
    lines.append("    PRINT 'Executing individual item workflow';")
    lines.append("END;")
    
    return lines

def generate_batch_processing(framework_api_details):
    """Generate batch processing pattern."""
    lines = []
    
    lines.append("-- Batch processing pattern with cursor and error handling")
    lines.append("")
    lines.append("-- Batch configuration")
    lines.append("DECLARE @batch_size int = 100;")
    lines.append("DECLARE @total_processed int = 0;")
    lines.append("DECLARE @error_count int = 0;")
    lines.append("DECLARE @current_batch_start int = 1;")
    lines.append("")
    lines.append("-- Temporary table for batch items")
    lines.append("CREATE TABLE #batch_items (")
    lines.append("    id int IDENTITY(1,1),")
    lines.append("    item_id int,")
    lines.append("    item_data nvarchar(255),")
    lines.append("    processed bit DEFAULT 0,")
    lines.append("    error_message nvarchar(1000) NULL")
    lines.append(");")
    lines.append("")
    lines.append("-- Populate batch items (example data)")
    lines.append("INSERT INTO #batch_items (item_id, item_data)")
    lines.append("SELECT id, 'Sample data ' + CAST(id AS nvarchar)")
    lines.append("FROM (VALUES (1),(2),(3),(4),(5)) AS v(id);")
    lines.append("")
    lines.append("-- Process batches")
    lines.append("WHILE EXISTS (SELECT 1 FROM #batch_items WHERE processed = 0)")
    lines.append("BEGIN")
    lines.append("    DECLARE @current_item_id int;")
    lines.append("    DECLARE @current_item_data nvarchar(255);")
    lines.append("    ")
    lines.append("    -- Get next unprocessed item")
    lines.append("    SELECT TOP 1 @current_item_id = item_id, @current_item_data = item_data")
    lines.append("    FROM #batch_items")
    lines.append("    WHERE processed = 0")
    lines.append("    ORDER BY id;")
    lines.append("    ")
    lines.append("    BEGIN TRY")
    lines.append("        -- Process individual item")
    lines.append("        -- EXEC dbo.sp_process_item @current_item_id, @current_item_data;")
    lines.append("        ")
    lines.append("        -- Mark as processed")
    lines.append("        UPDATE #batch_items SET processed = 1")
    lines.append("        WHERE item_id = @current_item_id;")
    lines.append("        ")
    lines.append("        SET @total_processed = @total_processed + 1;")
    lines.append("    END TRY")
    lines.append("    BEGIN CATCH")
    lines.append("        -- Log error and continue")
    lines.append("        UPDATE #batch_items")
    lines.append("        SET processed = 1, error_message = ERROR_MESSAGE()")
    lines.append("        WHERE item_id = @current_item_id;")
    lines.append("        ")
    lines.append("        SET @error_count = @error_count + 1;")
    lines.append("    END CATCH;")
    lines.append("END;")
    lines.append("")
    lines.append("-- Report results")
    lines.append("PRINT 'Batch processing completed';")
    lines.append("PRINT 'Total processed: ' + CAST(@total_processed AS nvarchar);")
    lines.append("PRINT 'Errors encountered: ' + CAST(@error_count AS nvarchar);")
    lines.append("")
    lines.append("-- Cleanup")
    lines.append("DROP TABLE #batch_items;")
    
    return lines

def generate_transaction_management(framework_api_details):
    """Generate transaction management pattern."""
    lines = []
    
    lines.append("-- Advanced transaction management with savepoints")
    lines.append("")
    lines.append("-- Transaction variables")
    lines.append("DECLARE @savepoint_name nvarchar(50) = 'step_savepoint';")
    lines.append("DECLARE @transaction_started bit = 0;")
    lines.append("")
    lines.append("-- Start main transaction")
    lines.append("BEGIN TRANSACTION main_transaction;")
    lines.append("SET @transaction_started = 1;")
    lines.append("")
    lines.append("BEGIN TRY")
    lines.append("    -- Step 1: Primary operation")
    lines.append("    PRINT 'Executing step 1 - Primary operation';")
    lines.append("    -- EXEC dbo.sp_primary_operation @param1, @param2;")
    lines.append("    ")
    lines.append("    -- Create savepoint before risky operation")
    lines.append("    SAVE TRANSACTION step1_savepoint;")
    lines.append("    ")
    lines.append("    -- Step 2: Risky operation that might fail")
    lines.append("    PRINT 'Executing step 2 - Risky operation';")
    lines.append("    BEGIN TRY")
    lines.append("        -- EXEC dbo.sp_risky_operation @param3, @param4;")
    lines.append("        ")
    lines.append("        -- If successful, continue to step 3")
    lines.append("        PRINT 'Step 2 completed successfully';")
    lines.append("    END TRY")
    lines.append("    BEGIN CATCH")
    lines.append("        PRINT 'Step 2 failed, rolling back to savepoint';")
    lines.append("        ROLLBACK TRANSACTION step1_savepoint;")
    lines.append("        ")
    lines.append("        -- Continue with alternative step")
    lines.append("        PRINT 'Executing alternative step 2';")
    lines.append("        -- EXEC dbo.sp_alternative_operation @param3, @param4;")
    lines.append("    END CATCH;")
    lines.append("    ")
    lines.append("    -- Step 3: Finalization")
    lines.append("    PRINT 'Executing step 3 - Finalization';")
    lines.append("    -- EXEC dbo.sp_finalize_operation @result_param;")
    lines.append("    ")
    lines.append("    -- All steps completed successfully")
    lines.append("    COMMIT TRANSACTION main_transaction;")
    lines.append("    SET @transaction_started = 0;")
    lines.append("    PRINT 'All operations committed successfully';")
    lines.append("")
    lines.append("END TRY")
    lines.append("BEGIN CATCH")
    lines.append("    -- Handle major failure")
    lines.append("    IF @transaction_started = 1 AND @@TRANCOUNT > 0")
    lines.append("    BEGIN")
    lines.append("        ROLLBACK TRANSACTION main_transaction;")
    lines.append("        PRINT 'Transaction rolled back due to error: ' + ERROR_MESSAGE();")
    lines.append("    END;")
    lines.append("    ")
    lines.append("    THROW;")
    lines.append("END CATCH;")
    
    return lines

def generate_dynamic_execution(framework_api_details):
    """Generate dynamic execution pattern."""
    lines = []
    
    lines.append("-- Dynamic execution pattern with SQL generation")
    lines.append("")
    lines.append("-- Dynamic execution parameters")
    lines.append("DECLARE @table_name nvarchar(128) = 'users';")
    lines.append("DECLARE @filter_column nvarchar(128) = 'status';")
    lines.append("DECLARE @filter_value nvarchar(255) = 'active';")
    lines.append("DECLARE @operation_type nvarchar(50) = 'select';")
    lines.append("DECLARE @dynamic_sql nvarchar(max);")
    lines.append("DECLARE @param_definition nvarchar(500);")
    lines.append("")
    lines.append("-- Validate inputs to prevent SQL injection")
    lines.append("IF @table_name NOT IN ('users', 'products', 'orders')")
    lines.append("BEGIN")
    lines.append("    RAISERROR('Invalid table name specified', 16, 1);")
    lines.append("    RETURN;")
    lines.append("END;")
    lines.append("")
    lines.append("IF @filter_column NOT IN ('status', 'type', 'category')")
    lines.append("BEGIN")
    lines.append("    RAISERROR('Invalid filter column specified', 16, 1);")
    lines.append("    RETURN;")
    lines.append("END;")
    lines.append("")
    lines.append("-- Build dynamic SQL based on operation type")
    lines.append("IF @operation_type = 'select'")
    lines.append("BEGIN")
    lines.append("    SET @dynamic_sql = N'SELECT * FROM ' + QUOTENAME(@table_name) +")
    lines.append("                       N' WHERE ' + QUOTENAME(@filter_column) + N' = @filter_value_param';")
    lines.append("    SET @param_definition = N'@filter_value_param nvarchar(255)';")
    lines.append("END")
    lines.append("ELSE IF @operation_type = 'count'")
    lines.append("BEGIN")
    lines.append("    SET @dynamic_sql = N'SELECT COUNT(*) as record_count FROM ' + QUOTENAME(@table_name) +")
    lines.append("                       N' WHERE ' + QUOTENAME(@filter_column) + N' = @filter_value_param';")
    lines.append("    SET @param_definition = N'@filter_value_param nvarchar(255)';")
    lines.append("END")
    lines.append("ELSE")
    lines.append("BEGIN")
    lines.append("    RAISERROR('Unsupported operation type', 16, 1);")
    lines.append("    RETURN;")
    lines.append("END;")
    lines.append("")
    lines.append("-- Execute dynamic SQL safely")
    lines.append("BEGIN TRY")
    lines.append("    PRINT 'Executing: ' + @dynamic_sql;")
    lines.append("    PRINT 'Parameters: @filter_value_param = ' + @filter_value;")
    lines.append("    ")
    lines.append("    EXEC sp_executesql")
    lines.append("        @dynamic_sql,")
    lines.append("        @param_definition,")
    lines.append("        @filter_value_param = @filter_value;")
    lines.append("    ")
    lines.append("    PRINT 'Dynamic execution completed successfully';")
    lines.append("END TRY")
    lines.append("BEGIN CATCH")
    lines.append("    PRINT 'Dynamic execution failed: ' + ERROR_MESSAGE();")
    lines.append("    THROW;")
    lines.append("END CATCH;")
    
    return lines

def generate_sample_value(param_name, param_type):
    """Generate realistic sample values based on parameter name and type."""
    param_name_lower = param_name.lower()
    param_type_lower = param_type.lower() if param_type else 'nvarchar'
    
    # ID parameters
    if 'id' in param_name_lower:
        if 'user_id' in param_name_lower:
            return "1001"
        elif 'card_id' in param_name_lower:
            return "2001"
        else:
            return "123"
    
    # Name parameters
    if 'name' in param_name_lower:
        if 'user' in param_name_lower:
            return "N'John Doe'"
        elif 'file' in param_name_lower:
            return "N'document.pdf'"
        else:
            return "N'Sample Name'"
    
    # Email parameters
    if 'email' in param_name_lower:
        return "N'user@example.com'"
    
    # Status parameters
    if 'status' in param_name_lower:
        return "N'active'"
    
    # Boolean parameters
    if 'is_' in param_name_lower or param_type_lower == 'bit':
        return "1"
    
    # Date parameters
    if 'date' in param_name_lower or 'time' in param_name_lower or 'datetime' in param_type_lower:
        return "GETDATE()"
    
    # Numeric types
    if any(t in param_type_lower for t in ['int', 'decimal', 'numeric', 'float', 'money']):
        if 'amount' in param_name_lower or 'price' in param_name_lower:
            return "99.99"
        elif 'count' in param_name_lower or 'size' in param_name_lower:
            return "10"
        else:
            return "1"
    
    # String parameters (default)
    if 'description' in param_name_lower:
        return "N'Sample description text'"
    elif 'comment' in param_name_lower:
        return "N'Sample comment'"
    elif 'path' in param_name_lower:
        return "N'/path/to/resource'"
    else:
        return "N'sample value'"

def extract_procedures_from_script(script):
    """Extract procedure names from a generated script."""
    procedures = []
    exec_matches = re.finditer(r'EXEC\s+(?:dbo\.)?(\w+)', script, re.IGNORECASE)
    for match in exec_matches:
        proc_name = f"dbo.{match.group(1)}"
        if proc_name not in procedures:
            procedures.append(proc_name)
    return procedures

def save_synthetic_training_data(training_examples, output_filename="synthetic_training_data.json"):
    """Save synthetic training data to JSON file."""
    training_data = {
        "metadata": {
            "generation_timestamp": datetime.now().isoformat(),
            "total_examples": len(training_examples),
            "description": "Synthetic training data for TSQL framework learning",
            "complexity_distribution": {},
            "example_types": {}
        },
        "training_examples": training_examples,
        "learning_guide": {
            "beginner_examples": [],
            "intermediate_examples": [],
            "advanced_examples": [],
            "expert_examples": []
        }
    }
    
    # Calculate distributions
    complexity_counts = {}
    type_counts = {}
    
    for example in training_examples:
        complexity = example.get("complexity_level", "unknown")
        example_type = example.get("example_type", "unknown")
        
        complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
        type_counts[example_type] = type_counts.get(example_type, 0) + 1
        
        # Categorize into learning guide
        if complexity == "beginner":
            training_data["learning_guide"]["beginner_examples"].append(example)
        elif complexity == "intermediate":
            training_data["learning_guide"]["intermediate_examples"].append(example)
        elif complexity == "advanced":
            training_data["learning_guide"]["advanced_examples"].append(example)
        elif complexity == "expert":
            training_data["learning_guide"]["expert_examples"].append(example)
    
    training_data["metadata"]["complexity_distribution"] = complexity_counts
    training_data["metadata"]["example_types"] = type_counts
    
    # Add learning progression recommendations
    training_data["learning_progression"] = {
        "recommended_order": [
            "Start with simple_single_procedure examples to learn basic syntax",
            "Progress to validation_focused examples to understand error handling",
            "Practice crud_* examples to learn common workflow patterns",
            "Study error_handling_focused examples for robust code practices",
            "Advance to multi_procedure_workflow examples for complex scenarios",
            "Master advanced_* examples for enterprise-level implementations"
        ],
        "key_concepts_by_level": {
            "beginner": [
                "Basic EXEC syntax",
                "Parameter declaration and passing",
                "Simple variable usage",
                "Basic error checking"
            ],
            "intermediate": [
                "Parameter validation patterns",
                "TRY-CATCH error handling",
                "Conditional logic (IF-ELSE)",
                "Context variable usage",
                "CRUD operation patterns"
            ],
            "advanced": [
                "Multi-procedure workflows",
                "Transaction management",
                "Complex error handling",
                "Performance considerations",
                "Security best practices"
            ],
            "expert": [
                "Dynamic SQL generation",
                "Batch processing patterns",
                "Advanced transaction control",
                "Optimization techniques",
                "Enterprise patterns"
            ]
        }
    }
    
    save_memory_file(output_filename, training_data)
    print(f"SYNTHETIC_DATA: Saved {len(training_examples)} training examples to {output_filename}")
    
    return training_data

def create_training_prompt_templates(training_examples, output_filename="training_prompts.json"):
    """Create prompt templates for LLM training based on synthetic examples."""
    
    prompt_templates = {
        "metadata": {
            "generation_timestamp": datetime.now().isoformat(),
            "description": "LLM training prompt templates for TSQL framework",
            "total_templates": 0
        },
        "prompt_categories": {
            "code_completion": [],
            "code_explanation": [],
            "code_generation": [],
            "debugging_assistance": [],
            "optimization_suggestions": [],
            "best_practices": []
        }
    }
    
    print("PROMPT_TEMPLATES: Creating LLM training prompt templates...")
    
    for example in training_examples:
        # Create code completion prompts
        script_lines = example["sql_script"].split('\n')
        if len(script_lines) > 5:
            # Take first 70% of lines for completion prompt
            completion_point = int(len(script_lines) * 0.7)
            partial_script = '\n'.join(script_lines[:completion_point])
            complete_script = example["sql_script"]
            
            prompt_templates["prompt_categories"]["code_completion"].append({
                "prompt_type": "code_completion",
                "difficulty": example["complexity_level"],
                "input_prompt": f"""Complete this TSQL script that demonstrates {example['example_type']}:

Use case: {example['use_case']}

Partial script:
```sql
{partial_script}
```

Complete the remaining script following TSQL.APP framework best practices.""",
                "expected_output": complete_script,
                "learning_objectives": example["learning_objectives"],
                "procedures_involved": example["procedures_used"]
            })
        
        # Create code explanation prompts
        prompt_templates["prompt_categories"]["code_explanation"].append({
            "prompt_type": "code_explanation",
            "difficulty": example["complexity_level"],
            "input_prompt": f"""Explain this TSQL script step by step:

```sql
{example['sql_script']}
```

Focus on:
1. What each section does
2. Why certain patterns are used
3. How it follows TSQL.APP framework conventions
4. What beginners should learn from this example""",
            "expected_output": f"""This script demonstrates {example['example_type']} pattern with the following key elements:

Use Case: {example['use_case']}

Learning Objectives:
{chr(10).join('- ' + obj for obj in example['learning_objectives'])}

The script shows proper usage of: {', '.join(example['procedures_used'])}""",
            "learning_objectives": example["learning_objectives"],
            "procedures_involved": example["procedures_used"]
        })
        
        # Create code generation prompts
        prompt_templates["prompt_categories"]["code_generation"].append({
            "prompt_type": "code_generation",
            "difficulty": example["complexity_level"],
            "input_prompt": f"""Generate a TSQL script for the following requirement:

{example['use_case']}

Requirements:
- Use these procedures: {', '.join(example['procedures_used'])}
- Follow {example['complexity_level']} level patterns
- Include proper error handling
- Follow TSQL.APP framework conventions

Target learning objectives:
{chr(10).join('- ' + obj for obj in example['learning_objectives'])}""",
            "expected_output": example["sql_script"],
            "learning_objectives": example["learning_objectives"],
            "procedures_involved": example["procedures_used"]
        })
        
        # Create debugging prompts (introduce intentional errors)
        if example["complexity_level"] in ["intermediate", "advanced", "expert"]:
            buggy_script = introduce_common_errors(example["sql_script"])
            prompt_templates["prompt_categories"]["debugging_assistance"].append({
                "prompt_type": "debugging_assistance",
                "difficulty": example["complexity_level"],
                "input_prompt": f"""Find and fix the errors in this TSQL script:

```sql
{buggy_script}
```

The script should {example['use_case'].lower()}

Identify:
1. Syntax errors
2. Logic errors
3. Best practice violations
4. Potential runtime issues""",
                "expected_output": example["sql_script"],
                "common_errors_introduced": ["Missing error handling", "Incorrect parameter usage", "Transaction issues"],
                "learning_objectives": example["learning_objectives"],
                "procedures_involved": example["procedures_used"]
            })
    
    # Create best practices prompts
    for complexity in ["beginner", "intermediate", "advanced", "expert"]:
        complexity_examples = [ex for ex in training_examples if ex["complexity_level"] == complexity]
        if complexity_examples:
            sample_example = random.choice(complexity_examples)
            
            prompt_templates["prompt_categories"]["best_practices"].append({
                "prompt_type": "best_practices",
                "difficulty": complexity,
                "input_prompt": f"""Review this {complexity}-level TSQL script and suggest improvements:

```sql
{sample_example['sql_script']}
```

Provide feedback on:
1. Code organization and readability
2. Error handling completeness
3. Performance considerations
4. Security best practices
5. TSQL.APP framework compliance""",
                "expected_output": f"""This script demonstrates good {complexity}-level practices including:

Strengths:
- Proper error handling with TRY-CATCH
- Clear parameter validation
- Appropriate use of framework procedures
- Good code organization

Potential improvements:
- Consider adding more detailed comments
- Could optimize for better performance
- Might benefit from additional validation

Overall assessment: Well-structured example following TSQL.APP conventions.""",
                "learning_objectives": sample_example["learning_objectives"],
                "procedures_involved": sample_example["procedures_used"]
            })
    
    # Calculate totals
    total_templates = sum(len(templates) for templates in prompt_templates["prompt_categories"].values())
    prompt_templates["metadata"]["total_templates"] = total_templates
    
    save_memory_file(output_filename, prompt_templates)
    print(f"PROMPT_TEMPLATES: Created {total_templates} training prompt templates")
    
    return prompt_templates

def introduce_common_errors(script):
    """Introduce common errors into a script for debugging exercises."""
    lines = script.split('\n')
    modified_lines = []
    
    for line in lines:
        modified_line = line
        
        # Randomly introduce errors (30% chance per applicable line)
        if random.random() < 0.3:
            # Missing semicolon
            if line.strip().endswith(';') and 'EXEC' in line:
                modified_line = line.rstrip(';')
            
            # Incorrect parameter syntax
            elif '@' in line and '=' in line:
                modified_line = line.replace('@', '') # Remove @ from parameter
            
            # Missing TRY in BEGIN TRY
            elif 'BEGIN TRY' in line:
                modified_line = line.replace('BEGIN TRY', 'BEGIN')
            
            # Wrong procedure name (common typo)
            elif 'EXEC dbo.sp_' in line:
                modified_line = line.replace('sp_', 'sp') # Remove underscore
        
        modified_lines.append(modified_line)
    
    return '\n'.join(modified_lines)

def generate_comprehensive_training_curriculum(framework_api_details, script_patterns, relationships, output_filename="training_curriculum.json"):
    """Generate a comprehensive training curriculum based on framework analysis."""
    
    curriculum = {
        "metadata": {
            "generation_timestamp": datetime.now().isoformat(),
            "description": "Comprehensive TSQL.APP Framework Training Curriculum",
            "framework_procedures_count": len([obj for obj in framework_api_details if obj.get('object_type_short') == 'P']),
            "total_modules": 0
        },
        "learning_modules": [],
        "skill_assessments": [],
        "progression_path": []
    }
    
    print("CURRICULUM: Generating comprehensive training curriculum...")
    
    # Module 1: Framework Basics
    curriculum["learning_modules"].append({
        "module_id": 1,
        "module_name": "TSQL.APP Framework Basics",
        "difficulty_level": "beginner",
        "estimated_duration_hours": 4,
        "learning_objectives": [
            "Understand TSQL.APP framework structure",
            "Learn basic procedure calling syntax",
            "Master parameter passing techniques",
            "Understand context variables"
        ],
        "key_procedures": get_fundamental_procedures(framework_api_details),
        "practice_exercises": [
            "Call a simple framework procedure with parameters",
            "Use context variables like @user_id and @card_id",
            "Handle basic parameter validation",
            "Practice proper variable declaration"
        ],
        "assessment_criteria": [
            "Can call procedures with correct syntax",
            "Properly declares and uses variables",
            "Understands parameter naming conventions",
            "Uses context variables appropriately"
        ]
    })
    
    # Module 2: Error Handling and Validation
    curriculum["learning_modules"].append({
        "module_id": 2,
        "module_name": "Error Handling and Validation Patterns",
        "difficulty_level": "intermediate",
        "estimated_duration_hours": 6,
        "learning_objectives": [
            "Master TRY-CATCH error handling",
            "Implement parameter validation patterns",
            "Handle different types of errors appropriately",
            "Create robust error messages"
        ],
        "key_procedures": get_validation_procedures(framework_api_details),
        "practice_exercises": [
            "Implement comprehensive parameter validation",
            "Create TRY-CATCH blocks with proper error handling",
            "Handle business logic errors vs system errors",
            "Practice error logging patterns"
        ],
        "assessment_criteria": [
            "Implements complete error handling",
            "Validates parameters before execution",
            "Provides meaningful error messages",
            "Follows error handling best practices"
        ]
    })
    
    # Module 3: CRUD Operations and Workflows
    curriculum["learning_modules"].append({
        "module_id": 3,
        "module_name": "CRUD Operations and Business Workflows",
        "difficulty_level": "intermediate",
        "estimated_duration_hours": 8,
        "learning_objectives": [
            "Implement Create, Read, Update, Delete patterns",
            "Understand workflow orchestration",
            "Master data validation in CRUD operations",
            "Handle concurrent access scenarios"
        ],
        "key_procedures": get_crud_procedures(framework_api_details),
        "practice_exercises": [
            "Build complete CRUD workflows",
            "Implement optimistic concurrency control",
            "Create data validation chains",
            "Handle parent-child relationship operations"
        ],
        "assessment_criteria": [
            "Can implement full CRUD workflows",
            "Handles data validation properly",
            "Manages concurrent access issues",
            "Follows business logic patterns"
        ]
    })
    
    # Module 4: Advanced Multi-Procedure Workflows
    curriculum["learning_modules"].append({
        "module_id": 4,
        "module_name": "Advanced Multi-Procedure Workflows",
        "difficulty_level": "advanced",
        "estimated_duration_hours": 10,
        "learning_objectives": [
            "Orchestrate multiple related procedures",
            "Implement transaction management",
            "Handle complex business scenarios",
            "Optimize workflow performance"
        ],
        "key_procedures": get_workflow_procedures(framework_api_details, relationships),
        "practice_exercises": [
            "Create multi-step business workflows",
            "Implement transaction rollback scenarios",
            "Build conditional workflow paths",
            "Optimize procedure call sequences"
        ],
        "assessment_criteria": [
            "Can orchestrate complex workflows",
            "Properly manages transactions",
            "Handles workflow failure gracefully",
            "Optimizes for performance"
        ]
    })
    
    # Module 5: Enterprise Patterns and Optimization
    curriculum["learning_modules"].append({
        "module_id": 5,
        "module_name": "Enterprise Patterns and Performance Optimization",
        "difficulty_level": "expert",
        "estimated_duration_hours": 12,
        "learning_objectives": [
            "Implement enterprise-level patterns",
            "Master performance optimization techniques",
            "Handle large-scale data operations",
            "Implement advanced security patterns"
        ],
        "key_procedures": get_advanced_procedures(framework_api_details),
        "practice_exercises": [
            "Implement batch processing patterns",
            "Create dynamic SQL with security",
            "Build high-performance workflows",
            "Implement audit and logging patterns"
        ],
        "assessment_criteria": [
            "Can implement enterprise patterns",
            "Optimizes for performance at scale",
            "Handles security considerations",
            "Creates maintainable, robust code"
        ]
    })
    
    # Create skill assessments
    curriculum["skill_assessments"] = create_skill_assessments(framework_api_details)
    
    # Create progression path
    curriculum["progression_path"] = [
        {
            "step": 1,
            "title": "Foundation Building",
            "modules": [1],
            "completion_criteria": "Complete Module 1 with 80% assessment score"
        },
        {
            "step": 2,
            "title": "Robust Development",
            "modules": [2],
            "completion_criteria": "Complete Module 2 with error-free validation implementations"
        },
        {
            "step": 3,
            "title": "Business Application",
            "modules": [3],
            "completion_criteria": "Build complete CRUD application using framework procedures"
        },
        {
            "step": 4,
            "title": "Advanced Integration",
            "modules": [4],
            "completion_criteria": "Create complex multi-procedure workflow with proper transaction management"
        },
        {
            "step": 5,
            "title": "Enterprise Mastery",
            "modules": [5],
            "completion_criteria": "Implement enterprise-grade solution with performance optimization"
        }
    ]
    
    curriculum["metadata"]["total_modules"] = len(curriculum["learning_modules"])
    
    save_memory_file(output_filename, curriculum)
    print(f"CURRICULUM: Generated {len(curriculum['learning_modules'])} learning modules")
    
    return curriculum

def get_fundamental_procedures(framework_api_details):
    """Get procedures suitable for beginners."""
    fundamental = []
    for obj in framework_api_details:
        if obj.get('object_type_short') == 'P':
            proc_name = obj['object_name'].lower()
            param_count = len([p for p in obj.get('parameters', []) if p.get('name') != '[Return Value]'])
            
            # Simple procedures with few parameters
            if param_count <= 3 and any(keyword in proc_name for keyword in ['get', 'list', 'find', 'check']):
                fundamental.append(f"{obj['schema_name']}.{obj['object_name']}")
    
    return fundamental[:5]  # Limit to 5 for focus

def get_validation_procedures(framework_api_details):
    """Get procedures that demonstrate validation patterns."""
    validation = []
    for obj in framework_api_details:
        if obj.get('object_type_short') == 'P':
            proc_name = obj['object_name'].lower()
            if any(keyword in proc_name for keyword in ['validate', 'check', 'verify', 'hasrole', 'isempty']):
                validation.append(f"{obj['schema_name']}.{obj['object_name']}")
    
    return validation

def get_crud_procedures(framework_api_details):
    """Get procedures that demonstrate CRUD operations."""
    crud = []
    for obj in framework_api_details:
        if obj.get('object_type_short') == 'P':
            proc_name = obj['object_name'].lower()
            if any(keyword in proc_name for keyword in ['create', 'add', 'update', 'delete', 'modify', 'remove']):
                crud.append(f"{obj['schema_name']}.{obj['object_name']}")
    
    return crud

def get_workflow_procedures(framework_api_details, relationships):
    """Get procedures that work well together in workflows."""
    workflow = []
    proc_relationships = relationships.get("procedure_relationships", {})
    
    # Get most connected procedures
    most_connected = relationships.get("relationship_summary", {}).get("most_connected_procedures", [])
    for proc_info in most_connected[:5]:
        workflow.append(proc_info["procedure_name"])
    
    return workflow

def get_advanced_procedures(framework_api_details):
    """Get procedures suitable for advanced scenarios."""
    advanced = []
    for obj in framework_api_details:
        if obj.get('object_type_short') == 'P':
            proc_name = obj['object_name'].lower()
            param_count = len([p for p in obj.get('parameters', []) if p.get('name') != '[Return Value]'])
            
            # Complex procedures with many parameters or advanced keywords
            if (param_count > 5 or 
                any(keyword in proc_name for keyword in ['batch', 'process', 'execute', 'admin', 'sys'])):
                advanced.append(f"{obj['schema_name']}.{obj['object_name']}")
    
    return advanced

def create_skill_assessments(
    framework_api_details: List[Dict],
    script_patterns: Dict,
    relationships: Dict
) -> Dict:
    """Create skill assessments based on framework analysis."""
    logging.info("ASSESSMENTS: Generating skill assessments...")
    
    assessments = {
        "title": "T-SQL Framework Skill Assessments",
        "description": "Comprehensive skill assessment exercises",
        "levels": []
    }
    
    # Generate assessment levels
    for level in ["beginner", "intermediate", "advanced"]:
        level_assessment = {
            "level": level,
            "exercises": []
        }
        
        # Generate exercises for each pattern
        for pattern_name in script_patterns:
            exercise = {
                "pattern": pattern_name,
                "description": f"Implement {pattern_name} pattern",
                "complexity": level,
                "instructions": []
            }
            
            # Add instructions based on pattern complexity
            if level == "beginner":
                exercise["instructions"].append("Start with a simple implementation")
            elif level == "intermediate":
                exercise["instructions"].append("Include error handling")
            else:
                exercise["instructions"].append("Implement with optimizations")
            
            level_assessment["exercises"].append(exercise)
        
        assessments["levels"].append(level_assessment)
    
    # Beginner assessment
    assessments.append({
        "assessment_id": "beginner_validation",
        "title": "Validation Pattern Assessment",
        "difficulty": "beginner",
        "time_limit_minutes": 30,
        "tasks": [
            {
                "task_id": 1,
                "description": "Implement parameter validation with custom error messages",
                "success_criteria": ["Validates all required parameters", "Meaningful error messages", "Proper error handling flow"]
            },
            {
                "task_id": 2,
                "description": "Create TRY-CATCH block with proper error recovery",
                "success_criteria": ["Complete TRY-CATCH structure", "Proper error capture", "Graceful error handling"]
            },
            {
                "task_id": 3,
                "description": "Handle business logic validation",
                "success_criteria": ["Validates business rules", "Provides user-friendly messages", "Follows framework patterns"]
            }
        ]
    })
    
    # Advanced assessment
    assessments.append({
        "assessment_id": "advanced_workflows",
        "title": "Multi-Procedure Workflow Assessment",
        "difficulty": "advanced",
        "time_limit_minutes": 60,
        "tasks": [
            {
                "task_id": 1,
                "description": "Create workflow using 3+ related procedures",
                "success_criteria": ["Uses multiple procedures", "Proper workflow orchestration", "Handles inter-procedure dependencies"]
            },
            {
                "task_id": 2,
                "description": "Implement transaction management with rollback",
                "success_criteria": ["Proper transaction scope", "Handles rollback scenarios", "Maintains data consistency"]
            },
            {
                "task_id": 3,
                "description": "Build conditional workflow with multiple paths",
                "success_criteria": ["Multiple execution paths", "Proper condition evaluation", "All paths handle errors"]
            }
        ]
    })
    
    return assessments

# Integration function to add to main execution
def generate_all_training_materials(framework_api_details: List[Dict], 
                                    script_patterns: Dict, 
                                    relationships: Dict, 
                                    args: Dict) -> Dict:
    """Generate all training materials in one coordinated effort."""
    print("\nFRAMEWORK_TRAINING: Generating comprehensive training materials...")
    
    # Initialize generators
    simple_gen = SimpleExampleGenerator(framework_api_details, script_patterns)
    validation_gen = ValidationExampleGenerator(framework_api_details, script_patterns)
    crud_gen = CRUDExampleGenerator(framework_api_details, script_patterns)
    error_gen = ErrorHandlingExampleGenerator(framework_api_details, script_patterns)
    multi_gen = MultiProcedureExampleGenerator(framework_api_details, script_patterns)
    advanced_gen = AdvancedExampleGenerator(framework_api_details, script_patterns)
    
    # Generate examples with proper structure
    examples = []
    example_id = 1
    
    # Helper function to create example structure
    def create_example(category: str, example_data: Dict) -> Dict:
        """Create example structure with proper fields."""
        nonlocal example_id
        return {
            "example_id": f"pattern_example_{example_id}",
            "complexity_level": example_data["complexity"],
            "learning_objectives": example_data["learning_objectives"],
            "example_script": example_data["example_script"],
            "pattern_frequency": example_data.get("pattern_frequency", 0),
            "category": category
        }
    
    # Generate examples
    for category, generator in {
        "simple": simple_gen,
        "validation": validation_gen,
        "crud": crud_gen,
        "error_handling": error_gen,
        "multi_procedure": multi_gen,
        "advanced": advanced_gen
    }.items():
        count = args.get(f'{category}_count', 10)
        for i in range(count):
            example_data = generator.generate_example()
            examples.append(create_example(category, example_data))
            example_id += 1
    
    # Generate curriculum and assessments
    curriculum = generate_comprehensive_training_curriculum(
        framework_api_details,
        script_patterns,
        relationships
    )
    
    assessments = create_skill_assessments(
        framework_api_details,
        script_patterns,
        relationships
    )
    
    # Combine all materials
    training_materials = {
        'examples': examples,
        'curriculum': curriculum,
        'assessments': assessments
    }
    
    # Calculate statistics
    stats = {
        "total_examples": len(examples),
        "procedure_coverage": calculate_procedure_coverage(framework_api_details, examples),
        "difficulty_progression": validate_difficulty_progression(examples),
        "category_distribution": {
            category: len([e for e in examples if e['category'] == category])
            for category in set(e['category'] for e in examples)
        }
    }
    
    # Create output structure
    training_materials = {
        "framework_usage_patterns": script_patterns,
        "procedure_relationships": relationships,
        "training_examples": examples,
        "training_summary": stats
    }
    
    # Generate Markdown output if requested
    if args.get('output_format', 'json') == 'markdown':
        print("\nGenerating Markdown output...")
        markdown_gen = MarkdownGenerator(output_dir=args.get('output_dir', 'training_materials'))
        markdown_gen.generate_markdown(training_materials)
    
    return training_materials

def calculate_procedure_coverage(framework_api_details: List[Dict], 
                                    training_examples: Dict) -> float:
    """Calculate what percentage of framework procedures are covered in training examples."""
    all_procedures = set(
        f"{p['schema_name']}.{p['object_name']}"
        for p in framework_api_details if p.get('object_type_short') == 'P'
    )
    
    covered_procedures = set()
    for example_type, examples in training_examples.items():
        for example in examples:
            if example_type == 'multi_procedure':
                covered_procedures.update(example['procedures'])
            else:
                covered_procedures.add(example['procedure'])
    
    return len(covered_procedures) / len(all_procedures) if all_procedures else 0.0

def validate_difficulty_progression(training_examples: Dict) -> Dict:
    """Validate that examples provide good difficulty progression."""
    difficulty_counts = {
        "simple": 0,
        "medium": 0,
        "complex": 0
    }
    
    for example_type, examples in training_examples.items():
        for example in examples:
            difficulty = example.get('complexity', 'simple')
            difficulty_counts[difficulty] += 1
    
    beginner_pct = (complexity_counts.get("beginner", 0) / total) * 100
    intermediate_pct = (complexity_counts.get("intermediate", 0) / total) * 100
    advanced_pct = (complexity_counts.get("advanced", 0) / total) * 100
    expert_pct = (complexity_counts.get("expert", 0) / total) * 100
    
    # Good progression should have decreasing percentages as difficulty increases
    if beginner_pct >= intermediate_pct >= advanced_pct >= expert_pct and beginner_pct > 20:
        return "Good progression"
    else:
        return f"Needs adjustment: B:{beginner_pct:.0f}% I:{intermediate_pct:.0f}% A:{advanced_pct:.0f}% E:{expert_pct:.0f}%"

# Add this to the main execution section after co-occurrence stats are updated:
"""
    # Generate comprehensive training materials
    if not script_args_global.skip_relationships and current_framework_api and current_action_script_corpus:
        # Analyze script patterns for synthesis
        script_patterns = analyze_script_patterns(current_action_script_corpus, current_framework_api)
        
        # Get procedure relationships
        relationships_output_file = os.getenv('PROCEDURE_RELATIONSHIPS_FILE', 'procedure_relationships.json')
        relationships_data = generate_procedure_relationships_file(current_framework_api, relationships_output_file)
        
        # Generate all training materials
        training_materials = generate_all_training_materials(
            current_framework_api, script_patterns, relationships_data, script_args_global
        )
        
        print(f"\nTRAINING_MATERIALS: All training materials generated successfully!")
        print(f"Files created: synthetic_training_data.json, training_prompts.json, training_curriculum.json")
"""