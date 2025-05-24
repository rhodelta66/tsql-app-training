from .base_generator import ExampleGenerator
from typing import Dict, List
import random


class ValidationExampleGenerator(ExampleGenerator):
    """Generator for validation-focused examples."""
    
    def generate_example(self) -> Dict:
        """Generate a validation-focused example."""
        # Select a random procedure with parameters
        proc = random.choice([p for p in self.framework_api 
                             if p.get('object_type_short') == 'P' and p.get('parameters')])
        
        # Generate script with validation checks
        params = []
        for param in proc.get('parameters', []):
            value = self.generate_sample_value(param['name'], param['type'])
            params.append(f"@{param['name']} = {value}")
        
        # Add validation checks
        validation_checks = []
        for param in proc.get('parameters', []):
            if 'nvarchar' in param['type'].lower():
                validation_checks.append(f"IF LEN(@{param['name']}) > 0")
            elif 'int' in param['type'].lower():
                validation_checks.append(f"IF @{param['name']} > 0")
        
        validation_script = "\n    AND ".join(validation_checks)
        
        # Create example with proper structure
        return {
            "example_script": f"BEGIN\n    IF {validation_script}\n    BEGIN\n        EXEC {proc['schema_name']}.{proc['object_name']} {', '.join(params)}\n    END\n    ELSE\n    BEGIN\n        RAISERROR('Validation failed', 16, 1)\n    END\nEND",
            "complexity": "medium",
            "learning_objectives": ["Demonstrate input validation", "Show conditional execution"],
            "pattern_frequency": 90,
            "category": "validation"
        }
    
    def generate_validation_script(self, proc: Dict, patterns: Dict) -> str:
        """Generate a script with validation patterns."""
        # Generate script with validation checks
        params = []
        for param in proc.get('parameters', []):
            value = self.generate_sample_value(param['name'], param['type'])
            params.append(f"@{param['name']} = {value}")
        
        # Add validation checks
        validation_checks = []
        for param in proc.get('parameters', []):
            if 'nvarchar' in param['type'].lower():
                validation_checks.append(f"IF LEN(@{param['name']}) > 0")
            elif 'int' in param['type'].lower():
                validation_checks.append(f"IF @{param['name']} > 0")
        
        validation_script = "\n    AND ".join(validation_checks)
        
        return f"BEGIN\n    IF {validation_script}\n    BEGIN\n        EXEC {proc['schema_name']}.{proc['object_name']} {', '.join(params)}\n    END\n    ELSE\n    BEGIN\n        RAISERROR('Validation failed', 16, 1)\n    END\nEND"
