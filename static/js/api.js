// API配置和工具函数
const API_BASE = 'http://localhost:5000/api';

// 工具函数
const utils = {
    // 格式化数字（添加千分位）
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    },

    // 格式化日期
    formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN');
    },

    // 获取阶段标签
    getStageLabel(stage) {
        const labels = {
            'settings': '生成设定',
            'outline': '生成大纲',
            'detailed_outline': '生成细纲',
            'content': '生成内容',
            'export': '导出',
            'completed': '已完成'
        };
        return labels[stage] || '准备中';
    },

    // 获取进度百分比
    getProgressPercentage(stage) {
        const stages = {
            'settings': 20,
            'outline': 40,
            'detailed_outline': 60,
            'content': 80,
            'export': 90,
            'completed': 100
        };
        return stages[stage] || 0;
    },

    // 获取状态文本
    getStatusText(status) {
        const statusMap = {
            'pending': '待生成',
            'generating': '生成中',
            'completed': '已完成',
            'failed': '失败'
        };
        return statusMap[status] || status;
    },

    // 显示提示消息
    showMessage(message, type = 'info') {
        // 简单的提示实现，可以后续优化为更好的UI
        alert(message);
    },

    // 确认对话框
    confirm(message) {
        return window.confirm(message);
    }
};

// API调用封装
const api = {
    // 通用GET请求
    async get(url) {
        try {
            const response = await fetch(`${API_BASE}${url}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('API GET Error:', error);
            throw error;
        }
    },

    // 通用POST请求
    async post(url, data) {
        try {
            const response = await fetch(`${API_BASE}${url}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('API POST Error:', error);
            throw error;
        }
    },

    // 通用DELETE请求
    async delete(url) {
        try {
            const response = await fetch(`${API_BASE}${url}`, {
                method: 'DELETE'
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('API DELETE Error:', error);
            throw error;
        }
    },

    // 通用PUT请求
    async put(url, data) {
        try {
            const response = await fetch(`${API_BASE}${url}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('API PUT Error:', error);
            throw error;
        }
    },

    // 小说相关API
    novels: {
        getAll: () => api.get('/novels'),
        getById: (id) => api.get(`/novels/${id}`),
        create: (data) => api.post('/novels', data),
        delete: (id) => api.delete(`/novels/${id}`),
        start: (id) => api.post(`/novels/${id}/start`, {}),
        export: (id) => api.post(`/novels/${id}/export`, {}),
        getChapters: (id) => api.get(`/novels/${id}/chapters`),
        getLogs: (id) => api.get(`/novels/${id}/logs`),
        getTokenStats: (id) => api.get(`/novels/${id}/token-stats`)
    },

    // 统计API
    stats: {
        getGlobal: () => api.get('/stats'),
        getTokenStats: (params) => {
            const query = new URLSearchParams(params).toString();
            return api.get(`/token-stats?${query}`);
        }
    },

    // AI配置API
    configs: {
        getAll: () => api.get('/ai-configs'),
        create: (data) => api.post('/ai-configs', data),
        update: (id, data) => api.put(`/ai-configs/${id}`, data),
        delete: (id) => api.delete(`/ai-configs/${id}`),
        activate: (id) => api.post(`/ai-configs/${id}/activate`, {})
    }
};

// 导出到全局
window.utils = utils;
window.api = api;
