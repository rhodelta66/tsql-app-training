# TSQL.APP Framework Training Data Generator

A sophisticated system that automatically extracts framework usage patterns from real application scripts and generates comprehensive training materials for learning the TSQL.APP framework.

## 🎯 **Project Overview**

This project solves a critical challenge: **How to create effective training materials for a custom framework when you have real-world usage examples but need to make them generic and educational.**

The system analyzes production-quality scripts from any TSQL.APP solution (WMS, ERP, CRM, etc.) and automatically generates:
- **Framework usage patterns** - How procedures are typically used together
- **Procedure relationships** - Which procedures commonly work together
- **Training examples** - Complete, runnable scripts with educational annotations
- **Learning progressions** - From beginner to expert level examples

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    TSQL.APP Application                         │
│                  (WMS, ERP, CRM, etc.)                         │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                Metadata Explorer                                │
│          (Your existing main script)                           │
│  • Discovers framework procedures                              │
│  • Extracts parameter information                              │
│  • Fetches real application scripts                            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│            Framework Training Generator                         │
│                 (This project)                                 │
│                                                                 │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ Pattern         │ │ Relationship    │ │ Training        │   │
│  │ Analyzer        │ │ Analyzer        │ │ Generator       │   │
│  │                 │ │                 │ │                 │   │
│  │ • Error handling│ │ • Co-occurrence │ │ • Script        │   │
│  │ • Transactions  │ │ • Dependencies  │ │   templates     │   │
│  │ • Validation    │ │ • Workflows     │ │ • Learning      │   │
│  │ • Complexity    │ │ • Clusters      │ │   objectives    │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                Training Materials                               │
│                                                                 │
│  • framework_usage_patterns.json                               │
│  • procedure_relationships.json                                │
│  • training_examples.json                                      │
│  • training_summary.json                                       │
└─────────────────────────────────────────────────────────────────┘
```

## 🔍 **How It Works**

### **1. Pattern Analysis**
The system examines real application scripts and identifies:

- **Framework Usage Patterns**: How procedures are called (single, multiple, complex workflows)
- **Error Handling Styles**: TRY-CATCH, RAISERROR, early returns
- **Transaction Patterns**: Simple, rollback-enabled, savepoint-based
- **Validation Approaches**: NULL checks, length validation, business rules
- **Complexity Indicators**: Script structure, conditional logic, loops

### **2. Relationship Discovery**
Analyzes co-occurrence of procedures to understand:

- **Procedure Dependencies**: Which procedures are commonly used together
- **Workflow Patterns**: Typical sequences of procedure calls
- **Relationship Strength**: How frequently procedures appear together
- **Procedure Clusters**: Groups of procedures that form logical units

### **3. Training Generation**
Creates educational content based on discovered patterns:

- **Beginner Examples**: Single procedure calls with basic parameters
- **Intermediate Examples**: Multi-procedure workflows with validation
- **Advanced Examples**: Complex patterns with transactions and error handling
- **Expert Examples**: Enterprise-level patterns with optimization techniques

## 📊 **Input and Output**

### **Input Sources**
```sql
-- Real application scripts from tables like:
api_card_actions
├── id: 1001
├── name: "Create User Account"
└── sql_script: "EXEC sp_api_user_create @name = @user_name, @email = @email"

api_actions  
├── id: 2001
├── name: "Process Order"
└── unparsed_sql: "BEGIN TRY EXEC sp_api_order_process... END TRY"
```

### **Framework Metadata**
```sql
-- Discovered from system tables:
sys.objects + sys.parameters + sys.sql_modules
├── dbo.sp_api_user_create
│   ├── @name nvarchar(255) 
│   └── @email nvarchar(255)
└── dbo.sp_api_order_process
    ├── @order_id int
    └── @user_id int
```

### **Generated Outputs**

#### **1. Framework Usage Patterns**
```json
{
  "patterns": [
    {
      "description": "Single framework procedure call with error handling",
      "occurrence_count": 45,
      "average_complexity": 12.3,
      "common_procedures": {
        "dbo.sp_api_user_create": 15,
        "dbo.sp_api_user_validate": 12
      }
    }
  ]
}
```

#### **2. Procedure Relationships**
```json
{
  "procedures": {
    "dbo.sp_api_user_create": {
      "related_procedures": {
        "dbo.sp_api_user_validate": {
          "co_occurrence_count": 23,
          "relationship_strength": 0.85
        }
      },
      "relationship_count": 3
    }
  }
}
```

#### **3. Training Examples**
```json
{
  "examples": [
    {
      "example_id": "pattern_example_1",
      "complexity_level": "intermediate",
      "learning_objectives": [
        "Learn single framework procedure call with error handling",
        "Master TRY-CATCH error handling patterns"
      ],
      "example_script": "-- Training Example: Single framework procedure call with error handling\n-- Pattern Frequency: 45 occurrences\n\n-- Parameter Setup\nDECLARE @name nvarchar(255) = N'Sample Name';\n\n-- Error handling pattern\nBEGIN TRY\n    EXEC dbo.sp_api_user_create @name = @name;\nEND TRY\nBEGIN CATCH\n    PRINT 'Error occurred: ' + ERROR_MESSAGE();\n    THROW;\nEND CATCH;"
    }
  ]
}
```

## 🛠️ **Technical Implementation**

### **Core Components**

#### **Pattern Analyzer** (`pattern_analyzer.py`)
- Parses SQL scripts to identify framework procedure calls
- Analyzes script structure (conditionals, loops, transactions)
- Categorizes error handling approaches
- Groups similar patterns by signature
- Calculates complexity scores

#### **Relationship Analyzer** (`relationship_analyzer.py`)
- Tracks procedure co-occurrence across scripts
- Builds relationship networks between procedures
- Identifies procedure clusters and workflows
- Calculates relationship strength metrics

#### **Training Generator** (`training_generator.py`)
- Creates educational scripts from identified patterns
- Generates realistic parameter examples
- Adds educational comments and learning objectives
- Scales complexity from beginner to expert level

#### **Utilities** (`utils.py`)
- SQL text cleaning and normalization
- JSON file handling with proper formatting
- Sample value generation for parameters
- Common helper functions

### **Key Algorithms**

#### **Pattern Signature Creation**
```python
def create_pattern_signature(pattern):
    elements = []
    
    # Procedure call complexity
    if call_count == 1:
        elements.append("single_call")
    elif call_count <= 3:
        elements.append("multi_call")
    else:
        elements.append("complex_call")
    
    # Additional characteristics
    if has_error_handling:
        elements.append("with_error_handling")
    if has_transactions:
        elements.append("transactional")
    
    return "_".join(elements)
```

#### **Relationship Strength Calculation**
```python
def calculate_relationship_strength(proc1_usage, proc2_usage, co_occurrence):
    # Strength based on how often they appear together vs individually
    return (co_occurrence * 2) / (proc1_usage + proc2_usage)
```

## 🎓 **Educational Value**

### **Learning Progression**
The system creates a natural learning progression:

1. **Foundation** (Beginner)
   - Basic procedure syntax
   - Parameter declaration and passing
   - Simple variable usage

2. **Robustness** (Intermediate)
   - Error handling with TRY-CATCH
   - Parameter validation patterns
   - Basic transaction usage

3. **Workflows** (Advanced)
   - Multi-procedure orchestration
   - Complex error handling
   - Transaction management

4. **Enterprise** (Expert)
   - Performance optimization
   - Advanced patterns
   - Large-scale implementations

### **Teaching Features**
- **Real-world Based**: Patterns extracted from actual production code
- **Progressive Difficulty**: Clear advancement from simple to complex
- **Comprehensive Comments**: Educational annotations explain each concept
- **Best Practices**: Incorporates proven approaches from real applications
- **Framework-Focused**: Teaches framework usage, not business domain specifics

## 🔧 **Setup and Integration**

### **Quick Start**
1. **Run the setup script**:
   ```bash
   python setup_framework_training.py
   ```

2. **Integrate with your existing metadata explorer**:
   ```python
   # Add to metadata_explorer_final.py
   from framework_training import generate_all_training_materials
   
   # Call after data collection
   training_results = generate_all_training_materials(
       current_framework_api, 
       current_action_script_corpus
   )
   ```

3. **Generate training materials**:
   ```bash
   python metadata_explorer_final.py
   ```

### **Configuration Options**
```python
# Environment variables for customization
FRAMEWORK_OBJECT_PATTERNS = "sp_api_%,sp_sys_%,context_%"
MAX_CARD_ACTIONS_TO_CORPUS = "250"
MAX_API_ACTIONS_TO_CORPUS = "150"
TRAINING_OUTPUT_DIR = "training_output"
```

## 📈 **Benefits and Impact**

### **For Development Teams**
- **Faster Onboarding**: New developers learn framework patterns quickly
- **Consistent Usage**: Training promotes standardized framework usage
- **Best Practices**: Captures and teaches proven approaches
- **Documentation**: Automatically generated, always up-to-date

### **For Framework Maintainers**
- **Usage Insights**: Understand how the framework is actually used
- **Pattern Identification**: Discover common usage patterns and anti-patterns
- **Training Material**: Comprehensive educational content without manual effort
- **Quality Assurance**: Identify areas where better guidance is needed

### **For Organizations**
- **Knowledge Transfer**: Preserve institutional knowledge about framework usage
- **Training Efficiency**: Reduce time needed to train new team members
- **Code Quality**: Promote consistent, high-quality framework usage
- **Maintenance**: Easier maintenance through better understanding

## 🔮 **Future Enhancements**

### **Planned Features**
- **Interactive Learning Modules**: Web-based training interface
- **Performance Analysis**: Identify optimization opportunities in patterns
- **Anti-pattern Detection**: Identify and teach avoidance of problematic patterns
- **Custom Training Paths**: Personalized learning based on role and experience
- **Integration Testing**: Automated testing of generated examples

### **Advanced Analytics**
- **Usage Trend Analysis**: Track how framework usage evolves over time
- **Performance Correlation**: Link patterns to performance characteristics
- **Error Pattern Analysis**: Identify common error scenarios and solutions
- **Framework Evolution**: Guide framework development based on usage patterns

## 🏆 **Success Metrics**

### **Quality Indicators**
- **Pattern Coverage**: Percentage of framework procedures covered in training
- **Real-world Accuracy**: How closely generated examples match actual usage
- **Learning Effectiveness**: Improvement in developer productivity after training
- **Adoption Rate**: How frequently the training materials are used

### **Measurable Outcomes**
- Reduced onboarding time for new developers
- Increased consistency in framework usage across teams
- Decreased framework-related support requests
- Improved code quality in framework-dependent applications

---

**This project transforms the challenge of framework training from a manual, time-consuming process into an automated, continuously-improving system that scales with your codebase and evolves with your framework usage patterns.**