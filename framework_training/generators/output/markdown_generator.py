from typing import Dict, List
import os


class MarkdownGenerator:
    """Generator for creating training materials in Markdown format."""
    
    def __init__(self, output_dir: str = "training_materials"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_markdown(self, training_materials: Dict) -> None:
        """Generate all training materials in Markdown format."""
        # Generate examples markdown
        self._generate_examples_markdown(training_materials["examples"])
        
        # Generate curriculum markdown
        self._generate_curriculum_markdown(training_materials["curriculum"])
        
        # Generate assessments markdown
        self._generate_assessments_markdown(training_materials["assessments"])
        
        # Generate statistics markdown
        self._generate_statistics_markdown(training_materials["statistics"])
    
    def _generate_examples_markdown(self, examples: List[Dict]) -> None:
        """Generate markdown files for training examples."""
        examples_dir = os.path.join(self.output_dir, "examples")
        os.makedirs(examples_dir, exist_ok=True)
        
        for example in examples:
            filename = f"{example['example_id']}.md"
            filepath = os.path.join(examples_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self._format_example_markdown(example))
    
    def _format_example_markdown(self, example: Dict) -> str:
        """Format a single example as markdown."""
        md = []
        md.append(f"# {example['example_id']}")
        md.append(f"## Pattern Frequency: {example['pattern_frequency']}")
        md.append(f"## Complexity Level: {example['complexity_level']}")
        
        md.append("\n## Learning Objectives:")
        for obj in example['learning_objectives']:
            md.append(f"- {obj}")
        
        md.append("\n## Example Script:")
        md.append("```")
        md.append(example['example_script'])
        md.append("```")
        
        md.append("\n## Category: {example['category']}")
        return '\n'.join(md)
    
    def _generate_curriculum_markdown(self, curriculum: Dict) -> None:
        """Generate markdown for the curriculum."""
        filepath = os.path.join(self.output_dir, "curriculum.md")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Training Curriculum\n\n")
            for section, procedures in curriculum.items():
                f.write(f"## {section.title()}\n\n")
                for proc in procedures:
                    f.write(f"- {proc}\n")
    
    def _generate_assessments_markdown(self, assessments: List[Dict]) -> None:
        """Generate markdown for assessments."""
        filepath = os.path.join(self.output_dir, "assessments.md")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Skill Assessments\n\n")
            for i, assessment in enumerate(assessments, 1):
                f.write(f"## Assessment {i}\n\n")
                f.write(f"**Type:** {assessment['type']}\n\n")
                f.write(f"**Description:** {assessment['description']}\n\n")
                f.write(f"**Difficulty:** {assessment['difficulty']}\n\n")
                f.write("---\n\n")
    
    def _generate_statistics_markdown(self, stats: Dict) -> None:
        """Generate markdown for statistics."""
        filepath = os.path.join(self.output_dir, "statistics.md")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Training Material Statistics\n\n")
            f.write(f"## Total Examples: {stats['total_examples']}\n\n")
            f.write(f"## Procedure Coverage: {stats['procedure_coverage']:.2%}\n\n")
            f.write("## Difficulty Distribution:\n\n")
            for level, pct in stats['difficulty_progression']['difficulty_distribution'].items():
                f.write(f"- {level.title()}: {pct:.2%}\n")
