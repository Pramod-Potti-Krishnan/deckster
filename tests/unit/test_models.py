"""
Unit tests for Pydantic models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.messages import (
    UserInput, DirectorMessage, ClarificationQuestion,
    ClarificationRound, SlideContent, ChatData
)
from src.models.presentation import (
    Presentation, Slide, ComponentSpec, TextComponent,
    Position, Dimensions, LayoutType, ComponentType
)
from src.models.agents import (
    DirectorInboundOutput, RequirementAnalysis,
    AgentOutput
)


class TestMessageModels:
    """Test message model validation."""
    
    def test_user_input_valid(self):
        """Test valid user input creation."""
        user_input = UserInput(
            session_id="test_session",
            data={
                "text": "Create a presentation about AI"
            }
        )
        assert user_input.type == "user_input"
        assert user_input.session_id == "test_session"
        assert user_input.data["text"] == "Create a presentation about AI"
    
    def test_user_input_text_too_long(self):
        """Test user input with text exceeding limit."""
        with pytest.raises(ValidationError) as exc_info:
            UserInput(
                session_id="test_session",
                data={
                    "text": "x" * 6000  # Exceeds 5000 char limit
                }
            )
        assert "Text input cannot exceed 5000 characters" in str(exc_info.value)
    
    def test_clarification_question_valid(self):
        """Test valid clarification question."""
        question = ClarificationQuestion(
            question="What is your target audience?",
            question_type="choice",
            options=["Technical", "Business", "General"],
            required=True,
            category="audience",
            priority="high"
        )
        assert question.question_type == "choice"
        assert len(question.options) == 3
        assert question.required is True
    
    def test_clarification_round_valid(self):
        """Test valid clarification round."""
        questions = [
            ClarificationQuestion(
                question="How long should it be?",
                question_type="text",
                required=True,
                category="duration",
                priority="high"
            )
        ]
        round_obj = ClarificationRound(questions=questions)
        assert round_obj.current_round == 1
        assert round_obj.max_rounds == 3
        assert len(round_obj.questions) == 1
    
    def test_slide_content_valid(self):
        """Test valid slide content."""
        slide = SlideContent(
            slide_id="slide_1",
            slide_number=1,
            title="Introduction",
            body_content=[],
            layout_type="hero"
        )
        assert slide.slide_id == "slide_1"
        assert slide.layout_type == "hero"
    
    def test_slide_content_invalid_id(self):
        """Test slide content with invalid ID format."""
        with pytest.raises(ValidationError):
            SlideContent(
                slide_id="invalid_id",  # Should match slide_\d+
                slide_number=1,
                title="Test",
                body_content=[],
                layout_type="hero"
            )
    
    def test_director_message_requires_data(self):
        """Test that DirectorMessage requires either slide_data or chat_data."""
        with pytest.raises(ValidationError) as exc_info:
            DirectorMessage(
                session_id="test_session",
                source="director_inbound"
                # Missing both slide_data and chat_data
            )
        assert "Either slide_data or chat_data must be provided" in str(exc_info.value)


class TestPresentationModels:
    """Test presentation model validation."""
    
    def test_slide_creation(self):
        """Test valid slide creation."""
        slide = Slide(
            slide_number=1,
            title="Test Slide",
            layout_type=LayoutType.CONTENT
        )
        assert slide.slide_number == 1
        assert slide.layout_type == LayoutType.CONTENT
        assert len(slide.components) == 0
    
    def test_component_position_validation(self):
        """Test component position validation."""
        # Valid position
        pos = Position(x=50, y=25, z_index=1)
        assert pos.x == 50
        assert pos.y == 25
        
        # Invalid position (out of bounds)
        with pytest.raises(ValidationError):
            Position(x=150, y=25)  # x > 100
    
    def test_text_component_creation(self):
        """Test text component creation."""
        component = TextComponent(
            position=Position(x=10, y=10),
            dimensions=Dimensions(width=80, height=20),
            content="Hello World"
        )
        assert component.type == ComponentType.TEXT
        assert component.content == "Hello World"
    
    def test_text_component_content_limit(self):
        """Test text component content length limit."""
        with pytest.raises(ValidationError) as exc_info:
            TextComponent(
                position=Position(x=10, y=10),
                dimensions=Dimensions(width=80, height=20),
                content="x" * 6000  # Exceeds 5000 char limit
            )
        assert "Text content cannot exceed 5000 characters" in str(exc_info.value)
    
    def test_slide_component_limit(self):
        """Test slide component count limits."""
        components = []
        for i in range(4):
            components.append(
                TextComponent(
                    position=Position(x=i*20, y=10),
                    dimensions=Dimensions(width=15, height=10),
                    content=f"Component {i}"
                )
            )
        
        # Hero layout allows max 3 components
        with pytest.raises(ValidationError) as exc_info:
            Slide(
                slide_number=1,
                title="Test",
                layout_type=LayoutType.HERO,
                components=components  # 4 components
            )
        assert "supports maximum 3 components" in str(exc_info.value)
    
    def test_presentation_creation(self):
        """Test valid presentation creation."""
        from src.models.presentation import Theme, ColorPalette, Typography
        
        slides = [
            Slide(
                slide_number=1,
                title="Title Slide",
                layout_type=LayoutType.HERO
            ),
            Slide(
                slide_number=2,
                title="Content Slide",
                layout_type=LayoutType.CONTENT
            )
        ]
        
        theme = Theme(
            name="default",
            colors=ColorPalette(
                primary="#0066CC",
                secondary="#4D94FF",
                accent="#FF6B6B",
                background="#FFFFFF",
                text="#333333",
                text_secondary="#666666"
            ),
            typography=Typography()
        )
        
        presentation = Presentation(
            title="Test Presentation",
            slides=slides,
            theme=theme
        )
        
        assert presentation.title == "Test Presentation"
        assert len(presentation.slides) == 2
        assert presentation.version == 1
    
    def test_presentation_slide_numbering(self):
        """Test that slide numbers must be sequential."""
        slides = [
            Slide(slide_number=1, title="Slide 1", layout_type=LayoutType.CONTENT),
            Slide(slide_number=3, title="Slide 3", layout_type=LayoutType.CONTENT)  # Skip 2
        ]
        
        with pytest.raises(ValidationError) as exc_info:
            Presentation(
                title="Test",
                slides=slides,
                theme=Theme(
                    name="test",
                    colors=ColorPalette(
                        primary="#000", secondary="#111", accent="#222",
                        background="#FFF", text="#000", text_secondary="#555"
                    ),
                    typography=Typography()
                )
            )
        assert "Slide numbers must be sequential" in str(exc_info.value)


class TestAgentModels:
    """Test agent model validation."""
    
    def test_requirement_analysis_creation(self):
        """Test requirement analysis model."""
        analysis = RequirementAnalysis(
            completeness_score=0.75,
            missing_information=["target audience", "duration"],
            detected_intent="sales pitch",
            presentation_type="business",
            estimated_slides=15,
            complexity_level="moderate",
            key_topics=["Product features", "Benefits"],
            suggested_flow=["Intro", "Problem", "Solution", "Demo", "Closing"]
        )
        assert analysis.completeness_score == 0.75
        assert len(analysis.missing_information) == 2
        assert analysis.complexity_level == "moderate"
    
    def test_requirement_analysis_score_validation(self):
        """Test completeness score validation."""
        with pytest.raises(ValidationError):
            RequirementAnalysis(
                completeness_score=1.5,  # > 1
                missing_information=[],
                detected_intent="test",
                presentation_type="test",
                estimated_slides=10,
                complexity_level="simple",
                key_topics=[],
                suggested_flow=[]
            )
    
    def test_director_inbound_output(self):
        """Test Director Inbound output model."""
        output = DirectorInboundOutput(
            agent_id="director_inbound",
            output_type="analysis",
            session_id="test_session",
            correlation_id="corr_123",
            status="completed",
            confidence_score=0.9,
            analysis=RequirementAnalysis(
                completeness_score=0.8,
                missing_information=[],
                detected_intent="educational",
                presentation_type="workshop",
                estimated_slides=20,
                complexity_level="complex",
                key_topics=["AI", "Machine Learning"],
                suggested_flow=["Intro", "Theory", "Practice", "Q&A"]
            )
        )
        assert output.agent_id == "director_inbound"
        assert output.output_type == "analysis"
        assert output.confidence_score == 0.9
        assert output.analysis.estimated_slides == 20
    
    def test_agent_output_timestamp(self):
        """Test that agent output includes timestamp."""
        output = AgentOutput(
            agent_id="test_agent",
            output_type="test",
            session_id="test_session",
            correlation_id="corr_123",
            status="completed",
            confidence_score=1.0
        )
        assert isinstance(output.timestamp, datetime)
        assert output.metadata == {}


@pytest.mark.unit
class TestModelValidation:
    """Test cross-model validation and business rules."""
    
    def test_clarification_response_validation(self):
        """Test clarification response matches questions."""
        from src.models.messages import ClarificationResponse
        
        response = ClarificationResponse(
            round_id="round_001",
            responses={
                "q_001": "20 minutes",
                "q_002": "Technical audience"
            }
        )
        assert len(response.responses) == 2
        assert response.skipped_questions == []
    
    def test_presentation_metadata(self):
        """Test presentation metadata handling."""
        from src.models.messages import PresentationMetadata
        
        metadata = PresentationMetadata(
            title="AI in Healthcare",
            description="Overview of AI applications in healthcare",
            presentation_type="conference",
            industry="healthcare",
            target_audience="medical professionals",
            estimated_duration=30,
            tags=["AI", "healthcare", "innovation"]
        )
        assert metadata.estimated_duration == 30
        assert len(metadata.tags) == 3
    
    def test_color_palette_validation(self):
        """Test color palette hex validation."""
        from src.models.presentation import ColorPalette
        
        palette = ColorPalette(
            primary="#0066CC",
            secondary="#4D94FF",
            accent="#FF6B6B",
            background="#FFFFFF",
            text="#333333",
            text_secondary="#666666"
        )
        assert palette.primary == "#0066CC"
        assert palette.success == "#4CAF50"  # Default value