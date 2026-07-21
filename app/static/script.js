const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const chatForm = document.getElementById('chat-form');
const messagesContainer = document.getElementById('messages');

let isStreaming = false;
let conversationHistory = [];

// Auto-resize textarea
chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + 'px';
    updateSendButton();
});

// Keyboard shortcuts
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!sendBtn.disabled) sendMessage();
    }
});

// Send button
chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!sendBtn.disabled) sendMessage();
});

function updateSendButton() {
    sendBtn.disabled = chatInput.value.trim() === '' || isStreaming;
}

function scrollToBottom() {
    const chatContainer = document.getElementById('chat-container');
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addUserMessage(text) {
    const div = document.createElement('div');
    div.className = 'message user-message';
    div.innerHTML = `
        <div class="avatar user-avatar">U</div>
        <div class="message-content"><p>${escapeHtml(text)}</p></div>
    `;
    messagesContainer.appendChild(div);
    scrollToBottom();
}

function addAssistantMessage() {
    const div = document.createElement('div');
    div.className = 'message assistant-message';
    div.innerHTML = `
        <div class="avatar bot-avatar">🧪</div>
        <div class="message-content"></div>
    `;
    messagesContainer.appendChild(div);
    scrollToBottom();
    return div.querySelector('.message-content');
}

function addTypingIndicator() {
    const div = document.createElement('div');
    div.className = 'message assistant-message';
    div.innerHTML = `
        <div class="avatar bot-avatar">🧪</div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    messagesContainer.appendChild(div);
    scrollToBottom();
    return div.querySelector('.typing-indicator');
}

function formatMarkdown(text) {
    let html = escapeHtml(text);
    // Code blocks
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Bold
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    // Italic
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    return html;
}

function formatError(message) {
    return `<p style="color: var(--error);">⚠️ ${escapeHtml(message)}</p>`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || isStreaming) return;

    // Add user message
    addUserMessage(message);
    conversationHistory.push({ role: 'user', content: message });

    // Clear input
    chatInput.value = '';
    chatInput.style.height = 'auto';
    updateSendButton();

    // Add typing indicator
    const typingIndicator = addTypingIndicator();
    isStreaming = true;
    sendBtn.classList.add('loading');
    sendBtn.disabled = true;

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: 'sra_chem',
                user: 'local',
                messages: conversationHistory,
                stream: true,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Remove typing indicator
        typingIndicator.closest('.message').remove();

        // Create content div for streaming
        const contentDiv = addAssistantMessage();
        let buffer = '';

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') continue;

                    try {
                        const parsed = JSON.parse(data);
                        if (parsed.error) {
                            contentDiv.innerHTML = formatError(parsed.error);
                            conversationHistory.push({ role: 'assistant', content: `Error: ${parsed.error}` });
                            break;
                        }
                        const content = parsed.choices?.[0]?.delta?.content || '';
                        if (content) {
                            contentDiv.innerHTML = formatMarkdown(content);
                            scrollToBottom();
                        }
                    } catch {
                        // Skip malformed chunks
                    }
                }
            }
        }

        // Save final response
        const finalContent = contentDiv.textContent || contentDiv.innerText;
        if (finalContent.trim()) {
            conversationHistory.push({ role: 'assistant', content: finalContent });
        }

    } catch (error) {
        typingIndicator.closest('.message')?.remove();
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message assistant-message';
        errorDiv.innerHTML = `
            <div class="avatar bot-avatar">🧪</div>
            <div class="message-content">${formatError(error.message)}</div>
        `;
        messagesContainer.appendChild(errorDiv);
        console.error('Streaming error:', error);
    } finally {
        isStreaming = false;
        sendBtn.classList.remove('loading');
        updateSendButton();
        scrollToBottom();
        chatInput.focus();
    }
}
