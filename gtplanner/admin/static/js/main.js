/*
GTPlanner Admin - Main JavaScript
后台管理界面主脚本
*/

// 全局配置
const CONFIG = {
    apiBaseUrl: '/admin/api',
    refreshInterval: 30000, // 30秒自动刷新
};

// 工具函数
const Utils = {
    /**
     * 格式化日期时间
     */
    formatDateTime: (dateString) => {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    },

    /**
     * 格式化文件大小
     */
    formatFileSize: (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    },

    /**
     * 显示提示消息
     */
    showAlert: (message, type = 'info') => {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const container = document.querySelector('.content');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);

            // 5秒后自动关闭
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }
    },

    /**
     * 确认对话框
     */
    confirm: (message, callback) => {
        if (window.confirm(message)) {
            callback();
        }
    },

    /**
     * 加载动画
     */
    showLoading: (element) => {
        if (element) {
            element.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div>';
        }
    },
};

// API 请求
const API = {
    /**
     * 获取系统统计信息
     */
    async getStats() {
        try {
            const response = await fetch(`${CONFIG.apiBaseUrl}/stats`);
            if (!response.ok) throw new Error('获取统计信息失败');
            return await response.json();
        } catch (error) {
            console.error('Error fetching stats:', error);
            throw error;
        }
    },

    /**
     * 获取日志文件列表
     */
    async getLogFiles() {
        try {
            const response = await fetch(`${CONFIG.apiBaseUrl}/logs`);
            if (!response.ok) throw new Error('获取日志文件列表失败');
            const data = await response.json();
            return data.files;
        } catch (error) {
            console.error('Error fetching log files:', error);
            throw error;
        }
    },

    /**
     * 获取日志内容
     */
    async getLogContent(filename, lines = 100) {
        try {
            const response = await fetch(`${CONFIG.apiBaseUrl}/logs/${filename}?lines=${lines}`);
            if (!response.ok) throw new Error('获取日志内容失败');
            return await response.json();
        } catch (error) {
            console.error('Error fetching log content:', error);
            throw error;
        }
    },

    /**
     * 删除日志文件
     */
    async deleteLog(filename) {
        try {
            const response = await fetch(`${CONFIG.apiBaseUrl}/logs/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ filename }),
            });
            if (!response.ok) throw new Error('删除日志文件失败');
            return await response.json();
        } catch (error) {
            console.error('Error deleting log:', error);
            throw error;
        }
    },
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('GTPlanner Admin initialized');

    // 初始化所有tooltip
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 初始化所有popover
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // 如果在仪表盘页面，启用自动刷新
    if (window.location.pathname === '/admin/') {
        setInterval(() => {
            console.log('Auto refreshing stats...');
            // TODO: 实现自动刷新统计信息
        }, CONFIG.refreshInterval);
    }
});

// 导出全局对象
window.GTPlannerAdmin = {
    CONFIG,
    Utils,
    API,
};
