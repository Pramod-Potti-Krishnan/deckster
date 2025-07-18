Deckster: Revised WebSocket Communication Protocol
1. Guiding Principle

This revised protocol decouples messages by their frontend presentation purpose. Instead of a single, complex message type, the backend will emit distinct messages for chat content, slide updates, and user actions. This simplifies frontend logic, improves responsiveness, and creates a more robust system.
2. The New Streamlined Message Format

Every message from the backend to the frontend will now have a simple, consistent envelope. The type field tells the frontend exactly how to handle the payload.

New Message Envelope (Backend → Frontend):

{
  "message_id": "msg_unique_id",
  "session_id": "session_xyz",
  "timestamp": "2024-01-01T10:00:00.000Z",
  "type": "chat_message" | "action_request" | "slide_update" | "status_update",
  "payload": { ... }
}

    chat_message: Content for the chat interface.

    action_request: Prompts the user with buttons.

    slide_update: The full presentation structure for the slide view.

    status_update: A message to show the agent's status (e.g., "thinking...").

3. Rewriting the Conversation Flow with the New Protocol

Here is how the exact same conversation would flow using this new, streamlined model.
State 1: PROVIDE_GREETING

The backend sends one, simple chat_message.

Backend → Frontend:

{
  "message_id": "msg_abc123",
  "session_id": "session_xyz",
  "type": "chat_message",
  "payload": {
    "text": "Hello! I'm Deckster. I can help you structure a clear and compelling presentation on any topic. What would you like to build today?"
  }
}

Frontend Action: Renders payload.text in the chat window.
State 2: ASK_CLARIFYING_QUESTIONS

The backend sends one chat_message containing the structured questions.

Backend → Frontend:

{
  "message_id": "msg_def456",
  "session_id": "session_xyz",
  "type": "chat_message",
  "payload": {
    "text": "That's a great topic. To get this right, I have a few questions for you:",
    "list_items": [
      "Who is the target audience for this presentation (e.g., medical professionals, investors, general public)?",
      "What is the primary goal? Is it to inform, persuade, or educate?",
      "How long should the presentation be (in minutes)?",
      "Are there any specific AI applications in healthcare you want to focus on?"
    ]
  }
}

Frontend Action: Renders payload.text and the payload.list_items as a formatted list in the chat window.
State 3: CREATE_CONFIRMATION_PLAN

Here, we see the power of decoupling. The backend sends two messages in quick succession.

Message 1: The Summary (Backend → Frontend):

{
  "message_id": "msg_ghi789",
  "session_id": "session_xyz",
  "type": "chat_message",
  "payload": {
    "text": "Excellent, thank you. Based on your answers, I'm proposing a **6-slide** structure for your 15-minute presentation. Here is the plan I've put together:",
    "sub_title": "Key Assumptions I'm Making:",
    "list_items": [
        "The audience is technically savvy but focused on business value.",
        "The presentation should balance technical capabilities with financial benefits.",
        "We will include an 'Executive Summary' slide upfront as this is for a board meeting."
    ]
  }
}

Frontend Action: Renders the summary in the chat window, using the text, sub_title, and list_items to create a clean, structured message.

Message 2: The Action (Backend → Frontend):

{
  "message_id": "msg_ghi790",
  "session_id": "session_xyz",
  "type": "action_request",
  "payload": {
    "prompt_text": "Does this look correct?",
    "actions": [
      {"label": "Accept & Proceed", "value": "accept_plan"},
      {"label": "Request Changes", "value": "reject_plan"}
    ]
  }
}

Frontend Action: Renders the "Accept/Reject" buttons in the chat window.
State 4: GENERATE_STRAWMAN (The Biggest Improvement)

This is where the asynchronous nature shines. The backend can now communicate its status before delivering the final payload.

Message 1: Status Update (Backend → Frontend):
(Sent immediately after the user accepts the plan)

{
  "message_id": "msg_jkl010",
  "session_id": "session_xyz",
  "type": "status_update",
  "payload": {
    "status": "generating",
    "text": "Perfect! I'm now building your presentation outline. This might take a moment..."
  }
}

Frontend Action: Displays a "Deckster is thinking..." indicator.

Message 2: The Slide Data (Backend → Frontend):
(Sent a few seconds later, when generation is complete)

{
  "message_id": "msg_jkl011",
  "session_id": "session_xyz",
  "type": "slide_update",
  "payload": {
    "operation": "full_update",
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
        "slide_type": "title_slide",
        "title": "AI in Healthcare: Transforming Patient Care",
        "narrative": "Setting the stage for how AI is revolutionizing healthcare delivery",
        "key_points": ["Revolutionizing diagnostics", "Improving patient outcomes", "Reducing costs"],
        "analytics_needed": null,
        "visuals_needed": "**Goal:** Create an impactful opening visual. **Content:** A modern healthcare facility with AI elements. **Style:** Professional, futuristic, blue tones.",
        "diagrams_needed": null,
        "structure_preference": "Full-Bleed Visual"
      },
      {
        "slide_id": "slide_002",
        "slide_number": 2,
        "slide_type": "data_driven",
        "title": "Executive Summary: Key Impact Metrics",
        "narrative": "Highlighting the measurable benefits AI brings to healthcare operations",
        "key_points": ["30% reduction in diagnostic errors", "$2.5M annual cost savings", "45% improvement in patient satisfaction"],
        "analytics_needed": "**Goal:** Show dramatic improvements. **Content:** KPI dashboard with 3-4 key metrics. **Style:** Clean grid layout with trend arrows.",
        "visuals_needed": null,
        "diagrams_needed": null,
        "structure_preference": "Grid Layout"
      }
    ]
  }
}

Frontend Action: Receives the structured slide data and renders it according to the slide_type and structure_preference. The frontend is responsible for visual presentation based on these specifications.

Message 3: The Follow-up Action (Backend → Frontend):
(Sent immediately after the slide data)

{
  "message_id": "msg_jkl012",
  "session_id": "session_xyz",
  "type": "action_request",
  "payload": {
    "prompt_text": "I've generated the first draft of your presentation. How does it look?",
    "actions": [
      {"label": "Looks Good!", "value": "accept_strawman"},
      {"label": "Make Changes", "value": "request_refinement"}
    ]
  }
}

Frontend Action: Renders the new set of action buttons in the chat window.
4. Summary of Benefits

This revised, decoupled protocol provides significant advantages:

    Simplicity for Frontend: The frontend logic becomes a simple switch statement based on the message type. There is no need to parse complex, nested objects to update different UI components from a single message.

    Responsiveness & Asynchronous Support: The status_update type allows the backend to provide immediate feedback to the user while performing long-running tasks like strawman generation.

    Clear Separation of Concerns: Each message has one job. chat_message handles conversation, slide_update provides structured slide data with all planning fields preserved, and action_request handles user decisions.

    Data Preservation: All critical planning fields (analytics_needed, visuals_needed, diagrams_needed, structure_preference) are preserved and sent to the frontend, enabling rich visualization and proper layout selection.

    Extensibility: Adding new features becomes easier. For example, if you add a real-time collaboration feature, you could simply introduce a new message type: "collaborator_update" without affecting any of the existing frontend logic.