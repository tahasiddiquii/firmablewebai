// Configuration
// Use relative paths since frontend and API are on same domain
const API_BASE_URL = '/api';
const API_TOKEN = 'y7H9r!Pz3qT8mLw#Xv2Bf@Kc5jS1dG6n'; // Your API secret key

// DOM Elements
const analysisForm = document.getElementById('analysisForm');
const queryForm = document.getElementById('queryForm');
const analysisLoading = document.getElementById('analysisLoading');
const queryLoading = document.getElementById('queryLoading');
const analysisResults = document.getElementById('analysisResults');
const chatContainer = document.getElementById('chatContainer');

// State
let conversationHistory = [];

// Event Listeners
analysisForm.addEventListener('submit', handleAnalysis);
queryForm.addEventListener('submit', handleQuery);

// Analysis Handler
async function handleAnalysis(e) {
    e.preventDefault();
    
    const url = document.getElementById('websiteUrl').value;
    const questionsText = document.getElementById('questions').value;
    const questions = questionsText ? questionsText.split('\n').filter(q => q.trim()) : [];
    
    // Show loading
    analysisLoading.style.display = 'block';
    analysisResults.innerHTML = '';
    
    try {
        const response = await fetch(`${API_BASE_URL}/insights`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_TOKEN}`
            },
            body: JSON.stringify({
                url: url,
                questions: questions
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
        }
        
        const insights = await response.json();
        displayInsights(insights);
        
        // Update query URL to match analyzed URL
        document.getElementById('queryUrl').value = url;
        
    } catch (error) {
        showError('Analysis failed: ' + error.message);
    } finally {
        analysisLoading.style.display = 'none';
    }
}

// Query Handler
async function handleQuery(e) {
    e.preventDefault();
    
    const url = document.getElementById('queryUrl').value;
    const query = document.getElementById('userQuery').value;
    
    // Add user message to chat
    addMessage('user', query);
    
    // Show loading
    queryLoading.style.display = 'block';
    
    try {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_TOKEN}`
            },
            body: JSON.stringify({
                url: url,
                query: query,
                conversation_history: conversationHistory
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Query failed');
        }
        
        const result = await response.json();
        
        // Add assistant response to chat
        addMessage('assistant', result.answer);
        
        // Update conversation history
        conversationHistory = result.conversation_history;
        
        // Clear input
        document.getElementById('userQuery').value = '';
        
    } catch (error) {
        addMessage('assistant', 'Sorry, I encountered an error: ' + error.message);
    } finally {
        queryLoading.style.display = 'none';
    }
}

// Display Insights
function displayInsights(insights) {
    const insightsHtml = `
        <div class="success">
            <strong>✅ Analysis Complete!</strong> Here are the business insights:
        </div>
        <div class="insights-grid">
            <div class="insight-card">
                <h3>🏢 Industry</h3>
                <p>${insights.industry || 'Not specified'}</p>
            </div>
            <div class="insight-card">
                <h3>👥 Company Size</h3>
                <p>${insights.company_size || 'Not specified'}</p>
            </div>
            <div class="insight-card">
                <h3>📍 Location</h3>
                <p>${insights.location || 'Not specified'}</p>
            </div>
            <div class="insight-card">
                <h3>💡 Unique Selling Proposition</h3>
                <p>${insights.USP || 'Not specified'}</p>
            </div>
            <div class="insight-card">
                <h3>🛍️ Products/Services</h3>
                <p>${insights.products ? insights.products.join(', ') : 'Not specified'}</p>
            </div>
            <div class="insight-card">
                <h3>🎯 Target Audience</h3>
                <p>${insights.target_audience || 'Not specified'}</p>
            </div>
            ${insights.contact_info && Object.keys(insights.contact_info).length > 0 ? `
            <div class="insight-card">
                <h3>📞 Contact Information</h3>
                <p>${formatContactInfo(insights.contact_info)}</p>
            </div>
            ` : ''}
        </div>
    `;
    
    analysisResults.innerHTML = insightsHtml;
}

// Format Contact Info
function formatContactInfo(contactInfo) {
    const parts = [];
    
    if (contactInfo.emails) {
        parts.push(`📧 ${contactInfo.emails.join(', ')}`);
    }
    
    if (contactInfo.phones) {
        parts.push(`📞 ${contactInfo.phones.join(', ')}`);
    }
    
    if (contactInfo.addresses) {
        parts.push(`📍 ${contactInfo.addresses.join(', ')}`);
    }
    
    if (contactInfo.social_links) {
        parts.push(`🔗 ${contactInfo.social_links.join(', ')}`);
    }
    
    return parts.join('<br>') || 'Not available';
}

// Add Message to Chat
function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const roleLabel = role === 'user' ? 'You' : 'AI Assistant';
    messageDiv.innerHTML = `<strong>${roleLabel}:</strong> ${content}`;
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Show Error
function showError(message) {
    analysisResults.innerHTML = `
        <div class="error">
            <strong>❌ Error:</strong> ${message}
        </div>
    `;
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('FirmableWebAI Frontend Loaded');
    
    // Check if API token is configured
    if (API_TOKEN === 'your-api-token-here') {
        showError('Please configure your API token in script.js');
    }
});
