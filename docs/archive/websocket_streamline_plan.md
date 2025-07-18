# WebSocket Communication Protocol Streamlining Plan

## Executive Summary

This plan outlines the transformation of Deckster's WebSocket communication from a monolithic message structure to a streamlined, purpose-driven protocol. The new protocol separates messages by their frontend presentation purpose: chat content, slide updates, and user actions.

## Current State Analysis

### Problems with Current Implementation
1. **Single Complex Message Type**: The current `DirectorMessage` combines chat_data and slide_data in one message
2. **Frontend Complexity**: Frontend must parse nested objects and determine which UI components to update
3. **Poor Async Support**: Cannot show progress while generating content
4. **Tight Coupling**: Changes to one message component affect the entire structure

### Current Message Structure
```json
{
  "id": "msg_unique_id",
  "type": "director_message",
  "timestamp": "2024-01-01T10:00:00.000Z",
  "session_id": "session_abc123",
  "source": "director_inbound",
  "slide_data": { /* optional slide content */ },
  "chat_data": { /* chat content with embedded actions */ }
}
```

## Proposed Solution: Decoupled Message Protocol

### Core Principles
1. **Single Responsibility**: Each message has one clear purpose
2. **Frontend Simplicity**: Messages map directly to UI components
3. **Async-First**: Support for progress updates and streaming
4. **Extensibility**: Easy to add new message types without breaking existing code

### New Message Types

#### 1. Base Message Envelope
```json
{
  "message_id": "msg_unique_id",
  "session_id": "session_xyz",
  "timestamp": "2024-01-01T10:00:00.000Z",
  "type": "chat_message" | "action_request" | "slide_update" | "status_update",
  "payload": { /* type-specific content */ }
}
```

#### 2. Chat Message
Purpose: Display conversational content in the chat interface
```json
{
  "type": "chat_message",
  "payload": {
    "text": "Main message text",
    "sub_title": "Optional subtitle",
    "list_items": ["Optional", "list", "of", "items"],
    "format": "markdown" | "plain"
  }
}
```

#### 3. Action Request
Purpose: Present interactive buttons to the user
```json
{
  "type": "action_request",
  "payload": {
    "prompt_text": "What would you like to do?",
    "actions": [
      {
        "label": "Accept",
        "value": "accept_plan",
        "primary": true,
        "requires_input": false
      }
    ]
  }
}
```

#### 4. Slide Update
Purpose: Update the presentation view with pre-rendered HTML slides
```json
{
  "type": "slide_update",
  "payload": {
    "operation": "full_update" | "partial_update",
    "metadata": {
      "main_title": "AI in Healthcare: Transforming Patient Care",
      "overall_theme": "Data-driven and persuasive",
      "design_suggestions": "Modern professional with blue color scheme",
      "target_audience": "Healthcare executives",
      "presentation_duration": 15
    },
    "slides": [
      {
        "slide_id": "slide_001",
        "slide_number": 1,
        "html_content": "<div class='slide-container'>...</div>"
      },
      {
        "slide_id": "slide_002", 
        "slide_number": 2,
        "html_content": "<div class='slide-container'>...</div>"
      }
    ],
    "affected_slides": ["slide_001", "slide_003"] // For partial updates
  }
}
```

#### 5. Status Update
Purpose: Show processing status or progress
```json
{
  "type": "status_update",
  "payload": {
    "status": "idle" | "thinking" | "generating" | "complete" | "error",
    "text": "Building your presentation outline...",
    "progress": 65, // Optional percentage
    "estimated_time": 10 // Optional seconds remaining
  }
}
```

## State-by-State Message Flow

### PROVIDE_GREETING
**Current**: 1 director_message with chat_data
**New**: 1 chat_message

```
Backend sends:
1. chat_message: "Hello! I'm Deckster..."
```

### ASK_CLARIFYING_QUESTIONS
**Current**: 1 director_message with questions array
**New**: 1 chat_message with structured content

```
Backend sends:
1. chat_message: {
     text: "Great topic! I have some questions:",
     list_items: [questions...]
   }
```

### CREATE_CONFIRMATION_PLAN
**Current**: 1 director_message with summary and actions
**New**: 2 messages for clear separation

```
Backend sends:
1. chat_message: Summary and assumptions
2. action_request: Accept/Reject buttons
```

### GENERATE_STRAWMAN
**Current**: 1 large director_message with both slide and chat data
**New**: 3-4 messages for better UX with HTML generation

```
Backend flow:
1. Send status_update: "Generating presentation..." (immediate)
2. Generate PresentationStrawman from Director Agent
3. Render each slide to HTML using templates
4. Send slide_update: Pre-rendered HTML slides with metadata
5. Send action_request: Accept/Refine buttons

Message sequence:
1. status_update: "Generating your presentation slides..."
2. slide_update: {
     operation: "full_update",
     metadata: {...},
     slides: [{ slide_id, slide_number, html_content }]
   }
3. action_request: Accept/Refine options
```

### REFINE_STRAWMAN
**Current**: Same as GENERATE_STRAWMAN
**New**: 4 messages for clarity with partial HTML updates

```
Backend flow:
1. Send status_update: "Refining your presentation..." (immediate)
2. Identify changed slides from refinement request
3. Generate updated PresentationStrawman
4. Render ONLY changed slides to HTML
5. Send slide_update with partial update
6. Send chat_message explaining changes
7. Send action_request for further actions

Message sequence:
1. status_update: "Refining slides based on your feedback..."
2. slide_update: {
     operation: "partial_update",
     metadata: {...}, // Same as before
     slides: [{ slide_id: "slide_003", html_content: "..." }],
     affected_slides: ["slide_003"]
   }
3. chat_message: "I've updated slide 3 with more visuals and less text"
4. action_request: Accept/Further refine options
```

## Slide HTML Generation Architecture

### Overview
The backend will generate complete, self-contained HTML for each slide, transforming raw presentation data into ready-to-render content. This approach shifts all presentation logic to the backend while keeping the frontend as a lightweight display layer.

### HTML Structure Standards
Each slide's HTML will be self-contained with embedded styles:

```html
<div class="slide-container" data-slide-id="slide_001" data-slide-type="title_slide">
  <div class="slide-header">
    <h1 class="slide-title">AI in Healthcare: Transforming Patient Care</h1>
    <p class="slide-subtitle">Revolutionizing Diagnostics & Operations</p>
  </div>
  <div class="slide-body">
    <div class="content-grid">
      <div class="metric-card highlight">
        <span class="metric-value">30%</span>
        <span class="metric-label">Reduction in diagnostic errors</span>
      </div>
      <div class="metric-card">
        <span class="metric-value">$2.5M</span>
        <span class="metric-label">Annual cost savings</span>
      </div>
    </div>
  </div>
  <div class="slide-footer">
    <span class="slide-number">1</span>
    <span class="slide-total">/ 10</span>
  </div>
</div>
```

### Template Engine Architecture

#### 1. Template System
- **Engine**: Jinja2 for Python-based templating
- **Template Library**: Pre-built templates for each slide type
- **Asset Management**: Embedded SVGs and data URIs for images
- **Theming**: CSS variables for consistent styling

#### 2. Slide Type Templates
```
templates/
  ├── base_slide.html        # Base template with common structure
  ├── title_slide.html       # Title/hero slides
  ├── content_slide.html     # Text-heavy slides
  ├── metric_grid.html       # KPI/dashboard slides
  ├── chart_slide.html       # Data visualization slides
  ├── diagram_slide.html     # Process/flow slides
  └── conclusion_slide.html  # CTA/summary slides
```

#### 3. CSS Framework
- **Approach**: Inline critical CSS, external theme CSS
- **Responsive**: Mobile-first, scalable layouts
- **Print-ready**: Optimized for PDF export
- **Accessibility**: WCAG AA compliant

### Progressive Update Strategy

For REFINE_STRAWMAN, the backend will:
1. Identify changed slides by comparing with previous version
2. Generate HTML only for modified slides
3. Send partial update with affected slide IDs
4. Frontend replaces only the specified slides

Example partial update:
```json
{
  "type": "slide_update",
  "payload": {
    "operation": "partial_update",
    "metadata": { /* unchanged */ },
    "slides": [
      {
        "slide_id": "slide_003",
        "slide_number": 3,
        "html_content": "<div class='slide-container'>...updated content...</div>"
      }
    ],
    "affected_slides": ["slide_003"]
  }
}
```

### Asset Embedding Strategy

1. **Images**: Base64 encode small images (<100KB), external URLs for larger
2. **Charts**: Inline SVG for vector graphics, Canvas for complex visualizations
3. **Icons**: SVG sprites embedded in HTML
4. **Fonts**: Web fonts with fallback stack

### Security Considerations

1. **HTML Sanitization**: DOMPurify or similar to prevent XSS
2. **CSP Headers**: Restrict external resource loading
3. **Template Injection**: Escape all user-provided content
4. **Asset Validation**: Verify all embedded content

## Implementation Plan

### Phase 1: Foundation (Week 1)
1. **Create New Message Models**
   - File: `src/models/websocket_messages.py`
   - Define all new message types with Pydantic
   - Add validation and examples

2. **Create Streamlined Message Packager**
   - File: `src/utils/streamlined_packager.py`
   - Implement message generation for each state
   - Return list of messages instead of single message

3. **Add Feature Flag**
   - Update `config/settings.py`
   - Add `USE_STREAMLINED_PROTOCOL` setting
   - Default to False for safety

### Phase 2: Integration (Week 2)
1. **Update WebSocket Handler**
   - Modify `src/handlers/websocket.py`
   - Support sending multiple messages
   - Add configurable delays between messages
   - Switch packager based on feature flag

2. **Create Adapter Layer**
   - File: `src/utils/message_adapter.py`
   - Convert between old and new formats
   - Enable gradual migration

3. **Add Progress Tracking**
   - Implement status updates before long operations
   - Add progress reporting during generation

### Phase 3: Testing & Documentation (Week 3)
1. **Comprehensive Testing**
   - Unit tests for new message types
   - Integration tests for message flow
   - E2E tests with both protocols

2. **Documentation Updates**
   - Update `docs/websocket_json_flow.md`
   - Create migration guide
   - Add frontend implementation examples

3. **Frontend SDK/Examples**
   - Create TypeScript interfaces
   - Provide React component examples
   - WebSocket client wrapper

### Phase 4: Rollout (Week 4)
1. **Gradual Deployment**
   - Enable for 10% of sessions
   - Monitor metrics and errors
   - Increase to 50%, then 100%

2. **Deprecation Plan**
   - Mark old protocol as deprecated
   - Set removal date (3 months)
   - Notify frontend teams

## Technical Implementation Details

### Message Sending Logic
```python
# Pseudocode for new handler
async def send_messages(websocket, messages: List[Message]):
    for i, message in enumerate(messages):
        await websocket.send_json(message.dict())
        
        # Add small delay between messages for better UX
        if i < len(messages) - 1:
            await asyncio.sleep(0.1)
```

### State-Specific Message Generation
```python
# Example for CREATE_CONFIRMATION_PLAN
def package_confirmation_plan(plan: ConfirmationPlan) -> List[Message]:
    messages = []
    
    # Message 1: Summary
    messages.append(ChatMessage(
        payload=ChatPayload(
            text=f"Based on your input, I'm proposing a {plan.proposed_slide_count}-slide presentation.",
            sub_title="Key Assumptions:",
            list_items=plan.key_assumptions
        )
    ))
    
    # Message 2: Actions
    messages.append(ActionRequest(
        payload=ActionPayload(
            prompt_text="Does this look correct?",
            actions=[
                Action(label="Accept & Proceed", value="accept_plan", primary=True),
                Action(label="Request Changes", value="reject_plan")
            ]
        )
    ))
    
    return messages
```

### HTML Template Rendering
```python
# Example slide rendering with Jinja2
class SlideRenderer:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader('templates/slides'))
        
    def render_slide(self, slide: Slide) -> str:
        """Render a slide object to HTML"""
        template_map = {
            'title_slide': 'title_slide.html',
            'content_heavy': 'content_slide.html',
            'data_driven': 'chart_slide.html',
            'visual_heavy': 'visual_slide.html'
        }
        
        template_name = template_map.get(slide.slide_type, 'content_slide.html')
        template = self.env.get_template(template_name)
        
        return template.render(
            slide=slide,
            theme_vars=self.get_theme_variables(),
            assets=self.prepare_assets(slide)
        )
    
    def render_presentation(self, strawman: PresentationStrawman) -> List[dict]:
        """Render all slides in a presentation"""
        rendered_slides = []
        
        for slide in strawman.slides:
            rendered_slides.append({
                "slide_id": slide.slide_id,
                "slide_number": slide.slide_number,
                "html_content": self.render_slide(slide)
            })
            
        return rendered_slides
```

### Example HTML Template (title_slide.html)
```html
<div class="slide-container" data-slide-id="{{ slide.slide_id }}" data-slide-type="title_slide">
  <style>
    .slide-container { 
      height: 100vh; 
      display: flex; 
      flex-direction: column;
      background: var(--slide-bg, #ffffff);
    }
    .hero-section {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 3rem;
    }
    .slide-title {
      font-size: 3.5rem;
      font-weight: 700;
      color: var(--primary-color, #1e40af);
      margin-bottom: 1rem;
    }
    .slide-subtitle {
      font-size: 1.5rem;
      color: var(--secondary-color, #64748b);
    }
  </style>
  
  <div class="hero-section">
    <div>
      <h1 class="slide-title">{{ slide.title }}</h1>
      {% if slide.narrative %}
        <p class="slide-subtitle">{{ slide.narrative }}</p>
      {% endif %}
    </div>
  </div>
  
  <div class="slide-footer">
    <span class="slide-number">{{ slide.slide_number }}</span>
  </div>
</div>
```

## Benefits & Impact

### Frontend Benefits
1. **Simplified Logic**: Direct mapping from message type to UI component
2. **Better Performance**: Smaller messages, less parsing
3. **Improved UX**: Progressive updates, immediate feedback
4. **Easier Testing**: Mock individual message types
5. **No Layout Logic**: Frontend just renders pre-built HTML
6. **Consistent Rendering**: All formatting controlled server-side
7. **Reduced Complexity**: No need for slide templating libraries

### Backend Benefits
1. **Cleaner Architecture**: Separation of concerns
2. **Better Async Support**: Natural progress reporting
3. **Easier Debugging**: Focused message types
4. **Extensibility**: Add new features without breaking changes
5. **Full Control**: Complete control over slide appearance
6. **Template Reuse**: Share templates across different outputs (web, PDF, etc.)
7. **A/B Testing**: Easy to test different slide layouts server-side

### HTML-Specific Benefits
1. **Performance**: Pre-rendered HTML loads instantly
2. **SEO Friendly**: Content is immediately available
3. **Accessibility**: Server-side rendering ensures proper ARIA attributes
4. **Print Ready**: HTML/CSS optimized for printing
5. **Export Options**: Easy conversion to PDF or other formats
6. **Theme Switching**: CSS variables enable instant theme changes
7. **Offline Support**: HTML can be cached for offline viewing

### Code Simplification Example
```javascript
// Before: Complex nested parsing
if (message.type === 'director_message') {
  if (message.chat_data) {
    if (message.chat_data.type === 'question') {
      updateQuestions(message.chat_data.content.questions);
    } else if (message.chat_data.type === 'summary') {
      updateSummary(message.chat_data.content);
      if (message.chat_data.actions) {
        showActions(message.chat_data.actions);
      }
    }
  }
  if (message.slide_data) {
    updateSlides(message.slide_data);
  }
}

// After: Clean switch statement
switch(message.type) {
  case 'chat_message':
    chatUI.render(message.payload);
    break;
  case 'action_request':
    actionUI.render(message.payload);
    break;
  case 'slide_update':
    slideUI.render(message.payload);
    break;
  case 'status_update':
    statusUI.render(message.payload);
    break;
}
```

## Risk Mitigation

### Potential Risks
1. **Breaking Changes**: Frontend compatibility
   - Mitigation: Feature flag, adapter layer, gradual rollout

2. **Message Ordering**: Messages arriving out of order
   - Mitigation: Sequence numbers, client-side queuing

3. **Increased Complexity**: More message types to maintain
   - Mitigation: Strong typing, comprehensive tests

4. **Network Overhead**: More individual messages
   - Mitigation: Batching for high-frequency updates

## Success Metrics

1. **Frontend Complexity**: 50% reduction in message handling code
2. **User Experience**: 80% faster perceived response time
3. **Developer Satisfaction**: Positive feedback from frontend team
4. **Error Rate**: No increase in WebSocket errors
5. **Performance**: No degradation in message throughput

## Timeline

- **Week 1**: Foundation - Models and packager
- **Week 2**: Integration - Handler updates and adapter
- **Week 3**: Testing - Comprehensive test suite
- **Week 4**: Rollout - Gradual deployment
- **Week 5-8**: Migration support and monitoring
- **Week 12**: Deprecate old protocol

## Next Steps

1. Review and approve this plan
2. Create detailed technical specifications
3. Set up feature flag infrastructure
4. Begin Phase 1 implementation
5. Coordinate with frontend team on migration timeline

## Phase 5: Production Implementation (Weeks 5-8)

### Overview
With the foundation, integration, and testing complete, Phase 5 focuses on production-ready features and monitoring for successful deployment.

### 5.1 HTML Template Engine Implementation

#### Jinja2 Template System Setup
1. **Create Template Structure**
   ```
   templates/slides/
   ├── base/
   │   ├── base_slide.html
   │   ├── theme_variables.css
   │   └── common_components.html
   ├── layouts/
   │   ├── title_slide.html
   │   ├── content_slide.html
   │   ├── metric_grid.html
   │   ├── chart_slide.html
   │   ├── diagram_slide.html
   │   ├── visual_heavy.html
   │   └── conclusion_slide.html
   ├── components/
   │   ├── metric_card.html
   │   ├── chart_container.html
   │   ├── key_points_list.html
   │   └── speaker_notes.html
   └── themes/
       ├── professional_blue.css
       ├── modern_tech.css
       ├── healthcare.css
       └── corporate.css
   ```

2. **Implement SlideRenderer Class**
   - File: `src/utils/slide_renderer.py`
   - Jinja2 environment configuration
   - Template selection logic based on slide_type
   - Theme application system
   - Asset embedding (images, icons, charts)

3. **Create Template Examples**
   ```html
   <!-- title_slide.html -->
   <div class="slide-container" data-slide-id="{{ slide.slide_id }}" data-slide-type="title_slide">
     <style>
       {% include 'themes/' + theme + '.css' %}
     </style>
     <div class="slide-background">
       {% if slide.visuals_needed %}
         <div class="background-image" style="background-image: url('{{ generate_visual(slide.visuals_needed) }}')"></div>
       {% endif %}
     </div>
     <div class="slide-content">
       <h1 class="main-title">{{ slide.title }}</h1>
       {% if slide.narrative %}
         <p class="subtitle">{{ slide.narrative }}</p>
       {% endif %}
       <div class="presentation-meta">
         <span class="audience">{{ metadata.target_audience }}</span>
         <span class="duration">{{ metadata.presentation_duration }} minutes</span>
       </div>
     </div>
   </div>
   ```

4. **Asset Management**
   - SVG icon library for common business icons
   - Chart.js integration for data visualizations
   - Image optimization pipeline
   - Font loading strategy

### 5.2 Performance Monitoring

1. **Metrics to Track**
   - Message generation time per state
   - HTML rendering performance
   - WebSocket message latency
   - Protocol selection distribution
   - Error rates by protocol type

2. **Implementation with Logfire**
   ```python
   # Add to streamlined_packager.py
   @logfire.instrument("package_messages")
   async def package_messages(self, session_id: str, state: str, agent_output: Any):
       with logfire.span("streamlined_message_packaging", 
                        session_id=session_id, 
                        state=state,
                        protocol="streamlined"):
           # ... existing code
   ```

3. **Dashboard Creation**
   - Real-time protocol usage statistics
   - Performance comparison: legacy vs streamlined
   - Error tracking by message type
   - User experience metrics (time to first slide, etc.)

### 5.3 A/B Testing Framework

1. **Metrics Collection**
   - User engagement rates
   - Session completion rates
   - Error rates
   - Performance metrics
   - User feedback scores

2. **Analysis Tools**
   ```python
   # src/utils/ab_test_analyzer.py
   class StreamlinedProtocolAnalyzer:
       def analyze_conversion_rates(self):
           """Compare session completion rates between protocols"""
           
       def analyze_performance(self):
           """Compare message processing times"""
           
       def analyze_errors(self):
           """Compare error rates and types"""
           
       def generate_report(self):
           """Generate comprehensive A/B test report"""
   ```

3. **Rollout Strategy**
   - Week 5: 10% streamlined (early adopters)
   - Week 6: 25% streamlined (monitor metrics)
   - Week 7: 50% streamlined (performance validation)
   - Week 8: 100% streamlined (full rollout)

### 5.4 Frontend SDK Development

1. **TypeScript SDK**
   ```typescript
   // @deckster/websocket-client
   export class DecksterWebSocket {
     constructor(config: DecksterConfig) {
       this.detectProtocol = config.autoDetectProtocol ?? true;
     }
     
     onMessage(handler: MessageHandler) {
       // Automatic protocol detection and routing
     }
     
     // Typed message handlers
     onChatMessage(handler: (msg: ChatMessage) => void) {}
     onActionRequest(handler: (msg: ActionRequest) => void) {}
     onSlideUpdate(handler: (msg: SlideUpdate) => void) {}
     onStatusUpdate(handler: (msg: StatusUpdate) => void) {}
   }
   ```

2. **React Hooks**
   ```typescript
   // @deckster/react
   export function useDecksterWebSocket(sessionId: string) {
     const [messages, setMessages] = useState<Message[]>([]);
     const [slides, setSlides] = useState<Slide[]>([]);
     const [status, setStatus] = useState<Status>();
     
     // ... implementation
     
     return { messages, slides, status, sendMessage };
   }
   ```

3. **Example Applications**
   - Minimal vanilla JS example
   - React application example
   - Vue.js application example
   - Next.js SSR example

### 5.5 Migration Support Tools

1. **Protocol Compatibility Checker**
   ```python
   # src/utils/protocol_checker.py
   class ProtocolCompatibilityChecker:
       def validate_frontend_ready(self, session_id: str) -> bool:
           """Check if frontend properly handles streamlined messages"""
           
       def test_message_handling(self, websocket: WebSocket) -> Report:
           """Send test messages and verify proper handling"""
   ```

2. **Migration Assistant**
   - Automated frontend code analysis
   - Migration checklist generator
   - Common pattern replacements
   - Testing suite for migrated code

3. **Debug Tools**
   - Protocol switcher for testing
   - Message replay functionality
   - Side-by-side protocol comparison
   - Performance profiler

### 5.6 Documentation and Training

1. **Documentation Updates**
   - API reference with examples
   - Video tutorials for frontend teams
   - Common patterns cookbook
   - Troubleshooting guide

2. **Internal Training**
   - Workshop for frontend teams
   - Code review guidelines
   - Best practices document
   - Q&A sessions

### 5.7 Production Deployment Checklist

- [ ] Jinja2 templates implemented and tested
- [ ] Performance monitoring in place
- [ ] A/B test framework deployed
- [ ] Frontend SDK published
- [ ] Migration tools available
- [ ] Documentation complete
- [ ] Training completed
- [ ] Rollback plan documented
- [ ] Success metrics defined
- [ ] Go-live date scheduled

### 5.8 Success Criteria

1. **Performance**
   - 50% reduction in frontend message parsing time
   - 30% reduction in total message size
   - <100ms slide rendering time

2. **Developer Experience**
   - 80% positive feedback from frontend team
   - 60% reduction in message handling code
   - Zero breaking changes during migration

3. **User Experience**
   - Immediate status feedback for all operations
   - Smooth progress indicators
   - No perceived performance degradation

4. **Reliability**
   - <0.1% error rate increase
   - Successful rollback capability
   - No data loss during migration

## Appendix: Complete Message Examples

### Full Conversation Flow Example

#### State 1: Greeting
```json
// Backend sends:
{
  "message_id": "msg_001",
  "session_id": "session_abc",
  "timestamp": "2024-01-01T10:00:00Z",
  "type": "chat_message",
  "payload": {
    "text": "Hello! I'm Deckster. I can help you structure a clear and compelling presentation on any topic. What would you like to build today?"
  }
}
```

#### State 2: Questions
```json
// Backend sends:
{
  "message_id": "msg_002",
  "session_id": "session_abc",
  "timestamp": "2024-01-01T10:01:00Z",
  "type": "chat_message",
  "payload": {
    "text": "Great topic! To create the perfect presentation, I need to understand your needs better:",
    "list_items": [
      "Who is your target audience?",
      "What's the main goal of this presentation?",
      "How long will you be presenting?",
      "Any specific points you must cover?"
    ]
  }
}
```

#### State 3: Plan Confirmation
```json
// Backend sends (Message 1):
{
  "message_id": "msg_003",
  "session_id": "session_abc",
  "timestamp": "2024-01-01T10:02:00Z",
  "type": "chat_message",
  "payload": {
    "text": "Perfect! Based on your answers, I'll create a 10-slide presentation for your board meeting.",
    "sub_title": "Here's what I'm planning:",
    "list_items": [
      "Executive summary with key metrics upfront",
      "Problem/solution framework",
      "Market opportunity analysis",
      "Financial projections with 3-year outlook",
      "Clear call-to-action for funding"
    ]
  }
}

// Backend sends (Message 2):
{
  "message_id": "msg_004",
  "session_id": "session_abc",
  "timestamp": "2024-01-01T10:02:01Z",
  "type": "action_request",
  "payload": {
    "prompt_text": "Does this structure work for you?",
    "actions": [
      {"label": "Yes, let's build it!", "value": "accept_plan", "primary": true},
      {"label": "I'd like to make changes", "value": "reject_plan", "primary": false}
    ]
  }
}
```

#### State 4: Generation
```json
// Backend sends (Message 1 - Immediate):
{
  "message_id": "msg_005",
  "session_id": "session_abc",
  "timestamp": "2024-01-01T10:02:30Z",
  "type": "status_update",
  "payload": {
    "status": "generating",
    "text": "Excellent! I'm now creating your presentation. This will take about 15-20 seconds...",
    "progress": 0
  }
}

// Backend sends (Message 2 - After generation):
{
  "message_id": "msg_006",
  "session_id": "session_abc",
  "timestamp": "2024-01-01T10:02:45Z",
  "type": "slide_update",
  "payload": {
    "operation": "full_update",
    "metadata": {
      "main_title": "Series A Funding Proposal",
      "overall_theme": "Professional and compelling",
      "design_suggestions": "Modern tech startup aesthetic",
      "target_audience": "Venture capitalists",
      "presentation_duration": 10
    },
    "slides": [
      {
        "slide_id": "slide_001",
        "slide_number": 1,
        "html_content": "<div class='slide-container' data-slide-id='slide_001'><div class='hero-section'><h1 class='slide-title'>Series A Funding Proposal</h1><p class='slide-subtitle'>Revolutionizing Healthcare with AI</p></div></div>"
      },
      {
        "slide_id": "slide_002",
        "slide_number": 2,
        "html_content": "<div class='slide-container' data-slide-id='slide_002'><h2>Executive Summary</h2><div class='metric-grid'><div class='metric-card'><span class='metric-value'>$10M</span><span class='metric-label'>Series A Target</span></div></div></div>"
      }
    ]
  }
}

// Backend sends (Message 3):
{
  "message_id": "msg_007",
  "session_id": "session_abc",
  "timestamp": "2024-01-01T10:02:46Z",
  "type": "action_request",
  "payload": {
    "prompt_text": "Your presentation is ready! What would you like to do?",
    "actions": [
      {"label": "Looks perfect!", "value": "accept_strawman", "primary": true},
      {"label": "Make some changes", "value": "request_refinement", "primary": false}
    ]
  }
}
```

This plan provides a comprehensive roadmap for transforming Deckster's WebSocket communication into a clean, efficient, and maintainable protocol that will significantly improve both frontend and backend development experience.