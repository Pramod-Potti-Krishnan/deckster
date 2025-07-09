# DOUBLE-CLICK INSTRUCTIONS FOR STATE: ASK_CLARIFYING_QUESTIONS

## State 2: ASK_CLARIFYING_QUESTIONS

**Your Current Task:** The user has provided their initial topic. Your job is to analyze their request and formulate a single, concise set of 3-5 critical questions to gather the most important missing information needed to build a high-quality outline.

**Your Required Output:** You must output a single JSON object containing a `questions` key, which holds a list of strings.

**Example Output:**
```json
{
  "questions": [
    "Who is the target audience for this presentation (e.g., students, policymakers, general public)?",
    "What is the primary goal? Is it to inform, persuade, or something else?",
    "Do you have a rough idea of how long the presentation should be?",
    "Are there any specific case studies or data points you'd like to include?"
  ]
}
```