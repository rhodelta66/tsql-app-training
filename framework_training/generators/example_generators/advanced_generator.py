from .base_generator import ExampleGenerator
from typing import Dict, List
import random


class AdvancedExampleGenerator(ExampleGenerator):
    """Generator for advanced scenario examples."""
    
    def generate_example(self) -> Dict:
        """Generate an advanced example."""
        # Select a random procedure with parameters
        proc = random.choice([
            p for p in self.framework_api
            if p.get('object_type_short') == 'P' and
            p.get('parameters') and
            len(p.get('parameters', [])) > 3  # Consider procedures with more parameters as complex
        ])
        
        # Generate script with parameters
        params = []
        for param in proc.get('parameters', []):
            value = self.generate_sample_value(param['name'], param.get('type_from_sys', param.get('type_from_def', 'nvarchar')))
            params.append(f"@{param['name']} = {value}")
        
        # Create example with proper structure
        return {
            "example_script": f"EXEC {proc['schema_name']}.{proc['object_name']} {', '.join(params)}",
            "complexity": "complex",
            "learning_objectives": ["Demonstrate advanced procedure usage", "Show complex parameter handling"],
            "pattern_frequency": 50,
            "category": "advanced"
        }
    
    def generate_advanced_scenario_script(self, proc: Dict, api_details: List[Dict], patterns: Dict) -> str:
        """Generate an advanced scenario script."""
        # Generate script with parameters
        params = []
        for param in proc.get('parameters', []):
            value = self.generate_sample_value(param['name'], param.get('type_from_sys', param.get('type_from_def', 'nvarchar')))
            params.append(f"@{param['name']} = {value}")
        
        return f"EXEC {proc['schema_name']}.{proc['object_name']} {', '.join(params)}"
