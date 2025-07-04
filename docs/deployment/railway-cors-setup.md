# Railway CORS Configuration Guide

This guide explains how to configure CORS (Cross-Origin Resource Sharing) for your Railway deployment to allow your frontend to connect to the backend API.

## Quick Setup

1. **Go to your Railway project dashboard**
   - Navigate to your project at https://railway.app
   - Click on your backend service

2. **Open the Variables tab**
   - Click on the "Variables" tab in your service

3. **Add/Update the CORS_ORIGINS variable**
   - Click "New Variable" or edit the existing CORS_ORIGINS
   - Use this exact format (copy and paste):
   ```
   ["https://www.deckster.xyz","https://deckster.xyz","https://*.vercel.app","http://localhost:3000","http://localhost:5173"]
   ```

## Important Notes

### Format Requirements
- **MUST use double quotes** (`"`) inside the array, not single quotes (`'`)
- No spaces after commas (Railway will parse this as a JSON string)
- The entire value should be on one line

### Example Railway Variable
```
CORS_ORIGINS=["https://www.deckster.xyz","https://deckster.xyz","https://*.vercel.app","http://localhost:3000","http://localhost:5173"]
```

### What Each Origin Allows
- `https://www.deckster.xyz` - Your production frontend with www
- `https://deckster.xyz` - Your production frontend without www
- `https://*.vercel.app` - All Vercel preview deployments
- `http://localhost:3000` - Local Next.js development
- `http://localhost:5173` - Local Vite development

## Deployment Steps

1. **Update the environment variable** in Railway as shown above
2. **Redeploy your service** - Railway should automatically redeploy when you update variables
3. **Verify the deployment** - Check the deploy logs for any errors

## Testing the Configuration

After deployment, test CORS is working:

1. Open your frontend at https://www.deckster.xyz
2. Open browser DevTools (F12)
3. Try to connect to the WebSocket or make an API call
4. You should no longer see CORS errors

## Troubleshooting

### Still getting CORS errors?

1. **Check the format** - Ensure you used double quotes and no spaces
2. **Verify in Railway logs** - Look for the parsed CORS origins in your deployment logs
3. **Clear browser cache** - Sometimes old CORS headers are cached
4. **Check the exact error** - The browser console will show which origin is being blocked

### Common Mistakes

❌ Wrong (single quotes):
```
['https://www.deckster.xyz','https://deckster.xyz']
```

❌ Wrong (spaces after commas):
```
["https://www.deckster.xyz", "https://deckster.xyz"]
```

✅ Correct:
```
["https://www.deckster.xyz","https://deckster.xyz"]
```

### Need to Add More Origins?

Simply add them to the array following the same pattern:
```
["https://www.deckster.xyz","https://deckster.xyz","https://staging.deckster.xyz","https://*.vercel.app","http://localhost:3000","http://localhost:5173"]
```

## Security Note

Only add origins that you trust. Each origin in this list will be able to:
- Connect to your WebSocket
- Make API calls to your backend
- Access authentication endpoints

Never use `"*"` (wildcard for all origins) in production as it's a security risk.