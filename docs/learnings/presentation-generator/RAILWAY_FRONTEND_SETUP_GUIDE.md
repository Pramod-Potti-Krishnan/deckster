# Railway Frontend Setup Guide: Getting NEXT_PUBLIC_API_URL

This guide will walk you through the process of finding your Railway deployment URL and configuring it for your frontend application.

## Table of Contents
1. [Finding Your Railway Deployment URL](#1-finding-your-railway-deployment-url)
2. [Constructing the WebSocket URL](#2-constructing-the-websocket-url)
3. [Setting Up Frontend Environment Variables](#3-setting-up-frontend-environment-variables)
4. [Testing the Connection](#4-testing-the-connection)
5. [Troubleshooting Common Issues](#5-troubleshooting-common-issues)

---

## 1. Finding Your Railway Deployment URL

### Step 1: Access Railway Dashboard
1. Go to [railway.app](https://railway.app) and log in to your account
2. Navigate to your project dashboard

### Step 2: Locate Your Service
1. In your project, find the service running your Vibe Decker API
2. Click on the service card to open its details

   **Visual Guide:**
   ```
   [Railway Dashboard]
   ├── Project: vibe-decker-production
   │   ├── 🚀 vibe-decker-api (Click here)
   │   └── 🗄️ postgres-db
   ```

### Step 3: Find the Public Domain
1. In the service details, look for the "Settings" tab
2. Scroll to the "Domains" section
3. You'll see either:
   - A Railway-generated domain: `your-app-name.up.railway.app`
   - A custom domain if you've configured one

   **Example Railway Domain:**
   ```
   vibe-decker-api-production.up.railway.app
   ```

### Step 4: Copy the Full URL
1. Click the copy button next to the domain
2. The full URL will be: `https://your-app-name.up.railway.app`

   **Important:** Railway automatically provides HTTPS, so always use `https://` prefix

---

## 2. Constructing the WebSocket URL

Your frontend needs both HTTP and WebSocket URLs. Here's how to construct them:

### Base API URL (for HTTP requests)
```
https://your-app-name.up.railway.app
```

### WebSocket URL (for real-time communication)
```
wss://your-app-name.up.railway.app/ws
```

### Example URLs
If your Railway domain is `vibe-decker-api-production.up.railway.app`:

- **HTTP API URL:** `https://vibe-decker-api-production.up.railway.app`
- **WebSocket URL:** `wss://vibe-decker-api-production.up.railway.app/ws`

**Note:** 
- Use `wss://` (secure WebSocket) instead of `ws://` for Railway deployments
- The `/ws` path is the WebSocket endpoint defined in your API

---

## 3. Setting Up Frontend Environment Variables

### For Next.js Applications

#### Step 1: Create Environment File
Create a `.env.local` file in your frontend root directory:

```bash
# .env.local
NEXT_PUBLIC_API_URL=https://your-app-name.up.railway.app
```

#### Step 2: Update Your API Configuration
Create or update your API configuration file:

```javascript
// config/api.js or utils/api.js
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Construct WebSocket URL from API URL
const WS_URL = API_URL.replace(/^https/, 'wss').replace(/^http/, 'ws') + '/ws';

export const config = {
  API_URL,
  WS_URL,
  endpoints: {
    createPresentation: `${API_URL}/api/presentations`,
    getPresentation: (id) => `${API_URL}/api/presentations/${id}`,
    updateSlide: (presentationId, slideId) => 
      `${API_URL}/api/presentations/${presentationId}/slides/${slideId}`,
  }
};
```

#### Step 3: Use in Your Components
```javascript
// components/PresentationGenerator.js
import { config } from '../config/api';

const connectWebSocket = () => {
  const ws = new WebSocket(config.WS_URL);
  
  ws.onopen = () => {
    console.log('Connected to Vibe Decker API');
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Handle incoming messages
  };
  
  return ws;
};
```

### For Other Frontend Frameworks

#### React (Create React App)
```bash
# .env
REACT_APP_API_URL=https://your-app-name.up.railway.app
```

#### Vue.js
```bash
# .env
VUE_APP_API_URL=https://your-app-name.up.railway.app
```

#### Vanilla JavaScript
```javascript
// config.js
const API_URL = 'https://your-app-name.up.railway.app';
const WS_URL = 'wss://your-app-name.up.railway.app/ws';
```

---

## 4. Testing the Connection

### Step 1: Test HTTP Connection
Open your browser console and run:

```javascript
// Test basic API connection
fetch('https://your-app-name.up.railway.app/health')
  .then(res => res.json())
  .then(data => console.log('API Health:', data))
  .catch(err => console.error('API Error:', err));
```

### Step 2: Test WebSocket Connection
```javascript
// Test WebSocket connection
const ws = new WebSocket('wss://your-app-name.up.railway.app/ws');

ws.onopen = () => {
  console.log('WebSocket connected!');
  ws.send(JSON.stringify({ type: 'ping' }));
};

ws.onmessage = (event) => {
  console.log('Received:', event.data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

### Step 3: Full Integration Test
Create a test file to verify the complete flow:

```javascript
// test-connection.js
const API_URL = 'https://your-app-name.up.railway.app';
const WS_URL = 'wss://your-app-name.up.railway.app/ws';

async function testFullIntegration() {
  console.log('Testing Vibe Decker API Integration...\n');
  
  // 1. Test HTTP endpoint
  console.log('1. Testing HTTP connection...');
  try {
    const response = await fetch(`${API_URL}/health`);
    const data = await response.json();
    console.log('✅ HTTP connection successful:', data);
  } catch (error) {
    console.error('❌ HTTP connection failed:', error);
    return;
  }
  
  // 2. Test WebSocket connection
  console.log('\n2. Testing WebSocket connection...');
  const ws = new WebSocket(WS_URL);
  
  ws.onopen = () => {
    console.log('✅ WebSocket connected');
    
    // 3. Test creating a presentation
    console.log('\n3. Testing presentation creation...');
    ws.send(JSON.stringify({
      type: 'create_presentation',
      data: {
        topic: 'Test Presentation',
        num_slides: 3
      }
    }));
  };
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('📨 Received message:', message.type);
    
    if (message.type === 'presentation_created') {
      console.log('✅ Presentation created successfully!');
      console.log('Presentation ID:', message.data.presentation_id);
      ws.close();
    }
  };
  
  ws.onerror = (error) => {
    console.error('❌ WebSocket error:', error);
  };
}

// Run the test
testFullIntegration();
```

---

## 5. Troubleshooting Common Issues

### Issue 1: CORS Errors
**Symptom:** Browser console shows CORS policy errors

**Solution:** Ensure your API has proper CORS configuration:
```python
# In your FastAPI app
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue 2: WebSocket Connection Fails
**Symptom:** WebSocket connection immediately closes or fails

**Possible Causes:**
1. **Wrong protocol:** Ensure you're using `wss://` not `ws://`
2. **Path issue:** Verify the WebSocket path is `/ws`
3. **Railway configuration:** Check Railway logs for any deployment issues

**Debug Steps:**
```javascript
const ws = new WebSocket(WS_URL);

ws.onopen = () => console.log('Connected');
ws.onclose = (e) => console.log('Closed:', e.code, e.reason);
ws.onerror = (e) => console.error('Error:', e);
```

### Issue 3: Environment Variables Not Loading
**Symptom:** `process.env.NEXT_PUBLIC_API_URL` is undefined

**Solutions:**
1. **Restart development server** after adding env variables
2. **Check variable naming:** Must start with `NEXT_PUBLIC_` for Next.js
3. **Verify file location:** `.env.local` should be in project root

### Issue 4: Mixed Content Error
**Symptom:** Browser blocks requests from HTTPS frontend to HTTP backend

**Solution:** Always use HTTPS URLs from Railway:
```javascript
// ❌ Wrong
const API_URL = 'http://your-app.up.railway.app';

// ✅ Correct
const API_URL = 'https://your-app.up.railway.app';
```

### Issue 5: Railway Service Not Accessible
**Symptom:** Cannot reach the Railway URL at all

**Check:**
1. **Service is running:** Check Railway dashboard for service status
2. **Domain is generated:** Ensure you've generated a domain in Railway settings
3. **Deployment succeeded:** Check deployment logs in Railway

**Railway CLI Debug:**
```bash
# Check service status
railway status

# View recent logs
railway logs

# Check environment variables
railway variables
```

---

## Quick Reference Card

```javascript
// Save this configuration for your frontend
const VIBE_DECKER_CONFIG = {
  // Replace with your actual Railway domain
  API_URL: 'https://your-app-name.up.railway.app',
  WS_URL: 'wss://your-app-name.up.railway.app/ws',
  
  // Common endpoints
  endpoints: {
    health: '/health',
    presentations: '/api/presentations',
    websocket: '/ws'
  },
  
  // WebSocket message types
  messageTypes: {
    CREATE_PRESENTATION: 'create_presentation',
    UPDATE_SLIDE: 'update_slide',
    PRESENTATION_READY: 'presentation_ready',
    ERROR: 'error'
  }
};

// Export for use in your app
export default VIBE_DECKER_CONFIG;
```

---

## Next Steps

1. **Set up monitoring:** Use Railway's metrics to monitor your API
2. **Configure custom domain:** Add your own domain in Railway settings
3. **Set up CI/CD:** Connect GitHub for automatic deployments
4. **Add error tracking:** Integrate services like Sentry for production monitoring

For more detailed API documentation, refer to the [API & WebSocket Documentation](../vibe-decker-api-ver-3/docs/API_N_WEBSOCKET.md).