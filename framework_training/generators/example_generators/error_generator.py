from .base_generator import ExampleGenerator
from typing import Dict, List
import random


class ErrorHandlingExampleGenerator(ExampleGenerator):
    """Generator for error handling examples."""
    
    def generate_example(self) -> Dict:
        """Generate an error handling example."""
        # Select a random procedure
        proc = random.choice([p for p in self.framework_api if p.get('object_type_short') == 'P'])
        
        # Generate script with parameters
        params = []
        for param in proc.get('parameters', []):
            value = self.generate_sample_value(param['name'], param.get('type_from_sys', param.get('type_from_def', 'nvarchar')))
            params.append(f"@{param['name']} = {value}")
        
        # Create example with proper structure
        return {
            "example_script": f"BEGIN TRY\n    EXEC {proc['schema_name']}.{proc['object_name']} {', '.join(params)}\nEND TRY\nBEGIN CATCH\n    PRINT 'Error occurred: ' + ERROR_MESSAGE();\n    THROW;\nEND CATCH;",
            "complexity": "medium",
            "learning_objectives": ["Demonstrate error handling with TRY-CATCH", "Show proper error message handling"],
            "pattern_frequency": 80,
            "category": "error_handling"
        }
    
    def generate_error_handling_script(self, proc: Dict, patterns: Dict) -> str:
        """Generate comprehensive error handling script."""
        # Generate script with parameters
        params = []
        for param in proc.get('parameters', []):
            value = self.generate_sample_value(param['name'], param.get('type_from_sys', param.get('type_from_def', 'nvarchar')))
            params.append(f"@{param['name']} = {value}")
        
        return f"BEGIN TRY\n    EXEC {proc['schema_name']}.{proc['object_name']} {', '.join(params)}\nEND TRY\nBEGIN CATCH\n    PRINT 'Error occurred: ' + ERROR_MESSAGE();\n    THROW;\nEND CATCH;"
