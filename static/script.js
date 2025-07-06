// Global variables
let currentTaskId = null;
let pollInterval = null;
let analysisStartTime = null;
let selectedFiles = {
    file1: null,
    file2: null
};

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        // Show loading screen
        showLoadingScreen();
        
        // Check system status
        await checkSystemHealth();
        
        // Initialize event listeners
        initializeEventListeners();
        
        // Hide loading screen after a delay
        setTimeout(() => {
            hideLoadingScreen();
        }, 2000);
        
    } catch (error) {
        console.error('Initialization error:', error);
        showError('System initialization failed. Please check if the backend is running.');
        hideLoadingScreen();
    }
}

function showLoadingScreen() {
    const loadingScreen = document.getElementById('loadingScreen');
    loadingScreen.classList.remove('hidden');
}

function hideLoadingScreen() {
    const loadingScreen = document.getElementById('loadingScreen');
    loadingScreen.classList.add('hidden');
}

function initializeEventListeners() {
    // File input listeners
    document.getElementById('file1').addEventListener('change', (e) => handleFileSelect(e, 1));
    document.getElementById('file2').addEventListener('change', (e) => handleFileSelect(e, 2));
    
    // Navigation listeners
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', handleNavigation);
    });
    
    // Scroll listener for active nav
    window.addEventListener('scroll', updateActiveNav);
    
    // Modal close listeners
    document.addEventListener('click', handleModalClose);
}

async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            console.log('✅ System is healthy:', data);
            return true;
        } else {
            throw new Error('System health check failed');
        }
    } catch (error) {
        console.error('❌ System health check failed:', error);
        throw error;
    }
}

function handleFileSelect(event, fileNumber) {
    const file = event.target.files[0];
    const uploadBox = document.getElementById(`uploadBox${fileNumber}`);
    const fileInfo = document.getElementById(`file${fileNumber}Info`);
    const uploadContent = uploadBox.querySelector('.upload-content');
    
    if (file) {
        // Validate file
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            showNotification('Please select a PDF file only.', 'error');
            return;
        }
        
        if (file.size > 50 * 1024 * 1024) { // 50MB limit
            showNotification('File size too large. Please select a file under 50MB.', 'error');
            return;
        }
        
        // Store file
        selectedFiles[`file${fileNumber}`] = file;
        
        // Update UI
        uploadBox.classList.add('has-file');
        fileInfo.style.display = 'flex';
        fileInfo.querySelector('.file-name').textContent = file.name;
        fileInfo.querySelector('.file-size').textContent = formatFileSize(file.size);
        uploadContent.querySelector('.btn-upload').style.display = 'none';
        uploadContent.querySelector('p').style.display = 'none';
        
        // Check if both files are selected
        updateAnalyzeButton();
        
        showNotification(`File "${file.name}" selected successfully!`, 'success');
    }
}

function removeFile(fileNumber) {
    const uploadBox = document.getElementById(`uploadBox${fileNumber}`);
    const fileInfo = document.getElementById(`file${fileNumber}Info`);
    const uploadContent = uploadBox.querySelector('.upload-content');
    const fileInput = document.getElementById(`file${fileNumber}`);
    
    // Clear file
    selectedFiles[`file${fileNumber}`] = null;
    fileInput.value = '';
    
    // Update UI
    uploadBox.classList.remove('has-file');
    fileInfo.style.display = 'none';
    uploadContent.querySelector('.btn-upload').style.display = 'inline-flex';
    uploadContent.querySelector('p').style.display = 'block';
    
    updateAnalyzeButton();
    showNotification('File removed.', 'info');
}

function updateAnalyzeButton() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const hasFiles = selectedFiles.file1 && selectedFiles.file2;
    
    analyzeBtn.disabled = !hasFiles;
    
    if (hasFiles) {
        analyzeBtn.innerHTML = '<i class="fas fa-brain"></i><span>Start AI Analysis</span>';
    } else {
        analyzeBtn.innerHTML = '<i class="fas fa-upload"></i><span>Select Both Documents First</span>';
    }
}

async function startAnalysis() {
    if (!selectedFiles.file1 || !selectedFiles.file2) {
        showNotification('Please select both documents first.', 'warning');
        return;
    }
    
    try {
        // Show loading state
        const analyzeBtn = document.getElementById('analyzeBtn');
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Starting Analysis...</span>';
        
        // Prepare form data
        const formData = new FormData();
        formData.append('document1', selectedFiles.file1);
        formData.append('document2', selectedFiles.file2);
        
        // Send analysis request
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Analysis request failed');
        }
        
        const data = await response.json();
        currentTaskId = data.task_id;
        analysisStartTime = new Date();
        
        // Show results section and start polling
        showResultsSection();
        startPolling();
        
        showNotification('AI analysis started successfully!', 'success');
        
    } catch (error) {
        console.error('Analysis start error:', error);
        showNotification(`Failed to start analysis: ${error.message}`, 'error');
        
        // Reset button
        const analyzeBtn = document.getElementById('analyzeBtn');
        analyzeBtn.disabled = false;
        updateAnalyzeButton();
    }
}

function showResultsSection() {
    const resultsSection = document.getElementById('results');
    const progressContainer = document.getElementById('progressContainer');
    const resultsDisplay = document.getElementById('resultsDisplay');
    const errorDisplay = document.getElementById('errorDisplay');
    
    // Show results section
    resultsSection.style.display = 'block';
    
    // Show progress, hide others
    progressContainer.style.display = 'block';
    resultsDisplay.style.display = 'none';
    errorDisplay.style.display = 'none';
    
    // Update task info
    document.getElementById('taskId').textContent = currentTaskId;
    document.getElementById('analysisTime').textContent = new Date().toLocaleString();
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function startPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
    }
    
    pollInterval = setInterval(async () => {
        try {
            await checkAnalysisStatus();
        } catch (error) {
            console.error('Polling error:', error);
            clearInterval(pollInterval);
            showAnalysisError('Connection lost during analysis. Please refresh and try again.');
        }
    }, 3000); // Poll every 3 seconds
}

async function checkAnalysisStatus() {
    if (!currentTaskId) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/status/${currentTaskId}`);
        const data = await response.json();
        
        updateProgressDisplay(data);
        
        if (data.status === 'completed') {
            clearInterval(pollInterval);
            showAnalysisComplete(data);
        } else if (data.status === 'error') {
            clearInterval(pollInterval);
            showAnalysisError(data.error || 'Analysis failed');
        }
        
    } catch (error) {
        console.error('Status check error:', error);
        throw error;
    }
}

function updateProgressDisplay(statusData) {
    const progressTitle = document.getElementById('progressTitle');
    const progressPhase = document.getElementById('progressPhase');
    const progressDetails = document.getElementById('progressDetails');
    const progressFill = document.getElementById('progressFill');
    
    let progressPercentage = 20; // Default progress
    let phaseText = 'Processing...';
    let detailsText = 'AI is analyzing your documents...';
    
    if (statusData.progress) {
        phaseText = statusData.progress.current_phase || phaseText;
        detailsText = statusData.progress.details || detailsText;
        
        // Calculate progress based on phase
        if (phaseText.includes('Phase 1')) progressPercentage = 25;
        else if (phaseText.includes('Phase 2')) progressPercentage = 45;
        else if (phaseText.includes('Phase 3')) progressPercentage = 70;
        else if (phaseText.includes('Phase 4')) progressPercentage = 90;
    }
    
    progressTitle.textContent = 'AI Analysis in Progress';
    progressPhase.textContent = phaseText;
    progressDetails.textContent = detailsText;
    progressFill.style.width = `${progressPercentage}%`;
}

function showAnalysisComplete(data) {
    const progressContainer = document.getElementById('progressContainer');
    const resultsDisplay = document.getElementById('resultsDisplay');
    const downloadBtn = document.getElementById('downloadBtn');
    
    // Hide progress, show results
    progressContainer.style.display = 'none';
    resultsDisplay.style.display = 'block';
    
    // Update summary cards
    document.getElementById('documentsAnalyzed').textContent = '2 Documents Analyzed';
    document.getElementById('complianceScore').textContent = 'Available in Report';
    document.getElementById('requirementsCount').textContent = 'Available in Report';
    
    // Calculate and show analysis time
    if (analysisStartTime) {
        const completionTime = new Date();
        const duration = Math.round((completionTime - analysisStartTime) / 1000);
        const minutes = Math.floor(duration / 60);
        const seconds = duration % 60;
        document.getElementById('analysisCompleteTime').textContent = 
            `${minutes}m ${seconds}s`;
    }
    
    // Enable download button
    downloadBtn.disabled = false;
    
    showNotification('🎉 AI analysis completed! Your comprehensive report is ready.', 'success');
}

function showAnalysisError(errorMessage) {
    const progressContainer = document.getElementById('progressContainer');
    const errorDisplay = document.getElementById('errorDisplay');
    const errorMessageEl = document.getElementById('errorMessage');
    
    // Hide progress, show error
    progressContainer.style.display = 'none';
    errorDisplay.style.display = 'block';
    
    errorMessageEl.textContent = errorMessage;
    
    showNotification('Analysis failed. Please try again.', 'error');
}

async function downloadReport() {
    if (!currentTaskId) {
        showNotification('No report available for download.', 'warning');
        return;
    }
    
    try {
        const downloadBtn = document.getElementById('downloadBtn');
        const originalContent = downloadBtn.innerHTML;
        
        // Show loading state
        downloadBtn.disabled = true;
        downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Preparing Download...</span>';
        
        // Download the report
        const response = await fetch(`${API_BASE_URL}/download/${currentTaskId}`);
        
        if (!response.ok) {
            throw new Error('Failed to download report');
        }
        
        // Create download link
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ai_compliance_analysis_${currentTaskId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        // Restore button
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = originalContent;
        
        showNotification('Report downloaded successfully!', 'success');
        
    } catch (error) {
        console.error('Download error:', error);
        showNotification(`Download failed: ${error.message}`, 'error');
        
        // Restore button
        const downloadBtn = document.getElementById('downloadBtn');
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = '<i class="fas fa-download"></i><span>Download Report</span>';
    }
}

function startNewAnalysis() {
    // Reset everything
    currentTaskId = null;
    analysisStartTime = null;
    selectedFiles = { file1: null, file2: null };
    
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
    
    // Reset UI
    document.getElementById('results').style.display = 'none';
    document.getElementById('file1').value = '';
    document.getElementById('file2').value = '';
    removeFile(1);
    removeFile(2);
    
    // Scroll to upload section
    scrollToUpload();
    
    showNotification('Ready for new analysis!', 'info');
}

// Navigation and scrolling functions
function handleNavigation(event) {
    event.preventDefault();
    const targetId = event.target.getAttribute('href');
    const targetElement = document.querySelector(targetId);
    
    if (targetElement) {
        targetElement.scrollIntoView({ behavior: 'smooth' });
    }
}

function updateActiveNav() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');
    
    let currentSection = '';
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        if (window.scrollY >= sectionTop - 200) {
            currentSection = section.getAttribute('id');
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${currentSection}`) {
            link.classList.add('active');
        }
    });
}

function scrollToUpload() {
    const uploadSection = document.getElementById('upload');
    uploadSection.scrollIntoView({ behavior: 'smooth' });
}

// System status and info functions
async function checkSystemStatus() {
    try {
        showModal('systemStatusModal');
        const statusContent = document.getElementById('systemStatusContent');
        statusContent.innerHTML = '<div class="loading-spinner"></div><p>Checking system status...</p>';
        
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        let statusHtml = '';
        if (data.status === 'healthy') {
            statusHtml = `
                <div style="text-align: center;">
                    <i class="fas fa-check-circle" style="font-size: 48px; color: var(--success-color); margin-bottom: 16px;"></i>
                    <h3 style="color: var(--success-color); margin-bottom: 16px;">System Healthy</h3>
                    <div style="text-align: left;">
                        <p><strong>Version:</strong> ${data.version}</p>
                        <p><strong>System:</strong> ${data.system}</p>
                        <p><strong>AI Powered:</strong> ${data.ai_powered ? 'Yes' : 'No'}</p>
                        <div style="margin-top: 16px;">
                            <h4>Capabilities:</h4>
                            <ul style="margin-left: 20px;">
                                ${data.capabilities.map(cap => `<li>${cap}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        } else {
            statusHtml = `
                <div style="text-align: center;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 48px; color: var(--error-color); margin-bottom: 16px;"></i>
                    <h3 style="color: var(--error-color);">System Issues Detected</h3>
                    <p>Please check the backend service.</p>
                </div>
            `;
        }
        
        statusContent.innerHTML = statusHtml;
        
    } catch (error) {
        console.error('System status check failed:', error);
        const statusContent = document.getElementById('systemStatusContent');
        statusContent.innerHTML = `
            <div style="text-align: center;">
                <i class="fas fa-times-circle" style="font-size: 48px; color: var(--error-color); margin-bottom: 16px;"></i>
                <h3 style="color: var(--error-color);">Connection Failed</h3>
                <p>Unable to connect to the backend service. Please ensure the server is running.</p>
            </div>
        `;
    }
}

async function showSystemInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/capabilities`);
        const data = await response.json();
        
        showInfoModal('System Capabilities', `
            <div class="system-info">
                <h4>AI Intelligence Features:</h4>
                <ul>
                    <li><strong>Document Understanding:</strong> ${data.ai_intelligence.document_understanding}</li>
                    <li><strong>Requirement Extraction:</strong> ${data.ai_intelligence.requirement_extraction}</li>
                    <li><strong>Compliance Analysis:</strong> ${data.ai_intelligence.compliance_analysis}</li>
                    <li><strong>Gap Identification:</strong> ${data.ai_intelligence.gap_identification}</li>
                </ul>
                
                <h4>Analysis Features:</h4>
                <ul>
                    ${data.analysis_features.map(feature => `<li>${feature}</li>`).join('')}
                </ul>
                
                <h4>AI Capabilities:</h4>
                <ul>
                    ${data.ai_capabilities.map(capability => `<li>${capability}</li>`).join('')}
                </ul>
            </div>
        `);
    } catch (error) {
        showInfoModal('System Information', '<p>Unable to load system information. Please try again.</p>');
    }
}

async function showCapabilities() {
    try {
        const response = await fetch(`${API_BASE_URL}/supported-document-types`);
        const data = await response.json();
        
        const content = `
            <div class="capabilities-info">
                <h4>Regulatory Documents Supported:</h4>
                ${Object.entries(data.regulatory_documents).map(([category, docs]) => `
                    <div style="margin-bottom: 16px;">
                        <strong>${category.charAt(0).toUpperCase() + category.slice(1)}:</strong>
                        <ul style="margin-left: 20px;">
                            ${docs.map(doc => `<li>${doc}</li>`).join('')}
                        </ul>
                    </div>
                `).join('')}
                
                <h4>Compliance Documents Supported:</h4>
                ${Object.entries(data.compliance_documents).map(([category, docs]) => `
                    <div style="margin-bottom: 16px;">
                        <strong>${category.charAt(0).toUpperCase() + category.slice(1)}:</strong>
                        <ul style="margin-left: 20px;">
                            ${docs.map(doc => `<li>${doc}</li>`).join('')}
                        </ul>
                    </div>
                `).join('')}
                
                <div style="background: var(--background-alt); padding: 16px; border-radius: 8px; margin-top: 16px;">
                    <p><strong>Note:</strong> ${data.analysis_note}</p>
                </div>
            </div>
        `;
        
        showInfoModal('Supported Document Types', content);
    } catch (error) {
        showInfoModal('Capabilities', '<p>Unable to load capabilities information. Please try again.</p>');
    }
}

function showHelp() {
    const content = `
        <div class="help-content">
            <h4>How to Use the AI Legal Compliance Analyzer:</h4>
            <ol style="margin-left: 20px; line-height: 1.8;">
                <li><strong>Upload Documents:</strong> Select two PDF documents for analysis. The AI will automatically determine which is the regulatory document and which is the compliance target.</li>
                <li><strong>Start Analysis:</strong> Click the "Start AI Analysis" button to begin the intelligent analysis process.</li>
                <li><strong>Monitor Progress:</strong> Watch the real-time progress as the AI processes your documents through 5 intelligent phases.</li>
                <li><strong>Download Report:</strong> Once complete, download your comprehensive compliance analysis report.</li>
            </ol>
            
            <h4>Tips for Best Results:</h4>
            <ul style="margin-left: 20px; line-height: 1.8;">
                <li>Ensure PDFs contain selectable text (not scanned images)</li>
                <li>Use clear, well-structured documents for optimal analysis</li>
                <li>Documents should be in English for best AI understanding</li>
                <li>File size limit is 50MB per document</li>
            </ul>
            
            <h4>AI Analysis Phases:</h4>
            <ol style="margin-left: 20px; line-height: 1.8;">
                <li><strong>Document Understanding:</strong> AI analyzes structure and content</li>
                <li><strong>Strategy Selection:</strong> Determines optimal analysis approach</li>
                <li><strong>Requirement Extraction:</strong> Dynamically extracts compliance requirements</li>
                <li><strong>Compliance Analysis:</strong> Performs detailed compliance checking</li>
                <li><strong>Report Generation:</strong> Creates comprehensive analysis report</li>
            </ol>
        </div>
    `;
    
    showInfoModal('Help & User Guide', content);
}

function showTechnicalInfo() {
    const content = `
        <div class="technical-info">
            <h4>Technical Specifications:</h4>
            <ul style="margin-left: 20px; line-height: 1.8;">
                <li><strong>AI Engine:</strong> Advanced Large Language Model</li>
                <li><strong>Document Processing:</strong> Intelligent PDF text extraction</li>
                <li><strong>Analysis Method:</strong> 100% dynamic, zero hardcoded rules</li>
                <li><strong>Supported Formats:</strong> PDF documents</li>
                <li><strong>File Size Limit:</strong> 50MB per document</li>
                <li><strong>Processing Time:</strong> 3-7 minutes depending on complexity</li>
                <li><strong>Offline Capability:</strong> Runs completely offline once installed</li>
            </ul>
            
            <h4>System Requirements:</h4>
            <ul style="margin-left: 20px; line-height: 1.8;">
                <li><strong>Operating System:</strong> Windows 10/11, macOS 10.15+, Linux</li>
                <li><strong>RAM:</strong> Minimum 8GB, Recommended 16GB</li>
                <li><strong>Storage:</strong> 10GB available space</li>
                <li><strong>Internet:</strong> Not required after installation</li>
            </ul>
            
            <h4>AI Advantages:</h4>
            <ul style="margin-left: 20px; line-height: 1.8;">
                <li>No predefined templates or rules</li>
                <li>Adapts to any legal domain or jurisdiction</li>
                <li>Learns from document context and structure</li>
                <li>Provides intelligent, contextual recommendations</li>
                <li>Continuously improves analysis quality</li>
            </ul>
        </div>
    `;
    
    showInfoModal('Technical Information', content);
}

function showAbout() {
    const content = `
        <div class="about-content">
            <div style="text-align: center; margin-bottom: 24px;">
                <i class="fas fa-brain" style="font-size: 48px; color: var(--primary-color); margin-bottom: 16px;"></i>
                <h3>AI Legal Compliance Analyzer</h3>
                <p style="color: var(--text-secondary);">Revolutionary AI-Powered Document Analysis</p>
            </div>
            
            <h4>About This System:</h4>
            <p style="line-height: 1.8;">
                This is a cutting-edge artificial intelligence system designed to revolutionize legal compliance analysis. 
                Unlike traditional rule-based systems, our AI dynamically understands any type of legal document and 
                performs intelligent compliance analysis without any hardcoded requirements or templates.
            </p>
            
            <h4>Key Innovations:</h4>
            <ul style="margin-left: 20px; line-height: 1.8;">
                <li><strong>Zero Hardcoding:</strong> No predefined rules or templates</li>
                <li><strong>Universal Compatibility:</strong> Works with any document type</li>
                <li><strong>Intelligent Understanding:</strong> True AI comprehension of legal content</li>
                <li><strong>Dynamic Analysis:</strong> Adapts to any legal domain</li>
                <li><strong>Offline Operation:</strong> Complete privacy and security</li>
            </ul>
            
            <h4>Perfect For:</h4>
            <ul style="margin-left: 20px; line-height: 1.8;">
                <li>Legal professionals and law firms</li>
                <li>Compliance officers and departments</li>
                <li>Contract managers and administrators</li>
                <li>Business analysts and consultants</li>
                <li>Anyone needing document compliance analysis</li>
            </ul>
            
            <div style="background: var(--background-alt); padding: 16px; border-radius: 8px; margin-top: 16px;">
                <p><strong>Version:</strong> 4.0.0 - 100% Dynamic AI System</p>
                <p><strong>Technology:</strong> Advanced Large Language Models</p>
                <p><strong>Privacy:</strong> All processing happens locally on your machine</p>
            </div>
        </div>
    `;
    
    showInfoModal('About AI Legal Compliance', content);
}

function showErrorDetails() {
    if (!currentTaskId) {
        showInfoModal('Error Details', '<p>No error details available.</p>');
        return;
    }
    
    // This would typically fetch detailed error information
    const content = `
        <div class="error-details">
            <h4>Analysis Error Information:</h4>
            <p><strong>Task ID:</strong> ${currentTaskId}</p>
            <p><strong>Error Time:</strong> ${new Date().toLocaleString()}</p>
            
            <h4>Possible Causes:</h4>
            <ul style="margin-left: 20px; line-height: 1.8;">
                <li>PDF documents contain only scanned images (no selectable text)</li>
                <li>Documents are password protected or corrupted</li>
                <li>Insufficient readable content for AI analysis</li>
                <li>System resource limitations during processing</li>
                <li>Network connection issues (if applicable)</li>
            </ul>
            
            <h4>Recommended Solutions:</h4>
            <ul style="margin-left: 20px; line-height: 1.8;">
                <li>Verify PDFs contain selectable text (not just images)</li>
                <li>Try with different, simpler document formats</li>
                <li>Ensure documents have substantial text content</li>
                <li>Check system resources and restart if needed</li>
                <li>Contact support if problems persist</li>
            </ul>
        </div>
    `;
    
    showInfoModal('Error Details', content);
}

// Modal functions
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.add('show');
    modal.style.display = 'flex';
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.remove('show');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

function showInfoModal(title, content) {
    // Create dynamic modal
    const modal = document.createElement('div');
    modal.className = 'modal show';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3><i class="fas fa-info-circle"></i> ${title}</h3>
                <button class="modal-close" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal-body">
                ${content}
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

function handleModalClose(event) {
    if (event.target.classList.contains('modal')) {
        const modalId = event.target.id;
        if (modalId) {
            closeModal(modalId);
        } else {
            event.target.remove();
        }
    }
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--background-card);
        border: 1px solid var(--border-color);
        border-left: 4px solid var(--${type === 'error' ? 'error' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'primary'}-color);
        border-radius: var(--radius-lg);
        padding: var(--space-4);
        box-shadow: var(--shadow-lg);
        z-index: 1001;
        max-width: 400px;
        animation: slideInRight 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--space-3);
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

function getNotificationIcon(type) {
    switch (type) {
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-circle';
        case 'warning': return 'exclamation-triangle';
        default: return 'info-circle';
    }
}

// Add notification animations to CSS
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        flex-grow: 1;
    }
    
    .notification-close {
        background: none;
        border: none;
        color: var(--text-muted);
        cursor: pointer;
        padding: var(--space-1);
        transition: color var(--transition-base);
    }
    
    .notification-close:hover {
        color: var(--text-primary);
    }
`;
document.head.appendChild(notificationStyles);