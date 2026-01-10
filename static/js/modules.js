// Token统计管理模块
const tokenManager = {
    // 加载Token统计
    async loadTokenStats() {
        try {
            const days = document.getElementById('tokenDays').value;
            const novelId = document.getElementById('tokenNovelFilter').value;

            const params = { days };
            if (novelId) params.novel_id = novelId;

            const data = await api.stats.getTokenStats(params);

            // 计算总计
            let totalTokens = 0, totalPrompt = 0, totalCompletion = 0, totalCost = 0;
            data.usages.forEach(u => {
                totalTokens += u.total_tokens || 0;
                totalPrompt += u.prompt_tokens || 0;
                totalCompletion += u.completion_tokens || 0;
                totalCost += u.cost || 0;
            });

            // 更新统计卡片
            document.getElementById('tokenStatsTotal').textContent = utils.formatNumber(totalTokens);
            document.getElementById('tokenStatsPrompt').textContent = utils.formatNumber(totalPrompt);
            document.getElementById('tokenStatsCompletion').textContent = utils.formatNumber(totalCompletion);
            document.getElementById('tokenStatsCost').textContent = `$${totalCost.toFixed(2)}`;

            // 按阶段统计表格
            this.renderStageStats(data.stage_stats);

            // 按日期趋势表格
            this.renderDailyStats(data.daily_stats);

            // 详细记录列表
            this.renderUsagesList(data.usages);
        } catch (error) {
            console.error('加载Token统计失败:', error);
        }
    },

    // 渲染阶段统计
    renderStageStats(stats) {
        const stageNames = {
            'settings': '小说设定',
            'outline': '大纲生成',
            'detailed_outline': '细纲生成',
            'content': '内容生成',
            'check': '质量检查'
        };

        const html = `
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: rgba(245, 247, 250, 0.8);">
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid var(--border-color);">阶段</th>
                        <th style="padding: 12px; text-align: right; border-bottom: 2px solid var(--border-color);">Token数</th>
                        <th style="padding: 12px; text-align: right; border-bottom: 2px solid var(--border-color);">费用</th>
                        <th style="padding: 12px; text-align: right; border-bottom: 2px solid var(--border-color);">调用次数</th>
                    </tr>
                </thead>
                <tbody>
                    ${stats.map(stat => `
                        <tr style="border-bottom: 1px solid #f0f0f0;">
                            <td style="padding: 12px;">${stageNames[stat.stage] || stat.stage}</td>
                            <td style="padding: 12px; text-align: right; font-weight: 600;">${utils.formatNumber(stat.total_tokens)}</td>
                            <td style="padding: 12px; text-align: right; color: var(--primary-color);">$${stat.total_cost.toFixed(4)}</td>
                            <td style="padding: 12px; text-align: right;">${stat.count}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        document.getElementById('stageStatsTable').innerHTML = html;
    },

    // 渲染日期统计
    renderDailyStats(stats) {
        const html = `
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: rgba(245, 247, 250, 0.8);">
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid var(--border-color);">日期</th>
                        <th style="padding: 12px; text-align: right; border-bottom: 2px solid var(--border-color);">Token数</th>
                        <th style="padding: 12px; text-align: right; border-bottom: 2px solid var(--border-color);">费用</th>
                    </tr>
                </thead>
                <tbody>
                    ${stats.map(stat => `
                        <tr style="border-bottom: 1px solid #f0f0f0;">
                            <td style="padding: 12px;">${stat.date}</td>
                            <td style="padding: 12px; text-align: right; font-weight: 600;">${utils.formatNumber(stat.total_tokens)}</td>
                            <td style="padding: 12px; text-align: right; color: var(--primary-color);">$${stat.total_cost.toFixed(4)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        document.getElementById('dailyStatsTable').innerHTML = html;
    },

    // 渲染使用记录列表
    renderUsagesList(usages) {
        const stageNames = {
            'settings': '小说设定',
            'outline': '大纲生成',
            'detailed_outline': '细纲生成',
            'content': '内容生成',
            'check': '质量检查'
        };

        const html = usages.slice(0, 50).map(usage => `
            <div style="border-bottom: 1px solid #f0f0f0; padding: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <strong style="color: var(--text-color);">${stageNames[usage.stage] || usage.stage} - ${usage.operation}</strong>
                    <span style="color: var(--text-secondary); font-size: 0.9em;">${utils.formatDate(usage.created_at)}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.9em; color: var(--text-secondary);">
                    <span>Token: ${utils.formatNumber(usage.total_tokens)} (输入: ${utils.formatNumber(usage.prompt_tokens)}, 输出: ${utils.formatNumber(usage.completion_tokens)})</span>
                    <span>费用: $${usage.cost.toFixed(4)} | 耗时: ${usage.duration ? usage.duration.toFixed(2) + 's' : '-'}</span>
                </div>
                ${usage.chapter_number ? `<div style="font-size: 0.85em; color: #999; margin-top: 5px;">第${usage.chapter_number}章</div>` : ''}
            </div>
        `).join('') || '<p style="text-align: center; color: var(--text-secondary); padding: 40px;">暂无数据</p>';

        document.getElementById('tokenUsagesList').innerHTML = html;
    },

    // 加载小说列表用于筛选
    async loadNovelListForFilter() {
        try {
            const novels = await api.novels.getAll();
            const select = document.getElementById('tokenNovelFilter');

            select.innerHTML = '<option value="">全部小说</option>' +
                novels.map(novel => `<option value="${novel.id}">${novel.title || '未命名小说'}</option>`).join('');
        } catch (error) {
            console.error('加载小说列表失败:', error);
        }
    }
};

// AI配置管理模块
const configManager = {
    // 加载配置列表
    async loadConfigs() {
        try {
            const configs = await api.configs.getAll();
            const container = document.getElementById('configsList');

            if (configs.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <h3>还没有配置</h3>
                        <p>点击"添加新配置"开始设置AI模型</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = configs.map(config => {
                const typeLabels = {
                    'both': '通用',
                    'generation': '生成',
                    'check': '校验'
                };
                const typeColors = {
                    'both': 'var(--primary-color)',
                    'generation': 'var(--success-color)',
                    'check': 'var(--warning-color)'
                };
                const typeLabel = typeLabels[config.config_type] || '通用';
                const typeColor = typeColors[config.config_type] || 'var(--primary-color)';

                return `
                <div class="novel-card ${config.is_active ? 'active' : ''}" style="${config.is_active ? 'border-color: var(--success-color);' : ''}">
                    <div class="novel-card-header">
                        <div class="novel-title">
                            ${config.name}
                            ${config.is_active ? '<span style="color: var(--success-color); margin-left: 10px;">✓ 当前使用</span>' : ''}
                        </div>
                        <span style="padding: 4px 12px; background: ${typeColor}15; color: ${typeColor}; border-radius: 12px; font-size: 0.85em; font-weight: 600;">
                            ${typeLabel}
                        </span>
                    </div>
                    <div class="novel-info">
                        <div>API: ${config.api_base}</div>
                        <div>模型: ${config.model_name}</div>
                    </div>
                    <div class="novel-actions">
                        ${!config.is_active ? `
                            <button class="btn btn-success" onclick="configManager.activateConfig(${config.id})">
                                激活
                            </button>
                        ` : ''}
                        <button class="btn btn-secondary" onclick="configManager.editConfig(${config.id})">
                            编辑
                        </button>
                        <button class="btn btn-danger" onclick="configManager.deleteConfig(${config.id})">
                            删除
                        </button>
                    </div>
                </div>
            `}).join('');
        } catch (error) {
            console.error('加载配置失败:', error);
        }
    },

    // 添加配置
    async addConfig(formData) {
        try {
            await api.configs.create(formData);
            utils.showMessage('配置添加成功！');
            this.loadConfigs();
        } catch (error) {
            console.error('添加配置失败:', error);
            utils.showMessage('添加失败: ' + error.message);
        }
    },

    // 编辑配置
    async editConfig(configId) {
        try {
            // 获取配置详情
            const response = await fetch(`${API_BASE}/ai-configs`);
            const configs = await response.json();
            const config = configs.find(c => c.id === configId);

            if (!config) {
                utils.showMessage('配置不存在');
                return;
            }

            // 填充表单
            document.getElementById('editConfigId').value = config.id;
            document.getElementById('editConfigName').value = config.name;
            document.getElementById('editConfigApiBase').value = config.api_base;
            document.getElementById('editConfigApiKey').value = ''; // 密钥不显示
            document.getElementById('editConfigModelName').value = config.model_name;
            document.getElementById('editConfigType').value = config.config_type || 'both';

            // 显示编辑模态框
            app.showModal('editConfigModal');
        } catch (error) {
            console.error('加载配置失败:', error);
            utils.showMessage('加载配置失败: ' + error.message);
        }
    },

    // 更新配置
    async updateConfig(configId, formData) {
        try {
            await api.configs.update(configId, formData);
            utils.showMessage('配置更新成功！');
            this.loadConfigs();
        } catch (error) {
            console.error('更新配置失败:', error);
            utils.showMessage('更新失败: ' + error.message);
        }
    },

    // 激活配置
    async activateConfig(configId) {
        try {
            await api.configs.activate(configId);
            utils.showMessage('配置已激活！');
            this.loadConfigs();
        } catch (error) {
            console.error('激活配置失败:', error);
            utils.showMessage('激活失败: ' + error.message);
        }
    },

    // 删除配置
    async deleteConfig(configId) {
        if (!utils.confirm('确定要删除这个配置吗？')) return;

        try {
            await api.configs.delete(configId);
            utils.showMessage('删除成功！');
            this.loadConfigs();
        } catch (error) {
            console.error('删除配置失败:', error);
            utils.showMessage('删除失败: ' + error.message);
        }
    }
};

// 导出到全局
window.tokenManager = tokenManager;
window.configManager = configManager;
