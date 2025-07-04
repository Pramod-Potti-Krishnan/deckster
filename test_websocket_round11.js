// Quick WebSocket test for Round 11.1 fixes
const WebSocket = require('ws');

async function testWebSocket() {
    console.log('🧪 Testing Round 11.1 WebSocket fixes...');
    
    // Get authentication token
    console.log('1. Getting auth token...');
    const response = await fetch('https://deckster-production.up.railway.app/api/auth/demo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'round11_websocket_test' })
    });
    
    if (!response.ok) {
        console.error('❌ Failed to get token:', response.status);
        return;
    }
    
    const { access_token } = await response.json();
    console.log('✅ Token obtained');
    
    // Test WebSocket connection
    console.log('2. Testing WebSocket connection...');
    const ws = new WebSocket(`wss://deckster-production.up.railway.app/ws?token=${access_token}`);
    
    ws.on('open', () => {
        console.log('✅ WebSocket connected - session creation should work now!');
        
        // Send test message
        const testMessage = {
            message_id: 'test_' + Date.now(),
            timestamp: new Date().toISOString(),
            session_id: null,
            type: 'user_input',
            data: { 
                text: 'Test message for Round 11.1', 
                response_to: null, 
                attachments: [], 
                ui_references: [], 
                frontend_actions: [] 
            }
        };
        
        console.log('3. Sending test message...');
        ws.send(JSON.stringify(testMessage));
    });
    
    ws.on('message', (data) => {
        const message = JSON.parse(data.toString());
        console.log('📨 Received:', message.type);
        
        if (message.type === 'connection') {
            console.log('🎉 Session created successfully! Status:', message.status);
            console.log('🎉 Session ID:', message.session_id);
        } else if (message.type === 'director') {
            console.log('🤖 Director response:', message.chat_data?.content);
        }
        
        // Close after receiving messages
        setTimeout(() => {
            ws.close();
            console.log('✅ Test completed successfully!');
        }, 2000);
    });
    
    ws.on('error', (error) => {
        console.error('❌ WebSocket error:', error.message);
    });
    
    ws.on('close', (code, reason) => {
        console.log('🔌 WebSocket closed:', code, reason.toString());
    });
}

// Run if we have fetch (Node 18+) or use a simple message
if (typeof fetch !== 'undefined') {
    testWebSocket().catch(console.error);
} else {
    console.log('This test requires Node.js 18+ with fetch support');
    console.log('Run in browser console instead:');
    console.log(`
// Paste this in browser console on https://deckster.xyz
(async () => {
  const tokenRes = await fetch('https://deckster-production.up.railway.app/api/auth/demo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: 'browser_test' })
  });
  const { access_token } = await tokenRes.json();
  console.log('✅ Token obtained');
  
  const ws = new WebSocket(\`wss://deckster-production.up.railway.app/ws?token=\${access_token}\`);
  ws.onopen = () => console.log('✅ WebSocket connected');
  ws.onmessage = (e) => console.log('📨 Received:', JSON.parse(e.data));
  ws.onerror = (e) => console.error('❌ Error:', e);
})();
    `);
}