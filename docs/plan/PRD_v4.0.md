# Product Requirements Document: AI-Powered Presentation Generator

## 1. Introduction

This document outlines the product requirements for an AI-powered presentation generation platform. The system will leverage a multi-agent architecture to intelligently create compelling and visually appealing presentations based on user inputs. The platform will streamline the presentation creation process, from initial concept to final output, by automating content research, data analysis, visual design, and layout.

## 2. Guiding Principles

The following principles will guide the development of this platform:

### Technology Stack (Starting Point)

- The output of each agent will be standardized using Base Model in the Pydantic library, making communication seamless between agents.
- Agents will be built using Pydantic AI, Agent Module, which provides multi-LLM access through a single window.
- Logging will be maintained using Pyrantic Log Fire.
- Agent orchestration and chaining will be implemented using LangGraph.
- Pre-built capabilities and tools available on the MCP server will be leveraged where possible.
- **FastAPI**: For high-performance communication between the frontend and the Director agents, and potentially between the agents themselves. FastAPI is extremely fast, includes automatic API documentation, and has native integration with Pydantic, which simplifies development.
- **JSON** as the primary communication protocol between agents, with the slide's visual content embedded as an HTML string within the JSON payload.

### Development Focus

- Significant attention will be given to the quality and clarity of prompts for each agent.
- A clear structure will be established for how agents utilize short-term (contextual) and long-term memory.

## 3. High-Level Agent Workflow

The platform will utilize a series of specialized agents, orchestrated by a central "Director" agent, to manage the presentation creation process. The workflow is designed to be iterative and collaborative, allowing for user feedback at key stages.

### Workflow Stages

1. **User Input & Clarification**: The Director (Inbound) agent will interact with the user to gather and clarify project requirements.
2. **Straw Man Creation**: The Director (Inbound) will generate a "straw man" or outline of the presentation for user approval.
3. **Task Delegation**: Once the straw man is approved, the Director (Inbound) will delegate tasks to specialized "worker" agents.
4. **Content Generation & Design**: The worker agents (Researcher, Data Analyst, Visual Designer, UX Architect, UX Analyst) will generate the content, visuals, and layout for each slide.
5. **Assembly & Quality Assurance**: The Director (Outbound) will assemble the outputs from the worker agents, ensure quality and consistency, and present the final slides to the user.
6. **Iteration & Refinement**: The user can provide feedback on the slides generated, which the Director (Inbound) will use to initiate further revisions.

## 4. Roles and Responsibilities of Agents

### 4.1. User/Frontend

- The user interacts with the system through a frontend interface.
- The frontend is responsible for rendering the output provided by the Director agents and capturing user input.

### 4.2. Director (Inbound)

The Director (Inbound) agent is the primary point of contact for the user and the orchestrator of the presentation creation process.

#### Key Responsibilities

- Engages the user with customized questions to clarify requirements such as presentation length, audience type, topic, number of slides, and desired balance between verbose and visual content.
- Confirms its understanding of the requirements with the user before proceeding. This can be an auto-accept or require explicit user approval.
- Before building the straw man, the director confirms with the user its understanding and what it is planning to do. It might be auto-accept, or the user can stop to make some changes. Generally, that is the confirmation after asking questions the director will do, and then it starts the process of building the straw man.

#### Straw Man Creation

Builds the straw man including:

- What is the theme that is going to be used across the presentation?
- The title of each slide.
- Narrative and hook in each slide.
- Description of each slide and high level of how it would be structured.
- Potential Images / Analysis / Videos / Diagrams to be added to the slide.
- How it should be structured for the audience for impact.
- What is this type of slide which includes:
  - Is it a visual heavy slide?
  - Is it an analysis heavy slide?
  - Is it a diagrammatic slide?
  - Is it a plain text slide?, etc.
  - If it is a plain text slide, how might be best positioned? Or would it be a major text with some image / analysis.
  - Is it a sub-section / breaker slide, etc.

The straw man is provided in HTML format embedded in JSON to be rendered by the front-end.

Iteratively refines the straw man based on user feedback, with the ability to edit specific slides while retaining others.

Once confirmed by the user, this would also be passed on to further sub-worker agents.

#### Task Delegation

Provides clear and detailed instructions to each worker agent. This includes specifying user-provided inputs versus director-generated inputs, with user inputs being treated as sacrosanct.

Can request work for slides one by one to maintain focus.

Maintains an iteration number for tracking changes.

Director intake provides tasks clearly for each of the next set of agents to do in addition to the simple HTML. This includes:

- **For the researcher**: What content is needed per slide, what references, what the narrative is, what is the structure of the content needed (title, sub-topic, classification etc.). Approximate words. These could be more than the actual number of words needed. Could be 3 acts or so because the director outbound would take a very strategic call on the content needed based on the layout architect's inputs.
- **For the artist**: It would provide content on image needed or video needed or GIF needed and necessary details to make it into the right context. It would also share the theme and what are the requirements of the image.
- **For the analyst**: It would provide the context of what the analysis is needed, what the analysis would prove out in the context of the slide and how it will add value, etc.
- **For the layout architect**: It would provide clear instructions on the initial thought process on the slide, what elements need to be there. While director may provide multiple options like an image or chart for a specific slide, the layout architect has to be clear and layout architects makes a very strategic choice which will be used as a final HTML that we are using to build that specific page.
- **For the analyst, building diagrams**: Clear instructions in terms of what kind of diagram it is (process diagram, hierarchy diagram, architecture diagram, etc.) and using that context on what needs to be built. If it is such a slide, the input would have also gone to the researcher that the content that the researcher is preparing would be sent to the diagrams analyst who would actually convert that into a diagram. So, specifics of that would also go to the researcher.

While internally interacting, the director has to make it explicit as to what is provided by the user as an input vs. what's an input from the director. A user input has to be sacrosanct. A director input could have some variations because the director is looking at the others to validate that. So, user input has to be validated by the director outbound to make sure that it meets all the quality criteria.

Director inbounds also communicates with Director Outbound to ensure it is prepared when the outputs come to it from the worker agents.

Once Director (Outbound) shares output with user, and any further interactions would again be with the Director (Inbound). This case the input might on specific slides or specific aspects of slides like a chart or such. In this case the Director calls specific agents with specific instructions to change.

The director can ask for input for slides one by one giving worker agents focus. Rather than trying to get all at once.

The iteration number might also need to be maintained.

#### Capabilities

- Knowledge of best practice frameworks for Decks.
- Search user-uploaded documents.
- Themes to use. Type of slides to use.
- Build straw man.
- Ask questions and clarify.
- Clearly provide instructions.

### 4.3. UX Architect

- Starts on confirmation from the Director (Inbound).
- Initially sets up a consistent theme across slides, including title slides, content slides, and visual slides. These include main title: size, position, fonts, font colors, slide elements: themes, footers, etc. This is determined and stored. This will be the standard across all slides. This is built using director's and user's input, trying to match as close as possible following design principles. This one set is typically not changed unless asked by the director or user.
- **Slide by slide**: the slide structure + theme provided in Straw Man is converted into actual boxes placed in the layout, and the title, header, footer, etc. follow point #2. The content space is laid out in this phase following best practices on alignment, white spaces, structural balance, theme, etc. This could naturally differ between text heavy slides vs. text with supporting visual slides vs visual with supporting text slides vs title slides vs section header slides etc.
- The slide is built as a HTML or YAML with placeholder text for title, subtitle, description, visual etc. This will be replaced by a Director Outbound when stitching together with the actual content and actual text and images and analysis and other things provided across.
- Layout Architect sends slide-by-slide to Director(Outbound) to ensure that it can be easily assembled rather than wait for the entire content.

### 4.4. Researcher

- The Researcher takes the input from the director + user to build content necessary for the appropriate slides. The content is built in the structure asked for by the director.
- The Researcher can search internal documents and external data through search for building content.
- The Researcher can summarize data and bring it into a structure that is necessary. The reference links to where the content is extracted from is kept and provided back to the director outbound so that reference links can also be published.
- The content is shared with the director outbound slide by slide in the structure provided by the director inbound.

#### Capabilities

- Internal document search
- External search
- Summarization

### 4.5. Data Analyst

A very interesting profile and a differentiator with competitors.

- Based on the slide where an analysis is asked for and its prominence in the slide bracket, that is, if the slide is only for showcasing the analysis vs. if it is supporting a text, larger text on the slide - basically the size and relevance of the charting space.; The analyst takes a call in what might be an analysis that can be shown to make an impact and the data needed for the same.
- The analyst looks at existing data available, and if existing data can provide value, that is taken as priority #1 to build one of the potential analyses to support the slide.
- If existing data is not available, analysts contemplate between external data and synthetic data that it can generate to build high-priority analysis for the slide.
- The data is processed, transformed, and quality-checked. The chart or visualization is built. The chart for each slide is provided as an image with a link to the underlying data. An analysis of the chart including some text of insights along with the title of the chart is provided. We need to ensure the chart is the scales are shown, the x-axis, y-axis, or the various axes are shown, etc.

#### Tools

- Ability to potentially run Python-based scripts, import a library like Scikit Learn or Matplotlib or Seaborn.
- Ability to search external libraries for data.
- Ability to create synthetic data using Python code, etc.
- Knowledge of potential visualizations that can really make a difference in slides.

### 4.6. Visual Designer

- Builds an image, GIF, icon, vector, or video.
- Builds a consistent theme to be used across all the images for a specific tech. This is a one-time activity, and this is a text content in terms of how what is the theme across all the different things it builds.
- **Image**: Based on the t-shirt sizing of the image received along with the content that is necessary in the image. It builds the amount of details necessary in it to convey the story. It calls a diffusion model to build the image with the right context, content, theme, size, etc. to build the image.
- **GIFs**: Same as above, with animation explained.
- **Icons**: Provided as vectors, small size, simpler models. Typically one color vectors.
- **Videos**: Storyline is built and shared with a theme and context.
- Output is provided slide by slide to the Director (Outbound).

### 4.7. UX Analyst (Diagrams Guy)

The UX Analyst specializes in creating diagrams to visually represent complex concepts, which is a significant differentiator.

- Selects the appropriate diagram type (e.g., process flow, hierarchy) based on the Director's instructions. What is the type of diagram that can best represent this construct? Is it a process flow or is it a hierarchical structure, etc.? Typically, this is provided by the director inbound.
- Based on the type of diagram, an existing template or a framework is leveraged to build the appropriate structure.
- Size of the content that can fill within the template is provided in terms of number of characters.
- Content provided by the researcher is structured, simplified, and fit into the diagram to actually build the diagram. Therefore, the UX analyst is only able to work after the researcher has completed the research.
- Color combination for the diagrams template would need to be aligned with the overall theme.
- The UX analyst would need to have access to a collection of pre-built templates for easy processing.

### 4.8. Director (Outbound)

#### Slide Assembly

- Uses the templates from the UX Architect as the foundation for each slide.
- Summarizes and fits the content from the Researcher into the slide layout.
- Stitches together all elements of a slide, including text, visuals, and diagrams.

#### User-Facing Output

- Can provide a first draft of the content to the user before all visual elements are ready, with visuals being lazy-loaded. Output produced and shared slide by slide.
- Shares the completed slides with the user/frontend in HTML format packaged in a JSON.
- Provides a summary of the work accomplished at the end of the process.

#### Quality Validation

- Ensures that all outgoing slides are consistent with the user's requirements and the Director (Inbound)'s instructions.
- Performs quality checks and can send content back to the Researcher for revisions if necessary (a feature that may be implemented later).

# Communication Protocols and Requirements

## 5. Communication Protocols

Clear and consistent communication protocols are essential for the smooth operation of the multi-agent system and for a seamless user experience.

### 5.1 Director(I) and Director(O) to the User / Frontend

Any communication with the user would be common protocol regardless of where it goes from Director (Inbound) or Director (Outbound). Need to have a simple and common messaging schema by which the Director(Inbound) and the Director (Outbound) communicate with the user. If it is a common protocol, it makes it easy for the front-end to display to the user. This should include:

- **Data to be displayed in the slide section of the interface** which includes HTML/YAML template with links to image, videos, charts, diagrams, other links, etc.
- **Data to be displayed on the chat section with the user.** This could be:
  - Questions to the user
  - Summary of actions performed
  - Processing updates when the system is working
  - Any actions that the system wants a user to perform (like "accept changes" or "acknowledge that it can proceed", etc.)

### 5.2 User / Frontend to Director (Inbound)

This could be answers to questions or general inputs from user at any point of time, including text.

- There could be images, pdfs, ppts, docs or other modes and data the user may upload, including voice. These must have a method for taking in and processing.
- They could be action callouts like accepting changes also.
- There could be specific changes within a slide that the user might want to change, including the HTML tags for the same so that a specific slide could be referenced. This should include a common protocol by which we may let communication from the user on the slide and the elements within the slide be transferred to it.

### 5.3 Director (Intake) to All Sub-Agents and Director (Outbound)

- Director (Intake) interacts with the user and orchestrates the process. It is important for a director to therefore provide clear instructions to other agents in the line.
- It provides a base HTML, YAML, or JSON layout the structure, title, description, hook, narrative per slide, and the type of slide (like a visual heavy or analysis heavy or text heavy or diagrammatic) including images, gifs, icons, analyses (i.e. charts) required by each slide.
- Further it could provide separate instruction for each of the sub-agents in the JSON. E.g., 
  - (i) The image/ analysis needed specifically for the slides and context, etc. This makes it easer for each agent to look at the exact instruction for it + use the rest of it as context.
  - (ii) Diagram needed could include type of presentation (like process or hierarchy or etc.). Diagram is unique and starts only after content is prepared by the researcher.
- There is a unique ID for every content being built by each, and this could include a slide number, item number, etc.

### 5.4 Worker Agents to Director (Outbound) and UX Analyst (Diagrams)

- This could include a combination of referencing to the item like slide number, item number, HTML tag, type of item, etc.
- And the work output. This could be text, link to an image, link to a chart with the data, link to the data of the chart, etc.

## 6. Non-Functional Requirements

- **Performance**: The system should be responsive, with minimal delays in agent communication and content generation. The lazy loading of images is one strategy to enhance perceived performance.
- **Scalability**: The architecture should be able to handle multiple users and presentation generation requests concurrently.
- **Reliability**: The system should be robust and handle errors gracefully, with clear error messaging to the user when a request cannot be fulfilled.
- **Security**: User-uploaded documents and personal information must be handled securely and with privacy in mind.

## 7. Success Metrics

The success of the AI-powered presentation generator will be measured by:

- **User Adoption**: The number of active users and presentations created.
- **User Satisfaction**: Positive user feedback, high ratings, and low churn rate.
- **Task Completion Rate**: The percentage of users who successfully generate a complete presentation.
- **Time to Completion**: The average time it takes for a user to create a presentation from start to finish.
- **Quality of Output**: User ratings on the quality, relevance, and visual appeal of the generated presentations.