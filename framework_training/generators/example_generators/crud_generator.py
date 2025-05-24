from .base_generator import ExampleGenerator
from typing import Dict, List, Optional
import random


class CRUDExampleGenerator(ExampleGenerator):
    """Generator for CRUD workflow examples."""
    
    def generate_example(self) -> Dict:
        """Generate a CRUD workflow example."""
        # Select a random CRUD operation
        operation = random.choice(['create', 'read', 'update', 'delete'])
        
        # Select an appropriate procedure
        proc = self._select_crud_procedure(operation)
        
        if not proc:
            return None
            
        # Generate the example
        example = {
            "example_script": self.generate_crud_script(proc, operation, self.patterns),
            "complexity": "medium",
            "learning_objectives": [f"Demonstrate CRUD {operation} operation", 
                                  f"Show proper parameter usage for {operation} operation"],
            "pattern_frequency": 75,
            "category": f"crud_{operation}"
        }
        
        return example
    
    def _select_crud_procedure(self, operation: str) -> Dict:
        """Select an appropriate procedure for the given CRUD operation."""
        # For testing, just select a random procedure
        return random.choice([p for p in self.framework_api if p.get('object_type_short') == 'P'])
    
    def generate_crud_script(self, proc: Dict, operation: str, patterns: Dict) -> str:
        """Generate a CRUD-specific script."""
        params = []
        for param in proc.get('parameters', []):
            value = self.generate_sample_value(param['name'], param.get('type_from_sys', param.get('type_from_def', 'nvarchar')))
            params.append(f"@{param['name']} = {value}")
        
        # Add appropriate CRUD pattern
        if operation == 'create':
            script = f"-- Create new record\nEXEC {proc['schema_name']}.{proc['object_name']} {', '.join(params)}"
        elif operation == 'read':
            script = f"-- Read existing record\nEXEC {proc['schema_name']}.{proc['object_name']} {', '.join(params)}"
        elif operation == 'update':
            script = f"-- Update existing record\nEXEC {proc['schema_name']}.{proc['object_name']} {', '.join(params)}"
        else:  # delete
            script = f"-- Delete record\nEXEC {proc['schema_name']}.{proc['object_name']} {', '.join(params)}"
        
        return script
