# Railway Deployment Round 9: JSON Parsing Error Fix

## Date: July 4, 2025

## Issue Encountered
After fixing CORS in Round 8 by changing from JSON array format to comma-separated format, the application crashed with JSON parsing errors.

### Error Messages
```
pydantic_settings.exceptions.SettingsError: error parsing value for field "cors_origins" from source "EnvSettingsSource"
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

## Root Cause Analysis

### 1. Pydantic Auto-parsing
- Fields typed as `List[str]` trigger automatic JSON parsing by Pydantic
- This happens BEFORE custom validators run
- When Railway provides comma-separated strings, JSON parsing fails

### 2. Environment Variable Format Mismatch
Railway was providing:
```json
{
  "CORS_ORIGINS": "https://www.deckster.xyz,https://deckster.xyz,https://*.vercel.app,http://localhost:3000,http://localhost:5173"
}
```

But Pydantic expected JSON arrays for `List[str]` fields:
```json
{
  "CORS_ORIGINS": "[\"https://www.deckster.xyz\",\"https://deckster.xyz\"]"
}
```

### 3. Validator Execution Order
- Pydantic attempts JSON parsing during field assignment
- Custom validators with `mode="before"` run too late
- The error occurs before our parsing logic can handle it

## Solution Implemented

### 1. Changed Field Types
Updated field declarations to accept both string and list inputs:

```python
# Before
cors_origins: List[str] = Field(
    default=["http://localhost:3000", "http://localhost:5173"],
    env="CORS_ORIGINS"
)

# After
cors_origins: Union[str, List[str]] = Field(
    default=["http://localhost:3000", "http://localhost:5173"],
    env="CORS_ORIGINS"
)
```

Applied to:
- `cors_origins`
- `allowed_file_extensions`
- `fallback_llm_models`

### 2. Enhanced Validators
Kept existing before validators to handle conversion:
```python
@field_validator("cors_origins", mode="before")
def parse_cors_origins(cls, v):
    """Parse CORS origins from string or list."""
    if isinstance(v, str):
        if not v:
            return []
        # Try JSON first for backward compatibility
        if v.startswith('['):
            try:
                import json
                return json.loads(v)
            except:
                pass
        # Fall back to comma-separated
        return [origin.strip() for origin in v.split(",") if origin.strip()]
    return v
```

### 3. Added After Validator
Ensures fields are always lists after processing:
```python
@field_validator("cors_origins", "allowed_file_extensions", "fallback_llm_models", mode="after")
def ensure_list_fields(cls, v):
    """Ensure these fields are always lists after processing."""
    if isinstance(v, str):
        return [v]
    return v if isinstance(v, list) else []
```

## Lessons Learned

### 1. Type Annotations Matter
- Pydantic uses type hints to determine parsing behavior
- `List[str]` triggers automatic JSON parsing
- `Union[str, List[str]]` allows flexible input

### 2. Validator Timing
- `mode="before"` validators run after type coercion
- Type errors occur during field assignment
- Field type must accept the raw input format

### 3. Environment Variable Formats
- Railway provides strings, not JSON
- Comma-separated is simpler than JSON arrays
- Support both formats for flexibility

### 4. Debugging Deployment Errors
- Stack traces show the exact parsing path
- Check field types before validators
- Test with actual environment variable formats

## Best Practices

### 1. Flexible Field Types
Use Union types for fields that accept environment variables:
```python
field: Union[str, List[str]] = Field(...)
```

### 2. Robust Parsing
Support multiple formats in validators:
- JSON arrays: `["value1","value2"]`
- Comma-separated: `value1,value2`
- Empty strings: Return defaults

### 3. Clear Error Messages
Log the actual values being parsed:
```python
logger.info(f"Parsing CORS origins: {value}")
```

### 4. Test Environment Variables
Create a test script to verify parsing:
```python
os.environ["CORS_ORIGINS"] = "value1,value2"
settings = Settings()
assert settings.cors_origins == ["value1", "value2"]
```

## Configuration Examples

### Railway Environment Variables
Simple comma-separated format:
```
CORS_ORIGINS=https://www.deckster.xyz,https://deckster.xyz,https://*.vercel.app
ALLOWED_FILE_EXTENSIONS=.pdf,.docx,.xlsx,.png,.jpg
FALLBACK_LLM_MODELS=openai:gpt-4,anthropic:claude-3
```

### Local .env File
Can use either format:
```bash
# Comma-separated
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Or JSON array
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

## Files Modified
- `/src/config/settings.py` - Changed field types and validators

## Next Steps
1. Consider creating a custom Pydantic field type for comma-separated lists
2. Add unit tests for environment variable parsing
3. Document supported formats in README
4. Consider using a dedicated config management tool for complex deployments