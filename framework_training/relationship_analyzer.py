from datetime import datetime
from .utils import clean_sql_text
import json
import os
from collections import Counter

class RelationshipAnalyzer:
    """Analyzes relationships between stored procedures."""
    
    def __init__(self, framework_api_details, framework_knowledge=None):
        self.framework_api = framework_api_details
        self.framework_knowledge = framework_knowledge or {}
        self.relationships = {}
        self.relationship_counts = Counter()
        
    def _should_ignore_relationship(self, proc1, proc2):
        """Check if relationship should be ignored based on framework knowledge."""
        ignore_rules = self.framework_knowledge.get('relationship_rules', {})
        
        # Check if proc1 has ignore rules
        if proc1 in ignore_rules:
            if proc2 in ignore_rules[proc1].get('ignore_relationships_with', []):
                return True
                
        # Check if proc2 has ignore rules
        if proc2 in ignore_rules:
            if proc1 in ignore_rules[proc2].get('ignore_relationships_with', []):
                return True
                
        return False

class ProcedureRelationshipAnalyzer:
    """Analyzes relationships between framework procedures."""
    
    def __init__(self, framework_api_details, framework_knowledge=None):
        self.framework_api = framework_api_details
        self.framework_knowledge = framework_knowledge or {}
        self.framework_procedures = self._build_procedure_lookup()
    
    def _build_procedure_lookup(self):
        """Build lookup of framework procedures."""
        procedures = {}
        for obj in self.framework_api:
            if obj.get('object_type_short') == 'P':
                proc_name = obj['object_name']
                full_name = f"{obj['schema_name']}.{proc_name}"
                procedures[proc_name.lower()] = {
                    'full_name': full_name,
                    'short_name': proc_name
                }
        return procedures
    
    def analyze_relationships(self, action_scripts_corpus):
        """Analyze procedure relationships from scripts."""
        print("  Analyzing procedure relationships...")
        
        relationships = {
            "metadata": {
                "analysis_date": datetime.now().isoformat(),
                "scripts_analyzed": len(action_scripts_corpus),
                "procedures_found": len(self.framework_procedures)
            },
            "procedures": {},
            "relationship_summary": []
        }
        
        # Initialize procedure data
        for proc_info in self.framework_procedures.values():
            full_name = proc_info['full_name']
            relationships["procedures"][full_name] = {
                "procedure_name": full_name,
                "related_procedures": {},
                "relationship_count": 0
            }
        
        # Track co-occurrence
        co_occurrence = {}
        
        for script_info in action_scripts_corpus:
            sql_text = script_info.get('sql_source', '')
            if not sql_text:
                continue
                
            # Find framework procedures in this script
            found_procs = self._find_procedures_in_script(sql_text)
            
            # Record co-occurrences for procedures that appear together
            if len(found_procs) > 1:
                for i, proc1 in enumerate(found_procs):
                    for proc2 in found_procs[i+1:]:
                        # Skip relationships that should be ignored based on framework knowledge
                        if self._should_ignore_relationship(proc1, proc2):
                            continue
                            
                        # Create consistent key (alphabetical order)
                        key = tuple(sorted([proc1, proc2]))
                        co_occurrence[key] = co_occurrence.get(key, 0) + 1
        
        # Build relationship data
        for (proc1, proc2), co_count in co_occurrence.items():
            if co_count >= 2:  # Only include relationships that occur 2+ times
                # Add to both procedures' relationship lists
                if proc1 in relationships["procedures"]:
                    relationships["procedures"][proc1]["related_procedures"][proc2] = {
                        "co_occurrence_count": co_count
                    }
                    relationships["procedures"][proc1]["relationship_count"] += 1
                
                if proc2 in relationships["procedures"]:
                    relationships["procedures"][proc2]["related_procedures"][proc1] = {
                        "co_occurrence_count": co_count
                    }
                    relationships["procedures"][proc2]["relationship_count"] += 1
        
        # Create relationship summary
        most_connected = sorted(
            [(proc, data["relationship_count"]) 
             for proc, data in relationships["procedures"].items()],
            key=lambda x: x[1], reverse=True
        )[:10]
        
        relationships["relationship_summary"] = [
            {"procedure": proc, "connection_count": count} 
            for proc, count in most_connected if count > 0
        ]
        
        connected_proc_count = len([p for p in relationships['procedures'].values() if p['relationship_count'] > 0])
        print(f"  ✓ Found relationships for {connected_proc_count} procedures")
        
        return relationships
    
    def _should_ignore_relationship(self, proc1, proc2):
        """Check if relationship should be ignored based on framework knowledge."""
        ignore_rules = self.framework_knowledge.get('relationship_rules', {})
        
        # Check if proc1 has ignore rules
        if proc1 in ignore_rules:
            if proc2 in ignore_rules[proc1].get('ignore_relationships_with', []):
                return True
                
        # Check if proc2 has ignore rules
        if proc2 in ignore_rules:
            if proc1 in ignore_rules[proc2].get('ignore_relationships_with', []):
                return True
                
        return False
    
    def _find_procedures_in_script(self, sql_text):
        """Find framework procedures used in a script."""
        found = []
        
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
                        full_name = self.framework_procedures[proc_name]['full_name']
                        if full_name not in found:
                            found.append(full_name)
        
        return found
