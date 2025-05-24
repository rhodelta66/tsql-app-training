from generators.synthetic_training_generator import generate_all_training_materials

# Sample framework API details
framework_api_details = [
    {
        'schema_name': 'dbo',
        'object_name': 'sp_user_create',
        'object_type_short': 'P',
        'parameters': [
            {'name': '@username', 'type': 'nvarchar(50)'}
        ],
        'complexity': 'simple'
    },
    {
        'schema_name': 'dbo',
        'object_name': 'sp_user_update',
        'object_type_short': 'P',
        'parameters': [
            {'name': '@user_id', 'type': 'int'},
            {'name': '@new_email', 'type': 'nvarchar(100)'}
        ],
        'complexity': 'simple'
    },
    {
        'schema_name': 'dbo',
        'object_name': 'sp_user_transfer',
        'object_type_short': 'P',
        'parameters': [
            {'name': '@user_id', 'type': 'int'},
            {'name': '@old_department', 'type': 'int'},
            {'name': '@new_department', 'type': 'int'},
            {'name': '@transfer_date', 'type': 'datetime'}
        ],
        'complexity': 'complex'
    }
]

# Sample script patterns
script_patterns = {
    'simple_patterns': [
        'EXEC dbo.sp_user_create @username = @username',
        'EXEC dbo.sp_user_update @user_id = @user_id, @new_email = @new_email'
    ]
}

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
