// 主应用模块
const app = {
    // 初始化
    init() {
        this.bindEvents();
        this.loadStats();
        this.loadRecentNovels();
        // 移除自动刷新，改为手动刷新
    },

    // 绑定事件
    bindEvents() {
        // 创建小说表单
        const createForm = document.getElementById('createNovelForm');
        if (createForm) {
            createForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleCreateNovel();
            });
        }

        // AI配置表单
        const configForm = document.getElementById('addConfigForm');
        if (configForm) {
            configForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleAddConfig();
            });
        }

        // 编辑AI配置表单
        const editConfigForm = document.getElementById('editConfigForm');
        if (editConfigForm) {
            editConfigForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleEditConfig();
            });
        }

        // 关闭模态框（点击背景）
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    },

    // 切换标签页
    switchTab(tabName, event) {
        // 更新标签状态
        document.querySelectorAll('.nav-tab').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        if (event && event.target) {
            event.target.classList.add('active');
        } else {
            const button = document.querySelector(`[onclick*="'${tabName}'"]`);
            if (button) button.classList.add('active');
        }

        const tabContent = document.getElementById(tabName);
        if (tabContent) tabContent.classList.add('active');

        // 加载对应数据
        switch(tabName) {
            case 'dashboard':
                this.loadStats();
                this.loadRecentNovels();
                break;
            case 'novels':
                novelManager.loadNovels();
                break;
            case 'tokens':
                tokenManager.loadTokenStats();
                tokenManager.loadNovelListForFilter();
                break;
            case 'settings':
                configManager.loadConfigs();
                break;
        }
    },

    // 加载统计数据
    async loadStats() {
        try {
            const stats = await api.stats.getGlobal();

            document.getElementById('totalNovels').textContent = stats.total_novels || 0;
            document.getElementById('completedNovels').textContent = stats.completed_novels || 0;
            document.getElementById('generatingNovels').textContent = stats.generating_novels || 0;
            document.getElementById('failedNovels').textContent = stats.failed_novels || 0;
            document.getElementById('totalTokens').textContent = utils.formatNumber(stats.total_tokens || 0);
            document.getElementById('totalCost').textContent = `$${(stats.total_cost || 0).toFixed(2)}`;
        } catch (error) {
            console.error('加载统计数据失败:', error);
        }
    },

    // 加载最近的小说
    async loadRecentNovels() {
        try {
            const novels = await api.novels.getAll();
            const container = document.getElementById('recentNovels');

            if (novels.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <h3>还没有小说</h3>
                        <p>点击"创建小说"开始创作吧！</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = novels.slice(0, 5).map(novel =>
                novelManager.createNovelCard(novel)
            ).join('');
        } catch (error) {
            console.error('加载最近小说失败:', error);
        }
    },

    // 处理创建小说
    async handleCreateNovel() {
        const formData = {
            theme: document.getElementById('theme').value,
            background: document.getElementById('background').value,
            target_words: parseInt(document.getElementById('targetWords').value),
            target_chapters: parseInt(document.getElementById('targetChapters').value)
        };

        await novelManager.createNovel(formData);

        // 清空表单
        document.getElementById('createNovelForm').reset();
    },

    // 处理添加AI配置
    async handleAddConfig() {
        const formData = {
            name: document.getElementById('configName').value,
            api_base: document.getElementById('configApiBase').value,
            api_key: document.getElementById('configApiKey').value,
            model_name: document.getElementById('configModelName').value,
            config_type: document.getElementById('configType').value,
            is_active: false
        };

        await configManager.addConfig(formData);

        // 清空表单并关闭模态框
        document.getElementById('addConfigForm').reset();
        this.closeModal('addConfigModal');
    },

    // 处理编辑AI配置
    async handleEditConfig() {
        const configId = parseInt(document.getElementById('editConfigId').value);
        const apiKey = document.getElementById('editConfigApiKey').value;

        const formData = {
            name: document.getElementById('editConfigName').value,
            api_base: document.getElementById('editConfigApiBase').value,
            model_name: document.getElementById('editConfigModelName').value,
            config_type: document.getElementById('editConfigType').value
        };

        // 只有在输入了新密钥时才更新
        if (apiKey) {
            formData.api_key = apiKey;
        }

        await configManager.updateConfig(configId, formData);

        // 清空表单并关闭模态框
        document.getElementById('editConfigForm').reset();
        this.closeModal('editConfigModal');
    },

    // 关闭模态框
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
        }

        // 如果是进度模态框，停止监控
        if (modalId === 'progressModal') {
            novelManager.stopProgressMonitoring();
        }
    },

    // 显示模态框
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
        }
    },

    // 手动刷新当前页面数据
    refreshCurrentTab() {
        const activeTabElement = document.querySelector('.tab-content.active');
        if (!activeTabElement) return;

        const activeTab = activeTabElement.id;
        if (activeTab === 'dashboard') {
            this.loadStats();
            this.loadRecentNovels();
        } else if (activeTab === 'novels') {
            novelManager.loadNovels();
        } else if (activeTab === 'tokens') {
            tokenManager.loadTokenStats();
        } else if (activeTab === 'settings') {
            configManager.loadConfigs();
        }

        utils.showMessage('数据已刷新');
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});

// 导出到全局
window.app = app;
