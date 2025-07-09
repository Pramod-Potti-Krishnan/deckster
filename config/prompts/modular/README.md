# Modular Prompt Architecture

This directory contains the modular prompt system for Deckster, designed to reduce token usage and improve maintainability.

## Structure

```
modular/
├── base_prompt.md                    # Core identity and workflow overview
├── provide_greeting.md               # State 1: Welcome message
├── ask_clarifying_questions.md       # State 2: Gather information
├── create_confirmation_plan.md       # State 3: Create plan
├── generate_strawman.md              # State 4: Generate full outline (includes all rules)
└── refine_strawman.md                # State 5: Refine based on feedback (includes all rules)
```

## Assembly Rules

### For PROVIDE_GREETING:
```
base_prompt.md + provide_greeting.md
```

### For ASK_CLARIFYING_QUESTIONS:
```
base_prompt.md + ask_clarifying_questions.md
```

### For CREATE_CONFIRMATION_PLAN:
```
base_prompt.md + create_confirmation_plan.md
```

### For GENERATE_STRAWMAN:
```
base_prompt.md + generate_strawman.md
```
*Note: generate_strawman.md includes all necessary components (presentation fields, slide rules, layout toolkit, asset guidelines) inline for complete context*

### For REFINE_STRAWMAN:
```
base_prompt.md + refine_strawman.md
```
*Note: refine_strawman.md includes all necessary components (presentation fields, slide rules, layout toolkit, asset guidelines) inline for complete context*

## Token Savings

- **Monolithic prompt**: ~2,864 tokens for all states
- **Modular approach**:
  - Simple states (GREETING, QUESTIONS, PLAN): ~300-500 tokens
  - Complex states (GENERATE, REFINE): ~1,200-1,500 tokens
- **Average reduction**: ~60-70% for simple states, ~45-50% for complex states

## Implementation Notes

1. The ContextBuilder should cache loaded modules to avoid repeated file I/O
2. Module concatenation should preserve markdown formatting
3. Each module should end with a newline for clean concatenation
4. The system should fall back to the monolithic prompt if module loading fails
5. GENERATE and REFINE states include all necessary components inline for better human readability and maintainability