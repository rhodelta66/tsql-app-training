from generators.synthetic_training_generator import generate_all_training_materials

import json

# Load framework API details from JSON file
with open('../framework_api_details.json', 'r', encoding='utf-8') as f:
    api_data = json.load(f)
    framework_api_details = api_data['api_objects']

# Filter to get only stored procedures
framework_api_details = [
    proc for proc in framework_api_details
    if proc.get('object_type_short') == 'P'
]

# Generate script patterns from real usage examples
script_patterns = {}
for proc in framework_api_details:
    if proc.get('real_usage_examples'):
        patterns = []
        for ex in proc['real_usage_examples']:
            if 'sql_source' in ex:
                patterns.append(ex['sql_source'])
        if patterns:
            script_patterns[proc['object_name']] = patterns

# Sample relationships
relationships = {
    'procedure_clusters': [
        ['dbo.sp_user_create', 'dbo.sp_user_update']
    ],
    'common_workflows': [
        ['dbo.sp_user_create', 'dbo.sp_user_update']
    ],
    'relationships': {
        'dbo.sp_user_create': ['dbo.sp_user_update'],
        'dbo.sp_user_update': ['dbo.sp_user_create']
    }
}

# Generate training materials with Markdown output
args = {
    'output_format': 'markdown',
    'output_dir': 'test_markdown_output',
    'simple_count': 2,
    'validation_count': 2,
    'crud_count': 2,
    'error_count': 2,
    'multi_count': 2,
    'advanced_count': 2
}

training_materials = generate_all_training_materials(
    framework_api_details,
    script_patterns,
    relationships,
    args
)

print("Training materials generated successfully!")
