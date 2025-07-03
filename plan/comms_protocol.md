# Communication Protocols - Single Source of Truth

This document defines the standardized JSON communication templates for all communication streams in the presentation generation system.

## 5.1 Director (I/O) → User/Frontend

### Unified Director-to-User Message Template
Both Director (Inbound) and Director (Outbound) use this common protocol for all user communications.

```json
{
  "message_id": "msg_unique_id_123",
  "timestamp": "2024-01-01T10:00:00Z",
  "session_id": "session_abc123",
  "type": "director_message",
  "source": "director_inbound" | "director_outbound",
  "data": {
    "slide_data": {
      "slides": [
        {
          "slide_id": "slide_1",
          "slide_number": 1,
          "title": "Introduction to Our Product",
          "html_content": "<div class='slide' id='slide_1'>\n  <h1>{{title}}</h1>\n  <img src='{{image_1}}' alt='Hero Image'/>\n  <div class='content'>{{body_text}}</div>\n  <div class='chart' id='chart_1'>{{chart_1}}</div>\n</div>",
          "yaml_template": "slide:\n  type: hero\n  layout: centered\n  components:\n    - type: title\n      content: \"{{title}}\"\n    - type: image\n      id: image_1\n      placeholder: true\n    - type: text\n      content: \"{{body_text}}\"\n    - type: chart\n      id: chart_1\n      placeholder: true",
          "assets": {
            "images": [
              {
                "id": "image_1",
                "url": "https://storage.example.com/session_abc123/slide_1/hero.png",
                "alt_text": "Product overview hero image",
                "type": "hero_image"
              }
            ],
            "videos": [
              {
                "id": "video_1",
                "url": "https://storage.example.com/session_abc123/slide_1/demo.mp4",
                "thumbnail": "https://storage.example.com/session_abc123/slide_1/demo_thumb.png",
                "duration": 120
              }
            ],
            "charts": [
              {
                "id": "chart_1",
                "type": "line_chart",
                "data_url": "https://api.example.com/data/chart_1.json",
                "config": {
                  "title": "Revenue Growth",
                  "x_axis": "Month",
                  "y_axis": "Revenue ($M)"
                }
              }
            ],
            "diagrams": [
              {
                "id": "diagram_1",
                "type": "flowchart",
                "svg_url": "https://storage.example.com/session_abc123/slide_1/process.svg",
                "mermaid_source": "graph LR\n  A[Start] --> B[Process]\n  B --> C[End]"
              }
            ],
            "external_links": [
              {
                "id": "link_1",
                "url": "https://example.com/more-info",
                "text": "Learn More",
                "target": "_blank"
              }
            ]
          }
        }
      ],
      "presentation_metadata": {
        "total_slides": 10,
        "current_version": 3,
        "last_updated": "2024-01-01T10:00:00Z",
        "status": "in_progress" | "completed" | "awaiting_feedback"
      }
    },
    "chat_data": {
      "type": "question" | "summary" | "progress" | "action_required",
      "content": {
        "message": "What is your target audience for this presentation?",
        "context": "This will help me customize the content and tone appropriately.",
        "options": ["B2B Enterprise", "B2C Consumers", "Investors", "Internal Team", "Other"],
        "required": true,
        "question_id": "q_audience_001"
      },
      "actions": [
        {
          "action_id": "action_001",
          "type": "accept_changes" | "acknowledge" | "provide_input" | "choose_option",
          "label": "Accept Changes",
          "primary": true,
          "data": {
            "affected_slides": ["slide_3", "slide_5"],
            "change_summary": "Updated charts with quarterly data"
          }
        }
      ],
      "progress": {
        "current_step": "Generating visual assets",
        "percentage": 65,
        "estimated_time_remaining": 30,
        "steps_completed": ["Requirements gathered", "Structure created", "Content generated"],
        "current_agent": "visual_designer"
      }
    }
  }
}
```

### Example: Question to User
```json
{
  "message_id": "msg_q_001",
  "timestamp": "2024-01-01T10:00:00Z",
  "session_id": "session_abc123",
  "type": "director_message",
  "source": "director_inbound",
  "data": {
    "slide_data": null,
    "chat_data": {
      "type": "question",
      "content": {
        "message": "What key metrics should we highlight in the performance section?",
        "context": "This will help create impactful data visualizations.",
        "options": null,
        "required": true,
        "question_id": "q_metrics_001"
      },
      "actions": null,
      "progress": null
    }
  }
}
```

### Example: Progress Update
```json
{
  "message_id": "msg_prog_001",
  "timestamp": "2024-01-01T10:05:00Z",
  "session_id": "session_abc123",
  "type": "director_message",
  "source": "director_outbound",
  "data": {
    "slide_data": null,
    "chat_data": {
      "type": "progress",
      "content": {
        "message": "Creating visual assets for your presentation",
        "context": null,
        "options": null,
        "required": false,
        "question_id": null
      },
      "actions": null,
      "progress": {
        "current_step": "Generating images with AI",
        "percentage": 40,
        "estimated_time_remaining": 45,
        "steps_completed": ["Structure defined", "Content written"],
        "current_agent": "visual_designer"
      }
    }
  }
}
```

## 5.2 User/Frontend → Director (Inbound)

### User Input Message Template

**Note**: The frontend does NOT classify the user's intent. It only captures what the user provides (text, files, voice, UI element references). The Director (Inbound) agent is responsible for interpreting the user's intent and determining the appropriate action.

```json
{
  "message_id": "usr_msg_001",
  "timestamp": "2024-01-01T10:10:00Z",
  "session_id": "session_abc123",
  "type": "user_input",
  "data": {
    "text": "Make the chart on slide 3 a pie chart instead and use more vibrant colors",
    "response_to": "q_audience_001",  // Optional: if responding to a specific question
    "attachments": [
      {
        "type": "file",
        "file_id": "file_001",
        "filename": "company_data.xlsx",
        "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "size_bytes": 245632,
        "upload_url": "https://storage.example.com/uploads/session_abc123/file_001"
      },
      {
        "type": "voice",
        "audio_url": "https://storage.example.com/uploads/session_abc123/voice_001.wav",
        "duration_seconds": 15,
        "transcription": "Also add our Q4 revenue numbers to the executive summary",
        "language": "en-US"
      }
    ],
    "ui_references": [
      {
        "reference_type": "slide",
        "slide_id": "slide_3"
      },
      {
        "reference_type": "element",
        "slide_id": "slide_3",
        "element_id": "chart_1",
        "css_selector": "#chart_1",
        "html_context": "<div class='chart' id='chart_1'><!-- Current chart HTML --></div>"
      }
    ],
    "frontend_actions": [
      {
        "action_id": "action_001",
        "action_type": "button_click",
        "button_id": "accept_changes",
        "context": {
          "presented_changes": ["slide_3", "slide_5"]
        }
      }
    ]
  }
}
```

### Director (Inbound) Intent Determination

The Director (Inbound) agent analyzes the user input and determines:

1. **Intent Classification**: What the user wants to do
2. **Target Identification**: Which slides/elements are affected
3. **Action Planning**: How to fulfill the request

```json
{
  "director_analysis": {
    "user_intent": "modify_visualization",
    "confidence": 0.95,
    "detected_actions": [
      {
        "action": "change_chart_type",
        "target": {
          "slide_id": "slide_3",
          "element_id": "chart_1"
        },
        "parameters": {
          "new_type": "pie_chart",
          "maintain_data": true
        }
      },
      {
        "action": "update_color_scheme",
        "target": {
          "slide_id": "slide_3"
        },
        "parameters": {
          "style": "vibrant"
        }
      }
    ],
    "requires_clarification": false
  }
}
```

### Example: Simple Text Input
```json
{
  "message_id": "usr_msg_002",
  "timestamp": "2024-01-01T10:15:00Z",
  "session_id": "session_abc123",
  "type": "user_input",
  "data": {
    "text": "Our target audience is B2B enterprise clients in the financial sector",
    "response_to": "q_audience_001",
    "attachments": [],
    "ui_references": [],
    "frontend_actions": []
  }
}
```

### Example: File Upload with Text
```json
{
  "message_id": "usr_msg_003",
  "timestamp": "2024-01-01T10:16:00Z",
  "session_id": "session_abc123",
  "type": "user_input",
  "data": {
    "text": "Here's our brand guidelines and last quarter's financial data",
    "response_to": null,
    "attachments": [
      {
        "type": "file",
        "file_id": "file_002",
        "filename": "brand_guidelines.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 5242880,
        "upload_url": "https://storage.example.com/uploads/session_abc123/file_002"
      },
      {
        "type": "file",
        "file_id": "file_003",
        "filename": "Q4_financial_data.xlsx",
        "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "size_bytes": 186425,
        "upload_url": "https://storage.example.com/uploads/session_abc123/file_003"
      }
    ],
    "ui_references": [],
    "frontend_actions": []
  }
}
```

### Example: User References Specific Slide Elements
```json
{
  "message_id": "usr_msg_004",
  "timestamp": "2024-01-01T10:20:00Z",
  "session_id": "session_abc123",
  "type": "user_input",
  "data": {
    "text": "Make this slide more visual and less text-heavy",
    "response_to": null,
    "attachments": [],
    "ui_references": [
      {
        "reference_type": "slide",
        "slide_id": "slide_5"
      },
      {
        "reference_type": "element",
        "slide_id": "slide_5",
        "element_id": "main-content",
        "css_selector": ".content-block",
        "html_context": "<div class='content-block' id='main-content'>\n  <ul>\n    <li>Point 1: 40% growth</li>\n    <li>Point 2: 300 new clients</li>\n    <li>Point 3: $5M revenue</li>\n  </ul>\n</div>"
      }
    ],
    "frontend_actions": []
  }
}
```

### Example: Voice Input with UI Action
```json
{
  "message_id": "usr_msg_005",
  "timestamp": "2024-01-01T10:25:00Z",
  "session_id": "session_abc123",
  "type": "user_input",
  "data": {
    "text": "",
    "response_to": null,
    "attachments": [
      {
        "type": "voice",
        "audio_url": "https://storage.example.com/uploads/session_abc123/voice_002.wav",
        "duration_seconds": 8,
        "transcription": "Yes, that looks perfect. Let's go with those changes.",
        "language": "en-US"
      }
    ],
    "ui_references": [],
    "frontend_actions": [
      {
        "action_id": "action_002",
        "action_type": "button_click",
        "button_id": "accept_changes",
        "context": {
          "presented_changes": ["slide_2", "slide_4", "slide_7"]
        }
      }
    ]
  }
}
```

### Example: Complex Mixed Input
```json
{
  "message_id": "usr_msg_006",
  "timestamp": "2024-01-01T10:30:00Z",
  "session_id": "session_abc123",
  "type": "user_input",
  "data": {
    "text": "Change the chart to show quarterly data instead of monthly, and use the color scheme from this brand guide",
    "response_to": null,
    "attachments": [
      {
        "type": "file",
        "file_id": "file_004",
        "filename": "brand_colors.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 1048576,
        "upload_url": "https://storage.example.com/uploads/session_abc123/file_004"
      }
    ],
    "ui_references": [
      {
        "reference_type": "element",
        "slide_id": "slide_7",
        "element_id": "revenue-chart",
        "css_selector": "#revenue-chart",
        "html_context": "<div id='revenue-chart' class='chart-container'><!-- Chart component --></div>"
      }
    ],
    "frontend_actions": []
  }
}
```

### Director (Inbound) Processing Examples

When the Director (Inbound) receives these inputs, it determines the user's intent:

**Example 1 - Text mentioning slide edit without explicit classification:**
```json
{
  "user_input": {
    "text": "The chart on slide 3 needs to be a pie chart",
    "attachments": [],
    "ui_references": []
  },
  "director_interpretation": {
    "intent": "modify_chart",
    "confidence": 0.92,
    "extracted_targets": [
      {
        "type": "slide_reference",
        "slide_number": 3,
        "element_type": "chart",
        "inferred": true
      }
    ],
    "required_actions": [
      {
        "action": "change_visualization_type",
        "agent": "data_analyst",
        "parameters": {
          "new_type": "pie_chart",
          "locate_chart_on_slide": 3
        }
      }
    ]
  }
}
```

**Example 2 - Ambiguous request requiring clarification:**
```json
{
  "user_input": {
    "text": "Make it more professional",
    "attachments": [],
    "ui_references": [
      {
        "reference_type": "slide",
        "slide_id": "slide_2"
      }
    ]
  },
  "director_interpretation": {
    "intent": "style_change",
    "confidence": 0.65,
    "ambiguity": "high",
    "clarification_needed": true,
    "clarification_questions": [
      {
        "question": "What aspect would you like to make more professional?",
        "options": [
          "Color scheme and visual style",
          "Content tone and language",
          "Layout and structure",
          "All of the above"
        ]
      }
    ]
  }
}
```

## 5.3 Director (Inbound) → Sub-Agents & Director (Outbound)

### Director Instructions Template
```json
{
  "message_id": "dir_inst_001",
  "timestamp": "2024-01-01T10:25:00Z",
  "session_id": "session_abc123",
  "correlation_id": "task_batch_001",
  "type": "agent_instruction",
  "source": "director_inbound",
  "target_agents": ["ux_architect", "researcher", "visual_designer", "data_analyst", "ux_analyst_diagrams"],
  "data": {
    "presentation_structure": {
      "title": "Q4 2024 Financial Performance Review",
      "total_slides": 10,
      "theme": "professional_modern",
      "color_scheme": {
        "primary": "#1E40AF",
        "secondary": "#3B82F6",
        "accent": "#10B981",
        "background": "#FFFFFF",
        "text": "#1F2937"
      },
      "slides": [
        {
          "slide_id": "slide_1",
          "slide_number": 1,
          "title": "Q4 2024 Performance Overview",
          "description": "High-impact opening slide with key metrics",
          "hook": "Record-breaking quarter with 40% YoY growth",
          "narrative": "Set the stage with impressive growth numbers and visual impact",
          "slide_type": "visual_heavy",
          "layout_template": "hero_with_metrics",
          "components": [
            {
              "component_id": "comp_1_1",
              "type": "image",
              "position": "background",
              "requirements": {
                "style": "corporate_modern",
                "mood": "optimistic_growth",
                "elements": ["upward_trend", "technology", "success"]
              }
            },
            {
              "component_id": "comp_1_2",
              "type": "metric_cards",
              "position": "overlay_bottom",
              "data_source": "quarterly_metrics"
            }
          ]
        },
        {
          "slide_id": "slide_2",
          "slide_number": 2,
          "title": "Revenue Breakdown by Segment",
          "description": "Detailed analysis of revenue sources",
          "hook": "Diversified growth across all segments",
          "narrative": "Show how each business segment contributed to overall success",
          "slide_type": "analysis_heavy",
          "layout_template": "chart_focused",
          "components": [
            {
              "component_id": "comp_2_1",
              "type": "chart",
              "subtype": "stacked_bar",
              "position": "main",
              "data_requirements": {
                "metrics": ["revenue_by_segment"],
                "period": "quarterly",
                "comparison": "YoY"
              }
            },
            {
              "component_id": "comp_2_2",
              "type": "insights_text",
              "position": "sidebar",
              "auto_generate": true
            }
          ]
        },
        {
          "slide_id": "slide_3",
          "slide_number": 3,
          "title": "Customer Journey Optimization",
          "description": "Process improvements and their impact",
          "hook": "50% reduction in onboarding time",
          "narrative": "Demonstrate how process improvements led to better customer experience",
          "slide_type": "diagrammatic",
          "layout_template": "process_flow",
          "components": [
            {
              "component_id": "comp_3_1",
              "type": "diagram",
              "subtype": "process_flow",
              "position": "main",
              "diagram_requirements": {
                "flow_type": "customer_journey",
                "stages": ["Awareness", "Consideration", "Purchase", "Onboarding", "Success"],
                "highlight_improvements": true,
                "style": "modern_minimal"
              }
            }
          ]
        }
      ]
    },
    "agent_specific_instructions": {
      "ux_architect": {
        "general_guidelines": {
          "maintain_consistency": true,
          "responsive_design": true,
          "accessibility_standards": "WCAG_AA"
        },
        "slide_layouts": [
          {
            "slide_id": "slide_1",
            "layout_requirements": {
              "grid": "12_column",
              "hero_image_coverage": "full_bleed",
              "metric_cards": {
                "count": 3,
                "style": "glass_morphism",
                "animation": "fade_in_up"
              }
            }
          }
        ]
      },
      "researcher": {
        "content_guidelines": {
          "tone": "professional_confident",
          "data_accuracy": "verified_sources_only",
          "citation_style": "footnotes"
        },
        "research_tasks": [
          {
            "slide_id": "slide_1",
            "component_id": "comp_1_2",
            "research_type": "metrics_extraction",
            "data_sources": ["financial_reports", "analytics_dashboard"],
            "required_metrics": ["revenue", "growth_rate", "customer_count"]
          }
        ]
      },
      "visual_designer": {
        "brand_guidelines": {
          "logo_usage": "top_right_corner",
          "image_style": "photorealistic_with_overlay",
          "icon_set": "phosphor_regular"
        },
        "asset_requests": [
          {
            "slide_id": "slide_1",
            "component_id": "comp_1_1",
            "asset_type": "hero_image",
            "specifications": {
              "dimensions": "1920x1080",
              "format": "png",
              "style_prompt": "Modern office with growth charts on screens, blue color theme, professional atmosphere"
            }
          }
        ]
      },
      "data_analyst": {
        "visualization_standards": {
          "chart_library": "chartjs",
          "interactive": true,
          "mobile_responsive": true
        },
        "chart_requests": [
          {
            "slide_id": "slide_2",
            "component_id": "comp_2_1",
            "chart_specifications": {
              "type": "stacked_bar",
              "data_processing": {
                "source_table": "revenue_segments",
                "grouping": "by_quarter",
                "calculations": ["sum", "percentage_of_total"]
              },
              "styling": {
                "color_palette": "brand_colors",
                "show_values": true,
                "legend_position": "bottom"
              }
            }
          }
        ]
      },
      "ux_analyst_diagrams": {
        "diagram_standards": {
          "tool": "mermaid",
          "style_theme": "neutral",
          "export_format": "svg"
        },
        "diagram_requests": [
          {
            "slide_id": "slide_3",
            "component_id": "comp_3_1",
            "diagram_specifications": {
              "type": "flowchart",
              "direction": "left_to_right",
              "nodes": [
                {"id": "A", "label": "Awareness", "type": "start"},
                {"id": "B", "label": "Consideration", "type": "process"},
                {"id": "C", "label": "Purchase", "type": "decision"},
                {"id": "D", "label": "Onboarding", "type": "process", "highlight": true},
                {"id": "E", "label": "Success", "type": "end"}
              ],
              "connections": [
                {"from": "A", "to": "B", "label": "Marketing"},
                {"from": "B", "to": "C", "label": "Sales"},
                {"from": "C", "to": "D", "label": "Implementation"},
                {"from": "D", "to": "E", "label": "Support"}
              ],
              "styling": {
                "highlight_color": "#10B981",
                "node_shape": "rounded_rectangle"
              }
            }
          }
        ]
      }
    },
    "global_context": {
      "presentation_purpose": "quarterly_board_review",
      "audience": "executives_and_investors",
      "key_messages": ["record_growth", "operational_efficiency", "market_expansion"],
      "constraints": {
        "max_text_per_slide": 50,
        "required_branding": true,
        "data_confidentiality": "internal_only"
      }
    }
  }
}
```

## 5.4 Worker Agents → Director (Outbound) & UX Analyst (Diagrams)

### Agent Output Template
```json
{
  "message_id": "agent_out_001",
  "timestamp": "2024-01-01T10:30:00Z",
  "session_id": "session_abc123",
  "correlation_id": "task_batch_001",
  "type": "agent_output",
  "source": "visual_designer" | "data_analyst" | "researcher" | "ux_architect" | "ux_analyst_diagrams",
  "target": "director_outbound",
  "data": {
    "task_reference": {
      "slide_id": "slide_1",
      "component_id": "comp_1_1",
      "task_id": "task_visual_001"
    },
    "output_type": "image" | "chart" | "text" | "layout" | "diagram",
    "status": "completed" | "partial" | "failed",
    "result": {
      "content_type": "image",
      "format": "base64" | "url" | "html" | "json",
      "content": {
        "url": "https://storage.example.com/session_abc123/slide_1/hero_image.png",
        "base64": null,
        "metadata": {
          "width": 1920,
          "height": 1080,
          "size_bytes": 524288,
          "format": "png",
          "alt_text": "Modern office environment showing growth and success"
        }
      },
      "integration_instructions": {
        "html_snippet": "<img src='{{image_url}}' alt='{{alt_text}}' class='hero-image' />",
        "css_classes": ["hero-image", "full-bleed"],
        "position": "background",
        "z_index": 1
      }
    },
    "processing_metadata": {
      "generation_time_ms": 3500,
      "model_used": "dall-e-3",
      "iterations": 1,
      "cost_units": 0.04
    },
    "error": null
  }
}
```

### Example: Chart Output from Data Analyst
```json
{
  "message_id": "agent_out_002",
  "timestamp": "2024-01-01T10:32:00Z",
  "session_id": "session_abc123",
  "correlation_id": "task_batch_001",
  "type": "agent_output",
  "source": "data_analyst",
  "target": "director_outbound",
  "data": {
    "task_reference": {
      "slide_id": "slide_2",
      "component_id": "comp_2_1",
      "task_id": "task_chart_001"
    },
    "output_type": "chart",
    "status": "completed",
    "result": {
      "content_type": "chart",
      "format": "json",
      "content": {
        "chart_config": {
          "type": "bar",
          "data": {
            "labels": ["Q1", "Q2", "Q3", "Q4"],
            "datasets": [
              {
                "label": "Product A",
                "data": [12, 19, 23, 28],
                "backgroundColor": "#1E40AF"
              },
              {
                "label": "Product B",
                "data": [8, 11, 15, 19],
                "backgroundColor": "#3B82F6"
              },
              {
                "label": "Product C",
                "data": [5, 7, 9, 12],
                "backgroundColor": "#10B981"
              }
            ]
          },
          "options": {
            "responsive": true,
            "plugins": {
              "title": {
                "display": true,
                "text": "Revenue by Product Line (in millions)"
              },
              "tooltip": {
                "mode": "index",
                "intersect": false
              }
            },
            "scales": {
              "x": {
                "stacked": true
              },
              "y": {
                "stacked": true,
                "ticks": {
                  "callback": "function(value) { return '$' + value + 'M'; }"
                }
              }
            }
          }
        },
        "raw_data_url": "https://api.example.com/data/revenue_q4_2024.json",
        "interactive_features": ["zoom", "pan", "export"]
      },
      "integration_instructions": {
        "html_snippet": "<div class='chart-container'>\n  <canvas id='chart_{{component_id}}'></canvas>\n</div>",
        "javascript_init": "new Chart(document.getElementById('chart_{{component_id}}'), {{chart_config}});",
        "css_classes": ["chart-container", "responsive-chart"],
        "position": "main",
        "z_index": 10
      }
    },
    "processing_metadata": {
      "generation_time_ms": 1200,
      "data_points_processed": 12,
      "aggregation_method": "sum",
      "data_source": "financial_database"
    },
    "error": null
  }
}
```

### Example: Diagram Output to Both Director(O) and UX Analyst
```json
{
  "message_id": "agent_out_003",
  "timestamp": "2024-01-01T10:35:00Z",
  "session_id": "session_abc123",
  "correlation_id": "task_batch_001",
  "type": "agent_output",
  "source": "ux_analyst_diagrams",
  "target": ["director_outbound", "ux_analyst_diagrams"],
  "data": {
    "task_reference": {
      "slide_id": "slide_3",
      "component_id": "comp_3_1",
      "task_id": "task_diagram_001"
    },
    "output_type": "diagram",
    "status": "completed",
    "result": {
      "content_type": "diagram",
      "format": "html",
      "content": {
        "svg_url": "https://storage.example.com/session_abc123/slide_3/customer_journey.svg",
        "mermaid_source": "graph LR\n    A[Awareness] -->|Marketing| B[Consideration]\n    B -->|Sales| C{Purchase}\n    C -->|Implementation| D[Onboarding]\n    D -->|Support| E[Success]\n    style D fill:#10B981,stroke:#059669,stroke-width:3px\n    style E fill:#3B82F6,stroke:#2563EB,stroke-width:2px",
        "editable_url": "https://mermaid.live/edit#base64_encoded_diagram",
        "metadata": {
          "nodes": 5,
          "edges": 4,
          "diagram_type": "flowchart",
          "complexity": "simple"
        }
      },
      "integration_instructions": {
        "html_snippet": "<div class='diagram-container'>\n  <object data='{{svg_url}}' type='image/svg+xml' class='process-diagram'>\n    <img src='{{svg_url}}' alt='Customer Journey Process Flow'/>\n  </object>\n</div>",
        "css_classes": ["diagram-container", "process-flow"],
        "position": "main",
        "z_index": 10,
        "interaction_enabled": true
      }
    },
    "processing_metadata": {
      "generation_time_ms": 800,
      "renderer": "mermaid",
      "version": "9.4.3",
      "theme": "neutral"
    },
    "error": null
  }
}
```

### Example: Error Response
```json
{
  "message_id": "agent_out_004",
  "timestamp": "2024-01-01T10:40:00Z",
  "session_id": "session_abc123",
  "correlation_id": "task_batch_001",
  "type": "agent_output",
  "source": "visual_designer",
  "target": "director_outbound",
  "data": {
    "task_reference": {
      "slide_id": "slide_4",
      "component_id": "comp_4_1",
      "task_id": "task_visual_002"
    },
    "output_type": "image",
    "status": "failed",
    "result": null,
    "processing_metadata": {
      "generation_time_ms": 5000,
      "attempts": 3,
      "last_attempt": "2024-01-01T10:39:55Z"
    },
    "error": {
      "code": "GENERATION_FAILED",
      "message": "Unable to generate image: Content policy violation detected",
      "details": {
        "violated_policy": "corporate_imagery",
        "suggestion": "Modify prompt to avoid trademarked logos"
      },
      "recoverable": true,
      "fallback_available": true,
      "fallback_action": {
        "type": "use_stock_image",
        "stock_image_id": "stock_corporate_001",
        "stock_image_url": "https://storage.example.com/stock/corporate_001.jpg"
      }
    }
  }
}
```

## Additional Protocol Standards

### 1. Message Validation
All messages must be validated using Pydantic BaseModel schemas before transmission.

### 2. Error Handling
- All errors must include recoverable status and fallback options where applicable
- Error codes should follow the pattern: `AGENT_ERROR_DESCRIPTION`
- Always include actionable suggestions in error responses

### 3. Asset Management
- All assets must be stored with unique IDs following pattern: `{asset_type}_{session}_{slide}_{component}`
- URLs must be secure (HTTPS) and include access tokens where required
- Binary data should be base64 encoded only when necessary (prefer URLs)

### 4. Versioning
- All message templates include version in headers (not shown for brevity)
- Current protocol version: 1.0.0
- Backward compatibility maintained for 2 major versions

### 5. Performance Considerations
- Large assets (>1MB) should always use URL references
- Batch similar operations in single messages
- Use streaming for real-time updates
- Implement pagination for large result sets

### 6. Security
- All messages must include session validation
- Sensitive data must be encrypted in transit
- PII must be masked in logs
- Access tokens expire after 1 hour

This document serves as the single source of truth for all communication protocols in the presentation generation system. All implementations must strictly adhere to these templates.