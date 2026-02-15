/**
 * EgoZone - Web 应用 JavaScript
 */

// ⚠️ 本地调试模式：设为 true 跳过所有密码验证
const DEBUG_MODE = true;

// API 基础 URL（自动检测环境）
const API_BASE = window.location.origin + '/api';

// 全局状态
const state = {
    currentPage: 'chat',
    currentQuestion: null,
    chatId: 'default',
    isLoading: false
};

// DOM 元素
const elements = {
    // 导航
    navItems: document.querySelectorAll('.nav-item'),
    pages: document.querySelectorAll('.page'),

    // 对话
    chatMessages: document.getElementById('chat-messages'),
    chatInput: document.getElementById('chat-input'),
    sendBtn: document.getElementById('send-btn'),
    clearChat: document.getElementById('clear-chat'),

    // 问答
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

    // 知识库
    knowledgeTitle: document.getElementById('knowledge-title'),
    knowledgeContent: document.getElementById('knowledge-content'),
    addKnowledgeBtn: document.getElementById('add-knowledge-btn'),
    knowledgeCount: document.getElementById('knowledge-count'),
    knowledgeListContainer: document.getElementById('knowledge-list-container'),

    // 设置
    settingName: document.getElementById('setting-name'),
    settingEducation: document.getElementById('setting-education'),
    settingProfession: document.getElementById('setting-profession'),
    settingTone: document.getElementById('setting-tone'),
    settingEmoji: document.getElementById('setting-emoji'),
    saveSettingsBtn: document.getElementById('save-settings-btn'),

    // Toast
    toast: document.getElementById('toast')
};

// ========== 工具函数 ==========

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
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API 请求失败:', error);
        throw error;
    }
}

// ========== 导航 ==========

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
    // 更新导航
    elements.navItems.forEach(item => {
        item.classList.toggle('active', item.dataset.page === pageName);
    });

    // 更新页面
    elements.pages.forEach(page => {
        page.classList.toggle('active', page.id === `${pageName}-page`);
    });

    state.currentPage = pageName;

    // 加载页面数据
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

// ========== 对话功能 ==========

function initChat() {
    // 发送按钮
    elements.sendBtn.addEventListener('click', sendMessage);

    // 输入框
    elements.chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 自动调整高度
    elements.chatInput.addEventListener('input', () => {
        elements.chatInput.style.height = 'auto';
        elements.chatInput.style.height = Math.min(elements.chatInput.scrollHeight, 200) + 'px';
    });

    // 清空对话
    elements.clearChat.addEventListener('click', clearChat);
}

async function sendMessage() {
    const message = elements.chatInput.value.trim();
    if (!message || state.isLoading) return;

    state.isLoading = true;
    elements.sendBtn.disabled = true;

    // 添加用户消息
    addMessage(message, 'user');
    elements.chatInput.value = '';
    elements.chatInput.style.height = 'auto';

    // 移除欢迎消息
    const welcome = elements.chatMessages.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    // 添加加载指示器
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
        addMessage('抱歉，出现了一些问题，请稍后再试。', 'assistant');
        showToast('发送失败，请检查后端服务是否启动', 'error');
    }

    state.isLoading = false;
    elements.sendBtn.disabled = false;
}

function addMessage(content, role) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = role === 'user' ? '👤' : '🤖';

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
        <div class="message-avatar">🤖</div>
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
                    <h2>你好，我是 Ezio 的数字分身</h2>
                    <p>我可以模拟 Ezio 的说话风格和思维方式与你交流。</p>
                    <p>试着问我一些问题吧 👇</p>
                </div>
                <div class="welcome-tips">
                    <span class="welcome-tip" onclick="document.getElementById('chat-input').value='介绍一下你自己吧';document.getElementById('chat-input').focus()">💡 介绍一下你自己</span>
                    <span class="welcome-tip" onclick="document.getElementById('chat-input').value='你最近在忙什么？';document.getElementById('chat-input').focus()">🚀 最近在忙什么</span>
                    <span class="welcome-tip" onclick="document.getElementById('chat-input').value='你对AI的看法是什么？';document.getElementById('chat-input').focus()">🤔 对AI的看法</span>
                </div>
            </div>
        `;
        showToast('对话已清空');
    } catch (error) {
        showToast('清空失败', 'error');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}

// ========== 问答采集 ==========

function initInterview() {
    elements.skipBtn.addEventListener('click', loadNextQuestion);
    elements.submitAnswerBtn.addEventListener('click', submitAnswer);
}

async function loadInterviewData() {
    try {
        // 加载进度
        const progress = await apiRequest('/interview/progress');
        updateProgress(progress);

        // 加载类别
        const categories = await apiRequest('/interview/categories');
        renderCategories(categories);

        // 加载下一个问题
        await loadNextQuestion();

    } catch (error) {
        console.error('加载问答数据失败:', error);
        showToast('加载失败，请检查后端服务', 'error');
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
        elements.questionText.textContent = '无法加载问题';
    }
}

async function submitAnswer() {
    const answer = elements.answerInput.value.trim();
    if (!answer) {
        showToast('请输入回答', 'error');
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

        showToast('回答已保存！');

        // 更新进度
        const progress = await apiRequest('/interview/progress');
        updateProgress(progress);

        // 加载下一题
        await loadNextQuestion();

    } catch (error) {
        showToast('保存失败', 'error');
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
            <p>已回答 ${cat.answered_count} / ${cat.question_count}</p>
        </div>
    `).join('');
}

async function selectCategory(categoryId) {
    try {
        const questions = await apiRequest(`/interview/questions/${categoryId}`);
        if (questions.length > 0) {
            const unanswered = questions[0]; // 简化处理
            state.currentQuestion = unanswered;
            elements.questionCategory.textContent = unanswered.category_name;
            elements.questionText.textContent = unanswered.question;
            elements.answerInput.value = '';
        }
    } catch (error) {
        showToast('加载问题失败', 'error');
    }
}

// ========== 知识库 ==========

function initKnowledge() {
    elements.addKnowledgeBtn.addEventListener('click', addKnowledge);
}

async function loadKnowledgeData() {
    try {
        // 加载统计
        const stats = await apiRequest('/knowledge/stats');
        elements.knowledgeCount.textContent = stats.count || 0;

        // 加载列表
        const list = await apiRequest('/knowledge/list?limit=20');
        renderKnowledgeList(list.documents || []);

    } catch (error) {
        console.error('加载知识库失败:', error);
    }
}

async function addKnowledge() {
    const title = elements.knowledgeTitle.value.trim();
    const content = elements.knowledgeContent.value.trim();

    if (!content) {
        showToast('请输入知识内容', 'error');
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

        showToast('知识已添加！');
        elements.knowledgeTitle.value = '';
        elements.knowledgeContent.value = '';

        // 刷新列表
        await loadKnowledgeData();

    } catch (error) {
        showToast('添加失败', 'error');
    }
}

function renderKnowledgeList(documents) {
    if (documents.length === 0) {
        elements.knowledgeListContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📝</div>
                <p>还没有添加任何知识</p>
            </div>
        `;
        return;
    }

    elements.knowledgeListContainer.innerHTML = documents.map(doc => `
        <div class="knowledge-item">
            <div class="knowledge-item-title">${doc.metadata?.title || '无标题'}</div>
            <div class="knowledge-item-content">${escapeHtml(doc.content.slice(0, 200))}...</div>
            <div class="knowledge-item-meta">来源: ${doc.metadata?.source || 'manual'}</div>
        </div>
    `).join('');
}

// ========== 设置 ==========

function initSettings() {
    elements.saveSettingsBtn.addEventListener('click', saveSettings);

    // 自动保存逻辑
    const debouncedSave = debounce(saveSettings, 1000);

    // 为所有设置项添加监听器
    if (elements.settingName) elements.settingName.addEventListener('input', debouncedSave);
    if (elements.settingEducation) elements.settingEducation.addEventListener('input', debouncedSave);
    if (elements.settingProfession) elements.settingProfession.addEventListener('input', debouncedSave);
    if (elements.settingTone) elements.settingTone.addEventListener('change', debouncedSave);
    if (elements.settingEmoji) elements.settingEmoji.addEventListener('change', debouncedSave);

    // 页面加载时获取设置
    loadSettings();
}

async function loadSettings() {
    try {
        const response = await apiRequest('/settings/profile');
        if (response) {
            // 填充表单
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
                elements.settingTone.value = response.tone_of_voice || '温和';
            }
            if (elements.settingEmoji) {
                elements.settingEmoji.value = response.emoji_usage || 'moderate';
            }
        }
    } catch (error) {
        console.log('加载设置失败，使用默认值');
        // 设置默认值
        if (elements.settingEducation) {
            elements.settingEducation.value = '计算机专业本科';
        }
        if (elements.settingProfession) {
            elements.settingProfession.value = '互联网产品经理';
        }
    }
}

async function saveSettings() {
    const name = elements.settingName?.value || '';
    const education = elements.settingEducation?.value || '';
    const profession = elements.settingProfession?.value || '';
    const tone = elements.settingTone?.value || '温和';
    const emoji = elements.settingEmoji?.value || 'moderate';

    // 显示正在保存状态（可选，如果是自动保存不要太打扰）
    const isAutoSave = (event && event.type !== 'click');
    if (!isAutoSave) {
        elements.saveSettingsBtn.textContent = '保存中...';
        elements.saveSettingsBtn.disabled = true;
    } else {
        // 可以在角落显示一个小提示
        showToast('正在保存...', 'info');
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
                showToast('设置已保存！');
            }
        } else {
            showToast('保存失败', 'error');
        }
    } catch (error) {
        showToast('保存失败: ' + error.message, 'error');
    } finally {
        if (!isAutoSave) {
            elements.saveSettingsBtn.textContent = '保存设置';
            elements.saveSettingsBtn.disabled = false;
        }
    }
}



// ========== 管理员认证 ==========

// 状态
state.isAdmin = false;
state.adminToken = localStorage.getItem('adminToken') || null;

// DOM 元素（管理员相关）
const adminElements = {
    loginBtn: document.getElementById('admin-login-btn'),
    loginModal: document.getElementById('login-modal'),
    closeModal: document.getElementById('close-modal'),
    passwordInput: document.getElementById('admin-password'),
    loginSubmitBtn: document.getElementById('login-submit-btn'),
    adminOnlyItems: document.querySelectorAll('.admin-only')
};

function initAdmin() {
    // 登录按钮
    adminElements.loginBtn.addEventListener('click', () => {
        if (state.isAdmin) {
            logout();
        } else {
            showLoginModal();
        }
    });

    // 关闭弹窗
    adminElements.closeModal.addEventListener('click', hideLoginModal);
    adminElements.loginModal.addEventListener('click', (e) => {
        if (e.target === adminElements.loginModal) {
            hideLoginModal();
        }
    });

    // 提交登录
    adminElements.loginSubmitBtn.addEventListener('click', submitLogin);
    adminElements.passwordInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            submitLogin();
        }
    });

    // 检查现有 token
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
        showToast('请输入密码', 'error');
        return;
    }

    try {
        const response = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ password })
        });

        if (response.success) {
            state.adminToken = response.token;
            state.isAdmin = true;
            localStorage.setItem('adminToken', response.token);
            updateAdminUI();
            hideLoginModal();
            showToast('登录成功！管理功能已解锁');
        } else {
            showToast(response.message || '密码错误', 'error');
        }
    } catch (error) {
        showToast('登录失败', 'error');
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
            // Token 无效，清除
            localStorage.removeItem('adminToken');
            state.adminToken = null;
            state.isAdmin = false;
        }
    } catch (error) {
        // 验证失败，保持未登录状态
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
        // 忽略登出错误
    }

    localStorage.removeItem('adminToken');
    state.adminToken = null;
    state.isAdmin = false;
    updateAdminUI();
    switchPage('chat');
    showToast('已退出管理员模式');
}

function updateAdminUI() {
    // 更新按钮状态
    if (state.isAdmin) {
        adminElements.loginBtn.textContent = '🔓 退出管理';
        adminElements.loginBtn.classList.add('logged-in');
    } else {
        adminElements.loginBtn.textContent = '🔐 管理员';
        adminElements.loginBtn.classList.remove('logged-in');
    }

    // 更新菜单项
    adminElements.adminOnlyItems.forEach(item => {
        if (state.isAdmin) {
            item.classList.add('unlocked');
        } else {
            item.classList.remove('unlocked');
        }
    });
}

// 修改导航函数以检查权限
const originalSwitchPage = switchPage;
function switchPage(pageName) {
    // 检查是否需要管理员权限（调试模式跳过）
    const adminPages = ['interview', 'knowledge', 'settings'];
    if (!DEBUG_MODE && adminPages.includes(pageName) && !state.isAdmin) {
        showLoginModal();
        return;
    }

    // 调用原始函数
    // 更新导航
    elements.navItems.forEach(item => {
        item.classList.toggle('active', item.dataset.page === pageName);
    });

    // 更新页面
    elements.pages.forEach(page => {
        page.classList.toggle('active', page.id === `${pageName}-page`);
    });

    state.currentPage = pageName;

    // 加载页面数据
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

// ========== 移动端菜单 ==========

function initMobileMenu() {
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('mobile-overlay');

    if (!menuToggle || !sidebar || !overlay) return;

    // 点击菜单按钮
    menuToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('show');
        menuToggle.textContent = sidebar.classList.contains('open') ? '✕' : '☰';
    });

    // 点击遮罩层关闭菜单
    overlay.addEventListener('click', () => {
        sidebar.classList.remove('open');
        overlay.classList.remove('show');
        menuToggle.textContent = '☰';
    });

    // 点击导航项后关闭菜单（移动端）
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

// ========== 公共访问验证 ==========

state.hasAccess = false;
state.accessToken = localStorage.getItem('accessToken') || null;

function initAccessCheck() {
    // 调试模式：直接跳过密码验证，设置为管理员
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

    // 检查是否已有访问权限
    if (state.accessToken) {
        verifyAccessToken();
    } else {
        showAccessModal();
    }

    // 提交验证
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
        showToast('请输入访问密码', 'error');
        return;
    }

    try {
        const response = await apiRequest('/auth/access-login', {
            method: 'POST',
            body: JSON.stringify({ password })
        });

        if (response.success) {
            state.accessToken = response.token;
            state.hasAccess = true;
            localStorage.setItem('accessToken', response.token);
            hideAccessModal();
            showToast('验证成功，欢迎使用！');
        } else {
            showToast(response.message || '密码错误', 'error');
        }
    } catch (error) {
        showToast('验证失败', 'error');
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
        // 验证失败，显示弹窗
        showAccessModal();
    }
}

// ========== 初始化 ==========

function init() {
    initNavigation();
    initChat();
    initInterview();
    initKnowledge();
    initSettings();
    initAdmin();
    initMobileMenu();
    initAccessCheck();

    console.log('🚀 EgoZone Web 应用已启动');
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);

// 暴露全局函数
window.selectCategory = selectCategory;
