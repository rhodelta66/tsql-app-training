from typing import Dict, List, Optional
import random


class ExampleGenerator:
    """Base class for all example generators."""
    
    def __init__(self, framework_api_details: List[Dict], patterns: Dict):
        self.framework_api = framework_api_details
        self.patterns = patterns
        self.proc_map = self._create_procedure_map()
    
    def _create_procedure_map(self) -> Dict:
        """Create a lookup map for procedures."""
        return {
            f"{obj['schema_name']}.{obj['object_name']}": obj 
            for obj in self.framework_api if obj.get('object_type_short') == 'P'
        }
    
    def generate_examples(self, count: int) -> List[Dict]:
        """Generate multiple examples."""
        examples = []
        for _ in range(count):
            examples.append(self.generate_example())
        return examples
    
    def generate_example(self) -> Dict:
        """Generate a single example."""
        raise NotImplementedError("Subclasses must implement generate_example")
    
    def generate_use_case_description(self, proc: Dict) -> str:
        """Generate a realistic use case description for a procedure."""
        proc_name = f"{proc['schema_name']}.{proc['object_name']}"
        return f"Example demonstrating the usage of {proc_name}"
    
    def generate_sample_value(self, param_name: str, param_type: str) -> str:
        """Generate realistic sample values based on parameter name and type."""
        if 'nvarchar' in param_type.lower() or 'varchar' in param_type.lower():
            # For string parameters, use the parameter name as a base
            return f"'Sample_{param_name}'"
        elif 'int' in param_type.lower():
            return str(random.randint(1, 100))
        elif 'datetime' in param_type.lower():
            return "'2025-05-24T12:00:00'"
        else:
            return "DEFAULT"
