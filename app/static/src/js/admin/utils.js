/**
 * Admin Utilities Module
 * Common utility functions for admin dashboard
 */

export class AdminUtils {
    constructor() {
        this.cache = new Map();
        this.cacheTimeout = 30000; // 30 seconds default cache timeout
    }

    /**
     * Format bytes to human readable string
     * @param {number} bytes - Bytes to format
     * @param {number} decimals - Number of decimal places
     * @returns {string} Formatted string
     */
    formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
    }

    /**
     * Format duration to human readable string
     * @param {Object} duration - Duration object with days, hours, minutes
     * @returns {string} Formatted duration string
     */
    formatDuration(duration) {
        const parts = [];
        if (duration.days) parts.push(`${duration.days}d`);
        if (duration.hours) parts.push(`${duration.hours}h`);
        if (duration.minutes) parts.push(`${duration.minutes}m`);
        return parts.join(' ') || '0m';
    }

    /**
     * Get CSRF token from meta tag
     * @returns {string} CSRF token
     */
    getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.content;
    }

    /**
     * Generate cache key for API request
     * @param {string} url - API URL
     * @param {Object} params - Request parameters
     * @returns {string} Cache key
     */
    generateCacheKey(url, params = {}) {
        return `${url}:${JSON.stringify(params)}`;
    }

    /**
     * Check if cached data is still valid
     * @param {Object} cachedData - Cached data object
     * @returns {boolean} True if cache is valid
     */
    isCacheValid(cachedData) {
        if (!cachedData) return false;
        return (Date.now() - cachedData.timestamp) < this.cacheTimeout;
    }

    /**
     * Fetch data from API with caching
     * @param {string} url - API URL
     * @param {Object} options - Fetch options
     * @param {boolean} useCache - Whether to use cache
     * @returns {Promise<Object>} API response
     */
    async fetchWithCache(url, options = {}, useCache = true) {
        const cacheKey = this.generateCacheKey(url, options);
        
        // Check cache first if enabled
        if (useCache) {
            const cachedData = this.cache.get(cacheKey);
            if (this.isCacheValid(cachedData)) {
                return cachedData.data;
            }
        }

        // Add CSRF token to headers if method is not GET
        if (options.method && options.method !== 'GET') {
            options.headers = {
                ...options.headers,
                'X-CSRF-Token': this.getCsrfToken(),
            };
        }

        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            // Cache the response if caching is enabled
            if (useCache) {
                this.cache.set(cacheKey, {
                    timestamp: Date.now(),
                    data
                });
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    /**
     * Clear cache for specific key or all cache
     * @param {string} cacheKey - Optional cache key to clear
     */
    clearCache(cacheKey = null) {
        if (cacheKey) {
            this.cache.delete(cacheKey);
        } else {
            this.cache.clear();
        }
    }

    /**
     * Show toast notification
     * @param {string} message - Message to display
     * @param {string} type - Notification type (success, error, warning, info)
     */
    showNotification(message, type = 'info') {
        if (typeof toastr !== 'undefined') {
            toastr[type](message);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    /**
     * Show confirmation dialog
     * @param {Object} options - Dialog options
     * @returns {Promise<boolean>} User's choice
     */
    async showConfirmation({
        title = 'Confirm Action',
        text = 'Are you sure?',
        icon = 'warning',
        confirmButtonText = 'Yes',
        cancelButtonText = 'Cancel'
    } = {}) {
        if (typeof Swal !== 'undefined') {
            const result = await Swal.fire({
                title,
                text,
                icon,
                showCancelButton: true,
                confirmButtonText,
                cancelButtonText
            });
            return result.isConfirmed;
        }
        return window.confirm(text);
    }

    /**
     * Initialize DataTable with default configuration
     * @param {string} selector - Table selector
     * @param {Object} options - Additional options
     * @returns {DataTable} Initialized DataTable instance
     */
    initDataTable(selector, options = {}) {
        return $(selector).DataTable({
            responsive: true,
            lengthChange: true,
            autoWidth: false,
            buttons: ["copy", "csv", "excel", "pdf", "print"],
            ...options
        });
    }

    /**
     * Initialize tooltips for elements
     * @param {string} selector - Elements selector
     */
    initTooltips(selector = '[data-toggle="tooltip"]') {
        $(selector).tooltip();
    }
}
