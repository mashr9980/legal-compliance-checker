from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
import os
from pathlib import Path
from services.document_processor import DocumentProcessor
from services.compliance_checker import IntelligentComplianceEngine
from services.report_generator import IntelligentReportGenerator
from services.ollama_client import IntelligentAnalyzer
from models.schemas import AnalysisResponse
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid
import tempfile
import traceback
import json
import logging
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=4)

document_processor = None
compliance_engine = None
report_generator = None
llm_analyzer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global document_processor, compliance_engine, report_generator, llm_analyzer
    
    logger.info("Initializing AI Legal Compliance System...")
    
    try:
        llm_analyzer = IntelligentAnalyzer()
        await llm_analyzer.initialize()
        
        document_processor = DocumentProcessor()
        document_processor.set_llm_analyzer(llm_analyzer)
        
        compliance_engine = IntelligentComplianceEngine()
        
        report_generator = IntelligentReportGenerator()
        
        app.state.document_processor = document_processor
        app.state.compliance_engine = compliance_engine
        app.state.report_generator = report_generator
        app.state.llm_analyzer = llm_analyzer
        
        os.makedirs("temp_files", exist_ok=True)
        os.makedirs("reports", exist_ok=True)
        os.makedirs("static", exist_ok=True)
        
        logger.info("System initialized successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        yield
    
    finally:
        logger.info("Shutting down system...")
        if llm_analyzer:
            await llm_analyzer.close()
        executor.shutdown(wait=True)

app = FastAPI(
    title="AI Legal Compliance Analysis System",
    description="AI-Powered Universal Document Compliance Checker",
    version="4.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent

STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)

def setup_frontend_files():
    index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Legal Compliance Analyzer</title>
    <link rel="stylesheet" href="/static/styles.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div id="loadingScreen" class="loading-screen">
        <div class="loading-content">
            <div class="loading-spinner"></div>
            <h2>Initializing AI Legal Compliance System</h2>
            <p>Preparing intelligent document analysis...</p>
        </div>
    </div>

    <header class="header">
        <div class="container">
            <div class="header-content">
                <div class="logo">
                    <i class="fas fa-brain"></i>
                    <span>AI Legal Compliance</span>
                </div>
                <nav class="nav">
                    <a href="#home" class="nav-link active">Home</a>
                    <a href="#features" class="nav-link">Features</a>
                    <a href="#how-it-works" class="nav-link">How It Works</a>
                    <a href="#results" class="nav-link">Results</a>
                </nav>
                <div class="header-actions">
                    <button class="btn-secondary" onclick="checkSystemStatus()">
                        <i class="fas fa-heartbeat"></i> System Status
                    </button>
                </div>
            </div>
        </div>
    </header>

    <main class="main">
        <section id="home" class="hero">
            <div class="container">
                <div class="hero-content">
                    <div class="hero-text">
                        <h1>100% AI-Powered Legal Compliance Analysis</h1>
                        <p class="hero-subtitle">Revolutionary artificial intelligence that automatically detects document types, extracts requirements, and performs comprehensive compliance analysis without any hardcoded rules.</p>
                        <div class="hero-features">
                            <div class="feature-item">
                                <i class="fas fa-robot"></i>
                                <span>Zero Hardcoded Requirements</span>
                            </div>
                            <div class="feature-item">
                                <i class="fas fa-magic"></i>
                                <span>Universal Document Support</span>
                            </div>
                            <div class="feature-item">
                                <i class="fas fa-lightning-bolt"></i>
                                <span>Intelligent Analysis</span>
                            </div>
                        </div>
                        <button class="btn-primary hero-cta" onclick="scrollToUpload()">
                            <i class="fas fa-rocket"></i> Start AI Analysis
                        </button>
                    </div>
                    <div class="hero-visual">
                        <div class="ai-visualization">
                            <div class="ai-brain">
                                <i class="fas fa-brain"></i>
                            </div>
                            <div class="ai-connections">
                                <div class="connection"></div>
                                <div class="connection"></div>
                                <div class="connection"></div>
                                <div class="connection"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <section id="features" class="features">
            <div class="container">
                <div class="section-header">
                    <h2>Revolutionary AI Capabilities</h2>
                    <p>Advanced artificial intelligence that understands any legal document</p>
                </div>
                <div class="features-grid">
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-eye"></i>
                        </div>
                        <h3>Intelligent Document Detection</h3>
                        <p>Automatically identifies document types, purposes, and structures using advanced AI analysis.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-search-plus"></i>
                        </div>
                        <h3>Dynamic Requirement Extraction</h3>
                        <p>Extracts specific, actionable requirements from any legal or regulatory document without predefined rules.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-balance-scale"></i>
                        </div>
                        <h3>Adaptive Compliance Analysis</h3>
                        <p>Performs intelligent compliance checking that adapts to any domain, jurisdiction, or document type.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-chart-line"></i>
                        </div>
                        <h3>Strategic Insights</h3>
                        <p>Generates comprehensive assessments, risk evaluations, and strategic recommendations.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-globe"></i>
                        </div>
                        <h3>Universal Compatibility</h3>
                        <p>Works with any document type: laws, contracts, policies, regulations, standards, and agreements.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-shield-alt"></i>
                        </div>
                        <h3>Professional Grade</h3>
                        <p>Enterprise-level accuracy and reliability with comprehensive reporting and audit trails.</p>
                    </div>
                </div>
            </div>
        </section>

        <section id="how-it-works" class="how-it-works">
            <div class="container">
                <div class="section-header">
                    <h2>How AI Analysis Works</h2>
                    <p>5-phase intelligent analysis powered by advanced AI</p>
                </div>
                <div class="process-steps">
                    <div class="step">
                        <div class="step-number">1</div>
                        <div class="step-content">
                            <h3><i class="fas fa-file-search"></i> Document Understanding</h3>
                            <p>AI analyzes document structure, content, and purpose to understand what you're working with.</p>
                        </div>
                    </div>
                    <div class="step">
                        <div class="step-number">2</div>
                        <div class="step-content">
                            <h3><i class="fas fa-route"></i> Strategy Selection</h3>
                            <p>Determines the optimal analysis approach based on document types and relationships.</p>
                        </div>
                    </div>
                    <div class="step">
                        <div class="step-number">3</div>
                        <div class="step-content">
                            <h3><i class="fas fa-tasks"></i> Requirement Extraction</h3>
                            <p>Dynamically extracts specific requirements, obligations, and compliance criteria.</p>
                        </div>
                    </div>
                    <div class="step">
                        <div class="step-number">4</div>
                        <div class="step-content">
                            <h3><i class="fas fa-check-double"></i> Compliance Analysis</h3>
                            <p>Performs detailed compliance checking with evidence gathering and gap analysis.</p>
                        </div>
                    </div>
                    <div class="step">
                        <div class="step-number">5</div>
                        <div class="step-content">
                            <h3><i class="fas fa-chart-pie"></i> Strategic Reporting</h3>
                            <p>Generates comprehensive reports with insights, recommendations, and action plans.</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <section id="upload" class="upload-section">
            <div class="container">
                <div class="upload-container">
                    <div class="upload-header">
                        <h2><i class="fas fa-cloud-upload-alt"></i> Start Your AI Analysis</h2>
                        <p>Upload legal documents and policy for intelligent compliance analysis</p>
                    </div>
                    
                    <div class="upload-area">
                        <div class="upload-box" id="uploadBoxLegal">
                            <div class="upload-content">
                                <i class="fas fa-file-pdf"></i>
                                <h3>Legal Documents</h3>
                                <p>Upload legal documents (laws, regulations, standards, policies, etc.)</p>
                                <input type="file" id="legalFiles" accept=".pdf" multiple hidden>
                                <button class="btn-upload" onclick="document.getElementById('legalFiles').click()">
                                    <i class="fas fa-plus"></i> Choose PDFs
                                </button>
                                <div class="file-info-container" id="legalFilesInfo">
                                </div>
                            </div>
                        </div>

                        <div class="vs-separator">
                            <div class="vs-circle">
                                <i class="fas fa-arrows-alt-h"></i>
                            </div>
                        </div>

                        <div class="upload-box" id="uploadBoxPolicy">
                            <div class="upload-content">
                                <i class="fas fa-file-contract"></i>
                                <h3>Policy Document</h3>
                                <p>Upload policy document to analyze (contract, policy, procedure, etc.)</p>
                                <input type="file" id="policyFile" accept=".pdf" hidden>
                                <button class="btn-upload" onclick="document.getElementById('policyFile').click()">
                                    <i class="fas fa-plus"></i> Choose PDF
                                </button>
                                <div class="file-info" id="policyFileInfo" style="display: none;">
                                    <i class="fas fa-file-contract"></i>
                                    <span class="file-name"></span>
                                    <span class="file-size"></span>
                                    <button class="btn-remove" onclick="removePolicyFile()">
                                        <i class="fas fa-times"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="analysis-controls">
                        <button class="btn-analyze" id="analyzeBtn" onclick="startAnalysis()" disabled>
                            <i class="fas fa-brain"></i>
                            <span>Start AI Analysis</span>
                        </button>
                        <p class="analysis-note">
                            <i class="fas fa-info-circle"></i>
                            AI will automatically detect document types and determine optimal analysis strategy
                        </p>
                    </div>
                </div>
            </div>
        </section>

        <section id="results" class="results-section" style="display: none;">
            <div class="container">
                <div class="results-container">
                    <div class="results-header">
                        <h2><i class="fas fa-chart-line"></i> Analysis Results</h2>
                        <div class="results-meta">
                            <span class="task-id">Task ID: <span id="taskId"></span></span>
                            <span class="analysis-time">Started: <span id="analysisTime"></span></span>
                        </div>
                    </div>

                    <div class="progress-container" id="progressContainer">
                        <div class="progress-header">
                            <h3><i class="fas fa-cogs"></i> <span id="progressTitle">Processing...</span></h3>
                            <div class="progress-status">
                                <span id="progressPhase">Initializing...</span>
                            </div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="progressFill"></div>
                        </div>
                        <div class="progress-details" id="progressDetails">
                            AI is analyzing your documents...
                        </div>
                    </div>

                    <div class="results-display" id="resultsDisplay" style="display: none;">
                        <div class="results-summary">
                            <div class="summary-card">
                                <div class="summary-icon">
                                    <i class="fas fa-file-alt"></i>
                                </div>
                                <div class="summary-content">
                                    <h4>Documents Analyzed</h4>
                                    <p id="documentsAnalyzed">Documents</p>
                                </div>
                            </div>
                            <div class="summary-card">
                                <div class="summary-icon">
                                    <i class="fas fa-percentage"></i>
                                </div>
                                <div class="summary-content">
                                    <h4>Compliance Score</h4>
                                    <p id="complianceScore">--</p>
                                </div>
                            </div>
                            <div class="summary-card">
                                <div class="summary-icon">
                                    <i class="fas fa-tasks"></i>
                                </div>
                                <div class="summary-content">
                                    <h4>Requirements Analyzed</h4>
                                    <p id="requirementsCount">--</p>
                                </div>
                            </div>
                            <div class="summary-card">
                                <div class="summary-icon">
                                    <i class="fas fa-clock"></i>
                                </div>
                                <div class="summary-content">
                                    <h4>Analysis Time</h4>
                                    <p id="analysisCompleteTime">--</p>
                                </div>
                            </div>
                        </div>

                        <div class="results-actions">
                            <button class="btn-download" id="downloadBtn" onclick="downloadReport()" disabled>
                                <i class="fas fa-download"></i>
                                <span>Download Comprehensive Report</span>
                            </button>
                            <button class="btn-secondary" onclick="startNewAnalysis()">
                                <i class="fas fa-plus"></i>
                                <span>New Analysis</span>
                            </button>
                        </div>
                    </div>

                    <div class="error-display" id="errorDisplay" style="display: none;">
                        <div class="error-content">
                            <i class="fas fa-exclamation-triangle"></i>
                            <h3>Analysis Error</h3>
                            <p id="errorMessage">An error occurred during analysis.</p>
                            <div class="error-actions">
                                <button class="btn-primary" onclick="startNewAnalysis()">
                                    <i class="fas fa-redo"></i> Try Again
                                </button>
                                <button class="btn-secondary" onclick="showErrorDetails()">
                                    <i class="fas fa-info"></i> View Details
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-info">
                    <div class="logo">
                        <i class="fas fa-brain"></i>
                        <span>AI Legal Compliance</span>
                    </div>
                    <p>Powered by advanced artificial intelligence for intelligent legal document analysis.</p>
                </div>
                <div class="footer-links">
                    <h4>System</h4>
                    <a href="#" onclick="checkSystemStatus()">System Status</a>
                    <a href="#" onclick="showSystemInfo()">System Info</a>
                    <a href="#" onclick="showCapabilities()">Capabilities</a>
                </div>
                <div class="footer-links">
                    <h4>Support</h4>
                    <a href="#" onclick="showHelp()">Help & Guide</a>
                    <a href="#" onclick="showTechnicalInfo()">Technical Info</a>
                    <a href="#" onclick="showAbout()">About</a>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2024 AI Legal Compliance System. Advanced AI Technology.</p>
            </div>
        </div>
    </footer>

    <div id="systemStatusModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3><i class="fas fa-heartbeat"></i> System Status</h3>
                <button class="modal-close" onclick="closeModal('systemStatusModal')">&times;</button>
            </div>
            <div class="modal-body" id="systemStatusContent">
                <div class="loading-spinner"></div>
                <p>Checking system status...</p>
            </div>
        </div>
    </div>

    <div id="errorDetailsModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3><i class="fas fa-exclamation-triangle"></i> Error Details</h3>
                <button class="modal-close" onclick="closeModal('errorDetailsModal')">&times;</button>
            </div>
            <div class="modal-body" id="errorDetailsContent">
            </div>
        </div>
    </div>

    <script src="/static/script.js"></script>
</body>
</html>'''
    
    with open(STATIC_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

setup_frontend_files()

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    index_file = STATIC_DIR / "index.html"
    
    if index_file.exists():
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                content = f.read()
            return HTMLResponse(content=content)
        except Exception as e:
            logger.error(f"Error serving frontend: {e}")
            return HTMLResponse(content=get_fallback_html(), status_code=200)
    else:
        return HTMLResponse(content=get_fallback_html(), status_code=200)

def get_fallback_html():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Legal Compliance Analyzer</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2563eb; text-align: center; }
            .status { background: #eff6ff; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .endpoint { background: #f8fafc; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .endpoint code { background: #e2e8f0; padding: 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>AI Legal Compliance Analyzer</h1>
            <div class="status">
                <h2>System Status: Running</h2>
                <p>The backend system is operational. Frontend files not found - please add your frontend implementation to the 'static' directory.</p>
            </div>
            
            <h2>Available API Endpoints:</h2>
            <div class="endpoint">
                <strong>Health Check:</strong><br>
                <code>GET /health</code> - Check system status
            </div>
            <div class="endpoint">
                <strong>Document Analysis:</strong><br>
                <code>POST /analyze</code> - Start document analysis
            </div>
            <div class="endpoint">
                <strong>Analysis Status:</strong><br>
                <code>GET /status/{task_id}</code> - Check analysis progress
            </div>
            <div class="endpoint">
                <strong>Download Report:</strong><br>
                <code>GET /download/{task_id}</code> - Download analysis report
            </div>
            
            <div style="margin-top: 30px; text-align: center; color: #64748b;">
                <p>To add your frontend, place HTML, CSS, and JS files in the 'static' directory.</p>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "system": "AI Legal Compliance Analysis System",
        "version": "4.0.0",
        "ai_powered": True,
        "capabilities": [
            "Universal document type detection",
            "Dynamic requirement extraction",
            "Intelligent compliance analysis",
            "AI-driven recommendations",
            "Adaptive document processing"
        ],
        "endpoints": {
            "frontend": "/",
            "analyze": "/analyze",
            "status": "/status/{task_id}",
            "download": "/download/{task_id}",
            "capabilities": "/capabilities"
        }
    }

@app.get("/capabilities")
async def get_capabilities():
    return {
        "ai_intelligence": {
            "document_understanding": "Automatic detection of any document type",
            "requirement_extraction": "Dynamic extraction from any legal/regulatory document", 
            "compliance_analysis": "Intelligent assessment against any standard",
            "gap_identification": "AI-powered gap analysis and recommendations"
        },
        "analysis_features": [
            "Dynamic requirement extraction",
            "Intelligent document type detection",
            "Adaptive compliance checking", 
            "AI-powered gap analysis",
            "Smart recommendation generation",
            "Context-aware risk assessment"
        ],
        "ai_capabilities": [
            "Zero hardcoded rules or templates",
            "Universal document compatibility",
            "Contextual understanding",
            "Intelligent reasoning",
            "Adaptive analysis strategies"
        ]
    }

@app.get("/supported-document-types")
async def get_supported_document_types():
    return {
        "regulatory_documents": {
            "laws": ["Federal Laws", "State Laws", "Local Ordinances", "Constitutional Provisions"],
            "regulations": ["Federal Regulations", "Industry Standards", "Professional Guidelines", "Compliance Frameworks"],
            "policies": ["Government Policies", "Institutional Policies", "Organizational Standards", "Best Practices"],
            "standards": ["ISO Standards", "Industry Standards", "Technical Specifications", "Quality Standards"]
        },
        "compliance_documents": {
            "contracts": ["Employment Contracts", "Service Agreements", "Purchase Agreements", "Partnership Agreements"],
            "policies": ["Company Policies", "HR Policies", "Security Policies", "Operational Procedures"],
            "procedures": ["Standard Operating Procedures", "Implementation Guidelines", "Process Documentation"],
            "agreements": ["Terms of Service", "Privacy Policies", "License Agreements", "Compliance Documents"]
        },
        "analysis_note": "AI automatically detects document types and adapts analysis accordingly. No predefined templates required."
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_documents(
    background_tasks: BackgroundTasks,
    legal_documents: List[UploadFile] = File(..., description="Legal documents for analysis"),
    policy_document: UploadFile = File(..., description="Policy document for analysis")
):
    if not legal_documents or len(legal_documents) == 0:
        raise HTTPException(status_code=400, detail="At least one legal document must be uploaded")
    
    if not policy_document:
        raise HTTPException(status_code=400, detail="Policy document must be uploaded")
    
    for doc in legal_documents:
        if not doc.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"All files must be PDF format. Invalid file: {doc.filename}")
    
    if not policy_document.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Policy document must be PDF format")
    
    task_id = str(uuid.uuid4())
    logger.info(f"Starting analysis task: {task_id}")
    
    try:
        legal_doc_paths = []
        legal_doc_names = []
        
        for doc in legal_documents:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                doc_content = await doc.read()
                temp_file.write(doc_content)
                legal_doc_paths.append(temp_file.name)
                legal_doc_names.append(doc.filename)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_policy:
            policy_content = await policy_document.read()
            temp_policy.write(policy_content)
            policy_path = temp_policy.name
        
        background_tasks.add_task(
            analysis_pipeline,
            task_id, legal_doc_paths, policy_path, legal_doc_names, policy_document.filename
        )
        
        return AnalysisResponse(
            task_id=task_id,
            status="processing",
            message="AI-powered document analysis started. Processing time: 3-7 minutes depending on document complexity."
        )
        
    except Exception as e:
        logger.error(f"Analysis request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis request failed: {str(e)}")

@app.get("/status/{task_id}")
async def get_analysis_status(task_id: str):
    report_path = f"reports/{task_id}.pdf"
    error_path = f"reports/{task_id}.error"
    progress_path = f"reports/{task_id}.progress"
    
    if os.path.exists(report_path):
        file_size = os.path.getsize(report_path)
        return {
            "status": "completed", 
            "task_id": task_id,
            "report_size": file_size,
            "message": "Analysis completed successfully",
            "download_ready": True
        }
    
    elif os.path.exists(error_path):
        with open(error_path, 'r') as f:
            error_msg = f.read()
        return {
            "status": "error", 
            "task_id": task_id, 
            "error": error_msg,
            "message": "Analysis failed",
            "download_ready": False
        }
    
    elif os.path.exists(progress_path):
        try:
            with open(progress_path, 'r') as f:
                progress_info = json.loads(f.read())
            return {
                "status": "processing", 
                "task_id": task_id,
                "progress": progress_info,
                "message": progress_info.get('current_phase', 'Processing...'),
                "download_ready": False
            }
        except:
            pass
    
    return {
        "status": "processing", 
        "task_id": task_id,
        "message": "Analysis in progress...",
        "download_ready": False
    }

@app.get("/download/{task_id}")
async def download_report(task_id: str):
    report_path = f"reports/{task_id}.pdf"
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report not found or still processing")
    
    return FileResponse(
        path=report_path,
        filename=f"compliance_analysis_{task_id}.pdf",
        media_type="application/pdf"
    )

async def analysis_pipeline(task_id: str, legal_doc_paths: List[str], policy_path: str, 
                          legal_doc_names: List[str], policy_filename: str):
    loop = asyncio.get_event_loop()
    error_path = f"reports/{task_id}.error"
    progress_path = f"reports/{task_id}.progress"
    
    async def update_progress(phase: str, details: str):
        progress_info = {
            "current_phase": phase,
            "details": details,
            "timestamp": str(asyncio.get_event_loop().time())
        }
        try:
            with open(progress_path, 'w') as f:
                json.dump(progress_info, f)
        except Exception as e:
            logger.warning(f"Could not update progress: {e}")
    
    try:
        logger.info(f"Starting analysis pipeline for task: {task_id}")
        
        await update_progress("Phase 1: Document Processing", "Extracting and analyzing document content")
        
        legal_texts = []
        for i, doc_path in enumerate(legal_doc_paths):
            extraction = await document_processor.intelligent_extract_text(doc_path)
            text = extraction["extracted_text"]
            
            if len(text) < 200:
                raise Exception(f"Legal document {i+1} ({legal_doc_names[i]}) contains insufficient readable text")
            
            legal_texts.append(text)
        
        policy_extraction = await document_processor.intelligent_extract_text(policy_path)
        policy_text = policy_extraction["extracted_text"]
        
        if len(policy_text) < 200:
            raise Exception(f"Policy document ({policy_filename}) contains insufficient readable text")
        
        combined_legal_text = "\n\n--- DOCUMENT SEPARATOR ---\n\n".join(legal_texts)
        
        await update_progress("Phase 2: Document Understanding", "AI analyzing document types and content")
        analysis_context = await compliance_engine.analyze_documents(combined_legal_text, policy_text)
        
        await update_progress("Phase 3: Compliance Analysis", "Extracting requirements and checking compliance")
        policy_checklist = await compliance_engine.generate_intelligent_checklist(
            combined_legal_text, policy_text, analysis_context
        )
        
        await update_progress("Phase 4: Report Generation", "Creating comprehensive analysis report")
        report_path = f"reports/{task_id}.pdf"
        
        legal_docs_summary = f"{len(legal_doc_names)} Legal Documents: {', '.join(legal_doc_names)}"
        
        await loop.run_in_executor(
            executor,
            report_generator.generate_intelligent_report,
            policy_checklist,
            legal_docs_summary,
            policy_filename,
            report_path
        )
        
        logger.info(f"Analysis completed successfully for task: {task_id}")
        
    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        logger.error(f"Task {task_id}: {error_msg}")
        
        try:
            with open(error_path, 'w') as f:
                f.write(error_msg)
        except Exception as write_error:
            logger.error(f"Could not write error file: {write_error}")
        
    finally:
        try:
            for doc_path in legal_doc_paths:
                if os.path.exists(doc_path):
                    os.unlink(doc_path)
            if os.path.exists(policy_path):
                os.unlink(policy_path)
            if os.path.exists(progress_path):
                os.unlink(progress_path)
        except Exception as cleanup_error:
            logger.warning(f"Cleanup error: {cleanup_error}")

if __name__ == "__main__":
    print("AI Legal Compliance Analysis System")
    print("Version: 4.0.0")
    print("Starting server...")
    print("Web interface: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000,
        reload=False,
        log_level="info"
    )