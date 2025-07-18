# Future Communication Architecture - Phase 2/3 and Beyond

## Overview

This document outlines the planned communication architecture for Deckster's future phases. These features are NOT implemented in Phase 1 but represent the vision for a multi-agent, parallel processing presentation generation system.

**Status:** PLANNING DOCUMENT - Not yet implemented

## Phase 2: Multi-Agent Architecture

### Agent Ecosystem

Phase 2 introduces specialized agents working in parallel after strawman approval:

1. **Director IN (Inbound)**
   - Handles all user communication
   - Interprets user intent
   - Orchestrates agent tasks

2. **Director OUT (Outbound)**  
   - Assembles content from agents progressively
   - Manages slide-by-slide delivery
   - Coordinates parallel agent outputs

3. **Worker Agents** (Execute in Parallel):
   - **Layout/UX Architect**: Designs slide layouts using 160×90 grid system
   - **Researcher**: Gathers and verifies content
   - **Visual Designer**: Creates images and graphics
   - **Data Analyst**: Generates charts and visualizations
   - **UX Analyst**: Creates diagrams and flows

### Communication Flow

```
User ↔ Director IN → [Parallel Agents] → Director OUT → User
```

### Director IN → Worker Agents Message

```json
{
  "message_id": "dir_inst_001",
  "session_id": "session_abc123",
  "type": "agent_instruction",
  "source": "director_inbound",
  "target_agents": ["ux_architect", "researcher", "visual_designer"],
  "data": {
    "presentation_structure": {
      "title": "Q4 2024 Financial Review",
      "slides": [
        {
          "slide_id": "slide_001",
          "requirements": {
            "layout": "hero_with_metrics",
            "visuals": {
              "style": "corporate_modern",
              "elements": ["growth_charts", "success_imagery"]
            },
            "data": {
              "metrics": ["revenue", "growth_rate", "customers"]
            }
          }
        }
      ]
    },
    "agent_specific_instructions": {
      "ux_architect": {
        "grid_system": "160x90",
        "responsive": true,
        "accessibility": "WCAG_AA"
      },
      "visual_designer": {
        "brand_guidelines": "corporate_blue",
        "image_style": "photorealistic"
      }
    }
  }
}
```

### Worker Agent → Director OUT Response

```json
{
  "message_id": "agent_out_001",
  "session_id": "session_abc123",
  "type": "agent_output",
  "source": "visual_designer",
  "target": "director_outbound",
  "data": {
    "slide_id": "slide_001",
    "component_id": "hero_image",
    "output_type": "image",
    "status": "completed",
    "result": {
      "url": "https://storage.example.com/session_abc123/slide_001/hero.png",
      "metadata": {
        "width": 1920,
        "height": 1080,
        "alt_text": "Corporate growth visualization"
      }
    }
  }
}
```

## Phase 3: Advanced Features

### 1. HTML Slide Generation

Backend generates complete, styled HTML for each slide:

```json
{
  "type": "slide_update",
  "payload": {
    "slides": [
      {
        "slide_id": "slide_001",
        "html_content": "<div class='slide-container'>...</div>",
        "css_theme": "professional_blue"
      }
    ]
  }
}
```

### 2. Progressive Assembly

Director OUT sends slides as they complete:

```json
{
  "type": "slide_update",
  "payload": {
    "operation": "progressive_update",
    "completed_slides": ["slide_001", "slide_003"],
    "pending_slides": ["slide_002", "slide_004"],
    "slides": [/* only completed slides */]
  }
}
```

### 3. Real Asset Generation

Actual files created and stored:

```json
{
  "visuals_needed": {
    "type": "generated_image",
    "url": "https://storage.example.com/abc123/slide_001/visual.png",
    "thumbnail": "https://storage.example.com/abc123/slide_001/visual_thumb.png",
    "editable_url": "https://editor.example.com/edit/abc123"
  }
}
```

### 4. Grid-Based Layout System

160×90 grid for precise positioning:

```json
{
  "layout": {
    "grid": "160x90",
    "components": [
      {
        "id": "title",
        "position": {"x": 10, "y": 5, "width": 140, "height": 20}
      },
      {
        "id": "chart",
        "position": {"x": 10, "y": 30, "width": 70, "height": 50}
      }
    ]
  }
}
```

## Implementation Considerations

### LangGraph Integration

```python
# Parallel agent execution
workflow = StateGraph(PresentationState)

# Add parallel nodes
workflow.add_node("layout_architect", layout_agent)
workflow.add_node("researcher", research_agent)
workflow.add_node("visual_designer", visual_agent)

# Execute in parallel after strawman
workflow.add_edge("strawman_approved", ["layout_architect", "researcher", "visual_designer"])
```

### Asset Storage Architecture

```
storage/
├── sessions/
│   └── {session_id}/
│       └── slides/
│           └── {slide_id}/
│               ├── images/
│               ├── charts/
│               └── diagrams/
```

### Performance Optimizations

1. **Streaming Updates**: Use Server-Sent Events for real-time progress
2. **CDN Integration**: Store assets on CDN for fast delivery
3. **Caching Strategy**: Cache generated content for reuse
4. **Parallel Processing**: Maximum 5 agents concurrent per session

## Migration Path

### From Phase 1 to Phase 2

1. **Backend Changes**:
   - Split Director into IN/OUT components
   - Add LangGraph for orchestration
   - Implement worker agents
   - Add asset storage system

2. **Protocol Evolution**:
   - Maintain backward compatibility
   - Add new message types gradually
   - Use feature flags for rollout

3. **Frontend Adaptation**:
   - Support progressive updates
   - Handle asset URLs
   - Implement grid-based layouts

## Future Possibilities

### AI-Powered Features
- Voice narration generation
- Animation suggestions
- Audience-specific variations
- Real-time collaboration

### Advanced Integrations
- Direct export to PowerPoint/Google Slides
- Video generation from slides
- Interactive web presentations
- AR/VR presentation modes

### Enterprise Features
- Template marketplace
- Brand management system
- Analytics and tracking
- Compliance checking

## Technical Debt Considerations

As we implement these phases, we must:

1. Maintain clean separation between phases
2. Ensure backward compatibility
3. Document all protocol changes
4. Create migration tools
5. Performance test at scale

## Conclusion

This architecture represents the full vision for Deckster's communication system. Implementation should be incremental, with careful validation at each phase to ensure system stability and user satisfaction.