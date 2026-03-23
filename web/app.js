/**
 * EgoZone - Web Application JavaScript
 */

// Security mode: debug mode disabled, all features require proper authentication
const DEBUG_MODE = false; // Must remain false in production, authentication bypass prohibited

// API base URL (auto-detect environment)
const API_BASE = window.location.origin + '/api';

// Global state
const state = {
    currentPage: 'chat',
    currentQuestion: null,
    chatId: 'default',
    isLoading: false
};

// DOM elements
const elements = {
    // Navigation
    navItems: document.querySelectorAll('.nav-item'),
    pages: document.querySelectorAll('.page'),

    // Chat
    chatMessages: document.getElementById('chat-messages'),
    chatInput: document.getElementById('chat-input'),
    sendBtn: document.getElementById('send-btn'),
    clearChat: document.getElementById('clear-chat'),

    // Q&A
    questionCategory: document.getElementById('question-category'),
    questionText: document.getElementById('question-text'),
    answerInput: document.getElementById('answer-input'),
    skipBtn: document.getElementById('skip-btn'),
    submitAnswerBtn: document.getElementById('submit-answer-btn'),
    progressPercent: document.getElementById('progress-percent'),
    progressFill: document.getElementById('progress-fill'),
    answeredCount: document.getElementById('answered-count'),
    totalCount: document.getElementById('total-count'),
    categoriesContainer: document.getElementById('categories-container'),

    // Knowledge Base
    knowledgeTitle: document.getElementById('knowledge-title'),
    knowledgeContent: document.getElementById('knowledge-content'),
    addKnowledgeBtn: document.getElementById('add-knowledge-btn'),
    knowledgeCount: document.getElementById('knowledge-count'),
    knowledgeListContainer: document.getElementById('knowledge-list-container'),

    // Settings
    settingName: document.getElementById('setting-name'),
    settingEducation: document.getElementById('setting-education'),
    settingProfession: document.getElementById('setting-profession'),
    settingTone: document.getElementById('setting-tone'),
    settingEmoji: document.getElementById('setting-emoji'),
    saveSettingsBtn: document.getElementById('save-settings-btn'),

    // Toast
    toast: document.getElementById('toast')
};

// ========== Utility Functions ==========

function showToast(message, type = 'success') {
    elements.toast.textContent = message;
    elements.toast.className = `toast show ${type}`;
    setTimeout(() => {
        if (elements.toast) elements.toast.classList.remove('show');
    }, 3000);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

async function apiRequest(endpoint, options = {}) {
    try {
        // Add access token to request headers
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        // Use Authorization header uniformly, following standards
        if (state.accessToken) {
            headers['Authorization'] = `Bearer ${state.accessToken}`;
        }

        if (state.adminToken) {
            headers['Authorization'] = `Bearer ${state.adminToken}`;
        }

        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: headers,
            ...options
        });

        if (!response.ok) {
            // Handle authentication failure
            if (response.status === 401) {
                // Clear invalid tokens
                if (state.accessToken) {
                    localStorage.removeItem('accessToken');
                    state.accessToken = null;
                    state.hasAccess = false;
                }
                if (state.adminToken) {
                    localStorage.removeItem('adminToken');
                    state.adminToken = null;
                    state.isAdmin = false;
                }

                // Show access verification modal
                if (endpoint.includes('/chat/') || endpoint.includes('/knowledge/')) {
                    showAccessModal();
                }
            }
            throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// ========== Navigation ==========

function initNavigation() {
    elements.navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            switchPage(page);
        });
    });
}

function switchPage(pageName) {
    // Update navigation
    elements.navItems.forEach(item => {
        item.classList.toggle('active', item.dataset.page === pageName);
    });

    // Update pages
    elements.pages.forEach(page => {
        page.classList.toggle('active', page.id === `${pageName}-page`);
    });

    state.currentPage = pageName;

    // Load page data
    switch (pageName) {
        case 'interview':
            loadInterviewData();
            break;
        case 'knowledge':
            loadKnowledgeData();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// ========== Chat Functions ==========

function initChat() {
    // Send button
    elements.sendBtn.addEventListener('click', sendMessage);

    // Input box
    elements.chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-adjust height
    elements.chatInput.addEventListener('input', () => {
        elements.chatInput.style.height = 'auto';
        elements.chatInput.style.height = Math.min(elements.chatInput.scrollHeight, 200) + 'px';
    });

    // Clear chat
    elements.clearChat.addEventListener('click', clearChat);
}

async function sendMessage() {
    const message = elements.chatInput.value.trim();
    if (!message || state.isLoading) return;

    state.isLoading = true;
    elements.sendBtn.disabled = true;

    // Add user message
    addMessage(message, 'user');
    elements.chatInput.value = '';
    elements.chatInput.style.height = 'auto';

    // Remove welcome message
    const welcome = elements.chatMessages.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    // Add loading indicator
    const loadingId = addTypingIndicator();

    try {
        const response = await apiRequest('/chat/send', {
            method: 'POST',
            body: JSON.stringify({
                message: message,
                chat_id: state.chatId,
                stream: false
            })
        });

        removeTypingIndicator(loadingId);
        addMessage(response.message, 'assistant');

    } catch (error) {
        removeTypingIndicator(loadingId);
        addMessage('Sorry, something went wrong. Please try again later.', 'assistant');
        showToast('Failed to send. Please check if backend service is running', 'error');
    }

    state.isLoading = false;
    elements.sendBtn.disabled = false;
}

function addMessage(content, role) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = role === 'user' ? '<img src="/static/images/logo.png" alt="User" width="32" height="32" style="width: 32px; height: 32px;">' : '<img src="/static/images/logo.png" alt="EgoZone" width="32" height="32" style="width: 32px; height: 32px;">';

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-bubble">${escapeHtml(content)}</div>
    `;

    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addTypingIndicator() {
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.className = 'message assistant';
    div.id = id;
    div.innerHTML = `
        <div class="message-avatar"><img src="/static/images/logo.png" alt="EgoZone" width="32" height="32" style="width: 32px; height: 32px;"></div>
        <div class="message-bubble">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    elements.chatMessages.appendChild(div);
    scrollToBottom();
    return id;
}

function removeTypingIndicator(id) {
    const element = document.getElementById(id);
    if (element) element.remove();
}

function scrollToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

async function clearChat() {
    try {
        await apiRequest(`/chat/history/${state.chatId}`, { method: 'DELETE' });

        elements.chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-avatar">🤖</div>
                <div class="welcome-content">
                    <h2>Hello, I'm Ezio's Digital Twin</h2>
                    <p>I can simulate Ezio's speaking style and thinking patterns to communicate with you.</p>
                    <p>Feel free to ask me questions 👇</p>
                </div>
                <div class="welcome-tips">
                    <span class="welcome-tip" onclick="document.getElementById('chat-input').value='Introduce yourself';document.getElementById('chat-input').focus()">💡 Introduce yourself</span>
                    <span class="welcome-tip" onclick="document.getElementById('chat-input').value='What have you been up to lately?';document.getElementById('chat-input').focus()">🚀 What have you been up to</span>
                    <span class="welcome-tip" onclick="document.getElementById('chat-input').value='What are your thoughts on AI?';document.getElementById('chat-input').focus()">🤔 Thoughts on AI</span>
                </div>
            </div>
        `;
        showToast('Chat cleared');
    } catch (error) {
        showToast('Failed to clear', 'error');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}

// ========== Q&A Collection ==========

function initInterview() {
    elements.skipBtn.addEventListener('click', loadNextQuestion);
    elements.submitAnswerBtn.addEventListener('click', submitAnswer);
}

async function loadInterviewData() {
    try {
        // Load progress
        const progress = await apiRequest('/interview/progress');
        updateProgress(progress);

        // Load categories
        const categories = await apiRequest('/interview/categories');
        renderCategories(categories);

        // Load next question
        await loadNextQuestion();

    } catch (error) {
        console.error('Failed to load Q&A data:', error);
        showToast('Failed to load. Please check backend service', 'error');
    }
}

async function loadNextQuestion() {
    try {
        const question = await apiRequest('/interview/next');
        state.currentQuestion = question;

        elements.questionCategory.textContent = question.category_name;
        elements.questionText.textContent = question.question;
        elements.answerInput.value = '';

    } catch (error) {
        elements.questionText.textContent = 'Unable to load question';
    }
}

async function submitAnswer() {
    const answer = elements.answerInput.value.trim();
    if (!answer) {
        showToast('Please enter an answer', 'error');
        return;
    }

    if (!state.currentQuestion) return;

    try {
        await apiRequest('/interview/answer', {
            method: 'POST',
            body: JSON.stringify({
                question_id: state.currentQuestion.id,
                question: state.currentQuestion.question,
                answer: answer,
                category: state.currentQuestion.category
            })
        });

        showToast('Answer saved!');

        // Update progress
        const progress = await apiRequest('/interview/progress');
        updateProgress(progress);

        // Load next question
        await loadNextQuestion();

    } catch (error) {
        showToast('Failed to save', 'error');
    }
}

function updateProgress(progress) {
    const percent = progress.progress_percent || 0;
    elements.progressPercent.textContent = `${percent}%`;
    elements.progressFill.style.width = `${percent}%`;
    elements.answeredCount.textContent = progress.answered_count || 0;
    elements.totalCount.textContent = progress.total_questions || 0;
}

function renderCategories(categories) {
    elements.categoriesContainer.innerHTML = categories.map(cat => `
        <div class="category-card" onclick="selectCategory('${cat.id}')">
            <h4>${cat.name}</h4>
            <p>Answered ${cat.answered_count} / ${cat.question_count}</p>
        </div>
    `).join('');
}

async function selectCategory(categoryId) {
    try {
        const questions = await apiRequest(`/interview/questions/${categoryId}`);
        if (questions.length > 0) {
            const unanswered = questions[0]; // Simplified handling
            state.currentQuestion = unanswered;
            elements.questionCategory.textContent = unanswered.category_name;
            elements.questionText.textContent = unanswered.question;
            elements.answerInput.value = '';
        }
    } catch (error) {
        showToast('Failed to load questions', 'error');
    }
}

// ========== Knowledge Base ==========

function initKnowledge() {
    elements.addKnowledgeBtn.addEventListener('click', addKnowledge);
}

async function loadKnowledgeData() {
    try {
        // Load statistics
        const stats = await apiRequest('/knowledge/stats');
        elements.knowledgeCount.textContent = stats.count || 0;

        // Load list
        const list = await apiRequest('/knowledge/list?limit=20');
        renderKnowledgeList(list.documents || []);

    } catch (error) {
        console.error('Failed to load knowledge base:', error);
    }
}

async function addKnowledge() {
    const title = elements.knowledgeTitle.value.trim();
    const content = elements.knowledgeContent.value.trim();

    if (!content) {
        showToast('Please enter knowledge content', 'error');
        return;
    }

    try {
        await apiRequest('/knowledge/add', {
            method: 'POST',
            body: JSON.stringify({
                content: content,
                title: title || null,
                source: 'manual',
                doc_type: 'text'
            })
        });

        showToast('Knowledge added!');
        elements.knowledgeTitle.value = '';
        elements.knowledgeContent.value = '';

        // Refresh list
        await loadKnowledgeData();

    } catch (error) {
        showToast('Failed to add', 'error');
    }
}

function renderKnowledgeList(documents) {
    if (documents.length === 0) {
        elements.knowledgeListContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📝</div>
                <p>No knowledge added yet</p>
            </div>
        `;
        return;
    }

    elements.knowledgeListContainer.innerHTML = documents.map(doc => `
        <div class="knowledge-item">
            <div class="knowledge-item-title">${doc.metadata?.title || 'Untitled'}</div>
            <div class="knowledge-item-content">${escapeHtml(doc.content.slice(0, 200))}...</div>
            <div class="knowledge-item-meta">Source: ${doc.metadata?.source || 'manual'}</div>
        </div>
    `).join('');
}

// ========== Settings ==========

function initSettings() {
    elements.saveSettingsBtn.addEventListener('click', saveSettings);

    // Auto-save logic
    const debouncedSave = debounce(saveSettings, 1000);

    // Add listeners to all settings fields
    if (elements.settingName) elements.settingName.addEventListener('input', debouncedSave);
    if (elements.settingEducation) elements.settingEducation.addEventListener('input', debouncedSave);
    if (elements.settingProfession) elements.settingProfession.addEventListener('input', debouncedSave);
    if (elements.settingTone) elements.settingTone.addEventListener('change', debouncedSave);
    if (elements.settingEmoji) elements.settingEmoji.addEventListener('change', debouncedSave);

    // Load settings on page load
    loadSettings();
}

async function loadSettings() {
    try {
        const response = await apiRequest('/settings/profile');
        if (response) {
            // Fill form
            if (elements.settingName) {
                elements.settingName.value = response.name || '';
            }
            if (elements.settingEducation) {
                elements.settingEducation.value = response.education || '';
            }
            if (elements.settingProfession) {
                elements.settingProfession.value = response.profession || '';
            }
            if (elements.settingTone) {
                elements.settingTone.value = response.tone_of_voice || 'gentle';
            }
            if (elements.settingEmoji) {
                elements.settingEmoji.value = response.emoji_usage || 'moderate';
            }
        }
    } catch (error) {
        console.log('Failed to load settings, using defaults');
        // Set default values
        if (elements.settingEducation) {
            elements.settingEducation.value = 'BS in Computer Science';
        }
        if (elements.settingProfession) {
            elements.settingProfession.value = 'Product Manager';
        }
    }
}

async function saveSettings(event) {
    const name = elements.settingName?.value || '';
    const education = elements.settingEducation?.value || '';
    const profession = elements.settingProfession?.value || '';
    const tone = elements.settingTone?.value || 'gentle';
    const emoji = elements.settingEmoji?.value || 'moderate';

    // Show saving status (optional, less intrusive for auto-save)
    const isAutoSave = (event && event.type !== 'click');
    if (!isAutoSave) {
        elements.saveSettingsBtn.textContent = 'Saving...';
        elements.saveSettingsBtn.disabled = true;
    } else {
        // Can show a small hint in the corner
        showToast('Saving...', 'info');
    }

    try {
        const response = await apiRequest('/settings/profile', {
            method: 'PUT',
            body: JSON.stringify({
                name: name,
                education: education,
                profession: profession,
                tone_of_voice: tone,
                emoji_usage: emoji
            })
        });

        if (response.success) {
            if (!isAutoSave) {
                showToast('Settings saved!');
            }
        } else {
            showToast('Failed to save', 'error');
        }
    } catch (error) {
        showToast('Failed to save: ' + error.message, 'error');
    } finally {
        if (!isAutoSave) {
            elements.saveSettingsBtn.textContent = 'Save Settings';
            elements.saveSettingsBtn.disabled = false;
        }
    }
}



// ========== Admin Authentication ==========

// State
state.isAdmin = false;
state.adminToken = localStorage.getItem('adminToken') || null;

// DOM elements (admin related)
const adminElements = {
    loginBtn: document.getElementById('admin-login-btn'),
    loginModal: document.getElementById('login-modal'),
    closeModal: document.getElementById('close-modal'),
    passwordInput: document.getElementById('admin-password'),
    loginSubmitBtn: document.getElementById('login-submit-btn'),
    adminOnlyItems: document.querySelectorAll('.admin-only')
};

function initAdmin() {
    // Check if key elements exist
    if (!adminElements.loginBtn || !adminElements.loginModal || !adminElements.closeModal) {
        // If admin elements not found (possibly commented out), skip initialization
        return;
    }

    // Login button
    adminElements.loginBtn.addEventListener('click', () => {
        if (state.isAdmin) {
            logout();
        } else {
            showLoginModal();
        }
    });

    // Close modal
    adminElements.closeModal.addEventListener('click', hideLoginModal);
    adminElements.loginModal.addEventListener('click', (e) => {
        if (e.target === adminElements.loginModal) {
            hideLoginModal();
        }
    });

    // Submit login
    adminElements.loginSubmitBtn.addEventListener('click', submitLogin);
    adminElements.passwordInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            submitLogin();
        }
    });

    // Check existing token
    if (state.adminToken) {
        verifyToken();
    }
}

function showLoginModal() {
    adminElements.loginModal.classList.add('show');
    adminElements.passwordInput.value = '';
    adminElements.passwordInput.focus();
}

function hideLoginModal() {
    adminElements.loginModal.classList.remove('show');
}

async function submitLogin() {
    const password = adminElements.passwordInput.value;
    if (!password) {
        showToast('Please enter password', 'error');
        return;
    }

    const trustDevice = document.getElementById('admin-trust-device')?.checked || false;

    try {
        const response = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ password, trust_device: trustDevice })
        });

        if (response.success) {
            state.adminToken = response.token;
            state.isAdmin = true;
            localStorage.setItem('adminToken', response.token);
            updateAdminUI();
            hideLoginModal();
            showToast('Login successful! Admin features unlocked');
        } else {
            showToast(response.message || 'Incorrect password', 'error');
        }
    } catch (error) {
        showToast('Login failed', 'error');
    }
}

async function verifyToken() {
    try {
        const response = await apiRequest('/auth/verify', {
            method: 'POST',
            body: JSON.stringify({ token: state.adminToken })
        });

        if (response.valid) {
            state.isAdmin = true;
            updateAdminUI();
        } else {
            // Token invalid, clear it
            localStorage.removeItem('adminToken');
            state.adminToken = null;
            state.isAdmin = false;
        }
    } catch (error) {
        // Verification failed, remain logged out
        state.isAdmin = false;
    }
}

async function logout() {
    try {
        if (state.adminToken) {
            await apiRequest('/auth/logout', {
                method: 'POST',
                body: JSON.stringify({ token: state.adminToken })
            });
        }
    } catch (error) {
        // Ignore logout errors
    }

    localStorage.removeItem('adminToken');
    state.adminToken = null;
    state.isAdmin = false;
    updateAdminUI();
    switchPage('chat');
    showToast('Logged out of admin mode');
}

function updateAdminUI() {
    // Update button state
    if (state.isAdmin) {
        adminElements.loginBtn.textContent = '🔓 Logout Admin';
        adminElements.loginBtn.classList.add('logged-in');
    } else {
        adminElements.loginBtn.textContent = '🔐 Admin';
        adminElements.loginBtn.classList.remove('logged-in');
    }

    // Update menu items
    adminElements.adminOnlyItems.forEach(item => {
        if (state.isAdmin) {
            item.classList.add('unlocked');
        } else {
            item.classList.remove('unlocked');
        }
    });
}

// Modify navigation function to check permissions
const originalSwitchPage = switchPage;
function switchPage(pageName) {
    // Check if admin permission required (skip in debug mode)
    const adminPages = ['interview', 'knowledge', 'settings'];
    if (!DEBUG_MODE && adminPages.includes(pageName) && !state.isAdmin) {
        showLoginModal();
        return;
    }

    // Call original function
    // Update navigation
    elements.navItems.forEach(item => {
        item.classList.toggle('active', item.dataset.page === pageName);
    });

    // Update pages
    elements.pages.forEach(page => {
        page.classList.toggle('active', page.id === `${pageName}-page`);
    });

    state.currentPage = pageName;

    // Load page data
    switch (pageName) {
        case 'interview':
            loadInterviewData();
            break;
        case 'knowledge':
            loadKnowledgeData();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// ========== Mobile Menu ==========

function initMobileMenu() {
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('mobile-overlay');

    if (!menuToggle || !sidebar || !overlay) return;

    // Click menu button
    menuToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('show');
        menuToggle.textContent = sidebar.classList.contains('open') ? '✕' : '☰';
    });

    // Click overlay to close menu
    overlay.addEventListener('click', () => {
        sidebar.classList.remove('open');
        overlay.classList.remove('show');
        menuToggle.textContent = '☰';
    });

    // Close menu after clicking nav item (mobile)
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('open');
                overlay.classList.remove('show');
                menuToggle.textContent = '☰';
            }
        });
    });
}

// ========== Public Access Verification ==========

state.hasAccess = false;
state.accessToken = localStorage.getItem('accessToken') || null;

async function checkTrustedDevice() {
    try {
        const response = await fetch(`${API_BASE}/auth/check-device`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();

        if (data.trusted && data.token) {
            state.accessToken = data.token;
            state.hasAccess = true;
            localStorage.setItem('accessToken', data.token);
            hideAccessModal();
            showToast(`Trusted device auto-login successful: ${data.device_name || ''}`, 'success');
            return true;
        }
    } catch (error) {
        console.log('Trusted device check failed:', error);
    }
    return false;
}

function initAccessCheck() {
    // Debug mode: skip password verification, set as admin
    if (DEBUG_MODE) {
        state.hasAccess = true;
        state.isAdmin = true;
        updateAdminUI();
        return;
    }

    const accessModal = document.getElementById('access-modal');
    const accessPassword = document.getElementById('access-password');
    const accessSubmitBtn = document.getElementById('access-submit-btn');

    if (!accessModal || !accessPassword || !accessSubmitBtn) return;

    // First check if trusted device (auto passwordless login)
    checkTrustedDevice().then(isTrusted => {
        if (isTrusted) return; // Already logged in via trusted device

        // Check if valid access token exists
        if (state.accessToken) {
            verifyAccessToken();
        } else {
            showAccessModal();
        }
    });

    // Submit verification
    accessSubmitBtn.addEventListener('click', submitAccessPassword);
    accessPassword.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            submitAccessPassword();
        }
    });
}

function showAccessModal() {
    const accessModal = document.getElementById('access-modal');
    if (accessModal) {
        accessModal.classList.add('show');
        document.getElementById('access-password').focus();
    }
}

function hideAccessModal() {
    const accessModal = document.getElementById('access-modal');
    if (accessModal) {
        accessModal.classList.remove('show');
    }
}

async function submitAccessPassword() {
    const password = document.getElementById('access-password').value;
    if (!password) {
        showToast('Please enter access password', 'error');
        return;
    }

    const trustDevice = document.getElementById('access-trust-device')?.checked || false;

    try {
        const response = await apiRequest('/auth/access-login', {
            method: 'POST',
            body: JSON.stringify({ password, trust_device: trustDevice })
        });

        if (response.success) {
            state.accessToken = response.token;
            state.hasAccess = true;
            localStorage.setItem('accessToken', response.token);
            hideAccessModal();
            showToast('Verification successful, welcome!');
        } else {
            showToast(response.message || 'Incorrect password', 'error');
        }
    } catch (error) {
        showToast('Verification failed', 'error');
    }
}

async function verifyAccessToken() {
    try {
        const response = await apiRequest('/auth/verify-access', {
            method: 'POST',
            body: JSON.stringify({ token: state.accessToken })
        });

        if (response.valid) {
            state.hasAccess = true;
            hideAccessModal();
        } else {
            localStorage.removeItem('accessToken');
            state.accessToken = null;
            state.hasAccess = false;
            showAccessModal();
        }
    } catch (error) {
        // Verification failed, show modal
        showAccessModal();
    }
}

// ========== Initialization ==========

function init() {
    initNavigation();
    initChat();
    initInterview();
    initKnowledge();
    initSettings();
    initAdmin();
    initMobileMenu();
    initAccessCheck();

    console.log('🚀 EgoZone Web Application started');
}

// Initialize after page load
document.addEventListener('DOMContentLoaded', init);

// Expose global functions
window.selectCategory = selectCategory;
