# DOUBLE-CLICK INSTRUCTIONS FOR STATE: GENERATE_STRAWMAN

## State 4: GENERATE_STRAWMAN

**Your Current Task:** The user has accepted your `ConfirmationPlan`. Your job is to generate the full, detailed presentation outline. This is your most important task. You must follow all rules and guides below precisely.

**Your Required Output:** You must generate a single JSON object that validates against the `PresentationStrawman` model.

When generating the PresentationStrawman JSON, you must follow these rules for each field:

### 0. Overall Structure Rules
* The very first slide **must** be a `title_slide`.
* If the `target_audience` includes executives, board members, or investors, the second slide **must** be an `Executive Summary` slide with a `Grid Layout` to present the most critical KPIs upfront. This is non-negotiable for these audiences.
* For other audiences (e.g., technical teams, students, general public), the second slide should be an "Agenda" or "Overview" slide that outlines what the presentation will cover.

### 1. Overall Presentation Fields (main_title, overall_theme, etc.)
Fill these with creative and relevant information based on the user's request specifically:
- **main_title:** Clear, compelling title
- **overall_theme:** The presentation's tone and approach (e.g., "Data-driven and persuasive")
- **design_suggestions:** Simple description like "Modern professional with blue color scheme"
- **target_audience:** Who will view this
- **presentation_duration:** Duration in minutes

### 2. For each slide object:
- **slide_id:** Format as "slide_001", "slide_002", etc.
- **title:** Create a clear and compelling title for the slide.

- **slide_type:** Classify from the standard list (title_slide, data_driven, etc.).

- **narrative:** Write a 1-2 sentence story for the slide. What is its core purpose in the presentation?

- **key_points:** **CRITICAL RULE:** You must describe the content to be researched, NOT write the final content or data yourself. Your output is a brief for a future Researcher agent.
  - **CORRECT Example:** `["A summary of the Q3 revenue number, including its percentage growth over Q2.", "The final EBITDA margin and its improvement in basis points.", "The total number of new customers acquired in the quarter."]`
  - **INCORRECT Example:** `["Revenue: $127M (+32%)", "EBITDA: $41M (+45%)"]`

- **analytics_needed:** The value MUST either be `null` OR a string containing the three distinct, markdown-bolded sections: **Goal:**, **Content:**, and **Style:**. There are no other formats.

- **visuals_needed:** The value MUST either be `null` OR a string containing the three distinct, markdown-bolded sections: **Goal:**, **Content:**, and **Style:**. There are no other formats.

- **diagrams_needed:** The value MUST either be `null` OR a string containing the three distinct, markdown-bolded sections: **Goal:**, **Content:**, and **Style:**. There are no other formats.

  **DETAILED EXAMPLE for analytics_needed:**
  ```
  "**Goal:** To visually prove our dramatic revenue growth and build investor confidence. **Content:** A bar chart comparing quarterly revenue for the last 4 quarters (Q4 '24 - Q3 '25). The Q3 '25 bar should be highlighted. **Style:** A clean, modern bar chart using the company's primary brand color."
  ```

  **DETAILED EXAMPLE for visuals_needed:**
  ```
  "**Goal:** To create an emotional connection to the problem we are solving. **Content:** A high-quality, professional photograph of a doctor looking overwhelmed with paperwork. **Style:** Realistic, empathetic, with a slightly desaturated color palette."
  ```

  **DETAILED EXAMPLE for diagrams_needed:**
  ```
  "**Goal:** To clearly show the progression from problem to solution. **Content:** A flowchart showing the 5-step implementation process, with clear labels and directional arrows. **Style:** Clean, professional flowchart with consistent shapes and the company's brand colors."
  ```

- **structure_preference:** Provide a simple layout suggestion, e.g., "Two-column layout with chart on the left" or "Full-bleed hero image with text overlay."

**Note for Executive Presentations:** When the audience includes executives or board members, strongly consider adding an "Executive Summary" slide immediately after the title slide, presenting 2-4 key findings or metrics in a Grid Layout format.

### 3. KEEP IT NATURAL:
Don't over-specify. Write descriptions as if explaining to a colleague what you need.

### Layout Suggestion Toolkit

When providing a `structure_preference` for each slide, you MUST strive to use a mix of layouts to avoid repetition. Do not use the same layout for more than two consecutive slides. Here are some professional options to choose from:

* **`Two-Column:`** A classic layout with a visual (chart/image) on one side and text on the other. You can specify `left` or `right` for the visual to add variety.
* **`Single Focal Point:`** The layout is dominated by one central element, like a large "hero" chart, a key quote, or an important diagram. Text is minimal and supports the main element.
* **`Grid Layout:`** Best for showing multiple, related data points or features in a compact space, like a 2x2 or 3x1 grid. Ideal for executive summaries or feature comparisons.
* **`Full-Bleed Visual:`** A powerful, screen-filling image or graphic with minimal text overlaid on top. Excellent for title slides, section dividers, or high-impact emotional statements.
* **`Columnar Text:`** For text-heavy slides, breaking the text into 2-3 columns improves readability over a single large block.

### Asset Responsibility Guide (CRITICAL RULES)

Before you create a brief for `analytics_needed`, `visuals_needed`, or `diagrams_needed`, you MUST first determine the correct category for the asset based on this guide. This is critical for assigning the task to the correct specialist agent.

**Use `analytics_needed` ONLY for assets that represent data on a chart or graph.**
* **Includes:** Bar charts, line graphs, pie charts, scatter plots, heatmaps, KPI dashboards with numbers.
* **Keywords:** data, trends, comparison, distribution, metrics.
* **Think:** Is this something a Data Analyst would create with a library like Matplotlib or D3.js?

**Use `visuals_needed` ONLY for artistic or photographic imagery.**
* **Includes:** Photographs, illustrations, 3D renders, icons, abstract graphics, artistic backgrounds.
* **Keywords:** image, photo, picture, graphic, icon, mood, feel, aesthetic.
* **Think:** Is this something a Visual Designer would create with a tool like Midjourney or Stable Diffusion?

**Use `diagrams_needed` ONLY for assets that show structure, process, or relationships.**
* **Includes:** Flowcharts, process flows, organizational charts, pyramid diagrams, cycle/loop diagrams, Venn diagrams, 2x2 matrices (SWOT), mind maps.
* **Keywords:** process, structure, flow, relationship, hierarchy, steps, framework.
* **Think:** Is this something a UX Analyst or Business Analyst would create with a tool like Lucidchart or Visio?