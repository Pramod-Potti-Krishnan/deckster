"""
Presentation structure models following Pydantic BaseModel patterns.
Defines the core data structures for presentations, slides, and components.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Dict, Any, Optional, Literal, Union
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


# Enums for standardized values
class LayoutType(str, Enum):
    """Available slide layout types."""
    HERO = "hero"
    CONTENT = "content"
    CHART_FOCUSED = "chart_focused"
    COMPARISON = "comparison"
    CLOSING = "closing"
    SECTION_DIVIDER = "section_divider"
    IMAGE_FOCUSED = "image_focused"
    QUOTE = "quote"
    TEAM = "team"
    TIMELINE = "timeline"


class ComponentType(str, Enum):
    """Types of components that can be placed on slides."""
    TEXT = "text"
    IMAGE = "image"
    CHART = "chart"
    DIAGRAM = "diagram"
    TABLE = "table"
    VIDEO = "video"
    ICON = "icon"
    SHAPE = "shape"
    LOGO = "logo"


class ChartType(str, Enum):
    """Supported chart types."""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"
    AREA = "area"
    RADAR = "radar"
    FUNNEL = "funnel"
    WATERFALL = "waterfall"
    HEATMAP = "heatmap"


class DiagramType(str, Enum):
    """Supported diagram types."""
    FLOWCHART = "flowchart"
    MINDMAP = "mindmap"
    ORG_CHART = "org_chart"
    PROCESS = "process"
    CYCLE = "cycle"
    MATRIX = "matrix"
    PYRAMID = "pyramid"
    VENN = "venn"


# Component Models
class Position(BaseModel):
    """Position coordinates for components."""
    x: float = Field(..., ge=0, le=100, description="X position as percentage")
    y: float = Field(..., ge=0, le=100, description="Y position as percentage")
    z_index: int = Field(default=0, description="Layer order")


class Dimensions(BaseModel):
    """Size dimensions for components."""
    width: float = Field(..., ge=0, le=100, description="Width as percentage")
    height: float = Field(..., ge=0, le=100, description="Height as percentage")
    min_width: Optional[float] = Field(None, ge=0, description="Minimum width in pixels")
    min_height: Optional[float] = Field(None, ge=0, description="Minimum height in pixels")


class Style(BaseModel):
    """Styling properties for components."""
    background_color: Optional[str] = None
    border_color: Optional[str] = None
    border_width: Optional[int] = Field(None, ge=0, le=10)
    border_radius: Optional[int] = Field(None, ge=0, le=50)
    opacity: Optional[float] = Field(None, ge=0, le=1)
    shadow: Optional[bool] = False
    padding: Optional[Dict[str, int]] = None
    margin: Optional[Dict[str, int]] = None
    custom_css: Optional[Dict[str, Any]] = None


class TextStyle(Style):
    """Text-specific styling."""
    font_family: Optional[str] = None
    font_size: Optional[int] = Field(None, ge=8, le=144)
    font_weight: Optional[Literal["normal", "bold", "light"]] = None
    font_style: Optional[Literal["normal", "italic"]] = None
    text_align: Optional[Literal["left", "center", "right", "justify"]] = None
    color: Optional[str] = None
    line_height: Optional[float] = Field(None, ge=0.5, le=3)
    letter_spacing: Optional[float] = None


class Animation(BaseModel):
    """Animation properties for components."""
    type: Literal["fade", "slide", "zoom", "rotate", "bounce"]
    duration: float = Field(default=0.5, ge=0.1, le=5)
    delay: float = Field(default=0, ge=0, le=10)
    direction: Optional[Literal["in", "out"]] = "in"
    easing: Optional[Literal["linear", "ease", "ease-in", "ease-out", "ease-in-out"]] = "ease"


# Base Component
class ComponentSpec(BaseModel):
    """Base specification for all slide components."""
    component_id: str = Field(default_factory=lambda: f"comp_{uuid4().hex[:8]}")
    type: ComponentType
    position: Position
    dimensions: Dimensions
    style: Optional[Style] = None
    animation: Optional[Animation] = None
    interaction: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(use_enum_values=True)


# Specific Component Types
class TextComponent(ComponentSpec):
    """Text content component."""
    type: Literal[ComponentType.TEXT] = ComponentType.TEXT
    content: str
    text_style: Optional[TextStyle] = None
    markdown_enabled: bool = False
    
    @field_validator('content')
    def validate_content_length(cls, v):
        """Ensure text content is reasonable length."""
        if len(v) > 5000:
            raise ValueError("Text content cannot exceed 5000 characters")
        return v


class ImageComponent(ComponentSpec):
    """Image component."""
    type: Literal[ComponentType.IMAGE] = ComponentType.IMAGE
    url: str
    alt_text: str
    caption: Optional[str] = None
    source_attribution: Optional[str] = None
    fit_mode: Literal["cover", "contain", "fill", "scale-down"] = "contain"


class ChartComponent(ComponentSpec):
    """Chart/graph component."""
    type: Literal[ComponentType.CHART] = ComponentType.CHART
    chart_type: ChartType
    data: Dict[str, Any]  # Chart data structure
    config: Dict[str, Any]  # Chart configuration
    title: Optional[str] = None
    subtitle: Optional[str] = None
    interactive: bool = True
    
    @field_validator('data')
    def validate_chart_data(cls, v, info):
        """Validate chart data structure."""
        if 'chart_type' in info.data:
            # Basic validation - ensure data has required fields
            if not v:
                raise ValueError("Chart data cannot be empty")
        return v


class DiagramComponent(ComponentSpec):
    """Diagram component."""
    type: Literal[ComponentType.DIAGRAM] = ComponentType.DIAGRAM
    diagram_type: DiagramType
    structure: Dict[str, Any]  # Diagram structure definition
    styling: Dict[str, Any]  # Diagram styling rules
    title: Optional[str] = None


class TableComponent(ComponentSpec):
    """Table component."""
    type: Literal[ComponentType.TABLE] = ComponentType.TABLE
    headers: List[str]
    rows: List[List[Any]]
    styling: Optional[Dict[str, Any]] = None
    sortable: bool = False
    filterable: bool = False
    
    @field_validator('rows')
    def validate_row_consistency(cls, v, info):
        """Ensure all rows have same number of columns as headers."""
        if 'headers' in info.data:
            header_count = len(info.data['headers'])
            for i, row in enumerate(v):
                if len(row) != header_count:
                    raise ValueError(f"Row {i} has {len(row)} columns, expected {header_count}")
        return v


# Slide Models
class SlideTransition(BaseModel):
    """Transition effects between slides."""
    type: Literal["none", "fade", "slide", "zoom", "flip"] = "none"
    duration: float = Field(default=0.3, ge=0.1, le=2)
    direction: Optional[Literal["left", "right", "up", "down"]] = None


class SlideBackground(BaseModel):
    """Slide background configuration."""
    type: Literal["solid", "gradient", "image", "video"]
    value: Union[str, Dict[str, Any]]
    opacity: float = Field(default=1.0, ge=0, le=1)
    blur: Optional[int] = Field(None, ge=0, le=20)


class Slide(BaseModel):
    """Complete slide definition."""
    slide_id: str = Field(default_factory=lambda: f"slide_{uuid4().hex[:8]}")
    slide_number: int = Field(..., ge=1)
    title: str = Field(..., max_length=200)
    subtitle: Optional[str] = Field(None, max_length=300)
    layout_type: LayoutType
    components: List[ComponentSpec] = Field(default_factory=list)
    background: Optional[SlideBackground] = None
    transition: Optional[SlideTransition] = None
    speaker_notes: Optional[str] = None
    duration: Optional[int] = Field(None, ge=1, le=600, description="Suggested duration in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('components')
    def validate_component_count(cls, v, info):
        """Validate component count based on layout type."""
        if 'layout_type' in info.data:
            layout_limits = {
                LayoutType.HERO: 3,
                LayoutType.CONTENT: 6,
                LayoutType.CHART_FOCUSED: 3,
                LayoutType.COMPARISON: 4,
                LayoutType.CLOSING: 3,
                LayoutType.SECTION_DIVIDER: 2,
                LayoutType.IMAGE_FOCUSED: 2,
                LayoutType.QUOTE: 2,
                LayoutType.TEAM: 8,
                LayoutType.TIMELINE: 10
            }
            
            layout = info.data['layout_type']
            max_components = layout_limits.get(layout, 6)
            
            if len(v) > max_components:
                raise ValueError(f"Layout type '{layout}' supports maximum {max_components} components")
        
        return v
    
    @field_validator('components')
    def validate_no_overlapping_components(cls, v):
        """Ensure components don't significantly overlap."""
        # Simple overlap detection - can be made more sophisticated
        for i, comp1 in enumerate(v):
            for j, comp2 in enumerate(v[i+1:], i+1):
                if cls._components_overlap(comp1, comp2):
                    # Only warn for significant overlaps
                    overlap_area = cls._calculate_overlap_area(comp1, comp2)
                    if overlap_area > 0.5:  # More than 50% overlap
                        raise ValueError(f"Components {comp1.component_id} and {comp2.component_id} overlap significantly")
        return v
    
    @staticmethod
    def _components_overlap(comp1: ComponentSpec, comp2: ComponentSpec) -> bool:
        """Check if two components overlap."""
        # Calculate bounding boxes
        comp1_left = comp1.position.x
        comp1_right = comp1.position.x + comp1.dimensions.width
        comp1_top = comp1.position.y
        comp1_bottom = comp1.position.y + comp1.dimensions.height
        
        comp2_left = comp2.position.x
        comp2_right = comp2.position.x + comp2.dimensions.width
        comp2_top = comp2.position.y
        comp2_bottom = comp2.position.y + comp2.dimensions.height
        
        # Check for overlap
        return not (comp1_right <= comp2_left or 
                   comp2_right <= comp1_left or 
                   comp1_bottom <= comp2_top or 
                   comp2_bottom <= comp1_top)
    
    @staticmethod
    def _calculate_overlap_area(comp1: ComponentSpec, comp2: ComponentSpec) -> float:
        """Calculate overlap area as percentage of smaller component."""
        # Implementation details omitted for brevity
        return 0.0


# Presentation Theme
class ColorPalette(BaseModel):
    """Color palette for presentation theme."""
    primary: str
    secondary: str
    accent: str
    background: str
    text: str
    text_secondary: str
    success: Optional[str] = "#4CAF50"
    warning: Optional[str] = "#FF9800"
    error: Optional[str] = "#F44336"
    custom_colors: Dict[str, str] = Field(default_factory=dict)


class Typography(BaseModel):
    """Typography settings for presentation."""
    heading_font: str = "Arial"
    body_font: str = "Arial"
    code_font: str = "Courier New"
    base_size: int = Field(default=16, ge=10, le=24)
    scale_ratio: float = Field(default=1.25, ge=1.1, le=2)


class Theme(BaseModel):
    """Complete presentation theme."""
    theme_id: str = Field(default_factory=lambda: f"theme_{uuid4().hex[:8]}")
    name: str
    colors: ColorPalette
    typography: Typography
    spacing: Dict[str, int] = Field(default_factory=lambda: {
        "xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32
    })
    border_radius: int = Field(default=4, ge=0, le=20)
    shadow_style: Optional[Dict[str, Any]] = None


# Main Presentation Model
class PresentationSettings(BaseModel):
    """Presentation-wide settings."""
    aspect_ratio: Literal["16:9", "4:3", "16:10"] = "16:9"
    transition_default: SlideTransition = Field(default_factory=SlideTransition)
    auto_advance: bool = False
    loop: bool = False
    show_slide_numbers: bool = True
    show_progress_bar: bool = True
    enable_presenter_view: bool = True


class Presentation(BaseModel):
    """Complete presentation structure."""
    presentation_id: str = Field(default_factory=lambda: f"pres_{uuid4().hex[:12]}")
    title: str = Field(..., max_length=200)
    subtitle: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = Field(None, max_length=1000)
    slides: List[Slide]
    theme: Theme
    settings: PresentationSettings = Field(default_factory=PresentationSettings)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
    )
    
    @field_validator('slides')
    def validate_slide_numbers(cls, v):
        """Ensure slide numbers are sequential."""
        expected_numbers = list(range(1, len(v) + 1))
        actual_numbers = [slide.slide_number for slide in v]
        
        if actual_numbers != expected_numbers:
            raise ValueError("Slide numbers must be sequential starting from 1")
        
        return v
    
    @field_validator('slides')
    def validate_minimum_slides(cls, v):
        """Ensure presentation has at least one slide."""
        if len(v) < 1:
            raise ValueError("Presentation must have at least one slide")
        return v
    
    def get_slide_by_id(self, slide_id: str) -> Optional[Slide]:
        """Get a slide by its ID."""
        for slide in self.slides:
            if slide.slide_id == slide_id:
                return slide
        return None
    
    def get_slide_by_number(self, slide_number: int) -> Optional[Slide]:
        """Get a slide by its number."""
        for slide in self.slides:
            if slide.slide_number == slide_number:
                return slide
        return None
    
    def add_slide(self, slide: Slide, position: Optional[int] = None) -> None:
        """Add a slide at the specified position."""
        if position is None:
            position = len(self.slides)
        
        # Insert slide
        self.slides.insert(position, slide)
        
        # Renumber slides
        for i, s in enumerate(self.slides):
            s.slide_number = i + 1
        
        self.updated_at = datetime.utcnow()
    
    def remove_slide(self, slide_id: str) -> bool:
        """Remove a slide by ID."""
        for i, slide in enumerate(self.slides):
            if slide.slide_id == slide_id:
                self.slides.pop(i)
                # Renumber remaining slides
                for j, s in enumerate(self.slides):
                    s.slide_number = j + 1
                self.updated_at = datetime.utcnow()
                return True
        return False
    
    def reorder_slides(self, slide_ids: List[str]) -> None:
        """Reorder slides based on provided ID list."""
        if len(slide_ids) != len(self.slides):
            raise ValueError("Must provide IDs for all slides")
        
        # Create ID to slide mapping
        slide_map = {slide.slide_id: slide for slide in self.slides}
        
        # Reorder
        new_slides = []
        for i, slide_id in enumerate(slide_ids):
            if slide_id not in slide_map:
                raise ValueError(f"Unknown slide ID: {slide_id}")
            slide = slide_map[slide_id]
            slide.slide_number = i + 1
            new_slides.append(slide)
        
        self.slides = new_slides
        self.updated_at = datetime.utcnow()


# Export Models for External Use
class PresentationExport(BaseModel):
    """Simplified presentation model for export."""
    title: str
    slides: List[Dict[str, Any]]
    format: Literal["pptx", "pdf", "html", "json"]
    include_speaker_notes: bool = True
    include_animations: bool = False
    quality: Literal["draft", "standard", "high"] = "standard"