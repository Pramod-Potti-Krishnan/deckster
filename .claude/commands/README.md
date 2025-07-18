# Claude Commands for Deckster Development

This directory contains custom Claude commands to accelerate and standardize development workflows.

## Available Commands

### build-agent-architecture
**Purpose**: Analyzes a product concept document and generates a comprehensive solution architecture for a PydanticAI-based agent.

**Usage**:
```
/build-agent-architecture <path-to-product-concept.md>
```

**Example**:
```
/build-agent-architecture /home/gmk/Software/deckster.xyz/deckster/docs/example-product-concept.md
```

**Output**: A complete solution architecture including:
- PydanticAI agent design with base models, configuration, and tools
- Context and memory management integration
- Logfire logging implementation
- LangGraph workflow design
- Detailed implementation plan with tasks
- Code examples and best practices

## How Claude Commands Work

Claude commands are markdown files that provide structured instructions for complex, repeatable tasks. When you invoke a command, Claude:

1. Reads the command file for instructions
2. Analyzes any input files or parameters
3. Follows the defined process step-by-step
4. Generates comprehensive outputs based on the command's template

## Creating New Commands

To create a new command:

1. Create a new `.md` file in this directory
2. Name it descriptively (e.g., `generate-test-suite.md`)
3. Structure it with:
   - Clear overview and purpose
   - Usage instructions
   - Step-by-step process
   - Output format specification
   - Best practices and considerations

## Best Practices

1. **Be Specific**: Commands should have clear, well-defined outputs
2. **Include Examples**: Show sample inputs and expected outputs
3. **Reference Standards**: Link to relevant documentation and patterns
4. **Consider Context**: Commands should work within the existing architecture
5. **Document Assumptions**: Clearly state any assumptions made

## Command Development Workflow

1. **Identify Repetitive Tasks**: Look for complex tasks you do repeatedly
2. **Document the Process**: Write down the steps you follow
3. **Create the Command**: Structure it as a reusable template
4. **Test and Refine**: Use the command and improve based on results
5. **Share and Document**: Update this README with new commands

## Integration with Deckster

All commands in this directory are designed to work with Deckster's:
- Architecture patterns
- Coding standards
- Documentation style
- Development workflow

They reference key documents in `/docs/clean_documents/` for consistency.