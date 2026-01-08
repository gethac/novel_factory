// 小说管理模块
const novelManager = {
    // 当前监控的小说ID
    monitoringNovelId: null,
    monitoringInterval: null,

    // 加载小说列表
    async loadNovels() {
        try {
            const novels = await api.novels.getAll();
            const container = document.getElementById('novelsList');

            if (novels.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <h3>还没有小说</h3>
                        <p>点击"创建小说"开始创作吧！</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = novels.map(novel => this.createNovelCard(novel)).join('');
        } catch (error) {
            console.error('加载小说列表失败:', error);
            utils.showMessage('加载小说列表失败: ' + error.message);
        }
    },

    // 创建小说卡片HTML
    createNovelCard(novel) {
        const statusClass = `status-${novel.status}`;
        const statusText = utils.getStatusText(novel.status);
        const progressPercentage = utils.getProgressPercentage(novel.current_stage);
        const stageLabel = utils.getStageLabel(novel.current_stage);

        // 进度条（仅在生成中显示）
        const progressBar = novel.status === 'generating' ? `
            <div class="progress-bar-container">
                <div class="progress-bar-header">
                    <span class="progress-bar-label">生成进度</span>
                    <span class="progress-bar-stage">${stageLabel}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-bar-fill" style="width: ${progressPercentage}%"></div>
                </div>
            </div>
        ` : '';

        // Token统计（如果有）
        const tokenInfo = novel.total_tokens ? `
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee; font-size: 0.9em; color: #666;">
                Token: ${utils.formatNumber(novel.total_tokens)} | 费用: $${(novel.total_cost || 0).toFixed(2)}
            </div>
        ` : '';

        return `
            <div class="novel-card" data-novel-id="${novel.id}">
                <div class="novel-card-header">
                    <div class="novel-title">${novel.title || '未命名小说'}</div>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </div>
                <div class="novel-info">
                    <div>主题: ${novel.theme || '-'}</div>
                    <div>目标字数: ${utils.formatNumber(novel.target_words || 0)}</div>
                    <div>章节数: ${novel.target_chapters || 0}</div>
                    <div>创建时间: ${utils.formatDate(novel.created_at)}</div>
                </div>
                ${progressBar}
                ${tokenInfo}
                <div class="novel-actions">
                    ${novel.status === 'pending' ? `
                        <button class="btn btn-success" onclick="novelManager.startGeneration(${novel.id})">
                            开始生成
                        </button>
                    ` : ''}
                    ${novel.status === 'generating' ? `
                        <button class="btn btn-primary" onclick="novelManager.viewProgress(${novel.id})">
                            查看进度
                        </button>
                    ` : ''}
                    ${novel.status === 'completed' ? `
                        <button class="btn btn-primary" onclick="novelManager.exportNovel(${novel.id})">
                            导出TXT
                        </button>
                        <button class="btn btn-primary" onclick="novelManager.downloadNovel(${novel.id})">
                            下载
                        </button>
                    ` : ''}
                    <button class="btn btn-secondary" onclick="novelManager.viewDetail(${novel.id})">
                        查看详情
                    </button>
                    <button class="btn btn-secondary" onclick="novelManager.viewLogs(${novel.id})">
                        查看日志
                    </button>
                    <button class="btn btn-danger" onclick="novelManager.deleteNovel(${novel.id})">
                        删除
                    </button>
                </div>
            </div>
        `;
    },

    // 创建小说
    async createNovel(formData) {
        try {
            const novel = await api.novels.create(formData);
            utils.showMessage('小说任务创建成功！');

            // 自动开始生成
            await this.startGeneration(novel.id);

            // 切换到小说列表
            window.app.switchTab('novels');
        } catch (error) {
            console.error('创建小说失败:', error);
            utils.showMessage('创建失败: ' + error.message);
        }
    },

    // 开始生成
    async startGeneration(novelId) {
        try {
            await api.novels.start(novelId);
            utils.showMessage('小说生成已启动！这可能需要一些时间，请稍后查看进度。');
            this.loadNovels();
        } catch (error) {
            console.error('启动生成失败:', error);
            utils.showMessage('启动失败: ' + error.message);
        }
    },

    // 查看进度（实时更新）
    async viewProgress(novelId) {
        try {
            const novel = await api.novels.getById(novelId);
            const chapters = await api.novels.getChapters(novelId);

            // 显示进度模态框
            this.showProgressModal(novel, chapters);

            // 开始实时监控
            this.startProgressMonitoring(novelId);
        } catch (error) {
            console.error('加载进度失败:', error);
            utils.showMessage('加载进度失败: ' + error.message);
        }
    },

    // 显示进度模态框
    showProgressModal(novel, chapters) {
        const modal = document.getElementById('progressModal');
        const title = document.getElementById('progressModalTitle');
        const content = document.getElementById('progressModalContent');

        title.textContent = novel.title || '未命名小说';

        // 构建进度步骤
        const stages = [
            { key: 'settings', label: '小说设定', icon: '📝' },
            { key: 'outline', label: '大纲生成', icon: '📋' },
            { key: 'content', label: '内容生成', icon: '✍️' },
            { key: 'completed', label: '完成', icon: '✓' }
        ];

        const currentStageIndex = stages.findIndex(s => s.key === novel.current_stage);

        const stepsHTML = stages.map((stage, index) => {
            let className = 'progress-step';
            if (index < currentStageIndex) className += ' completed';
            if (index === currentStageIndex) className += ' active';

            return `
                <div class="${className}">
                    <div class="progress-step-circle">${stage.icon}</div>
                    <div class="progress-step-label">${stage.label}</div>
                </div>
            `;
        }).join('');

        // 构建详细内容展示
        let contentSections = '';

        // 1. 小说设定
        if (novel.settings) {
            contentSections += `
                <div class="generation-section ${novel.current_stage === 'settings' ? 'active' : 'completed'}">
                    <div class="section-header">
                        <h4>📝 小说设定</h4>
                        ${novel.current_stage === 'settings' ? '<span class="loading-spinner"></span>' : '<span class="status-check">✓</span>'}
                    </div>
                    <div class="section-content">
                        <pre>${novel.settings}</pre>
                    </div>
                </div>
            `;
        } else if (novel.current_stage === 'settings') {
            contentSections += `
                <div class="generation-section active">
                    <div class="section-header">
                        <h4>📝 小说设定</h4>
                        <span class="loading-spinner"></span>
                    </div>
                    <div class="section-content">
                        <p class="generating-text">正在生成小说设定...</p>
                    </div>
                </div>
            `;
        }

        // 2. 大纲
        if (novel.outline) {
            contentSections += `
                <div class="generation-section ${novel.current_stage === 'outline' ? 'active' : 'completed'}">
                    <div class="section-header">
                        <h4>📋 故事大纲</h4>
                        ${novel.current_stage === 'outline' ? '<span class="loading-spinner"></span>' : '<span class="status-check">✓</span>'}
                    </div>
                    <div class="section-content">
                        <pre>${novel.outline}</pre>
                    </div>
                </div>
            `;
        } else if (novel.current_stage === 'outline') {
            contentSections += `
                <div class="generation-section active">
                    <div class="section-header">
                        <h4>📋 故事大纲</h4>
                        <span class="loading-spinner"></span>
                    </div>
                    <div class="section-content">
                        <p class="generating-text">正在生成故事大纲...</p>
                    </div>
                </div>
            `;
        }

        // 3. 章节内容
        if (novel.current_stage === 'content' || chapters.length > 0) {
            const completedChapters = chapters.filter(ch => ch.status === 'completed').length;
            const totalChapters = novel.target_chapters;
            const progressPercent = totalChapters > 0 ? (completedChapters / totalChapters * 100).toFixed(1) : 0;

            contentSections += `
                <div class="generation-section ${novel.current_stage === 'content' ? 'active' : 'completed'}">
                    <div class="section-header">
                        <h4>✍️ 章节内容生成</h4>
                        ${novel.current_stage === 'content' ? '<span class="loading-spinner"></span>' : '<span class="status-check">✓</span>'}
                    </div>
                    <div class="section-content">
                        <div class="chapter-progress">
                            <div class="chapter-progress-info">
                                <span>进度: ${completedChapters} / ${totalChapters} 章</span>
                                <span>${progressPercent}%</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-bar-fill" style="width: ${progressPercent}%"></div>
                            </div>
                        </div>
                        <div class="chapters-list">
                            ${chapters.map(ch => `
                                <div class="chapter-item-mini ${ch.status}">
                                    <div class="chapter-item-header">
                                        <span class="chapter-number">第${ch.chapter_number}章</span>
                                        <span class="chapter-title">${ch.title}</span>
                                        <span class="chapter-status-icon">
                                            ${ch.status === 'completed' ? '✓' : ch.status === 'generating' ? '⏳' : '⏸'}
                                        </span>
                                    </div>
                                    ${ch.detailed_outline ? `
                                        <div class="chapter-outline-preview">
                                            <strong>细纲:</strong> ${ch.detailed_outline.substring(0, 100)}...
                                        </div>
                                    ` : ''}
                                    ${ch.word_count ? `
                                        <div class="chapter-word-count">字数: ${utils.formatNumber(ch.word_count)}</div>
                                    ` : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        }

        // 如果没有任何内容，显示等待状态
        if (!contentSections) {
            contentSections = `
                <div class="generation-section active">
                    <div class="section-header">
                        <h4>准备开始生成</h4>
                        <span class="loading-spinner"></span>
                    </div>
                    <div class="section-content">
                        <p class="generating-text">系统正在初始化...</p>
                    </div>
                </div>
            `;
        }

        content.innerHTML = `
            <div class="progress-container">
                <div class="progress-steps">
                    ${stepsHTML}
                </div>
                <div class="generation-content">
                    ${contentSections}
                </div>
            </div>
        `;

        modal.classList.add('active');
    },

    // 开始实时监控
    startProgressMonitoring(novelId) {
        // 清除之前的监控
        this.stopProgressMonitoring();

        this.monitoringNovelId = novelId;
        this.monitoringInterval = setInterval(async () => {
            try {
                const novel = await api.novels.getById(novelId);
                const chapters = await api.novels.getChapters(novelId);

                // 保存当前滚动位置
                const modalBody = document.querySelector('#progressModal .modal-body');
                const scrollPosition = modalBody ? modalBody.scrollTop : 0;

                // 更新进度显示
                this.showProgressModal(novel, chapters);

                // 恢复滚动位置
                if (modalBody) {
                    const newModalBody = document.querySelector('#progressModal .modal-body');
                    if (newModalBody) {
                        newModalBody.scrollTop = scrollPosition;
                    }
                }

                // 如果完成或失败，停止监控
                if (novel.status === 'completed' || novel.status === 'failed') {
                    this.stopProgressMonitoring();
                    if (novel.status === 'completed') {
                        utils.showMessage('小说生成完成！');
                    } else {
                        utils.showMessage('小说生成失败，请查看日志了解详情。');
                    }
                }
            } catch (error) {
                console.error('更新进度失败:', error);
            }
        }, 3000); // 每3秒更新一次
    },

    // 停止实时监控
    stopProgressMonitoring() {
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
        this.monitoringNovelId = null;
    },

    // 查看详情
    async viewDetail(novelId) {
        try {
            const novel = await api.novels.getById(novelId);
            const chapters = await api.novels.getChapters(novelId);

            const modal = document.getElementById('novelDetailModal');
            const title = document.getElementById('modalNovelTitle');
            const content = document.getElementById('novelDetailContent');

            title.textContent = novel.title || '未命名小说';

            content.innerHTML = `
                <div style="margin-bottom: 20px;">
                    <h3 style="color: var(--primary-color); margin-bottom: 15px;">基本信息</h3>
                    <div style="display: grid; gap: 10px;">
                        <p><strong>主题:</strong> ${novel.theme}</p>
                        <p><strong>背景:</strong> ${novel.background}</p>
                        <p><strong>目标字数:</strong> ${utils.formatNumber(novel.target_words)}</p>
                        <p><strong>目标章节:</strong> ${novel.target_chapters}</p>
                        <p><strong>状态:</strong> ${utils.getStatusText(novel.status)}</p>
                        <p><strong>当前阶段:</strong> ${utils.getStageLabel(novel.current_stage)}</p>
                    </div>
                </div>

                ${novel.settings ? `
                    <div style="margin-bottom: 20px;">
                        <h3 style="color: var(--primary-color); margin-bottom: 15px;">小说设定</h3>
                        <div class="content-preview">
                            <pre>${novel.settings}</pre>
                        </div>
                    </div>
                ` : ''}

                ${novel.outline ? `
                    <div style="margin-bottom: 20px;">
                        <h3 style="color: var(--primary-color); margin-bottom: 15px;">大纲</h3>
                        <div class="content-preview">
                            <pre>${novel.outline}</pre>
                        </div>
                    </div>
                ` : ''}

                <div>
                    <h3 style="color: var(--primary-color); margin-bottom: 15px;">章节列表 (${chapters.length}章)</h3>
                    <div class="chapter-list">
                        ${chapters.map(ch => `
                            <div class="chapter-item">
                                <div class="chapter-header">
                                    <span class="chapter-title">第${ch.chapter_number}章: ${ch.title}</span>
                                    <span class="chapter-status">${utils.getStatusText(ch.status)}</span>
                                </div>
                                <div class="chapter-info">字数: ${utils.formatNumber(ch.word_count || 0)}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;

            modal.classList.add('active');
        } catch (error) {
            console.error('加载详情失败:', error);
            utils.showMessage('加载详情失败: ' + error.message);
        }
    },

    // 查看日志
    async viewLogs(novelId) {
        try {
            const logs = await api.novels.getLogs(novelId);

            const modal = document.getElementById('logsModal');
            const content = document.getElementById('logsContent');

            content.innerHTML = logs.map(log => `
                <div class="log-entry ${log.level}" style="padding: 12px; margin-bottom: 10px; border-left: 4px solid var(--primary-color); background: #f8f9fa; border-radius: 5px;">
                    <div style="font-size: 0.85em; color: #999; margin-bottom: 5px;">
                        ${utils.formatDate(log.created_at)}
                    </div>
                    <div><strong>${log.stage}</strong>: ${log.message}</div>
                </div>
            `).join('') || '<p style="text-align: center; color: #999; padding: 40px;">暂无日志</p>';

            modal.classList.add('active');
        } catch (error) {
            console.error('加载日志失败:', error);
            utils.showMessage('加载日志失败: ' + error.message);
        }
    },

    // 导出小说
    async exportNovel(novelId) {
        try {
            await api.novels.export(novelId);
            utils.showMessage('导出成功！');
        } catch (error) {
            console.error('导出失败:', error);
            utils.showMessage('导出失败: ' + error.message);
        }
    },

    // 下载小说
    downloadNovel(novelId) {
        window.open(`${API_BASE.replace('/api', '')}/api/novels/${novelId}/download`, '_blank');
    },

    // 删除小说
    async deleteNovel(novelId) {
        if (!utils.confirm('确定要删除这部小说吗？')) return;

        try {
            await api.novels.delete(novelId);
            utils.showMessage('删除成功！');
            this.loadNovels();
            if (window.app) window.app.loadStats();
        } catch (error) {
            console.error('删除失败:', error);
            utils.showMessage('删除失败: ' + error.message);
        }
    }
};

// 导出到全局
window.novelManager = novelManager;
