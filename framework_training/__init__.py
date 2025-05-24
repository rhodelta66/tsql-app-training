"""
TSQL.APP Framework Training Data Generator

This package extracts framework usage patterns from real applications
and generates generic training materials for learning the framework.
"""

from .pattern_analyzer import FrameworkPatternAnalyzer
from .training_generator import TrainingExampleGenerator  
from .relationship_analyzer import ProcedureRelationshipAnalyzer
from .utils import save_json_file, load_json_file

__version__ = "1.0.0"
__author__ = "TSQL.APP Training System"

def generate_all_training_materials(framework_api_details, action_scripts_corpus, output_dir="training_output"):
    """
    Main function to generate all training materials.
    Call this from your main script.
    """
    print(f"\n=== TSQL.APP FRAMEWORK TRAINING GENERATOR v{__version__} ===")
    
    # Initialize analyzers
    pattern_analyzer = FrameworkPatternAnalyzer(framework_api_details)
    relationship_analyzer = ProcedureRelationshipAnalyzer(framework_api_details)
    training_generator = TrainingExampleGenerator(framework_api_details)
    
    results = {}
    
    # 1. Analyze framework usage patterns
    print("\n1. Analyzing framework usage patterns...")
    usage_patterns = pattern_analyzer.analyze_scripts(action_scripts_corpus)
    results['usage_patterns'] = usage_patterns
    save_json_file(f"{output_dir}/framework_usage_patterns.json", usage_patterns)
    
    # 2. Analyze procedure relationships
    print("\n2. Analyzing procedure relationships...")
    relationships = relationship_analyzer.analyze_relationships(action_scripts_corpus)
    results['relationships'] = relationships
    save_json_file(f"{output_dir}/procedure_relationships.json", relationships)
    
    # 3. Generate training examples
    print("\n3. Generating training examples...")
    training_examples = training_generator.generate_examples(usage_patterns, relationships)
    results['training_examples'] = training_examples
    save_json_file(f"{output_dir}/training_examples.json", training_examples)
    
    # 4. Generate summary report
    print("\n4. Creating summary report...")
    summary = create_summary_report(results)
    save_json_file(f"{output_dir}/training_summary.json", summary)
    
    print(f"\n=== TRAINING GENERATION COMPLETE ===")
    print(f"Generated {len(training_examples.get('examples', []))} training examples")
    print(f"Found {len(usage_patterns.get('patterns', []))} usage patterns")
    print(f"Output files saved to '{output_dir}/' directory")
    
    return results

def create_summary_report(results):
    """Create a summary report of all generated training materials."""
    from datetime import datetime
    
    return {
        "generation_date": datetime.now().isoformat(),
        "summary": {
            "usage_patterns_found": len(results.get('usage_patterns', {}).get('patterns', [])),
            "training_examples_generated": len(results.get('training_examples', {}).get('examples', [])),
            "procedures_analyzed": len(results.get('relationships', {}).get('procedures', {})),
        },
        "files_generated": [
            "framework_usage_patterns.json",
            "procedure_relationships.json", 
            "training_examples.json",
            "training_summary.json"
        ]
    }
