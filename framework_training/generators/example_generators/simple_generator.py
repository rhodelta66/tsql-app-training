from .base_generator import ExampleGenerator
from typing import Dict, List
import random


class SimpleExampleGenerator(ExampleGenerator):
    """Generator for simple single-procedure examples."""
    
    def generate_example(self) -> Dict:
        """Generate a simple example for a single procedure."""
        # Select a random procedure
        proc = random.choice([p for p in self.framework_api if p.get('object_type_short') == 'P'])
        
        # Generate script with parameters
        params = []
        for param in proc.get('parameters', []):
            value = self.generate_sample_value(param['name'], param.get('type_from_sys', param.get('type_from_def', 'nvarchar')))
            params.append(f"@{param['name']} = {value}")
        
        # Create example with proper structure
        return {
            "script": f"EXEC {proc['schema_name']}.{proc['object_name']} {', '.join(params)}",
            "complexity": "simple",
            "objectives": ["Demonstrate basic procedure call with parameters"],
            "pattern_frequency": 100,
            "example_script": f"EXEC {proc['schema_name']}.{proc['object_name']} {', '.join(params)}",
            "learning_objectives": ["Demonstrate basic procedure call with parameters"],
            "category": "simple"
        }
    
    def generate_simple_script(self, proc: Dict, patterns: Dict) -> str:
        """Generate a simple script for a single procedure."""
        # Generate script with parameters
        params = []
        for param in proc.get('parameters', []):
            value = self.generate_sample_value(param['name'], param.get('type_from_sys', param.get('type_from_def', 'nvarchar')))
            params.append(f"@{param['name']} = {value}")
        
        return f"EXEC {proc['schema_name']}.{proc['object_name']} {', '.join(params)}"
