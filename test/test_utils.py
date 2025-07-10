"""
Shared utilities for testing the Director agent.
"""
import os
import sys
from typing import Dict, Any, List
from datetime import datetime
import json

# Add parent directory to path to import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.agents import StateContext, UserIntent, ClarifyingQuestions, ConfirmationPlan, PresentationStrawman


class Colors:
    """Terminal colors for output formatting."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def format_state(state: str) -> str:
    """Format state name with icon."""
    return f"{Colors.CYAN}📍 [{state}]{Colors.ENDC}"


def format_user_message(message: str) -> str:
    """Format user message with color."""
    return f"{Colors.GREEN}User: {message}{Colors.ENDC}"


def format_agent_message(message: str) -> str:
    """Format agent message with color."""
    return f"{Colors.BLUE}Deckster: {message}{Colors.ENDC}"


def format_error(message: str) -> str:
    """Format error message with color."""
    return f"{Colors.RED}Error: {message}{Colors.ENDC}"


def format_success(message: str) -> str:
    """Format success message with color."""
    return f"{Colors.GREEN}✓ {message}{Colors.ENDC}"


def print_separator() -> None:
    """Print a visual separator."""
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")


def create_initial_context(state: str = "PROVIDE_GREETING") -> StateContext:
    """Create an initial state context."""
    return StateContext(
        current_state=state,
        conversation_history=[],
        session_data={}
    )


def add_to_history(context: StateContext, role: str, content: Any) -> None:
    """Add a message to conversation history."""
    context.conversation_history.append({
        "role": role,
        "content": content if isinstance(content, str) else content.model_dump() if hasattr(content, 'model_dump') else str(content),
        "timestamp": datetime.now().isoformat()
    })


def format_clarifying_questions(questions: ClarifyingQuestions) -> str:
    """Format clarifying questions for display."""
    output = "I have a few questions to better understand your needs:\n"
    for i, question in enumerate(questions.questions, 1):
        output += f"{i}. {question}\n"
    return output


def format_confirmation_plan(plan: ConfirmationPlan) -> str:
    """Format confirmation plan for display."""
    output = f"\n{Colors.BOLD}Presentation Plan:{Colors.ENDC}\n"
    output += f"\nSummary: {plan.summary_of_user_request}\n"
    output += f"\nKey Assumptions:\n"
    for assumption in plan.key_assumptions:
        output += f"• {assumption}\n"
    output += f"\nProposed Slides: {plan.proposed_slide_count}\n"
    return output


def format_strawman_summary(strawman: PresentationStrawman) -> str:
    """Format strawman summary for display with all fields."""
    output = f"\n{Colors.BOLD}📊 Presentation Strawman:{Colors.ENDC}\n"
    output += f"\n🎯 Title: {strawman.main_title}\n"
    output += f"🎨 Theme: {strawman.overall_theme}\n"
    output += f"👥 Audience: {strawman.target_audience}\n"
    output += f"⏱️  Duration: {strawman.presentation_duration} minutes\n"
    output += f"\n{Colors.BOLD}Slides ({len(strawman.slides)}):{Colors.ENDC}\n"
    
    for slide in strawman.slides:
        output += f"\n{Colors.BOLD}📄 {slide.slide_id}: {slide.title}{Colors.ENDC}\n"
        output += f"  Type: {slide.slide_type}\n"
        output += f"  Narrative: {slide.narrative}\n"
        
        # Key Points
        if hasattr(slide, 'key_points') and slide.key_points:
            output += f"\n  {Colors.CYAN}📝 Key Points:{Colors.ENDC}\n"
            for point in slide.key_points:
                output += f"    • {point}\n"
        
        # Analytics Needed
        if hasattr(slide, 'analytics_needed'):
            output += f"\n  {Colors.YELLOW}📈 Analytics Needed:{Colors.ENDC} "
            if slide.analytics_needed:
                output += f"\n    {slide.analytics_needed}\n"
            else:
                output += "None\n"
        
        # Visuals Needed
        if hasattr(slide, 'visuals_needed'):
            output += f"\n  {Colors.HEADER}🎨 Visuals Needed:{Colors.ENDC} "
            if slide.visuals_needed:
                output += f"\n    {slide.visuals_needed}\n"
            else:
                output += "None\n"
        
        # Diagrams Needed
        if hasattr(slide, 'diagrams_needed'):
            output += f"\n  {Colors.BLUE}🔧 Diagrams Needed:{Colors.ENDC} "
            if slide.diagrams_needed:
                output += f"\n    {slide.diagrams_needed}\n"
            else:
                output += "None\n"
        
        # Structure Preference
        if hasattr(slide, 'structure_preference') and slide.structure_preference:
            output += f"\n  {Colors.GREEN}📐 Layout:{Colors.ENDC} {slide.structure_preference}\n"
        
        output += f"\n  {'-' * 50}\n"
    
    return output


def format_validation_results(slide, validation_rules: dict) -> str:
    """Format detailed validation results for a slide."""
    output = f"\n{Colors.BOLD}🔍 Validating Slide {slide.slide_id}:{Colors.ENDC}\n"
    
    # Check required fields
    for field in validation_rules["required_slide_fields"]:
        if hasattr(slide, field) and getattr(slide, field) is not None:
            output += f"  ✅ {field}: Present\n"
        else:
            output += f"  ❌ {field}: Missing\n"
    
    # Check important optional fields
    for field in validation_rules.get("important_slide_fields", []):
        if hasattr(slide, field):
            value = getattr(slide, field)
            if value is not None:
                # Check if it's in the correct format for asset fields
                if field in ["analytics_needed", "visuals_needed", "diagrams_needed"]:
                    if "**Goal:**" in str(value) and "**Content:**" in str(value) and "**Style:**" in str(value):
                        output += f"  ✅ {field}: Present (Goal/Content/Style format)\n"
                    else:
                        output += f"  ⚠️  {field}: Present but not in Goal/Content/Style format\n"
                else:
                    output += f"  ✅ {field}: Present\n"
            else:
                output += f"  ⚠️  {field}: None/Empty\n"
        else:
            output += f"  ⚠️  {field}: Not defined\n"
    
    return output


def save_conversation(context: StateContext, filename: str) -> None:
    """Save conversation to a JSON file."""
    data = {
        "timestamp": datetime.now().isoformat(),
        "current_state": context.current_state,
        "conversation_history": context.conversation_history,
        "session_data": context.session_data
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(format_success(f"Conversation saved to {filename}"))


def load_conversation(filename: str) -> StateContext:
    """Load conversation from a JSON file."""
    with open(filename, 'r') as f:
        data = json.load(f)
    
    context = StateContext(
        current_state=data["current_state"],
        conversation_history=data["conversation_history"],
        session_data=data["session_data"]
    )
    
    print(format_success(f"Conversation loaded from {filename}"))
    return context


def create_mock_response(state: str, scenario: str = "default") -> str:
    """Create mock user responses for different states and scenarios."""
    responses = {
        "PROVIDE_GREETING": {
            "default": "I need to create a presentation about AI in healthcare",
            "executive": "I need a board presentation on Q3 financial results",
            "technical": "I want to present our new microservices architecture to the engineering team"
        },
        "ASK_CLARIFYING_QUESTIONS": {
            "default": "1. Hospital administrators and doctors\n2. To inform about AI benefits\n3. 15 minutes\n4. Yes, I have some case studies from Mayo Clinic",
            "executive": "1. Board members and investors\n2. Show strong Q3 performance\n3. 10 minutes\n4. Revenue growth 32%, EBITDA up 45%",
            "technical": "1. Senior engineers and architects\n2. Get buy-in for migration\n3. 30 minutes\n4. Performance benchmarks and migration timeline"
        },
        "CREATE_CONFIRMATION_PLAN": {
            "default": "yes",
            "executive": "yes", 
            "technical": "yes"
        },
        "GENERATE_STRAWMAN": {
            "default": "Make slide 3 more visual with patient success stories",
            "executive": "Add more detail to the financial metrics slide",
            "technical": "Include a diagram showing the system architecture"
        }
    }
    
    return responses.get(state, {}).get(scenario, "continue")