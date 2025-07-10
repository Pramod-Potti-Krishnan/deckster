Deckster: Phased Memory & Context Management Plan (RAG & State-Aware)
Overview

This document outlines a three-phase plan to upgrade Deckster's memory system. The goal is to evolve from the current "full context" model to an intelligent, state-aware architecture that is more efficient, scalable, and capable.

This plan integrates two powerful concepts:

    State-Aware Context Selection: The system intelligently assembles a minimal, relevant context package based on the agent's current task.

    User-Centric RAG: For specific tasks, the system performs Retrieval-Augmented Generation on user-uploaded documents to ground its output in factual, user-provided data.

Phase 1: Foundational Cleanup & RAG Preparation

Goal: To clean up the data structure and lay the essential groundwork for both state-aware context and the user-centric RAG system.
Practical Steps:

    Decouple Structured Data:

        Action: In your sessions table, move confirmation_plan and presentation_strawman into their own dedicated JSONB columns, separate from the conversation_history.

        Reasoning: This treats core deliverables as first-class data artifacts, making them easier to manage and query.

    Introduce a "Context Builder" Module:

        Action: Create a dedicated ContextBuilder class. For this phase, its logic will be simple: concatenate all session data and history for the LLM prompt.

        Reasoning: This abstracts context creation, creating a clean seam in the code to add more intelligence in later phases.

    Prepare the Database Schema for RAG:

        Action: Create the user_document_chunks table in Supabase with session_id, content, embedding, and source_filename columns. Enable the pgvector extension and create an index for efficient search.

        Reasoning: This prepares the necessary infrastructure to store and search vectorized content from user uploads.

Benefit of Phase 1: The database and codebase are now modular and ready to support the advanced logic of Phase 2.
Phase 2: Implementing State-Aware Context & Core RAG

Goal: To build the core intelligence of the memory system. The ContextBuilder will become state-aware, and it will learn to use RAG as a specialized tool for the strawman generation task.
Practical Steps:

    Build the Document Ingestion Pipeline:

        Action: Create a background process to handle user file uploads. This pipeline will extract text, chunk it, create vector embeddings, and store the results in the user_document_chunks table, linked to the session_id.

        Reasoning: This converts the user's unstructured documents into a searchable, session-specific knowledge base.

    Upgrade the ContextBuilder with State-Aware Logic and RAG:

        Action: This is the most critical step. Evolve the ContextBuilder to first check the current_state and then assemble a tailored context package. RAG is now a sub-routine called only when needed.

        Reasoning: This combines the efficiency of state-awareness with the power of RAG, ensuring the right information is used at the right time.

        State-Aware Context Building Logic with RAG:

        # In src/context_builder.py
        class ContextBuilder:
            def build_context(self, session_data: dict) -> str:
                state = session_data.get("current_state")

                if state == "CREATE_CONFIRMATION_PLAN":
                    # This state only needs the initial request and clarifying answers. No RAG needed.
                    return self._build_plan_context(session_data)

                elif state == "GENERATE_STRAWMAN":
                    # This state needs the plan AND relevant facts from the user's docs.
                    # It calls the RAG sub-routine.
                    return self._build_rag_generate_context(session_data)

                elif state == "REFINE_STRAWMAN":
                    # This state needs the strawman, recent messages, and maybe new RAG results.
                    return self._build_rag_refine_context(session_data)

                else: # For greeting, asking questions, etc.
                    # Fallback to simpler context (e.g., just recent conversation history).
                    return self._build_simple_context(session_data)

            def _build_rag_generate_context(self, session_data: dict) -> str:
                plan = session_data.get("confirmation_plan")
                session_id = session_data.get("id")

                # 1. Generate a search query from the plan
                search_query = f"Key points for a presentation titled '{plan['main_title']}'"

                # 2. Perform vector search on user's documents
                retrieved_chunks = self._perform_rag_search(session_id, search_query)

                # 3. Assemble the final prompt with both plan and RAG context
                final_prompt = f"""
                Here is the user-approved plan: {plan}

                Here is some relevant information retrieved from the documents the user uploaded:
                ---
                {retrieved_chunks}
                ---
                Based on the plan AND the retrieved information, generate the PresentationStrawman.
                """
                return final_prompt

Benefit of Phase 2: You achieve a massive reduction in token usage across most states, while making the most critical state (GENERATE_STRAWMAN) dramatically more intelligent by grounding it in the user's own data.
Phase 3: Advanced RAG & Hyper-Contextual Awareness

Goal: To refine the RAG process and context selection, making it interactive, precise, and maximally efficient.
Practical Steps:

    Implement Slide-Specific RAG Queries:

        Action: Instead of one general RAG query for the whole presentation, the ContextBuilder will loop through each slide in the ConfirmationPlan. For each slide, it will use the slide's title and narrative to generate a highly specific query, retrieve the relevant chunks, and inject them into the prompt for that specific slide's generation.

        Reasoning: This provides hyper-relevant, "just-in-time" facts for each individual slide, leading to a much higher quality and more accurate output.

    Introduce RAG-Powered Q&A:

        Action: Empower the agent to use the RAG system during the ASK_CLARIFYING_QUESTIONS phase. Before asking the user a question, it will first perform a quick search on the uploaded documents to see if it can find the answer itself.

        Reasoning: This creates a magical user experience. The agent becomes proactive, reducing the number of questions it needs to ask and demonstrating a deeper understanding of the user's provided materials.

    Implement Progressive Summarization:

        Action: After major milestones (like Plan Accepted), trigger a fast LLM call to create a "session summary." This summary, combined with the "sliding window" of the last few messages and targeted RAG results, becomes the ultimate context package.

        Reasoning: This is the final step for production-grade scalability. It ensures the context window remains small and efficient, even for extremely long and complex refinement sessions, while never losing the core mission or factual grounding.