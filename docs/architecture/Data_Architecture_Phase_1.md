# Data Architecture - Phase 1

## Overview

This document describes the data architecture implemented in Phase 1 of Deckster using Supabase (PostgreSQL). The architecture is designed to support a stateful AI presentation generation system with user session management, content persistence, and preparation for future AI-powered features.

## Database Stack

- **Database**: PostgreSQL (via Supabase)
- **Extensions**: 
  - `uuid-ossp` - UUID generation
  - `vector` - Vector similarity search for embeddings
  - `pg_trgm` - Text similarity and fuzzy matching
- **Features**: Row Level Security (RLS), JSONB storage, Vector indexes

## Table Architecture

### 1. Sessions Table

The core table managing user conversations with the Director agent.

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    conversation_history JSONB[] DEFAULT ARRAY[]::JSONB[],
    current_state JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    expires_at TIMESTAMPTZ NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB
);
```

#### Column Details

| Column | Type | Purpose | Notes |
|--------|------|---------|-------|
| `id` | TEXT | Primary key | Generated UUID string |
| `user_id` | TEXT | User identifier | Added in migration, NOT NULL |
| `conversation_history` | JSONB[] | Array of conversation turns | Each element contains role and content |
| `current_state` | JSONB | Flexible state storage | Stores all session state data |
| `created_at` | TIMESTAMPTZ | Creation timestamp | Auto-set to UTC |
| `updated_at` | TIMESTAMPTZ | Last update timestamp | Updated via trigger |
| `expires_at` | TIMESTAMPTZ | Session expiration | For cleanup |
| `metadata` | JSONB | Additional flexible data | For future use |

#### Indexes
- `idx_sessions_user_id` - User-specific queries
- `idx_sessions_expires_at` - Expiration cleanup
- `idx_sessions_user_created` - User sessions by date
- `idx_sessions_user_state` - State-based queries

#### Triggers
- `update_sessions_updated_at` - Auto-updates `updated_at` on row modification

#### Data Stored in current_state JSONB

The `current_state` JSONB field stores the actual session data:

```json
{
  "current_state": "ASK_CLARIFYING_QUESTIONS",
  "user_initial_request": "Create a presentation about AI",
  "clarifying_answers": {
    "audience": "executives",
    "duration": "15 minutes"
  },
  "confirmation_plan": {
    "summary_of_user_request": "...",
    "key_assumptions": ["..."],
    "proposed_slide_count": 10
  },
  "presentation_strawman": {
    "main_title": "...",
    "slides": [...]
  },
  "refinement_feedback": "Make it more technical"
}
```

### 2. Presentations Table

Stores completed presentations with AI embeddings for similarity search.

```sql
CREATE TABLE presentations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    structure JSONB NOT NULL,
    embedding vector(1536),
    presentation_type TEXT,
    industry TEXT,
    target_audience TEXT,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    metadata JSONB DEFAULT '{}'::JSONB,
    version INTEGER DEFAULT 1,
    is_template BOOLEAN DEFAULT FALSE
);
```

#### Key Features
- **Vector Embeddings**: 1536-dimensional vectors for semantic search (OpenAI text-embedding-3-small)
- **Cascade Delete**: Presentations deleted when session is deleted
- **Version Tracking**: Support for presentation iterations
- **Template System**: Can mark presentations as reusable templates

#### Indexes
- `idx_presentations_session_id` - Foreign key lookups
- `idx_presentations_type` - Filter by type
- `idx_presentations_created_at` - Time-based queries
- `presentations_embedding_idx` - IVFFlat index for vector similarity

### 3. Visual Assets Table

Manages generated images, charts, and diagrams.

```sql
CREATE TABLE visual_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    presentation_id UUID REFERENCES presentations(id) ON DELETE CASCADE,
    slide_number INTEGER NOT NULL,
    asset_type TEXT NOT NULL CHECK (asset_type IN ('image', 'chart', 'diagram', 'icon')),
    url TEXT NOT NULL,
    prompt TEXT,
    style_params JSONB DEFAULT '{}'::JSONB,
    embedding vector(512),
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    metadata JSONB DEFAULT '{}'::JSONB,
    usage_count INTEGER DEFAULT 0,
    quality_score FLOAT CHECK (quality_score >= 0 AND quality_score <= 1),
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW()),
    created_by TEXT
);
```

#### Key Features
- **Asset Types**: Enforced via CHECK constraint
- **Visual Embeddings**: 512-dimensional vectors (CLIP embeddings)
- **Quality Tracking**: Score between 0-1 for asset quality
- **Usage Analytics**: Track asset reuse
- **Tag System**: Array-based tagging for categorization

#### Indexes
- `idx_visual_assets_presentation_id` - Foreign key lookups
- `idx_visual_assets_type` - Filter by asset type
- `idx_visual_assets_tags` - GIN index for tag searches
- `visual_assets_embedding_idx` - IVFFlat index for visual similarity

### 4. Agent Outputs Table

Tracks all agent interactions for debugging and analytics.

```sql
CREATE TABLE agent_outputs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    agent_id TEXT NOT NULL,
    output_type TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('completed', 'partial', 'failed')),
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    error_message TEXT,
    processing_time_ms INTEGER,
    tokens_used JSONB,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc', NOW())
);
```

#### Key Features
- **Correlation Tracking**: Link related agent calls
- **Performance Metrics**: Processing time and token usage
- **Error Tracking**: Capture failure reasons
- **Complete Audit Trail**: Input/output pairs for debugging

#### Indexes
- `idx_agent_outputs_session_id` - Session queries
- `idx_agent_outputs_agent_id` - Agent-specific analysis
- `idx_agent_outputs_correlation_id` - Request tracking
- `idx_agent_outputs_created_at` - Time-based analysis

## Database Functions

### match_presentations()

Finds similar presentations using vector cosine similarity.

```sql
match_presentations(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10,
    filter_type text DEFAULT NULL,
    filter_industry text DEFAULT NULL
) RETURNS TABLE (
    id uuid,
    title text,
    description text,
    similarity float
)
```

**Usage**: Find presentations similar to user's request for inspiration or reuse.

### match_visual_assets()

Finds similar visual assets.

```sql
match_visual_assets(
    query_embedding vector(512),
    asset_type_filter text DEFAULT NULL,
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
) RETURNS TABLE (
    id uuid,
    url text,
    asset_type text,
    similarity float
)
```

**Usage**: Find reusable visual assets based on visual similarity.

### cleanup_expired_sessions()

Removes expired sessions for data hygiene.

```sql
cleanup_expired_sessions() RETURNS void
```

**Usage**: Called periodically to clean up old sessions.

## Row Level Security (RLS)

All tables have RLS enabled to ensure data isolation:

### Sessions Table Policies
```sql
-- Users can only see their own sessions
CREATE POLICY "Users can view own sessions" ON sessions
    FOR SELECT USING (auth.uid()::text = user_id);

-- Users can create their own sessions
CREATE POLICY "Users can create own sessions" ON sessions
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

-- Users can update their own sessions
CREATE POLICY "Users can update own sessions" ON sessions
    FOR UPDATE USING (auth.uid()::text = user_id);

-- Users can delete their own sessions
CREATE POLICY "Users can delete own sessions" ON sessions
    FOR DELETE USING (auth.uid()::text = user_id);
```

Similar policies cascade through related tables via foreign key relationships.

## Data Flow

### 1. Session Creation
```
User connects → Create session record → Generate session_id → Store initial state
```

### 2. Conversation Flow
```
User message → Update conversation_history → Update current_state → Store agent outputs
```

### 3. Presentation Generation
```
Generate strawman → Store in current_state → Create presentation record → Generate embeddings
```

### 4. Asset Creation
```
Identify asset needs → Generate assets → Store URLs → Create embeddings → Link to presentation
```

## Application Integration

### SupabaseOperations Class
Located in `src/storage/supabase.py`, provides:
- Singleton client management
- Basic CRUD operations
- Currently only implements session operations

### SessionManager Class
Located in `src/utils/session_manager.py`, provides:
- In-memory caching layer
- High-level session operations
- State transition management
- Conversation history management

### Data Access Pattern
```
Application → SessionManager (cache) → SupabaseOperations → Supabase → PostgreSQL
```

## Performance Considerations

### Indexing Strategy
1. **Primary Keys**: All tables use efficient UUID or TEXT primary keys
2. **Foreign Keys**: Indexed for fast joins
3. **Common Queries**: Composite indexes for frequent query patterns
4. **Vector Search**: IVFFlat indexes for similarity search

### JSONB Advantages
1. **Flexibility**: Schema evolution without migrations
2. **Performance**: Binary storage format with indexing
3. **Querying**: Rich query operators for nested data
4. **Compression**: Automatic compression for large objects

### Caching
- SessionManager implements in-memory caching
- Reduces database round trips
- Cache invalidation on updates

## Security Architecture

### Row Level Security
- Enforced at database level
- Cannot be bypassed by application bugs
- Automatic user data isolation

### Data Privacy
- User sessions isolated by user_id
- Cascade deletes ensure data cleanup
- No cross-user data access possible

### Connection Security
- SSL/TLS encryption in transit
- Supabase anon key for public operations
- Service key for admin operations (not used in app)

## Future Extensibility

### Phase 2 Preparations
1. **Agent Outputs Table**: Ready for multi-agent tracking
2. **Vector Embeddings**: Infrastructure for AI features
3. **JSONB Flexibility**: Easy to add new fields

### Potential Enhancements
1. **Partitioning**: Time-based partitioning for agent_outputs
2. **Archival**: Move old sessions to cold storage
3. **Analytics**: Materialized views for performance metrics
4. **Versioning**: Full presentation version history

## Migration Management

### Current Migrations
1. **Initial Schema**: Complete database setup
2. **Add User ID**: Added user_id column with proper defaults and indexes

### Migration Best Practices
- Always add NOT NULL columns with defaults
- Create indexes for new foreign keys
- Update RLS policies for new columns
- Test migrations on staging first

## Monitoring and Maintenance

### Key Metrics to Monitor
1. **Table Sizes**: Especially agent_outputs growth
2. **Query Performance**: Slow query log analysis
3. **Index Usage**: Ensure indexes are being used
4. **Connection Pool**: Monitor active connections

### Maintenance Tasks
1. **Daily**: Run cleanup_expired_sessions()
2. **Weekly**: Vacuum analyze for statistics
3. **Monthly**: Review slow query logs
4. **Quarterly**: Audit RLS policies

## Conclusion

The Phase 1 data architecture provides a robust foundation for Deckster's AI-powered presentation system. Key strengths include:

1. **Flexibility**: JSONB allows schema evolution
2. **Performance**: Proper indexing and caching
3. **Security**: RLS ensures data isolation
4. **AI-Ready**: Vector embeddings for future features
5. **Scalability**: Designed for growth

The architecture balances current needs with future extensibility, ensuring the system can evolve without major refactoring.