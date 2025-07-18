# JSON-Based Grid System Design (Phase 2 Enhanced)

## Executive Summary

A simplified, declarative JSON system for slide rendering using the proven 160×90 grid. This design prioritizes simplicity, predictability, and ease of adoption through constraints. **Phase 2 Enhancement**: Integration with backend Layout Architect agent for intelligent layout generation.

## Core Principles

1. **Less is More** - Minimal schema with maximum clarity
2. **Theme-Driven** - Themes define layouts and typography
3. **Container-Based** - All content lives in positioned containers
4. **Grid-Only** - Everything uses Grid Units (GU), no pixels
5. **Backend-Driven Intelligence** - Layout Architect provides smart container placement

## The Grid System

- **Grid Size**: 160×90 Grid Units (16:9 aspect ratio)
- **Positioning**: One horizontal + one vertical property per element
- **No Ambiguity**: Explicit sizing, no auto-height or relative positioning

## Theme System

### Theme Structure

```json
{
  "theme": {
    "name": "corporate",
    "layouts": {
      "titleSlide": {
        "containers": {
          "title": { "leftInset": 20, "topInset": 35, "width": 120, "height": 20 },
          "subtitle": { "leftInset": 20, "topInset": 55, "width": 120, "height": 10 },
          "footer": { "leftInset": 10, "bottomInset": 5, "width": 140, "height": 5 }
        }
      },
      "contentSlide": {
        "containers": {
          "header": { "leftInset": 10, "topInset": 5, "width": 140, "height": 10 },
          "title": { "leftInset": 10, "topInset": 18, "width": 140, "height": 8 },
          "body": { "leftInset": 10, "topInset": 30, "width": 140, "height": 50 },
          "footer": { "leftInset": 10, "bottomInset": 5, "width": 140, "height": 5 }
        }
      },
      "sectionHeader": {
        "containers": {
          "title": { "xCenterOffset": 0, "yCenterOffset": -5, "width": 120, "height": 15 },
          "subtitle": { "xCenterOffset": 0, "yCenterOffset": 10, "width": 100, "height": 8 }
        }
      }
    },
    "typography": {
      "h1": { 
        "fontSize": 48, 
        "fontFamily": "Inter", 
        "fontWeight": "bold", 
        "color": "#1a1a1a",
        "textAlign": "center"
      },
      "h2": { 
        "fontSize": 36, 
        "fontFamily": "Inter", 
        "fontWeight": "semibold", 
        "color": "#2a2a2a",
        "textAlign": "left"
      },
      "h3": { 
        "fontSize": 24, 
        "fontFamily": "Inter", 
        "fontWeight": "medium", 
        "color": "#3a3a3a",
        "textAlign": "left"
      },
      "body": { 
        "fontSize": 18, 
        "fontFamily": "Inter", 
        "fontWeight": "normal", 
        "color": "#4a4a4a",
        "textAlign": "left",
        "lineHeight": 1.5
      },
      "caption": { 
        "fontSize": 14, 
        "fontFamily": "Inter", 
        "fontWeight": "normal", 
        "color": "#6a6a6a",
        "textAlign": "center"
      }
    },
    "colors": {
      "background": "#ffffff",
      "primary": "#0066cc",
      "secondary": "#666666",
      "accent": "#00cc66",
      "surface": "#f5f5f5",
      "warning": "#ff9900",
      "error": "#cc0000"
    }
  }
}
```

## Backend-Frontend Layout Mapping

### Slide Type to Layout Mapping

The Layout Architect agent maps backend slide types to frontend theme layouts:

```json
{
  "layout_mapping": {
    "title_slide": ["titleSlide", "heroSlide"],
    "section_divider": ["sectionHeader", "chapterBreak"],
    "content_heavy": ["contentSlide", "textFocused"],
    "visual_heavy": ["visualSlide", "mediaFocused"],
    "data_driven": ["dataSlide", "dashboardSlide"],
    "diagram_focused": ["diagramSlide", "processSlide"],
    "mixed_content": ["twoColumn", "splitLayout"],
    "conclusion_slide": ["closingSlide", "summarySlide"]
  }
}
```

### Layout Hints from Backend

The Layout Architect can provide hints to guide frontend rendering:

```json
{
  "layout_hints": {
    "content_density": "high",       // high, medium, low
    "visual_emphasis": 0.7,          // 0-1 scale
    "preferred_flow": "vertical",    // vertical, horizontal, grid
    "color_intensity": "vibrant",    // muted, balanced, vibrant
    "spacing_preference": "compact"  // compact, balanced, airy
  }
}
```

### Dynamic Container Generation

When content doesn't fit predefined theme layouts, the Layout Architect generates custom containers:

```json
{
  "custom_containers": [
    {
      "name": "main_content",
      "content_ref": "key_points[0-2]",
      "position": {
        "leftInset": 10,
        "topInset": 25,
        "width": 70,
        "height": 40
      },
      "layout_role": "primary"
    },
    {
      "name": "supporting_visual",
      "content_ref": "visuals_needed",
      "position": {
        "rightInset": 10,
        "topInset": 25,
        "width": 60,
        "height": 40
      },
      "layout_role": "secondary"
    }
  ]
}
```

## Slide Structure

### Basic Slide (Phase 2 Enhanced)

```json
{
  "slide": {
    "id": "slide-1",
    "layout": "contentSlide",
    "background": "#ffffff",
    "layout_spec": {  // NEW: From Layout Architect
      "source": "theme",  // "theme" or "custom"
      "layout_hints": {
        "content_density": "medium",
        "visual_emphasis": 0.3
      }
    },
    "containers": [
      {
        "name": "title",
        "content": {
          "type": "text",
          "text": "Introduction to Our Product",
          "style": "h2"
        }
      },
      {
        "name": "body",
        "content": {
          "type": "text",
          "text": "Our product revolutionizes the way teams collaborate...",
          "style": "body"
        }
      }
    ]
  }
}
```

### Container Properties

Containers support optional styling properties:

```json
{
  "name": "callout",
  "position": {
    "leftInset": 10,
    "topInset": 40,
    "width": 50,
    "height": 20
  },
  "zIndex": 10,  // Optional: Controls layering (default: 1)
  "padding": {   // Optional: Inner spacing in GU
    "all": 2,    // or specify individually:
    "top": 2,
    "right": 3,
    "bottom": 2,
    "left": 3
  },
  "background": "@colors.primary",  // Optional: References theme colors
  "content": {
    "type": "text",
    "text": "Important: This is a highlighted callout box",
    "style": "body"
  }
}
```

### Custom Container Positioning

When you need containers beyond the theme layout:

```json
{
  "slide": {
    "id": "slide-2",
    "layout": "contentSlide",
    "containers": [
      {
        "name": "title",
        "content": {
          "type": "text",
          "text": "Sales Performance",
          "style": "h2"
        }
      },
      {
        "name": "chart",
        "position": {
          "leftInset": 10,
          "topInset": 35,
          "width": 70,
          "height": 45
        },
        "content": {
          "type": "chart",
          "chartType": "bar",
          "data": {
            "labels": ["Q1", "Q2", "Q3", "Q4"],
            "values": [100, 150, 125, 200]
          }
        }
      },
      {
        "name": "summary",
        "position": {
          "rightInset": 10,
          "topInset": 35,
          "width": 60,
          "height": 45
        },
        "content": {
          "type": "text",
          "text": "Key insights:\n• 50% growth in Q2\n• Strong Q4 finish",
          "style": "body"
        }
      }
    ]
  }
}
```

## Content Object Types

### Text Content

```json
{
  "type": "text",
  "text": "Your text here",
  "style": "h1"  // References theme typography
}
```

### Image Content

```json
{
  "type": "image",
  "src": "https://example.com/image.jpg",
  "alt": "Description"
}
```

### Video Content

```json
{
  "type": "video",
  "src": "https://example.com/video.mp4",
  "poster": "https://example.com/poster.jpg"
}
```

### Chart Content

```json
{
  "type": "chart",
  "chartType": "bar",
  "data": {
    "labels": ["A", "B", "C"],
    "values": [10, 20, 30]
  }
}
```

## Positioning Rules

### Available Properties

Each container must use exactly ONE horizontal and ONE vertical property:

**Horizontal Options:**
- `leftInset`: Distance from left edge in GU
- `rightInset`: Distance from right edge in GU
- `xCenterOffset`: Offset from horizontal center in GU

**Vertical Options:**
- `topInset`: Distance from top edge in GU
- `bottomInset`: Distance from bottom edge in GU
- `yCenterOffset`: Offset from vertical center in GU

### Examples

```json
// Top-left positioning
{
  "position": {
    "leftInset": 10,
    "topInset": 10,
    "width": 50,
    "height": 30
  }
}

// Centered element
{
  "position": {
    "xCenterOffset": 0,
    "yCenterOffset": 0,
    "width": 80,
    "height": 40
  }
}

// Bottom-right positioning
{
  "position": {
    "rightInset": 10,
    "bottomInset": 10,
    "width": 40,
    "height": 20
  }
}
```

## Complete Example

### Title Slide

```json
{
  "slide": {
    "id": "title-1",
    "layout": "titleSlide",
    "background": {
      "gradient": {
        "type": "linear",
        "angle": 135,
        "colors": ["#0066cc", "#004499"]
      }
    },
    "containers": [
      {
        "name": "title",
        "content": {
          "type": "text",
          "text": "Annual Report 2024",
          "style": "h1"
        }
      },
      {
        "name": "subtitle",
        "content": {
          "type": "text",
          "text": "Building the Future Together",
          "style": "h3"
        }
      },
      {
        "name": "footer",
        "content": {
          "type": "text",
          "text": "Confidential - Internal Use Only",
          "style": "caption"
        }
      }
    ]
  }
}
```

### Content Slide with Mixed Media

```json
{
  "slide": {
    "id": "content-1",
    "layout": "contentSlide",
    "containers": [
      {
        "name": "title",
        "content": {
          "type": "text",
          "text": "Product Overview",
          "style": "h2"
        }
      },
      {
        "name": "leftColumn",
        "position": {
          "leftInset": 10,
          "topInset": 30,
          "width": 65,
          "height": 45
        },
        "content": {
          "type": "image",
          "src": "/images/product-hero.jpg",
          "alt": "Product screenshot"
        }
      },
      {
        "name": "rightColumn",
        "position": {
          "rightInset": 10,
          "topInset": 30,
          "width": 65,
          "height": 45
        },
        "content": {
          "type": "text",
          "text": "Key Features:\n\n• Cloud-native architecture\n• Real-time collaboration\n• Enterprise security\n• 99.9% uptime SLA",
          "style": "body"
        }
      }
    ]
  }
}
```

### Advanced Example with Styled Containers

```json
{
  "slide": {
    "id": "highlights-1",
    "layout": "contentSlide",
    "containers": [
      {
        "name": "title",
        "content": {
          "type": "text",
          "text": "Key Achievements",
          "style": "h2"
        }
      },
      {
        "name": "achievement1",
        "position": {
          "leftInset": 10,
          "topInset": 30,
          "width": 40,
          "height": 20
        },
        "background": "@colors.surface",
        "padding": { "all": 3 },
        "zIndex": 2,
        "content": {
          "type": "text",
          "text": "50% Revenue Growth\nYear over Year",
          "style": "h3"
        }
      },
      {
        "name": "achievement2",
        "position": {
          "xCenterOffset": 0,
          "topInset": 30,
          "width": 40,
          "height": 20
        },
        "background": "@colors.accent",
        "padding": { "all": 3 },
        "zIndex": 2,
        "content": {
          "type": "text",
          "text": "10,000+ New Customers\nGlobal Expansion",
          "style": "h3"
        }
      },
      {
        "name": "achievement3",
        "position": {
          "rightInset": 10,
          "topInset": 30,
          "width": 40,
          "height": 20
        },
        "background": "@colors.primary",
        "padding": { "all": 3 },
        "zIndex": 2,
        "content": {
          "type": "text",
          "text": "Industry Leader\n#1 in Customer Satisfaction",
          "style": "h3"
        }
      },
      {
        "name": "warningNote",
        "position": {
          "leftInset": 10,
          "bottomInset": 10,
          "width": 140,
          "height": 8
        },
        "background": "@colors.warning",
        "padding": { "top": 1, "bottom": 1, "left": 2, "right": 2 },
        "zIndex": 3,
        "content": {
          "type": "text",
          "text": "Note: All metrics are based on fiscal year 2024 performance",
          "style": "caption"
        }
      }
    ]
  }
}
```

## Benefits

1. **Simplicity**: One positioning method, clear rules
2. **Predictability**: No ambiguous layouts or cascading effects
3. **Theme Power**: Change entire presentation style instantly
4. **Maintainability**: Easy to understand and debug
5. **Performance**: Simple calculations, no complex layout engine
6. **Intelligence**: Backend Layout Architect ensures optimal layouts

## Progressive Assembly Architecture (Phase 2/3)

### Parallel Agent Flow

1. **Director (Inbound)** generates content-focused strawman
2. **Parallel Agents** process strawman concurrently:
   - Layout Architect (Phase 2)
   - Researcher (Phase 3)
   - Visual Designer (Phase 3)
   - Data Analyst (Phase 3)
   - UX Analyst (Phase 3)
3. **Director OUT** assembles content progressively
4. **Frontend** receives updates as content becomes available

### Progressive Slide Updates

```json
{
  "message_type": "slide_update",
  "payload": {
    "operation": "partial_update",
    "update_sequence": 1,
    "slide_status": {
      "slide_001": {
        "layout": "complete",
        "content": "pending",
        "visuals": "pending",
        "charts": "pending"
      }
    },
    "slides": [{
      "slide_id": "slide_001",
      "layout": "dataSlide",
      "layout_spec": { /* Layout details */ },
      "content_placeholders": {
        "research": { "status": "loading", "estimated_time": 5 },
        "visuals": { "status": "loading", "estimated_time": 8 },
        "charts": { "status": "loading", "estimated_time": 10 }
      }
    }]
  }
}
```

### Multi-Agent Content Assembly

As agents complete their work, Director OUT merges contributions:

```json
{
  "slide_id": "slide_001",
  "assembly_state": {
    "base": { /* Original strawman */ },
    "contributions": {
      "layout_architect": {
        "timestamp": "2024-01-01T10:00:00Z",
        "content": { /* Layout spec */ }
      },
      "researcher": {
        "timestamp": "2024-01-01T10:00:05Z",
        "content": { /* Enhanced text */ }
      },
      "visual_designer": {
        "timestamp": "2024-01-01T10:00:08Z",
        "content": { /* Image URLs */ }
      }
    }
  }
}

### Progressive Enhancement Slide Structure

```json
{
  "slide": {
    "id": "slide-2",
    "slide_type": "data_driven",
    "layout": "dataSlide",
    "layout_spec": { /* From Layout Architect */ },
    
    // Phase 2: Layout ready, content pending
    "content_state": {
      "layout": {
        "status": "complete",
        "provider": "layout_architect",
        "timestamp": "2024-01-01T10:00:02Z"
      },
      "research": {
        "status": "pending",
        "provider": "researcher",
        "placeholder": "Content being researched..."
      },
      "visuals": {
        "status": "pending",
        "provider": "visual_designer",
        "placeholder": "/images/placeholder-chart.svg"
      }
    },
    
    // Progressive content containers
    "containers": [
      {
        "name": "title",
        "content": {
          "type": "text",
          "text": "Q3 Revenue Analysis",  // From strawman
          "style": "h2"
        }
      },
      {
        "name": "chart_main",
        "content": {
          "type": "placeholder",
          "placeholder_type": "chart",
          "loading_state": {
            "message": "Analyzing data...",
            "progress": 45
          }
        }
      },
      {
        "name": "insights",
        "content": {
          "type": "placeholder",
          "placeholder_type": "text",
          "loading_state": {
            "message": "Generating insights...",
            "estimated_time": 5
          }
        }
      }
    ]
  }
}
```

### Content Layer Updates

When agents complete their work, containers are updated:

```json
{
  "message_type": "slide_update",
  "payload": {
    "operation": "content_update",
    "update_sequence": 2,
    "affected_slides": ["slide-2"],
    "container_updates": [
      {
        "slide_id": "slide-2",
        "container_name": "chart_main",
        "content": {
          "type": "chart",
          "chart_type": "bar",
          "data": { /* Chart data from Data Analyst */ },
          "styling": { /* From Layout hints */ }
        }
      }
    ]
  }
}
```

### Layout Intelligence Features

1. **Content Analysis**: Layout Architect analyzes text length, visual requirements
2. **Visual Balance**: Ensures proper weight distribution across the slide
3. **Variety Management**: Tracks layouts used to avoid repetition
4. **Responsive Adaptation**: Provides breakpoint hints for different screen sizes
5. **Accessibility**: Ensures reading order and contrast requirements

### API Contract

Frontend expects:
- `layout`: Theme layout name to use as base
- `layout_spec.source`: Whether using theme or custom layout
- `layout_spec.custom_containers`: Array of positioned containers (if custom)
- `layout_spec.layout_hints`: Visual treatment preferences

Backend provides all the above through the Layout Architect's analysis.

## Frontend Implementation Considerations

### Progressive Rendering

1. **Initial Render**: Show slide with layout and placeholders
2. **Content Updates**: Replace placeholders as content arrives
3. **Loading States**: Display progress for pending content
4. **Error Handling**: Graceful fallbacks for failed content

### State Management

```javascript
// Frontend slide state
const slideState = {
  slide_001: {
    layout: { status: 'complete', data: {...} },
    content: { status: 'loading', placeholder: '...' },
    visuals: { status: 'pending', estimated: 10 },
    charts: { status: 'error', fallback: 'static_chart.png' }
  }
}

// Update handler
function handleSlideUpdate(update) {
  const { slide_id, container_updates } = update
  
  // Apply updates to specific containers
  container_updates.forEach(update => {
    updateContainer(slide_id, update.container_name, update.content)
  })
  
  // Trigger re-render only for affected areas
  renderSlideContainers(slide_id, container_updates)
}
```

### User Experience

1. **Immediate Feedback**: Show layout structure instantly
2. **Progressive Enhancement**: Content appears as ready
3. **Smart Placeholders**: Context-aware loading states
4. **Smooth Transitions**: Animate content replacement

## Refinement Flow (Phase 2+)

### Targeted Refinements

When users request changes, Director IN routes to specific agents:

```json
{
  "refinement_request": {
    "target_slide": "slide_002",
    "refinement_type": "layout",
    "user_feedback": "Make this slide more visual-heavy",
    "affected_agents": ["layout_architect"],
    "preserve_content": ["research", "charts"]
  }
}
```

### Refinement States

- REFINE_LAYOUT → Layout Architect
- REFINE_CONTENT → Researcher
- REFINE_VISUALS → Visual Designer
- REFINE_CHARTS → Data Analyst
- REFINE_DIAGRAMS → UX Analyst

Each refinement processes only the affected components, preserving work from other agents.

## Migration Path

1. **Phase 1**: Sequential strawman generation (Complete)
2. **Phase 2**: 
   - Implement Layout Architect as first parallel agent
   - Build Director OUT progressive assembler
   - Enable slide-by-slide updates
3. **Phase 3**: 
   - Add remaining parallel agents
   - Full progressive enhancement
   - Multi-agent refinements
4. **Phase 4**: 
   - Learning from feedback
   - Optimization and caching
   - Advanced assembly strategies

This architecture enables true parallel processing while maintaining system coherence and user experience quality.