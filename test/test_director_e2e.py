#!/usr/bin/env python3
"""
End-to-end automated testing tool for the Director agent.
Tests complete conversation flows through all states with predefined scenarios.
"""
import asyncio
import json
import argparse
import sys
import os
import warnings
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Suppress the PydanticAI warning about additionalProperties
warnings.filterwarnings("ignore", message=".*additionalProperties.*is not supported by Gemini.*")

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.director import DirectorAgent
from src.agents.intent_router import IntentRouter
from src.models.agents import StateContext, UserIntent
from src.workflows.state_machine import WorkflowOrchestrator
from test_utils import (
    Colors, format_state, format_user_message, format_agent_message,
    format_error, format_success, print_separator,
    create_initial_context, add_to_history,
    format_clarifying_questions, format_confirmation_plan,
    format_strawman_summary, save_conversation, format_validation_results
)


class DirectorE2ETester:
    """Automated end-to-end tester for Director agent."""
    
    def __init__(self, scenario_file: str = "test_scenarios.json"):
        """Initialize the tester with scenarios."""
        self.director = DirectorAgent()
        self.intent_router = IntentRouter()
        self.workflow = WorkflowOrchestrator()
        
        # Load test scenarios
        scenario_path = os.path.join(os.path.dirname(__file__), scenario_file)
        with open(scenario_path, 'r') as f:
            self.scenarios_data = json.load(f)
            self.scenarios = self.scenarios_data["scenarios"]
            self.validation_rules = self.scenarios_data["validation_rules"]
    
    def show_scenarios_menu(self):
        """Display available scenarios in a formatted menu."""
        print(f"\n{Colors.BOLD}🎯 Available Scenarios:{Colors.ENDC}")
        print("═" * 60)
        
        scenarios_list = [
            ("1", "default", "AI in Healthcare", "Standard presentation about AI applications in healthcare"),
            ("2", "executive", "Q3 Financial Results", "Board presentation on quarterly financial performance"),
            ("3", "technical", "Microservices Architecture", "Technical presentation for engineering team"),
            ("4", "educational", "Climate Change Basics", "Educational presentation for high school students"),
            ("5", "sales", "Product Launch", "Sales presentation for new SaaS product")
        ]
        
        for num, key, name, desc in scenarios_list:
            print(f"\n{Colors.BOLD}{num}️⃣  {name}{Colors.ENDC}")
            print(f"    {desc}")
    
    def show_interactive_menu(self) -> str:
        """Show interactive menu and get user choice."""
        print(f"\n{Colors.BOLD}🎯 Deckster E2E Test Suite{Colors.ENDC}")
        print("═" * 60)
        
        self.show_scenarios_menu()
        
        print(f"\n{Colors.YELLOW}Please select a scenario (1-5) or 'q' to quit:{Colors.ENDC} ", end="")
        
        scenario_map = {
            "1": "default",
            "2": "executive", 
            "3": "technical",
            "4": "educational",
            "5": "sales"
        }
        
        while True:
            choice = input().strip().lower()
            if choice == 'q':
                print(f"{Colors.YELLOW}Exiting...{Colors.ENDC}")
                return None
            elif choice in scenario_map:
                return scenario_map[choice]
            else:
                print(f"{Colors.RED}Invalid choice. Please enter 1-5 or 'q':{Colors.ENDC} ", end="")
    
    async def run_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Run a complete test scenario."""
        if scenario_name not in self.scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = self.scenarios[scenario_name]
        print(f"\n{Colors.BOLD}🎬 Running Scenario: {scenario['name']}{Colors.ENDC}")
        print(f"📖 Description: {scenario['description']}")
        print_separator()
        
        results = {
            "scenario": scenario_name,
            "name": scenario["name"],
            "passed": True,
            "errors": [],
            "states_completed": [],
            "outputs": {}
        }
        
        # Initialize context
        context = create_initial_context()
        
        try:
            # State 1: PROVIDE_GREETING
            print(f"\n{format_state('PROVIDE_GREETING')}")
            print("─" * 60)
            greeting = await self.director.process(context)
            print(format_agent_message(greeting))
            add_to_history(context, "assistant", greeting)
            results["states_completed"].append("PROVIDE_GREETING")
            results["outputs"]["greeting"] = greeting
            
            # Simulate user providing initial topic
            user_topic = scenario["responses"]["initial_topic"]
            print(format_user_message(user_topic))
            add_to_history(context, "user", user_topic)
            
            # Classify intent and transition to next state
            intent = await self.intent_router.classify(
                user_topic, 
                {
                    'current_state': context.current_state,
                    'recent_history': context.conversation_history[-3:] if context.conversation_history else []
                }
            )
            context.user_intent = intent
            
            # Save initial topic to session data (simulating what websocket handler does)
            context.session_data['user_initial_request'] = user_topic
            context.current_state = "ASK_CLARIFYING_QUESTIONS"
            
            # State 2: ASK_CLARIFYING_QUESTIONS
            print(f"\n{format_state('ASK_CLARIFYING_QUESTIONS')}")
            print("─" * 60)
            questions = await self.director.process(context)
            print(format_agent_message(format_clarifying_questions(questions)))
            add_to_history(context, "assistant", questions)
            results["states_completed"].append("ASK_CLARIFYING_QUESTIONS")
            results["outputs"]["questions"] = questions
            
            # Validate questions
            if not self._validate_questions(questions, results):
                return results
            
            # Simulate user answering questions
            user_answers = "\n".join(scenario["responses"]["clarifying_answers"])
            print(format_user_message(user_answers))
            add_to_history(context, "user", user_answers)
            
            # Save clarifying answers to session data
            context.session_data['clarifying_answers'] = {
                "raw_answers": user_answers,
                "timestamp": datetime.now().isoformat()
            }
            
            # Transition to CREATE_CONFIRMATION_PLAN
            context.current_state = "CREATE_CONFIRMATION_PLAN"
            
            # State 3: CREATE_CONFIRMATION_PLAN
            print(f"\n{format_state('CREATE_CONFIRMATION_PLAN')}")
            print("─" * 60)
            plan = await self.director.process(context)
            print(format_agent_message(format_confirmation_plan(plan)))
            add_to_history(context, "assistant", plan)
            results["states_completed"].append("CREATE_CONFIRMATION_PLAN")
            results["outputs"]["plan"] = plan
            
            # Validate plan
            if not self._validate_plan(plan, scenario, results):
                return results
            
            # Simulate user accepting plan
            user_response = scenario["responses"]["plan_response"]
            print(format_user_message(user_response))
            add_to_history(context, "user", user_response)
            
            # Save confirmation plan to session data
            context.session_data['confirmation_plan'] = plan.model_dump() if hasattr(plan, 'model_dump') else plan
            
            # Transition to GENERATE_STRAWMAN
            context.current_state = "GENERATE_STRAWMAN"
            
            # State 4: GENERATE_STRAWMAN
            print(f"\n{format_state('GENERATE_STRAWMAN')}")
            print("─" * 60)
            strawman = await self.director.process(context)
            print(format_agent_message(format_strawman_summary(strawman)))
            add_to_history(context, "assistant", strawman)
            results["states_completed"].append("GENERATE_STRAWMAN")
            results["outputs"]["strawman"] = strawman
            
            # Validate strawman
            if not self._validate_strawman(strawman, scenario, results):
                return results
            
            # Simulate user requesting refinement
            refinement_request = scenario["responses"]["refinement_request"]
            print(format_user_message(refinement_request))
            add_to_history(context, "user", refinement_request)
            
            # Save strawman to session data
            context.session_data['presentation_strawman'] = strawman.model_dump() if hasattr(strawman, 'model_dump') else strawman
            
            # Transition to REFINE_STRAWMAN
            context.current_state = "REFINE_STRAWMAN"
            
            # State 5: REFINE_STRAWMAN
            print(f"\n{format_state('REFINE_STRAWMAN')}")
            print("─" * 60)
            refined_strawman = await self.director.process(context)
            
            # Validate refinement
            if hasattr(refined_strawman, 'slides') and hasattr(strawman, 'slides'):
                original_count = len(strawman.slides)
                refined_count = len(refined_strawman.slides)
                if refined_count != original_count:
                    print(format_error(f"Refinement changed slide count: {original_count} → {refined_count}"))
                    results["errors"].append(f"Refinement changed slide count from {original_count} to {refined_count}")
                else:
                    print(format_success(f"Refinement preserved slide count: {refined_count} slides"))
            
            print(format_agent_message("Strawman refined based on your feedback."))
            add_to_history(context, "assistant", refined_strawman)
            results["states_completed"].append("REFINE_STRAWMAN")
            results["outputs"]["refined_strawman"] = refined_strawman
            
            # Save conversation for analysis
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"test_results_{scenario_name}_{timestamp}.json"
            save_conversation(context, save_path)
            results["conversation_saved"] = save_path
            
        except Exception as e:
            results["passed"] = False
            results["errors"].append(f"Exception: {str(e)}")
            print(format_error(f"Test failed with exception: {str(e)}"))
        
        return results
    
    def _validate_questions(self, questions, results: Dict) -> bool:
        """Validate clarifying questions output."""
        try:
            if len(questions.questions) < self.validation_rules["min_questions"]:
                results["passed"] = False
                results["errors"].append(f"Too few questions: {len(questions.questions)}")
                return False
            
            if len(questions.questions) > self.validation_rules["max_questions"]:
                results["passed"] = False
                results["errors"].append(f"Too many questions: {len(questions.questions)}")
                return False
            
            print(format_success(f"Questions validation passed ({len(questions.questions)} questions)"))
            return True
            
        except Exception as e:
            results["passed"] = False
            results["errors"].append(f"Questions validation error: {str(e)}")
            return False
    
    def _validate_plan(self, plan, scenario: Dict, results: Dict) -> bool:
        """Validate confirmation plan output."""
        try:
            if plan.proposed_slide_count < self.validation_rules["min_slides"]:
                results["passed"] = False
                results["errors"].append(f"Too few slides: {plan.proposed_slide_count}")
                return False
            
            if plan.proposed_slide_count > self.validation_rules["max_slides"]:
                results["passed"] = False
                results["errors"].append(f"Too many slides: {plan.proposed_slide_count}")
                return False
            
            # Check if slide count is reasonable for scenario
            expected_slides = scenario.get("expected_slides", 0)
            if expected_slides > 0:
                diff = abs(plan.proposed_slide_count - expected_slides)
                if diff > 2:  # Allow some variance
                    print(f"{Colors.YELLOW}Warning: Slide count {plan.proposed_slide_count} differs from expected {expected_slides}{Colors.ENDC}")
            
            print(format_success(f"Plan validation passed ({plan.proposed_slide_count} slides)"))
            return True
            
        except Exception as e:
            results["passed"] = False
            results["errors"].append(f"Plan validation error: {str(e)}")
            return False
    
    def _validate_strawman(self, strawman, scenario: Dict, results: Dict) -> bool:
        """Validate strawman output with detailed field checking."""
        try:
            # Check slide count
            if len(strawman.slides) < self.validation_rules["min_slides"]:
                results["passed"] = False
                results["errors"].append(f"Too few slides in strawman: {len(strawman.slides)}")
                return False
            
            print(f"\n{Colors.BOLD}🔍 Validating Strawman Structure:{Colors.ENDC}")
            all_valid = True
            
            # Validate each slide
            for i, slide in enumerate(strawman.slides):
                slide_valid = True
                
                # Print validation results for this slide
                print(format_validation_results(slide, self.validation_rules))
                
                # Check required fields
                for field in self.validation_rules["required_slide_fields"]:
                    if not hasattr(slide, field) or getattr(slide, field) is None:
                        results["passed"] = False
                        results["errors"].append(f"Slide {slide.slide_id} missing required field: {field}")
                        slide_valid = False
                        all_valid = False
                
                # Check important optional fields
                missing_important = []
                for field in self.validation_rules.get("important_slide_fields", []):
                    if not hasattr(slide, field) or getattr(slide, field) is None:
                        missing_important.append(field)
                
                if missing_important:
                    print(f"  ⚠️  Note: Missing optional fields: {', '.join(missing_important)}")
                
                if slide_valid:
                    print(f"  {Colors.GREEN}✓ Slide {i+1} validation passed{Colors.ENDC}")
                else:
                    print(f"  {Colors.RED}✗ Slide {i+1} validation failed{Colors.ENDC}")
            
            # Check slide types match expected structure if provided
            if "expected_structure" in scenario:
                slide_types = [slide.slide_type for slide in strawman.slides]
                if slide_types != scenario["expected_structure"]:
                    print(f"\n{Colors.YELLOW}⚠️  Warning: Slide structure differs from expected{Colors.ENDC}")
                    print(f"  Expected: {scenario['expected_structure']}")
                    print(f"  Actual:   {slide_types}")
            
            if all_valid:
                print(f"\n{format_success(f'Strawman validation passed ({len(strawman.slides)} slides)')}")
            else:
                print(f"\n{format_error(f'Strawman validation failed')}")
            
            return all_valid
            
        except Exception as e:
            results["passed"] = False
            results["errors"].append(f"Strawman validation error: {str(e)}")
            return False
    
    async def run_all_scenarios(self) -> List[Dict[str, Any]]:
        """Run all available test scenarios."""
        results = []
        
        for scenario_name in self.scenarios.keys():
            print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
            result = await self.run_scenario(scenario_name)
            results.append(result)
            
            if result["passed"]:
                print(f"\n{format_success(f'Scenario {scenario_name} PASSED')}")
            else:
                print(f"\n{format_error(f'Scenario {scenario_name} FAILED')}")
                for error in result["errors"]:
                    print(f"  • {error}")
        
        return results
    
    def print_summary(self, results: List[Dict[str, Any]]) -> None:
        """Print test summary with enhanced formatting."""
        print(f"\n{Colors.BOLD}{'═'*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}📊 TEST SUMMARY{Colors.ENDC}")
        print(f"{Colors.BOLD}{'═'*60}{Colors.ENDC}\n")
        
        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        failed = total - passed
        
        print(f"🎯 Total Scenarios: {total}")
        print(f"{Colors.GREEN}✅ Passed: {passed}{Colors.ENDC}")
        print(f"{Colors.RED}❌ Failed: {failed}{Colors.ENDC}")
        
        if failed > 0:
            print(f"\n{Colors.BOLD}📝 Failed Scenarios:{Colors.ENDC}")
            for result in results:
                if not result["passed"]:
                    print(f"\n❌ {result['name']} ({result['scenario']})")
                    for error in result["errors"]:
                        print(f"  • {error}")
        
        print(f"\n{Colors.BOLD}📊 States Coverage:{Colors.ENDC}")
        all_states = ["PROVIDE_GREETING", "ASK_CLARIFYING_QUESTIONS", 
                      "CREATE_CONFIRMATION_PLAN", "GENERATE_STRAWMAN", "REFINE_STRAWMAN"]
        
        state_icons = {
            "PROVIDE_GREETING": "👋",
            "ASK_CLARIFYING_QUESTIONS": "❓",
            "CREATE_CONFIRMATION_PLAN": "📋",
            "GENERATE_STRAWMAN": "📊",
            "REFINE_STRAWMAN": "🔧"
        }
        
        for state in all_states:
            completed = sum(1 for r in results if state in r["states_completed"])
            icon = state_icons.get(state, "📍")
            status = "✅" if completed == total else "🔄" if completed > 0 else "❌"
            print(f"{icon} {state}: {completed}/{total} {status}")


async def main():
    """Main function to run the E2E tests."""
    # Check for required environment variables
    if not os.getenv('OPENAI_API_KEY') and not os.getenv('ANTHROPIC_API_KEY') and not os.getenv('GOOGLE_API_KEY'):
        print(format_error("No AI API key found!"))
        print("Please ensure your .env file contains one of:")
        print("- GOOGLE_API_KEY=...")
        print("- OPENAI_API_KEY=sk-...")
        print("- ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description="End-to-end testing for Director agent",
        epilog="Example: python test_director_e2e.py --scenario technical"
    )
    parser.add_argument(
        "--scenario", 
        type=str, 
        choices=["default", "executive", "technical", "educational", "sales"],
        help="Run specific scenario (default, executive, technical, educational, sales)"
    )
    parser.add_argument("--list", action="store_true", help="List available scenarios")
    
    args = parser.parse_args()
    
    tester = DirectorE2ETester()
    
    if args.list:
        tester.show_scenarios_menu()
        return
    
    if args.scenario:
        # Run specific scenario from command line
        print(f"\n{Colors.BOLD}🎯 Running scenario: {args.scenario}{Colors.ENDC}")
        result = await tester.run_scenario(args.scenario)
        tester.print_summary([result])
    else:
        # Show interactive menu
        scenario_choice = tester.show_interactive_menu()
        if scenario_choice:
            result = await tester.run_scenario(scenario_choice)
            tester.print_summary([result])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.ENDC}")
    except Exception as e:
        print(format_error(f"Fatal error: {str(e)}"))