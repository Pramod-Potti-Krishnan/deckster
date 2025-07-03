# PRD Phase 3: Integration of Visual Designer, Data Analyst, and UX Analyst

## References
- [PRD v4.0](./PRD_v4.0.md) - Main product requirements document
- [Communication Protocols](./comms_protocol.md) - Detailed JSON message templates and protocols
- [Technology Stack](./tech_stack.md) - Framework specifications and implementation guidelines
- [Security Requirements](./security.md) - MVP security implementation guidelines
- [Folder Structure](./folder_structure.md) - Project organization and file placement guide

## FEATURE:
Addition of specialized agents (Visual Designer/Artist, Data Analyst, UX Analyst for diagrams) to replace placeholders with actual visual content, with Director (Outbound) orchestrating the final presentation assembly.

## EXAMPLES:
- Visual Designer receives: `{"placeholder_id": "img_1", "context": "hero image for SaaS product", "style": "modern"}`
- Data Analyst processes: `{"data_request": "revenue growth chart", "data_points": [...], "visualization": "line_chart"}`
- UX Analyst creates: `{"diagram_type": "user_flow", "steps": [...], "style": "minimalist"}`
- Director (Outbound) produces: Complete presentation with all visuals embedded as HTML

## DOCUMENTATION:
- **Agent Framework**: Pydantic AI for all specialized agents
- **Orchestration**: Extended LangGraph workflow from Phase 2
- **Visualization**: Chart.js/D3.js for data viz, Mermaid for diagrams
- **Image Generation**: Integration with DALL-E/Stable Diffusion APIs
- **MCP Server**: Visual asset libraries, data sources, diagram templates
- **Output Format**: JSON with complete HTML-embedded visuals

## KEY COMPONENTS:

### 1. Specialized Agent Definitions
```python
class VisualDesignerAgent(Agent):
    name = "visual_designer"
    description = "Creates images and visual assets for presentations"
    
    async def create_visual(self, request: VisualRequest) -> VisualAsset:
        # Generate via AI image APIs
        # Apply style consistency
        # Return base64 encoded images in HTML
        
class DataAnalystAgent(Agent):
    name = "data_analyst"
    description = "Transforms data into compelling visualizations"
    
    async def create_visualization(self, request: DataVizRequest) -> ChartOutput:
        # Process raw data
        # Select optimal chart type
        # Generate interactive HTML charts
        
class UXAnalystAgent(Agent):
    name = "ux_analyst_diagrams"
    description = "Creates flowcharts, diagrams, and infographics"
    
    async def create_diagram(self, request: DiagramRequest) -> DiagramOutput:
        # Parse diagram requirements
        # Generate using Mermaid/PlantUML
        # Return SVG embedded in HTML
```

### 2. Extended LangGraph Workflow
```python
# Extend Phase 2 workflow
phase3_workflow = StateGraph()

# Previous nodes
phase3_workflow.add_node("director_outbound", director_processor)

# New specialized nodes
phase3_workflow.add_node("visual_designer", visual_creator)
phase3_workflow.add_node("data_analyst", data_visualizer)
phase3_workflow.add_node("ux_analyst", diagram_creator)

# Parallel processing for placeholders
phase3_workflow.add_conditional_edges(
    "director_outbound",
    route_to_specialist,  # Routes based on placeholder type
    {
        "image": "visual_designer",
        "chart": "data_analyst",
        "diagram": "ux_analyst"
    }
)
```

### 3. Enhanced Data Models
```python
class VisualRequest(BaseModel):
    placeholder_id: str
    context: str
    style_guide: StyleGuide
    dimensions: ImageDimensions
    requirements: Dict[str, Any]
    
class VisualAsset(BaseModel):
    asset_id: str
    type: Literal['image', 'illustration', 'icon']
    content: str  # Base64 encoded
    html_embed: str  # <img> tag with inline data
    metadata: AssetMetadata
    
class DataVizRequest(BaseModel):
    placeholder_id: str
    data_source: Union[List[Dict], str]  # Raw data or MCP query
    chart_type: Optional[str]
    preferences: ChartPreferences
    
class ChartOutput(BaseModel):
    chart_id: str
    type: str  # 'bar', 'line', 'pie', etc.
    html_component: str  # Complete Chart.js/D3 component
    interactive: bool
    data_summary: str
    
class DiagramRequest(BaseModel):
    placeholder_id: str
    diagram_type: Literal['flowchart', 'sequence', 'mindmap', 'architecture']
    content: DiagramContent
    styling: DiagramStyle
    
class DiagramOutput(BaseModel):
    diagram_id: str
    svg_content: str
    html_embed: str  # SVG wrapped in HTML
    editable_source: str  # Mermaid/PlantUML source
```

### 4. Placeholder Resolution System
```python
class PlaceholderResolver:
    async def resolve_all_placeholders(
        self,
        presentation: DraftPresentation,
        agents: Dict[str, Agent]
    ) -> FinalPresentation:
        # Identify all placeholders
        # Batch by type for efficiency
        # Parallel processing
        # Merge results back into presentation
```

## OTHER CONSIDERATIONS:

### Visual Consistency Engine
- **Style Transfer**: Ensure all visuals match presentation theme
- **Color Palette**: Automatic extraction and application
- **Typography**: Consistent font usage across diagrams
- **Spacing**: Uniform margins and padding

### MCP Server Enhanced Tools
- **Visual Designer Access**:
  - Stock image libraries
  - Icon repositories
  - Style templates
- **Data Analyst Access**:
  - Real-time data sources
  - Statistical functions
  - Chart template library
- **UX Analyst Access**:
  - Diagram templates
  - Symbol libraries
  - Layout patterns

### Performance Optimization
- **Parallel Processing**: All placeholders of same type processed together
- **Caching**: Store generated assets for reuse
- **Progressive Loading**: Stream completed slides as ready
- **Resource Management**: Queue system for API rate limits

### Output Format
```json
{
  "presentation_id": "pres_123",
  "slides": [
    {
      "slide_id": "slide_1",
      "html_content": "<div class='slide'>...</div>",
      "assets": {
        "images": ["img_1_base64", "img_2_base64"],
        "charts": ["chart_1_config"],
        "diagrams": ["diagram_1_svg"]
      }
    }
  ],
  "complete": true,
  "generation_time": 45.2
}
```

### Memory Management

#### Short-term Memory (Contextual)
- **Asset Generation Queue**: Redis + Supabase
  ```python
  class AssetGenerationContext(BaseModel):
      session_id: str
      placeholder_mappings: Dict[str, PlaceholderInfo]
      style_context: StyleGuide
      completed_assets: List[str]
      generation_queue: List[str]
      retry_count: Dict[str, int]
  ```
- **Style Consistency Cache**:
  - Redis: Active style parameters for session
  - Color palettes, fonts, spacing rules
  - Cross-agent style synchronization
- **Generation Progress**:
  - Real-time progress in Redis
  - Completed assets in Supabase
  - Batch processing state management

#### Long-term Memory (Tools & Knowledge)
- **Visual Asset Library** (Supabase):
  ```python
  class VisualAssetStore:
      async def store_generated_asset(self, asset: VisualAsset, context: Dict):
          # Store with embeddings for reuse
          await supabase.table('visual_assets').insert({
              'asset_type': asset.type,
              'embedding': await generate_visual_embedding(asset),
              'tags': extract_tags(context),
              'style_attributes': asset.metadata.style,
              'usage_context': context,
              'quality_score': await assess_quality(asset)
          })
          
      async def find_reusable_assets(self, request: VisualRequest) -> List[VisualAsset]:
          # Search for similar assets to reuse/adapt
          return await supabase.rpc('search_visual_assets', {
              'context_embedding': await generate_request_embedding(request),
              'style_match': request.style_guide.dict(),
              'min_quality': 0.8
          })
  ```
- **Data Visualization Templates**:
  - Chart.js configurations in Supabase
  - Successful visualization patterns
  - Data-to-chart type mappings
  - Performance metrics per chart type
- **Diagram Pattern Library**:
  - Mermaid/PlantUML templates
  - Industry-specific diagram styles
  - Complexity-based selection
  - User preference learning
- **AI Generation Optimization**:
  - Successful prompts for image generation
  - Style transfer parameters
  - Error patterns and fallbacks
  - Cost optimization strategies

### Quality Assurance
- **Visual Validation**: Check image quality and relevance
- **Data Accuracy**: Verify chart data integrity
- **Diagram Clarity**: Ensure readability and flow
- **Accessibility**: Alt text and ARIA labels

### Development Priorities
1. Implement Visual Designer with AI image generation
2. Build Data Analyst with visualization engine
3. Create UX Analyst with diagram generation
4. Extend LangGraph workflow for parallel processing
5. Implement placeholder resolution system
6. Add visual consistency engine
7. Create comprehensive test suite with visual regression

### Success Metrics
- Placeholder resolution rate: 100%
- Visual quality score: >85%
- Chart accuracy: 100%
- Total generation time: <60s for 20 slides
- User satisfaction: >90%