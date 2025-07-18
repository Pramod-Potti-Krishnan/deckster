# Security Requirements (MVP)

## Overview
Essential security requirements for the MVP phase of the presentation generation system. Focus on critical security measures that can be implemented quickly without delaying launch.

## 1. Authentication (Priority: HIGH)

### 1.1 Simple JWT Authentication
```python
# Basic JWT setup
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')  # Required
JWT_EXPIRES = timedelta(hours=24)  # Simple 24-hour expiry
```

### 1.2 WebSocket Authentication
- Validate JWT token on connection
- Disconnect on invalid/expired tokens
- One token per session

## 2. Essential Data Protection

### 2.1 HTTPS/WSS Only
- Use HTTPS for all API endpoints
- Use WSS for WebSocket connections
- Let hosting provider handle SSL certificates (e.g., Vercel, Railway)

### 2.2 Environment Variables
```bash
# .env (never commit)
JWT_SECRET_KEY=<generate-random-key>
SUPABASE_URL=<your-url>
SUPABASE_ANON_KEY=<your-anon-key>
OPENAI_API_KEY=<your-key>
```

### 2.3 Basic Supabase RLS
```sql
-- Enable RLS on main tables
ALTER TABLE presentations ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

-- Users can only access their own data
CREATE POLICY "Own data only" ON presentations
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Own sessions only" ON sessions
    FOR ALL USING (auth.uid() = user_id);
```

## 3. Input Validation (Priority: HIGH)

### 3.1 Basic Sanitization
```python
from pydantic import BaseModel, Field

class UserTextInput(BaseModel):
    text: str = Field(..., max_length=5000)  # Limit size
    session_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')
    
    @validator('text')
    def clean_text(cls, v):
        # Remove null bytes and basic XSS
        return v.replace('\0', '').strip()
```

### 3.2 File Upload Limits
```python
ALLOWED_EXTENSIONS = {'.pdf', '.pptx', '.docx', '.xlsx', '.png', '.jpg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file(file):
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("File type not allowed")
    
    # Check size
    if file.size > MAX_FILE_SIZE:
        raise ValueError("File too large")
```

## 4. API Security (Priority: HIGH)

### 4.1 Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/presentation")
@limiter.limit("10/minute")  # 10 requests per minute
async def create_presentation(request: Request):
    # Implementation
```

### 4.2 Basic Error Handling
```python
# Don't expose internal errors
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )
```

## 5. LLM Security (Priority: MEDIUM)

### 5.1 Simple Prompt Protection
```python
def validate_user_input(text: str) -> bool:
    """Basic check for prompt injection"""
    suspicious_phrases = [
        "ignore previous",
        "system prompt",
        "disregard instructions"
    ]
    
    text_lower = text.lower()
    for phrase in suspicious_phrases:
        if phrase in text_lower:
            return False
    return True
```

### 5.2 Token Limits
```python
# Prevent excessive API costs
MAX_TOKENS_PER_REQUEST = 2000
MAX_REQUESTS_PER_SESSION = 50
```

## 6. Logging (Priority: MEDIUM)

### 6.1 Basic Security Logging
```python
import logging

security_logger = logging.getLogger('security')

def log_auth_attempt(user_id: str, success: bool):
    security_logger.info(f"Auth attempt - User: {user_id}, Success: {success}")

def log_file_upload(user_id: str, filename: str):
    security_logger.info(f"File upload - User: {user_id}, File: {filename}")
```

## 7. Quick Implementation Checklist

### Week 1 - Critical Items
- [ ] Set up environment variables
- [ ] Implement JWT authentication
- [ ] Enable HTTPS/WSS
- [ ] Add basic input validation
- [ ] Set up Supabase RLS policies

### Week 2 - Important Items
- [ ] Add rate limiting
- [ ] Implement file upload validation
- [ ] Add error handling
- [ ] Set up basic logging
- [ ] Add prompt injection checks

### Post-MVP - Nice to Have
- [ ] Add refresh tokens
- [ ] Implement comprehensive audit logging
- [ ] Add file virus scanning
- [ ] Set up automated security scanning
- [ ] Add encryption at rest

## 8. Security Quick Wins

### Use Existing Services
1. **Supabase Auth** - Handles user management securely
2. **Vercel/Railway** - Automatic HTTPS
3. **Cloudflare** - Free DDoS protection
4. **GitHub Security** - Dependency scanning

### Simple Security Headers
```python
# Add to your API responses
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response
```

## 9. What NOT to Do (Save Time)

### Skip for MVP
- Complex encryption schemes
- Custom authentication systems
- Advanced threat detection
- Compliance certifications
- Penetration testing

### Use Instead
- HTTPS for encryption
- Supabase Auth
- Basic rate limiting
- Standard security headers
- Manual security review

## 10. Emergency Contacts

```yaml
# Keep this handy
contacts:
  - Supabase Support: support@supabase.io
  - Hosting Provider: [Your provider's support]
  - Team Lead: [Contact info]
```

## Summary

This MVP security approach provides:
- **User data protection** through authentication and RLS
- **System protection** through input validation and rate limiting
- **Cost protection** through API limits
- **Quick implementation** using existing tools

Total implementation time: ~1-2 weeks for a developer familiar with the stack.

Remember: Perfect security is not the goal for MVP. The goal is reasonable protection that doesn't delay launch. Enhance security iteratively after launch based on user growth and data sensitivity.