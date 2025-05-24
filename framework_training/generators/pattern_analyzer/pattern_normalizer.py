from typing import Dict, Optional


def normalize_patterns(patterns: Dict, procedure_relationships: Optional[Dict] = None) -> Dict:
    """Clean and normalize extracted patterns."""
    # Clean common structures
    patterns["common_structures"] = list(set(patterns["common_structures"]))
    
    # Clean parameter usage patterns
    for key, subdict in patterns["parameter_usage_patterns"].items():
        for subkey, subsubdict in subdict.items():
            try:
                patterns["parameter_usage_patterns"][key][subkey] = list(set(subsubdict))
            except TypeError:
                # If list contains unhashable types, keep original
                pass
    
    # Clean error handling patterns
    patterns["error_handling_patterns"] = list(set(patterns["error_handling_patterns"]))
    
    # Clean conditional patterns
    patterns["conditional_logic_patterns"] = list(set(patterns["conditional_logic_patterns"]))
    
    # Clean variable naming conventions
    patterns["variable_naming_conventions"] = {
        prefix: list(set(values)) 
        for prefix, values in patterns["variable_naming_conventions"].items()
    }
    
    # Clean procedure call patterns
    patterns["procedure_call_patterns"] = {
        proc: list(set(calls)) 
        for proc, calls in patterns["procedure_call_patterns"].items()
    }
    
    # Clean business logic patterns
    patterns["business_logic_patterns"] = list(set(patterns["business_logic_patterns"]))
    
    return patterns
