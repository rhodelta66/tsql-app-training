from .base_generator import ExampleGenerator
from typing import Dict, List
import random


class MultiProcedureExampleGenerator(ExampleGenerator):
    """Generator for examples using multiple related procedures."""
    
    def __init__(self, framework_api_details: List[Dict], patterns: Dict):
        super().__init__(framework_api_details, patterns)
        self.relationships = self._build_relationship_map()
    
    def _build_relationship_map(self) -> Dict:
        """Build a map of related procedures."""
        relationships = {}
        for proc in self.framework_api:
            if proc.get('object_type_short') == 'P':
                proc_key = f"{proc['schema_name']}.{proc['object_name']}"
                relationships[proc_key] = self._find_related_procedures(proc)
        return relationships
    
    def _find_related_procedures(self, proc: Dict) -> List[str]:
        """Find procedures related to the given procedure."""
        # Implementation remains the same as before
        pass
    
    def generate_example(self) -> Dict:
        """Generate a multi-procedure example."""
        # Get all procedures with relationships
        procedures_with_relationships = [
            p for p in self.framework_api
            if p.get('object_type_short') == 'P' and
            f"{p['schema_name']}.{p['object_name']}" in self.relationships.get('relationships', {})
        ]
        
        if not procedures_with_relationships:
            return {
                "example_script": "-- No related procedures found",
                "complexity": "complex",
                "learning_objectives": ["Show multi-procedure pattern"],
                "pattern_frequency": 60,
                "category": "multi_procedure"
            }
        
        # Select a random procedure
        proc = random.choice(procedures_with_relationships)
        proc_name = f"{proc['schema_name']}.{proc['object_name']}"
        
        # Get related procedures
        related_names = self.relationships['relationships'][proc_name]
        related_procedures = [
            p for p in self.framework_api
            if f"{p['schema_name']}.{p['object_name']}" in related_names
        ]
        
        # Generate scripts for each procedure
        scripts = []
        for related in [proc] + related_procedures:
            params = []
            for param in related.get('parameters', []):
                value = self.generate_sample_value(param['name'], param['type'])
                params.append(f"@{param['name']} = {value}")
            
            scripts.append(f"EXEC {related['schema_name']}.{related['object_name']} {', '.join(params)}")
        
        # Create example with proper structure
        return {
            "example_script": "\n-- Next operation\n".join(scripts),
            "complexity": "complex",
            "learning_objectives": ["Demonstrate multi-procedure workflow", "Show procedure chaining"],
            "pattern_frequency": 60,
            "category": "multi_procedure"
        }
    
    def generate_multi_procedure_script(self, proc_names: List[str], api_details: List[Dict], patterns: Dict) -> str:
        """Generate script using multiple related procedures."""
        # Implementation remains the same as before
        pass
