import re
from datetime import datetime
from .utils import clean_sql_text

class FrameworkPatternAnalyzer:
    """
    Analyzes framework usage patterns in application scripts.
    Focuses on how framework procedures are used, not business logic.
    """
    
    def __init__(self, framework_api_details):
        self.framework_api = framework_api_details
        self.framework_procedures = self._build_procedure_lookup()
        
    def _build_procedure_lookup(self):
        """Build lookup dictionary of framework procedures."""
        procedures = {}
        for obj in self.framework_api:
            if obj.get('object_type_short') == 'P':
                proc_name = obj['object_name'].lower()
                full_name = f"{obj['schema_name']}.{obj['object_name']}"
                procedures[proc_name] = {
                    'full_name': full_name,
                    'parameters': obj.get('parameters', []),
                    'object_info': obj
                }
        return procedures
    
    def analyze_scripts(self, action_scripts_corpus):
        """Analyze all scripts for framework usage patterns."""
        print(f"  Analyzing {len(action_scripts_corpus)} scripts for framework patterns...")
        
        patterns = {
            "metadata": {
                "analysis_date": datetime.now().isoformat(),
                "scripts_analyzed": len(action_scripts_corpus),
                "framework_procedures_available": len(self.framework_procedures)
            },
            "patterns": [],
            "pattern_summary": {},
            "common_practices": []
        }
        
        # Analyze each script
        script_patterns = []
        for i, script_info in enumerate(action_scripts_corpus):
            if i % 50 == 0:  # Progress indicator
                print(f"    Processing script {i+1}/{len(action_scripts_corpus)}...")
                
            pattern = self._analyze_single_script(script_info)
            if pattern:
                script_patterns.append(pattern)
        
        # Group similar patterns
        grouped_patterns = self._group_patterns(script_patterns)
        patterns["patterns"] = grouped_patterns
        
        print(f"  ✓ Found {len(grouped_patterns)} distinct framework usage patterns")
        
        return patterns
    
    def _analyze_single_script(self, script_info):
        """Analyze framework usage in a single script."""
        sql_text = script_info.get('sql_source', '')
        if not sql_text:
            return None
            
        cleaned_sql = clean_sql_text(sql_text)
        
        # Find framework procedure usage
        framework_calls = self._find_framework_calls(cleaned_sql)
        if not framework_calls:
            return None
            
        # Analyze script characteristics
        pattern = {
            "script_id": script_info.get('action_id', 'unknown'),
            "framework_calls": framework_calls,
            "call_count": len(framework_calls),
            "has_error_handling": 'BEGIN TRY' in sql_text.upper(),
            "has_transactions": 'BEGIN TRANSACTION' in sql_text.upper(),
            "has_validation": 'IF @' in sql_text and 'IS NULL' in sql_text.upper(),
            "complexity_score": len(framework_calls) + sql_text.count('IF') + sql_text.count('WHILE')
        }
        
        return pattern
    
    def _find_framework_calls(self, sql_text):
        """Find all framework procedure calls in SQL text."""
        calls = []
        
        # Simple approach - look for EXEC statements
        lines = sql_text.split('\n')
        for line in lines:
            line_upper = line.upper().strip()
            if line_upper.startswith('EXEC '):
                # Extract procedure name
                parts = line_upper.split()
                if len(parts) >= 2:
                    proc_part = parts[1]
                    # Remove dbo. prefix if present
                    if proc_part.startswith('DBO.'):
                        proc_part = proc_part[4:]
                    
                    proc_name = proc_part.lower()
                    
                    # Check if it's a framework procedure
                    if proc_name in self.framework_procedures:
                        call_info = {
                            "procedure": self.framework_procedures[proc_name]['full_name'],
                            "short_name": proc_name
                        }
                        calls.append(call_info)
        
        return calls
    
    def _group_patterns(self, script_patterns):
        """Group similar patterns together."""
        grouped = {}
        
        for pattern in script_patterns:
            # Create a simple signature
            signature_parts = []
            
            if pattern["call_count"] == 1:
                signature_parts.append("single_call")
            elif pattern["call_count"] <= 3:
                signature_parts.append("multi_call")
            else:
                signature_parts.append("complex_call")
            
            if pattern["has_error_handling"]:
                signature_parts.append("with_error_handling")
            
            if pattern["has_transactions"]:
                signature_parts.append("transactional")
            
            if pattern["has_validation"]:
                signature_parts.append("with_validation")
            
            signature = "_".join(signature_parts)
            
            if signature not in grouped:
                grouped[signature] = {
                    "signature": signature,
                    "description": self._describe_pattern(pattern),
                    "occurrence_count": 0,
                    "examples": [],
                    "common_procedures": {}
                }
            
            group = grouped[signature]
            group["occurrence_count"] += 1
            group["examples"].append(pattern)
            
            # Track procedure usage
            for call in pattern["framework_calls"]:
                proc_name = call["procedure"]
                group["common_procedures"][proc_name] = group["common_procedures"].get(proc_name, 0) + 1
        
        # Convert to list and filter
        result = []
        for signature, group in grouped.items():
            if group["occurrence_count"] >= 2:  # Only include patterns that occur multiple times
                group["average_complexity"] = sum(ex["complexity_score"] for ex in group["examples"]) / len(group["examples"])
                result.append(group)
        
        # Sort by occurrence count
        result.sort(key=lambda x: x["occurrence_count"], reverse=True)
        
        return result
    
    def _describe_pattern(self, pattern):
        """Create human-readable description of pattern."""
        call_count = pattern["call_count"]
        
        if call_count == 1:
            base = "Single framework procedure call"
        elif call_count <= 3:
            base = f"Multiple framework procedures ({call_count} calls)"
        else:
            base = f"Complex framework workflow ({call_count} procedures)"
        
        additions = []
        
        if pattern["has_error_handling"]:
            additions.append("with error handling")
        
        if pattern["has_transactions"]:
            additions.append("using transactions")
        
        if pattern["has_validation"]:
            additions.append("with validation")
        
        if additions:
            return base + " " + ", ".join(additions)
        
        return base
