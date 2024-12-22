/**
 * User selection functionality for admin module
 * This module provides reusable functions for user selection dropdowns
 */

class UserSelect {
    /**
     * Initialize user selection functionality
     * @param {string} selector - jQuery selector for the select element
     * @param {Object} options - Configuration options
     */
    constructor(selector, options = {}) {
        this.selector = selector;
        this.options = {
            placeholder: options.placeholder || 'Select user...',
            multiple: options.multiple || false,
            roleId: options.roleId || null,  // For filtering users by role
            excludeRoleId: options.excludeRoleId || null,  // For excluding users with specific role
            limit: options.limit || null,
            allowClear: options.allowClear !== undefined ? options.allowClear : true,
            dropdownParent: options.dropdownParent || null,
            onChange: options.onChange || null,
            templateResult: options.templateResult || this.formatUser,
            templateSelection: options.templateSelection || this.formatUserSelection,
            ...options
        };
        
        this.init();
    }

    /**
     * Initialize the Select2 dropdown
     */
    init() {
        const self = this;
        
        $(this.selector).select2({
            placeholder: this.options.placeholder,
            allowClear: this.options.allowClear,
            multiple: this.options.multiple,
            dropdownParent: this.options.dropdownParent,
            ajax: {
                url: '/admin/api/users/search',
                dataType: 'json',
                delay: 250,
                data: function(params) {
                    return {
                        term: params.term,
                        page: params.page || 1,
                        role_id: self.options.roleId,
                        exclude_role_id: self.options.excludeRoleId,
                        limit: self.options.limit
                    };
                },
                processResults: function(data, params) {
                    params.page = params.page || 1;
                    return {
                        results: data.results,
                        pagination: data.pagination
                    };
                },
                cache: true
            },
            templateResult: this.options.templateResult,
            templateSelection: this.options.templateSelection,
            escapeMarkup: function(markup) {
                return markup;
            },
            minimumInputLength: 0
        });

        // Bind change event if callback provided
        if (this.options.onChange) {
            $(this.selector).on('change', this.options.onChange);
        }

        // Initialize tooltips for user info
        this.initTooltips();
    }

    /**
     * Format user for dropdown results
     * @param {Object} user - User data
     * @returns {string} HTML string
     */
    formatUser(user) {
        if (user.loading) return user.text;
        
        const avatar = user.avatar_url
            ? `<img src="${user.avatar_url}" class="user-avatar-sm mr-2" alt="${user.text}">`
            : '<i class="fas fa-user mr-2"></i>';
        
        return `
            <div class="d-flex align-items-center">
                ${avatar}
                <div>
                    <div class="font-weight-bold">${user.text}</div>
                    ${user.email ? `<small class="text-muted">${user.email}</small>` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Format user for selected option
     * @param {Object} user - User data
     * @returns {string} HTML string
     */
    formatUserSelection(user) {
        if (!user.id) return user.text;
        
        const avatar = user.avatar_url
            ? `<img src="${user.avatar_url}" class="user-avatar-xs mr-1" alt="${user.text}">`
            : '<i class="fas fa-user mr-1"></i>';
        
        return `
            <div class="d-flex align-items-center">
                ${avatar}
                <span>${user.text}</span>
            </div>
        `;
    }

    /**
     * Initialize tooltips for user info
     */
    initTooltips() {
        const self = this;
        
        $(this.selector).on('select2:open', function() {
            setTimeout(() => {
                $('.select2-results__option').each(function() {
                    const $option = $(this);
                    if (!$option.data('tooltip-initialized')) {
                        $option.tooltip({
                            title: 'Click to select user',
                            placement: 'left'
                        });
                        $option.data('tooltip-initialized', true);
                    }
                });
            }, 100);
        });
    }

    /**
     * Get selected user(s)
     * @returns {Array|Object} Selected user data
     */
    getSelected() {
        return $(this.selector).select2('data');
    }

    /**
     * Set selected user(s)
     * @param {string|Array} value - User ID(s) to select
     */
    setSelected(value) {
        $(this.selector).val(value).trigger('change');
    }

    /**
     * Clear selection
     */
    clear() {
        $(this.selector).val(null).trigger('change');
    }

    /**
     * Enable/disable the select
     * @param {boolean} enabled - Whether to enable or disable
     */
    setEnabled(enabled) {
        $(this.selector).prop('disabled', !enabled);
    }

    /**
     * Refresh the dropdown options
     */
    refresh() {
        $(this.selector).select2('destroy');
        this.init();
    }

    /**
     * Update configuration options
     * @param {Object} options - New options
     */
    updateOptions(options) {
        this.options = { ...this.options, ...options };
        this.refresh();
    }

    /**
     * Destroy the Select2 instance
     */
    destroy() {
        $(this.selector).select2('destroy');
    }
}

// Add to global scope
window.UserSelect = UserSelect;

// CSS styles for user selection
$('<style>')
    .text(`
        .user-avatar-sm {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            object-fit: cover;
        }
        .user-avatar-xs {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            object-fit: cover;
        }
        .select2-container--bootstrap4 .select2-results__option {
            padding: 0.5rem;
            border-bottom: 1px solid #dee2e6;
        }
        .select2-container--bootstrap4 .select2-results__option:last-child {
            border-bottom: none;
        }
        .select2-container--bootstrap4 .select2-results__option--highlighted {
            background-color: #e9ecef;
            color: #000;
        }
        .select2-container--bootstrap4 .select2-results__option[aria-selected=true] {
            background-color: #007bff;
            color: #fff;
        }
    `)
    .appendTo('head');

// Example usage:
/*
const userSelect = new UserSelect('#user-select', {
    placeholder: 'Select user...',
    multiple: true,
    roleId: 1,  // Optional: filter by role
    excludeRoleId: 2,  // Optional: exclude users with role
    onChange: function(e) {
        console.log('Selected users:', $(this).select2('data'));
    }
});
*/
