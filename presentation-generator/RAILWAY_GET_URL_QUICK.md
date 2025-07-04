# Quick Guide: Get Your Railway API URL

## 1. Find Your Railway URL

Go to Railway Dashboard → Your Project → Click on Service → Settings Tab → Domains Section

Your URL will look like:
```
https://your-app-name.up.railway.app
```

## 2. Convert to WebSocket URL

Change `https://` to `wss://`:
```
wss://your-app-name.up.railway.app
```

## 3. Set in Frontend

Create `.env.local` in your Next.js frontend:
```env
NEXT_PUBLIC_API_URL=wss://your-app-name.up.railway.app
```

## 4. Test Connection

In browser console:
```javascript
const ws = new WebSocket('wss://your-app-name.up.railway.app/ws');
ws.onopen = () => console.log('Connected!');
ws.onerror = (e) => console.error('Error:', e);
```

## Common Issues

- **No domain showing?** → Click "Generate Domain" in Railway settings
- **Connection refused?** → Check if service is running (green status)
- **CORS errors?** → Backend should already handle this via settings

That's it! Your frontend can now connect to your Railway backend.