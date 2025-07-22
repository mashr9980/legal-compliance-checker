let currentTaskId = null;
let pollInterval = null;
let analysisStartTime = null;
let selectedRegulatoryFiles = [];
let selectedPolicyFile = null;

const API_BASE_URL = 'http://localhost:8010';

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM Content Loaded - Starting RAIA initialization...');
    setTimeout(initializeApp, 200);
});

async function initializeApp() {
    try {
        console.log('🔧 Starting app initialization...');
        showLoadingScreen();
        await checkSystemHealth();
        initializeEventListeners();
        setTimeout(() => {
            hideLoadingScreen();
            console.log('✅ RAIA initialization completed successfully');
        }, 2000);
    } catch (error) {
        console.error('❌ Initialization error:', error);
        showNotification('System initialization failed. Please check if the backend is running.', 'error');
        hideLoadingScreen();
    }
}

function showLoadingScreen() {
    const loadingScreen = document.getElementById('loadingScreen');
    if (loadingScreen) {
        loadingScreen.classList.remove('hidden');
    }
}

function hideLoadingScreen() {
    const loadingScreen = document.getElementById('loadingScreen');
    if (loadingScreen) {
        loadingScreen.classList.add('hidden');
    }
}

function initializeEventListeners() {
    console.log('🔧 Initializing event listeners...');
    
    const legalFiles = document.getElementById('legalFiles');
    const policyFile = document.getElementById('policyFile');
    
    console.log('Elements found:', { 
        legalFiles: !!legalFiles, 
        policyFile: !!policyFile,
        analyzeBtn: !!document.getElementById('analyzeBtn'),
        uploadBoxLegal: !!document.getElementById('uploadBoxLegal'),
        uploadBoxPolicy: !!document.getElementById('uploadBoxPolicy')
    });
    
    if (legalFiles) {
        legalFiles.addEventListener('change', handleRegulatoryFilesSelect);
        console.log('✅ Legal files event listener added');
    } else {
        console.error('❌ legalFiles element not found');
    }
    
    if (policyFile) {
        policyFile.addEventListener('change', handlePolicyFileSelect);
        console.log('✅ Policy file event listener added');
    } else {
        console.error('❌ policyFile element not found');
    }
    
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', handleNavigation);
    });
    
    window.addEventListener('scroll', updateActiveNav);
    document.addEventListener('click', handleModalClose);
    
    // Initialize the analyze button state
    updateAnalyzeButton();
    
    console.log('✅ All event listeners initialized');
}

async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            console.log('✅ RAIA system is healthy:', data);
            return true;
        } else {
            throw new Error('System health check failed');
        }
    } catch (error) {
        console.error('❌ System health check failed:', error);
        throw error;
    }
}

function handleRegulatoryFilesSelect(event) {
    console.log('📁 Handling regulatory files selection...');
    const files = Array.from(event.target.files);
    
    for (const file of files) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            showNotification('Please select PDF files only.', 'error');
            continue;
        }
        
        if (file.size > 50 * 1024 * 1024) {
            showNotification('File size too large. Please select files under 50MB.', 'error');
            continue;
        }
        
        if (selectedRegulatoryFiles.some(f => f.name === file.name)) {
            showNotification(`File "${file.name}" already selected.`, 'warning');
            continue;
        }
        
        selectedRegulatoryFiles.push(file);
        addRegulatoryFileToUI(file);
    }
    
    updateUploadBoxState();
    updateAnalyzeButton();
    
    if (files.length > 0) {
        showNotification(`${files.length} reward framework document(s) selected successfully!`, 'success');
    }
}

function addRegulatoryFileToUI(file) {
    const fileInfoContainer = document.getElementById('legalFilesInfo');
    const uploadBox = document.getElementById('uploadBoxLegal');
    
    if (!fileInfoContainer || !uploadBox) {
        console.error('❌ Required elements not found for file UI');
        return;
    }
    
    const fileInfo = document.createElement('div');
    fileInfo.className = 'file-info';
    fileInfo.innerHTML = `
        <i class="fas fa-file-pdf"></i>
        <span class="file-name">${file.name}</span>
        <span class="file-size">${formatFileSize(file.size)}</span>
        <button class="btn-remove" onclick="removeRegulatoryFile('${file.name.replace(/'/g, "\\'")}')">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    fileInfoContainer.appendChild(fileInfo);
    uploadBox.classList.add('has-file');
}

function removeRegulatoryFile(fileName) {
    selectedRegulatoryFiles = selectedRegulatoryFiles.filter(file => file.name !== fileName);
    
    const fileInfoContainer = document.getElementById('legalFilesInfo');
    if (!fileInfoContainer) return;
    
    const fileInfos = fileInfoContainer.querySelectorAll('.file-info');
    
    fileInfos.forEach(info => {
        const nameElement = info.querySelector('.file-name');
        if (nameElement && nameElement.textContent === fileName) {
            info.remove();
        }
    });
    
    updateUploadBoxState();
    updateAnalyzeButton();
    
    showNotification(`File "${fileName}" removed.`, 'info');
}

function handlePolicyFileSelect(event) {
    console.log('📄 Handling policy file selection...');
    const file = event.target.files[0];
    const uploadBox = document.getElementById('uploadBoxPolicy');
    const fileInfo = document.getElementById('policyFileInfo');
    
    if (!uploadBox || !fileInfo) {
        console.error('❌ Required elements not found for policy file');
        return;
    }
    
    const uploadContent = uploadBox.querySelector('.upload-content');
    
    if (file) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            showNotification('Please select a PDF file only.', 'error');
            return;
        }
        
        if (file.size > 50 * 1024 * 1024) {
            showNotification('File size too large. Please select a file under 50MB.', 'error');
            return;
        }
        
        selectedPolicyFile = file;
        
        uploadBox.classList.add('has-file');
        fileInfo.style.display = 'flex';
        
        const nameElement = fileInfo.querySelector('.file-name');
        const sizeElement = fileInfo.querySelector('.file-size');
        if (nameElement) nameElement.textContent = file.name;
        if (sizeElement) sizeElement.textContent = formatFileSize(file.size);
        
        if (uploadContent) {
            const uploadBtn = uploadContent.querySelector('.btn-upload');
            const uploadText = uploadContent.querySelector('p');
            if (uploadBtn) uploadBtn.style.display = 'none';
            if (uploadText) uploadText.style.display = 'none';
        }
        
        updateAnalyzeButton();
        
        showNotification(`Compensation file "${file.name}" selected successfully!`, 'success');
    }
}

function removePolicyFile() {
    const uploadBox = document.getElementById('uploadBoxPolicy');
    const fileInfo = document.getElementById('policyFileInfo');
    const fileInput = document.getElementById('policyFile');
    
    if (!uploadBox || !fileInfo || !fileInput) {
        console.warn('Some elements not found for removePolicyFile');
        return;
    }
    
    const uploadContent = uploadBox.querySelector('.upload-content');
    
    selectedPolicyFile = null;
    fileInput.value = '';
    
    uploadBox.classList.remove('has-file');
    fileInfo.style.display = 'none';
    
    if (uploadContent) {
        const uploadBtn = uploadContent.querySelector('.btn-upload');
        const uploadText = uploadContent.querySelector('p');
        if (uploadBtn) uploadBtn.style.display = 'inline-flex';
        if (uploadText) uploadText.style.display = 'block';
    }
    
    updateAnalyzeButton();
    showNotification('Policy file removed.', 'info');
}

function updateUploadBoxState() {
    const uploadBox = document.getElementById('uploadBoxLegal');
    if (!uploadBox) return;
    
    const uploadContent = uploadBox.querySelector('.upload-content');
    if (!uploadContent) return;
    
    const uploadBtn = uploadContent.querySelector('.btn-upload');
    const uploadText = uploadContent.querySelector('p');
    
    if (selectedRegulatoryFiles.length === 0) {
        uploadBox.classList.remove('has-file');
        if (uploadBtn) uploadBtn.style.display = 'inline-flex';
        if (uploadText) uploadText.style.display = 'block';
    } else {
        uploadBox.classList.add('has-file');
        if (uploadBtn) uploadBtn.style.display = 'none';
        if (uploadText) uploadText.style.display = 'none';
    }
}

function updateAnalyzeButton() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (!analyzeBtn) {
        console.warn('❌ analyzeBtn element not found');
        return;
    }
    
    const hasRegulatoryFiles = selectedRegulatoryFiles.length > 0;
    const hasPolicyFile = selectedPolicyFile !== null;
    
    analyzeBtn.disabled = !hasRegulatoryFiles || !hasPolicyFile;
    
    if (hasRegulatoryFiles && hasPolicyFile) {
        analyzeBtn.innerHTML = '<i class="fas fa-brain"></i><span>Start Rewards Analysis</span>';
    } else if (!hasRegulatoryFiles && !hasPolicyFile) {
        analyzeBtn.innerHTML = '<i class="fas fa-upload"></i><span>Select Reward Framework and Compensation Documents First</span>';
    } else if (!hasRegulatoryFiles) {
        analyzeBtn.innerHTML = '<i class="fas fa-upload"></i><span>Select Reward Framework Documents First</span>';
    } else {
        analyzeBtn.innerHTML = '<i class="fas fa-upload"></i><span>Select Compensation Document First</span>';
    }
}

async function startAnalysis() {
    if (selectedRegulatoryFiles.length === 0 || !selectedPolicyFile) {
        showNotification('Please select regulatory documents and policy document first.', 'warning');
        return;
    }
    
    try {
        const analyzeBtn = document.getElementById('analyzeBtn');
        if (analyzeBtn) {
            analyzeBtn.disabled = true;
            analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Starting Analysis...</span>';
        }
        
        const formData = new FormData();
        
        selectedRegulatoryFiles.forEach(file => {
            formData.append('legal_documents', file);
        });
        
        formData.append('policy_document', selectedPolicyFile);
        
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
        
        showResultsSection();
        startPolling();
        
        showNotification('🎯 RAIA rewards analysis started successfully!', 'success');
        
    } catch (error) {
        console.error('❌ Analysis start error:', error);
        showNotification(`Failed to start analysis: ${error.message}`, 'error');
        
        const analyzeBtn = document.getElementById('analyzeBtn');
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
            updateAnalyzeButton();
        }
    }
}

function showResultsSection() {
    const resultsSection = document.getElementById('results');
    const progressContainer = document.getElementById('progressContainer');
    const resultsDisplay = document.getElementById('resultsDisplay');
    const errorDisplay = document.getElementById('errorDisplay');
    
    if (resultsSection) resultsSection.style.display = 'block';
    if (progressContainer) progressContainer.style.display = 'block';
    if (resultsDisplay) resultsDisplay.style.display = 'none';
    if (errorDisplay) errorDisplay.style.display = 'none';
    
    const taskIdElement = document.getElementById('taskId');
    const analysisTimeElement = document.getElementById('analysisTime');
    
    if (taskIdElement) taskIdElement.textContent = currentTaskId;
    if (analysisTimeElement) analysisTimeElement.textContent = new Date().toLocaleString();
    
    if (resultsSection) {
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
}

function startPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
    }
    
    pollInterval = setInterval(async () => {
        try {
            await checkAnalysisStatus();
        } catch (error) {
            console.error('❌ Polling error:', error);
            clearInterval(pollInterval);
            showAnalysisError('Connection lost during analysis. Please refresh and try again.');
        }
    }, 3000);
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
        console.error('❌ Status check error:', error);
        throw error;
    }
}

function updateProgressDisplay(statusData) {
    const progressTitle = document.getElementById('progressTitle');
    const progressPhase = document.getElementById('progressPhase');
    const progressDetails = document.getElementById('progressDetails');
    const progressFill = document.getElementById('progressFill');
    
    let progressPercentage = 20;
    let phaseText = 'Processing...';
    let detailsText = 'RAIA is performing intelligent analysis of your policy documents...';
    
    if (statusData.progress) {
        phaseText = statusData.progress.current_phase || phaseText;
        detailsText = statusData.progress.details || detailsText;
        
        if (phaseText.includes('Phase 1')) progressPercentage = 30;
        else if (phaseText.includes('Phase 2')) progressPercentage = 70;
        else if (phaseText.includes('Phase 3')) progressPercentage = 90;
    }
    
    if (progressTitle) progressTitle.textContent = 'RAIA Analysis in Progress';
    if (progressPhase) progressPhase.textContent = phaseText;
    if (progressDetails) progressDetails.textContent = detailsText;
    if (progressFill) progressFill.style.width = `${progressPercentage}%`;
}

function showAnalysisComplete(data) {
    const progressContainer = document.getElementById('progressContainer');
    const resultsDisplay = document.getElementById('resultsDisplay');
    const downloadBtn = document.getElementById('downloadBtn');
    
    if (progressContainer) progressContainer.style.display = 'none';
    if (resultsDisplay) resultsDisplay.style.display = 'block';
    
    const totalDocs = selectedRegulatoryFiles.length + 1;
    const documentsAnalyzed = document.getElementById('documentsAnalyzed');
    const complianceScore = document.getElementById('complianceScore');
    const requirementsCount = document.getElementById('requirementsCount');
    
    if (documentsAnalyzed) documentsAnalyzed.textContent = `${totalDocs} Documents Analyzed`;
    if (complianceScore) complianceScore.textContent = 'Available in Report';
    if (requirementsCount) requirementsCount.textContent = 'Available in Report';
    
    if (analysisStartTime) {
        const completionTime = new Date();
        const duration = Math.round((completionTime - analysisStartTime) / 1000);
        const minutes = Math.floor(duration / 60);
        const seconds = duration % 60;
        const analysisCompleteTime = document.getElementById('analysisCompleteTime');
        if (analysisCompleteTime) {
            analysisCompleteTime.textContent = `${minutes}m ${seconds}s`;
        }
    }
    
    if (downloadBtn) downloadBtn.disabled = false;
    
    showNotification('🎉 RAIA analysis completed! Your comprehensive rewards report is ready.', 'success');
}

function showAnalysisError(errorMessage) {
    const progressContainer = document.getElementById('progressContainer');
    const errorDisplay = document.getElementById('errorDisplay');
    const errorMessageEl = document.getElementById('errorMessage');
    
    if (progressContainer) progressContainer.style.display = 'none';
    if (errorDisplay) errorDisplay.style.display = 'block';
    if (errorMessageEl) errorMessageEl.textContent = errorMessage;
    
    showNotification('Analysis failed. Please try again.', 'error');
}

async function downloadReport() {
    if (!currentTaskId) {
        showNotification('No report available for download.', 'warning');
        return;
    }
    
    try {
        const downloadBtn = document.getElementById('downloadBtn');
        const originalContent = downloadBtn ? downloadBtn.innerHTML : '';
        
        if (downloadBtn) {
            downloadBtn.disabled = true;
            downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Preparing Download...</span>';
        }
        
        const response = await fetch(`${API_BASE_URL}/download/${currentTaskId}`);
        
        if (!response.ok) {
            throw new Error('Failed to download report');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `raia_rewards_analysis_${currentTaskId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        if (downloadBtn) {
            downloadBtn.disabled = false;
            downloadBtn.innerHTML = originalContent;
        }
        
        showNotification('Professional rewards analysis report downloaded successfully!', 'success');
        
    } catch (error) {
        console.error('❌ Download error:', error);
        showNotification(`Download failed: ${error.message}`, 'error');
        
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.disabled = false;
            downloadBtn.innerHTML = '<i class="fas fa-download"></i><span>Download Rewards Analysis Report</span>';
        }
    }
}

function startNewAnalysis() {
    currentTaskId = null;
    analysisStartTime = null;
    selectedRegulatoryFiles = [];
    selectedPolicyFile = null;
    
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
    
    const resultsSection = document.getElementById('results');
    const legalFiles = document.getElementById('legalFiles');
    const policyFile = document.getElementById('policyFile');
    const legalFilesInfo = document.getElementById('legalFilesInfo');
    
    if (resultsSection) resultsSection.style.display = 'none';
    if (legalFiles) legalFiles.value = '';
    if (policyFile) policyFile.value = '';
    if (legalFilesInfo) legalFilesInfo.innerHTML = '';
    
    removePolicyFile();
    updateUploadBoxState();
    
    scrollToUpload();
    
    showNotification('Ready for new rewards analysis!', 'info');
}

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
    if (uploadSection) {
        uploadSection.scrollIntoView({ behavior: 'smooth' });
    }
}

async function checkSystemStatus() {
    try {
        showModal('systemStatusModal');
        const statusContent = document.getElementById('systemStatusContent');
        if (statusContent) {
            statusContent.innerHTML = '<div class="loading-spinner"></div><p>Checking system status...</p>';
        }
        
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
        
        if (statusContent) statusContent.innerHTML = statusHtml;
        
    } catch (error) {
        console.error('❌ System status check failed:', error);
        const statusContent = document.getElementById('systemStatusContent');
        if (statusContent) {
            statusContent.innerHTML = `
                <div style="text-align: center;">
                    <i class="fas fa-times-circle" style="font-size: 48px; color: var(--error-color); margin-bottom: 16px;"></i>
                    <h3 style="color: var(--error-color);">Connection Failed</h3>
                    <p>Unable to connect to RAIA backend service. Please ensure the server is running.</p>
                </div>
            `;
        }
    }
}

async function showSystemInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/capabilities`);
        const data = await response.json();
        
        const content = `
            <div class="system-info">
                <h4>AI Intelligence Features:</h4>
                <ul style="margin-left: 20px; line-height: 1.8;">
                    <li><strong>Document Understanding:</strong> ${data.ai_intelligence.document_understanding}</li>
                    <li><strong>Rewards Extraction:</strong> ${data.ai_intelligence.rewards_extraction}</li>
                    <li><strong>Equity Analysis:</strong> ${data.ai_intelligence.equity_analysis}</li>
                    <li><strong>Benchmark Identification:</strong> ${data.ai_intelligence.benchmark_identification}</li>
                </ul>
                
                <h4>Analysis Features:</h4>
                <ul style="margin-left: 20px; line-height: 1.8;">
                    ${data.analysis_features.map(feature => `<li>${feature}</li>`).join('')}
                </ul>
                
                <h4>AI Capabilities:</h4>
                <ul style="margin-left: 20px; line-height: 1.8;">
                    ${data.ai_capabilities.map(capability => `<li>${capability}</li>`).join('')}
                </ul>
            </div>
        `;
        
        showInfoModal('System Information', content);
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
                <h4>Rewards Documents Supported:</h4>
                ${Object.entries(data.rewards_documents).map(([category, docs]) => `
                    <div style="margin-bottom: 16px;">
                        <strong>${category.replace(/_/g, ' ').charAt(0).toUpperCase() + category.replace(/_/g, ' ').slice(1)}:</strong>
                        <ul style="margin-left: 20px;">
                            ${docs.map(doc => `<li>${doc}</li>`).join('')}
                        </ul>
                    </div>
                `).join('')}
                
                <h4>Compensation Documents Supported:</h4>
                ${Object.entries(data.compensation_documents).map(([category, docs]) => `
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
            <h4>How to Use RAIA - Rewards AI Assistant:</h4>
            <ol style="margin-left: 20px; line-height: 1.8;">
                <li><strong>Upload Reward Framework Documents:</strong> Select one or more PDF documents containing reward policies (salary guides, bonus plans, benefits handbooks, etc.).</li>
                <li><strong>Upload Compensation Document:</strong> Select one PDF document containing the compensation to be analyzed for alignment.</li>
                <li><strong>Start Analysis:</strong> Click the "Start Rewards Analysis" button to begin the intelligent analysis process.</li>
                <li><strong>Monitor Progress:</strong> Watch the real-time progress as RAIA processes your documents through 5 intelligent phases.</li>
                <li><strong>Download Report:</strong> Once complete, download your comprehensive rewards analysis report.</li>
            </ol>
            
            <h4>Tips for Best Results:</h4>
            <ul style="margin-left: 20px; line-height: 1.8;">
                <li>Ensure PDFs contain selectable text (not scanned images)</li>
                <li>Use clear, well-structured reward documents for optimal analysis</li>
                <li>Documents should be in English for best AI understanding</li>
                <li>File size limit is 50MB per document</li>
                <li>You can upload multiple reward framework documents to compare against one compensation document</li>
            </ul>
            
            <h4>RAIA Analysis Phases:</h4>
            <ol style="margin-left: 20px; line-height: 1.8;">
                <li><strong>Policy Recognition:</strong> RAIA analyzes document types and compensation structures</li>
                <li><strong>Reward Framework Mapping:</strong> Identifies optimal evaluation methods</li>
                <li><strong>Rewards Component Extraction:</strong> Extracts salary bands, bonuses, and benefits</li>
                <li><strong>Equity & Benchmark Analysis:</strong> Checks consistency and alignment</li>
                <li><strong>Rewards Insights & Actions:</strong> Provides recommendations and insights</li>
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
                <li><strong>Multiple Documents:</strong> Supports multiple reward framework documents vs one compensation document</li>
                <li><strong>Offline Capability:</strong> Runs completely offline once installed</li>
            </ul>
            
            <h4>System Requirements:</h4>
            <ul style="margin-left: 20px; line-height: 1.8;">
                <li><strong>Operating System:</strong> Windows 10/11, macOS 10.15+, Linux</li>
                <li><strong>RAM:</strong> Minimum 8GB, Recommended 16GB</li>
                <li><strong>Storage:</strong> 10GB available space</li>
                <li><strong>Internet:</strong> Not required after installation</li>
            </ul>
            
            <h4>RAIA Advantages:</h4>
            <ul style="margin-left: 20px; line-height: 1.8;">
                <li>No predefined templates or rules</li>
                <li>Adapts to any rewards framework or compensation structure</li>
                <li>Learns from document context and structure</li>
                <li>Provides intelligent, contextual recommendations</li>
                <li>Handles multiple reward documents simultaneously</li>
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
                <h3>RAIA - Rewards AI Assistant</h3>
                <p style="color: var(--text-secondary);">Revolutionary AI-Powered Rewards Analysis</p>
            </div>
            
            <h4>About RAIA:</h4>
            <p style="line-height: 1.8;">
                RAIA is a cutting-edge artificial intelligence system designed to revolutionize rewards and compensation analysis. 
                Unlike traditional rule-based systems, RAIA dynamically understands any type of reward document and 
                performs intelligent compensation analysis without any hardcoded requirements or templates.
            </p>
            
            <h4>Key Innovations:</h4>
            <ul style="margin-left: 20px; line-height: 1.8;">
                <li><strong>Zero Hardcoding:</strong> No predefined rules or templates</li>
                <li><strong>Universal Compatibility:</strong> Works with any reward document type</li>
                <li><strong>Intelligent Understanding:</strong> True AI comprehension of compensation content</li>
                <li><strong>Dynamic Analysis:</strong> Adapts to any rewards framework</li>
                <li><strong>Multiple Document Support:</strong> Analyze multiple reward documents against compensation</li>
                <li><strong>Offline Operation:</strong> Complete privacy and security</li>
            </ul>
            
            <h4>Perfect For:</h4>
            <ul style="margin-left: 20px; line-height: 1.8;">
                <li>HR professionals and compensation specialists</li>
                <li>Rewards managers and consultants</li>
                <li>Total rewards teams</li>
                <li>Business analysts and executives</li>
                <li>Anyone needing rewards analysis and benchmarking</li>
            </ul>
            
            <div style="background: var(--background-alt); padding: 16px; border-radius: 8px; margin-top: 16px;">
                <p><strong>Version:</strong> 4.0.0 - 100% Dynamic AI System</p>
                <p><strong>Technology:</strong> Advanced Large Language Models</p>
                <p><strong>Privacy:</strong> All processing happens locally on your machine</p>
            </div>
        </div>
    `;
    
    showInfoModal('About RAIA - Rewards AI Assistant', content);
}

function showErrorDetails() {
    if (!currentTaskId) {
        showInfoModal('Error Details', '<p>No error details available.</p>');
        return;
    }
    
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

function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        modal.style.display = 'flex';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }
}

function showInfoModal(title, content) {
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

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showNotification(message, type = 'info') {
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
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
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

// Add necessary CSS styles for notifications and animations
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
        font-size: 14px;
    }
    
    .notification-close:hover {
        color: var(--text-primary);
    }
    
    .loading-screen.hidden {
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
    }
`;

// Only add styles once
if (!document.getElementById('notification-styles')) {
    notificationStyles.id = 'notification-styles';
    document.head.appendChild(notificationStyles);
} 