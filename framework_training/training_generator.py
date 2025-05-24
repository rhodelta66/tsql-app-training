from datetime import datetime
from .utils import generate_sample_value
from .generators.synthetic_training_generator import (
    analyze_script_patterns,
    generate_all_training_materials,
    calculate_procedure_coverage,
    validate_difficulty_progression,
)
import json

class TrainingExampleGenerator:
    """Generates training examples from framework usage patterns."""
    
    def __init__(self, framework_api_details):
        self.framework_api = framework_api_details
        self.framework_procedures = self._build_procedure_lookup()
    
    def _build_procedure_lookup(self):
        """Build lookup of framework procedures."""
        procedures = {}
        for obj in self.framework_api:
            if obj.get('object_type_short') == 'P':
                full_name = f"{obj['schema_name']}.{obj['object_name']}"
                procedures[full_name] = obj
        return procedures
    
    def generate_examples(self, usage_patterns, relationships, action_scripts_corpus=None):
        """
        Generate training examples based on usage patterns and relationships.
        
        Args:
            usage_patterns (dict): Patterns extracted from usage data
            relationships (dict): Procedure relationships
            action_scripts_corpus (list, optional): Action scripts corpus
        
        Returns:
            dict: Generated training materials
        """
        print("\nFRAMEWORK_TRAINING: Generating training materials...")
        
        # Analyze script patterns if corpus is provided
        script_patterns = analyze_script_patterns(action_scripts_corpus, self.framework_api)
        
        # Generate comprehensive training materials
        results = generate_all_training_materials(
            self.framework_api,
            script_patterns,
            relationships,
            args={"num_examples": 50}  # Pass args as required by generate_all_training_materials
        )
        
        # Save results to file
        output_dir = "training_output"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "training_materials.json")
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\nFRAMEWORK_TRAINING: Training materials saved to {output_file}")
        return results['metadata']['example_types']['synthetic']
    
    def _create_example_from_pattern(self, pattern, example_number):
        """Create a training example from a pattern."""
        
        # Get most common procedure from this pattern
        common_procs = pattern.get("common_procedures", {})
        if not common_procs:
            return None
            
        primary_proc = list(common_procs.keys())[0]
        
        # Generate example script
        script = self._generate_example_script(pattern, primary_proc)
        
        # Determine complexity
        avg_complexity = pattern.get("average_complexity", 0)
        if avg_complexity < 5:
            complexity = "beginner"
        elif avg_complexity < 10:
            complexity = "intermediate"
        else:
            complexity = "advanced"
        
        return {
            "example_id": f"pattern_example_{example_number}",
            "pattern_description": pattern["description"],
            "complexity_level": complexity,
            "occurrence_frequency": pattern["occurrence_count"],
            "example_script": script,
            "key_procedures": list(common_procs.keys())[:3],
            "teaching_notes": f"This pattern appears {pattern['occurrence_count']} times in real applications"
        }
    
    def _generate_example_script(self, pattern, primary_proc_name):
        """Generate example script based on pattern."""
        
        lines = []
        
        # Header comment
        lines.append(f"-- Training Example: {pattern['description']}")
        lines.append(f"-- Pattern Frequency: {pattern['occurrence_count']} occurrences")
        lines.append("")
        
        # Get procedure details
        proc_obj = self.framework_procedures.get(primary_proc_name)
        if not proc_obj:
            return "-- Error: Procedure not found in framework"
        
        # Add parameters section
        params = [p for p in proc_obj.get('parameters', []) if p.get('name') != '[Return Value]']
        if params:
            lines.append("-- Parameter Setup")
            for param in params[:3]:  # Limit for readability
                param_name = param['name']
                param_type = param.get('type_from_sys', 'nvarchar(255)')
                sample_value = generate_sample_value(param_name, param_type)
                lines.append(f"DECLARE {param_name} {param_type} = {sample_value};")
            lines.append("")
        
        # Add error handling if pattern includes it
        if "error_handling" in pattern["signature"]:
            lines.append("-- Error handling pattern")
            lines.append("BEGIN TRY")
            lines.append("")
        
        # Add transaction if pattern includes it
        if "transactional" in pattern["signature"]:
            indent = "    " if "error_handling" in pattern["signature"] else ""
            lines.append(f"{indent}-- Transaction for data consistency")
            lines.append(f"{indent}BEGIN TRANSACTION;")
            lines.append("")
        
        # Add the main procedure call
        indent = "    " if "error_handling" in pattern["signature"] else ""
        lines.append(f"{indent}-- Framework procedure call")
        lines.append(f"{indent}EXEC {primary_proc_name};")
        
        # Close transaction if used
        if "transactional" in pattern["signature"]:
            lines.append("")
            lines.append(f"{indent}COMMIT TRANSACTION;")
        
        # Close error handling if used
        if "error_handling" in pattern["signature"]:
            lines.append("")
            lines.append("END TRY")
            lines.append("BEGIN CATCH")
            lines.append("    PRINT 'Error occurred: ' + ERROR_MESSAGE();")
            lines.append("    THROW;")
            lines.append("END CATCH;")
        
        return "\n".join(lines)
