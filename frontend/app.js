// DocuScan Frontend Application
class DocuScanApp {
    constructor() {
        this.apiBaseUrl = '/api/v1';
        this.currentSection = 'dashboard';
        this.documents = [];
        this.currentSearch = {};
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupNavigation();
        this.setupFileUpload();
        this.checkHealth();
        
        // Load initial data
        await this.loadDashboard();
        await this.loadDocuments();
        
        // Start health monitoring
        setInterval(() => this.checkHealth(), 30000);
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.target.getAttribute('href').substring(1);
                this.showSection(section);
            });
        });

        // Upload button
        document.getElementById('upload-btn').addEventListener('click', () => {
            this.uploadDocument();
        });

        // Search functionality
        document.getElementById('search-btn').addEventListener('click', () => {
            this.performSearch();
        });

        document.getElementById('clear-search-btn').addEventListener('click', () => {
            this.clearSearch();
        });

        // Export functionality
        document.getElementById('export-json-btn').addEventListener('click', () => {
            this.exportDocuments('json');
        });

        document.getElementById('export-csv-btn').addEventListener('click', () => {
            this.exportDocuments('csv');
        });

        // Modal close
        document.getElementById('close-modal').addEventListener('click', () => {
            this.closeModal();
        });

        // Search on enter key
        document.getElementById('search-query').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });
    }

    setupNavigation() {
        // Set initial active state
        this.showSection(this.currentSection);
    }

    setupFileUpload() {
        const fileInput = document.getElementById('file-upload');
        const uploadArea = fileInput.closest('.border-dashed');

        // File input change
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleFileSelection(file);
            }
        });

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelection(files[0]);
            }
        });
    }

    handleFileSelection(file) {
        // Validate file size
        const maxSize = 50 * 1024 * 1024; // 50MB
        if (file.size > maxSize) {
            this.showToast('File too large. Maximum size is 50MB.', 'error');
            return;
        }

        // Validate file type
        const allowedTypes = ['.pdf', '.docx', '.doc', '.txt', '.png', '.jpg', '.jpeg'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            this.showToast(`File type ${fileExtension} not supported.`, 'error');
            return;
        }

        // Update UI to show selected file
        const uploadArea = document.querySelector('.border-dashed');
        uploadArea.innerHTML = `
            <div class="space-y-1 text-center">
                <i class="fas fa-file text-4xl text-blue-500 mb-4"></i>
                <div class="text-sm text-gray-600">
                    <p class="font-medium">${file.name}</p>
                    <p class="text-xs">${this.formatFileSize(file.size)}</p>
                </div>
                <button type="button" class="text-blue-600 hover:text-blue-500 text-sm" onclick="location.reload()">
                    Choose different file
                </button>
            </div>
        `;
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });

        // Show selected section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.add('active');
            this.currentSection = sectionName;
        }

        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        const activeLink = document.querySelector(`.nav-link[href="#${sectionName}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }

        // Load section-specific data
        if (sectionName === 'documents') {
            this.loadDocuments();
        } else if (sectionName === 'dashboard') {
            this.loadDashboard();
        }
    }

    async checkHealth() {
        try {
            const response = await fetch('/health');
            const health = await response.json();
            
            const statusElement = document.getElementById('health-status');
            const isHealthy = health.status === 'healthy';
            
            statusElement.innerHTML = `
                <i class="fas fa-circle ${isHealthy ? 'text-green-400' : 'text-red-400'} mr-1"></i>
                ${isHealthy ? 'System Online' : 'System Issues'}
            `;
            
            if (!isHealthy) {
                console.warn('System health check failed:', health);
            }
        } catch (error) {
            console.error('Health check failed:', error);
            const statusElement = document.getElementById('health-status');
            statusElement.innerHTML = `
                <i class="fas fa-circle text-red-400 mr-1"></i>
                System Offline
            `;
        }
    }

    async uploadDocument() {
        const fileInput = document.getElementById('file-upload');
        const file = fileInput.files[0];
        
        if (!file) {
            this.showToast('Please select a file to upload.', 'error');
            return;
        }

        const uploadBtn = document.getElementById('upload-btn');
        const progressDiv = document.getElementById('upload-progress');
        const progressBar = document.getElementById('progress-bar');
        const statusText = document.getElementById('upload-status');

        // Show progress
        uploadBtn.disabled = true;
        uploadBtn.classList.add('btn-loading');
        progressDiv.classList.remove('hidden');

        try {
            const formData = new FormData();
            formData.append('file', file);
            
            // Add optional metadata
            const caseType = document.getElementById('case-type').value;
            const clientName = document.getElementById('client-name').value;
            const urgencyLevel = document.getElementById('urgency-level').value;
            
            if (caseType) formData.append('case_type', caseType);
            if (clientName) formData.append('client_name', clientName);
            if (urgencyLevel) formData.append('urgency_level', urgencyLevel);

            const response = await fetch(`${this.apiBaseUrl}/documents/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            const result = await response.json();
            
            // Animate progress to 100%
            progressBar.style.width = '100%';
            statusText.textContent = 'Upload complete!';
            
            this.showToast(`Document "${result.filename}" uploaded successfully!`, 'success');
            
            // Reset form after delay
            setTimeout(() => {
                this.resetUploadForm();
                this.loadDocuments(); // Refresh document list
                this.loadDashboard(); // Refresh dashboard stats
            }, 2000);

        } catch (error) {
            console.error('Upload error:', error);
            statusText.textContent = 'Upload failed!';
            this.showToast(`Upload failed: ${error.message}`, 'error');
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.classList.remove('btn-loading');
        }
    }

    resetUploadForm() {
        // Reset file input
        document.getElementById('file-upload').value = '';
        
        // Reset form fields
        document.getElementById('case-type').value = '';
        document.getElementById('client-name').value = '';
        document.getElementById('urgency-level').value = 'medium';
        
        // Hide progress
        document.getElementById('upload-progress').classList.add('hidden');
        document.getElementById('progress-bar').style.width = '0%';
        
        // Reset upload area
        location.reload(); // Simple way to reset the drag-drop area
    }

    async loadDashboard() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/documents/statistics/dashboard`);
            const stats = await response.json();
            
            // Update statistics cards
            document.getElementById('total-documents').textContent = stats.total_documents || 0;
            
            const highPriorityCount = (stats.urgency_levels?.high || 0) + (stats.urgency_levels?.critical || 0);
            document.getElementById('high-priority-count').textContent = highPriorityCount;
            
            document.getElementById('case-types-count').textContent = Object.keys(stats.case_types || {}).length;
            document.getElementById('active-clients-count').textContent = Object.keys(stats.top_clients || {}).length;
            
            // Update charts (simplified visualization)
            this.updateCharts(stats);
            
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        }
    }

    updateCharts(stats) {
        // Case types chart
        const caseTypesChart = document.getElementById('case-types-chart');
        if (stats.case_types && Object.keys(stats.case_types).length > 0) {
            caseTypesChart.innerHTML = this.createSimpleBarChart(stats.case_types, 'Case Types');
        }

        // Timeline chart
        const timelineChart = document.getElementById('timeline-chart');
        if (stats.documents_by_date && Object.keys(stats.documents_by_date).length > 0) {
            timelineChart.innerHTML = this.createTimelineChart(stats.documents_by_date);
        }
    }

    createSimpleBarChart(data, title) {
        const maxValue = Math.max(...Object.values(data));
        let html = '<div class="space-y-2">';
        
        Object.entries(data).forEach(([key, value]) => {
            const percentage = (value / maxValue) * 100;
            const displayKey = key.replace('_', ' ').toUpperCase();
            
            html += `
                <div class="flex items-center space-x-2">
                    <div class="w-20 text-xs font-medium text-gray-600">${displayKey}</div>
                    <div class="flex-1 bg-gray-200 rounded-full h-4">
                        <div class="bg-blue-500 h-4 rounded-full" style="width: ${percentage}%"></div>
                    </div>
                    <div class="w-8 text-xs text-gray-600">${value}</div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }

    createTimelineChart(data) {
        const maxValue = Math.max(...Object.values(data));
        let html = '<div class="flex items-end justify-between h-32 space-x-1">';
        
        Object.entries(data).slice(-7).forEach(([date, count]) => {
            const height = (count / maxValue) * 100;
            const shortDate = new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            
            html += `
                <div class="flex flex-col items-center">
                    <div class="bg-blue-500 rounded-t" style="height: ${height}%; width: 20px; min-height: 4px;"></div>
                    <div class="text-xs text-gray-600 mt-1 transform rotate-45 origin-left">${shortDate}</div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }

    async loadDocuments(searchParams = {}) {
        const loadingState = document.getElementById('loading-state');
        const emptyState = document.getElementById('empty-state');
        const resultsContainer = document.getElementById('search-results');

        // Show loading state
        loadingState.classList.remove('hidden');
        emptyState.classList.add('hidden');
        resultsContainer.innerHTML = '';

        try {
            const queryParams = new URLSearchParams(searchParams);
            queryParams.set('limit', '20');
            
            const response = await fetch(`${this.apiBaseUrl}/documents/search?${queryParams}`);
            const data = await response.json();
            
            this.documents = data.documents || [];
            
            // Hide loading state
            loadingState.classList.add('hidden');
            
            if (this.documents.length === 0) {
                emptyState.classList.remove('hidden');
                return;
            }
            
            // Render documents
            this.renderDocuments(this.documents);
            
        } catch (error) {
            console.error('Failed to load documents:', error);
            loadingState.classList.add('hidden');
            this.showToast('Failed to load documents.', 'error');
        }
    }

    renderDocuments(documents) {
        const container = document.getElementById('search-results');
        
        container.innerHTML = documents.map(doc => this.createDocumentCard(doc)).join('');
        
        // Add click handlers
        container.querySelectorAll('.document-card').forEach((card, index) => {
            card.addEventListener('click', () => {
                this.showDocumentModal(documents[index]);
            });
        });
    }

    createDocumentCard(doc) {
        const caseTypeBadge = doc.case_type ? 
            `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium badge-${doc.case_type}">
                ${doc.case_type.replace('_', ' ').toUpperCase()}
            </span>` : '';
        
        const urgencyBadge = `
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium urgency-${doc.urgency_level}">
                ${doc.urgency_level.toUpperCase()}
            </span>
        `;
        
        const statusBadge = `
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium status-${doc.status}">
                ${doc.status.toUpperCase()}
            </span>
        `;

        const tags = doc.tags ? doc.tags.slice(0, 3).map(tag => 
            `<span class="tag">${tag}</span>`
        ).join('') : '';

        const confidenceScore = doc.confidence_scores?.case_type || 0;
        const confidenceClass = confidenceScore > 0.8 ? 'confidence-high' : 
                               confidenceScore > 0.5 ? 'confidence-medium' : 'confidence-low';

        return `
            <div class="document-card bg-white shadow rounded-lg p-6 cursor-pointer">
                <div class="flex justify-between items-start mb-4">
                    <div class="flex-1">
                        <h3 class="text-lg font-medium text-gray-900 mb-1">${doc.original_filename}</h3>
                        <p class="text-sm text-gray-500">${doc.client_name || 'No client specified'}</p>
                    </div>
                    <div class="flex flex-col space-y-1">
                        ${statusBadge}
                        ${urgencyBadge}
                    </div>
                </div>
                
                <div class="mb-4">
                    <p class="text-gray-600 text-sm truncate-3">${doc.summary || 'No summary available'}</p>
                </div>
                
                <div class="flex justify-between items-center">
                    <div class="flex space-x-2">
                        ${caseTypeBadge}
                        ${tags}
                    </div>
                    <div class="text-xs text-gray-500">
                        ${new Date(doc.created_at).toLocaleDateString()}
                    </div>
                </div>
                
                ${confidenceScore > 0 ? `
                    <div class="mt-3">
                        <div class="flex justify-between text-xs text-gray-500 mb-1">
                            <span>Classification Confidence</span>
                            <span>${Math.round(confidenceScore * 100)}%</span>
                        </div>
                        <div class="confidence-bar bg-gray-200 rounded-full">
                            <div class="confidence-bar ${confidenceClass} rounded-full" style="width: ${confidenceScore * 100}%"></div>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    showDocumentModal(doc) {
        const modal = document.getElementById('document-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalContent = document.getElementById('modal-content');
        
        modalTitle.textContent = doc.original_filename;
        
        const entities = doc.extracted_entities || {};
        const entitiesHtml = Object.entries(entities)
            .filter(([key, values]) => values && values.length > 0)
            .map(([key, values]) => `
                <div class="mb-2">
                    <span class="font-medium text-gray-700">${key}:</span>
                    <span class="text-gray-600">${values.join(', ')}</span>
                </div>
            `).join('');

        modalContent.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <h4 class="text-lg font-medium text-gray-900 mb-3">Document Information</h4>
                    <div class="space-y-2 text-sm">
                        <div><span class="font-medium">File:</span> ${doc.original_filename}</div>
                        <div><span class="font-medium">Size:</span> ${this.formatFileSize(doc.file_size)}</div>
                        <div><span class="font-medium">Type:</span> ${doc.mime_type}</div>
                        <div><span class="font-medium">Uploaded:</span> ${new Date(doc.created_at).toLocaleString()}</div>
                        <div><span class="font-medium">Status:</span> ${doc.status.toUpperCase()}</div>
                    </div>
                </div>
                
                <div>
                    <h4 class="text-lg font-medium text-gray-900 mb-3">Classification</h4>
                    <div class="space-y-2 text-sm">
                        <div><span class="font-medium">Case Type:</span> ${doc.case_type ? doc.case_type.replace('_', ' ').toUpperCase() : 'Not classified'}</div>
                        <div><span class="font-medium">Client:</span> ${doc.client_name || 'Not specified'}</div>
                        <div><span class="font-medium">Urgency:</span> ${doc.urgency_level.toUpperCase()}</div>
                        <div><span class="font-medium">Tags:</span> ${doc.tags ? doc.tags.join(', ') : 'None'}</div>
                    </div>
                </div>
            </div>
            
            ${doc.summary ? `
                <div class="mt-6">
                    <h4 class="text-lg font-medium text-gray-900 mb-3">Summary</h4>
                    <p class="text-gray-600">${doc.summary}</p>
                </div>
            ` : ''}
            
            ${entitiesHtml ? `
                <div class="mt-6">
                    <h4 class="text-lg font-medium text-gray-900 mb-3">Extracted Entities</h4>
                    <div class="text-sm space-y-1">
                        ${entitiesHtml}
                    </div>
                </div>
            ` : ''}
        `;
        
        modal.classList.remove('hidden');
    }

    closeModal() {
        document.getElementById('document-modal').classList.add('hidden');
    }

    async performSearch() {
        const query = document.getElementById('search-query').value;
        const caseType = document.getElementById('filter-case-type').value;
        const urgency = document.getElementById('filter-urgency').value;
        
        const searchParams = {};
        if (query) searchParams.query = query;
        if (caseType) searchParams.case_type = caseType;
        if (urgency) searchParams.urgency_level = urgency;
        
        this.currentSearch = searchParams;
        await this.loadDocuments(searchParams);
        
        // Switch to documents section if not already there
        if (this.currentSection !== 'documents') {
            this.showSection('documents');
        }
    }

    clearSearch() {
        document.getElementById('search-query').value = '';
        document.getElementById('filter-case-type').value = '';
        document.getElementById('filter-urgency').value = '';
        
        this.currentSearch = {};
        this.loadDocuments();
    }

    async exportDocuments(format) {
        try {
            const queryParams = new URLSearchParams(this.currentSearch);
            queryParams.set('format', format);
            
            const response = await fetch(`${this.apiBaseUrl}/documents/export/search?${queryParams}`);
            
            if (!response.ok) {
                throw new Error('Export failed');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `documents_export.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            this.showToast(`Documents exported as ${format.toUpperCase()}`, 'success');
            
        } catch (error) {
            console.error('Export error:', error);
            this.showToast('Export failed', 'error');
        }
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toastId = 'toast-' + Date.now();
        
        const typeClasses = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            warning: 'bg-yellow-500 text-black',
            info: 'bg-blue-500 text-white'
        };
        
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast p-4 rounded-lg shadow-lg ${typeClasses[type]} max-w-sm`;
        toast.innerHTML = `
            <div class="flex items-center">
                <span class="flex-1">${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-lg">&times;</button>
            </div>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            const toastElement = document.getElementById(toastId);
            if (toastElement) {
                toastElement.classList.add('removing');
                setTimeout(() => toastElement.remove(), 300);
            }
        }, 5000);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DocuScanApp();
});