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
from services.intelligent_analyzer import IntelligentPolicyAnalyzer
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
policy_analyzer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global document_processor, compliance_engine, report_generator, policy_analyzer
    
    logger.info("🚀 Initializing RAIA - Intelligent Policy Analysis System...")
    
    try:
        policy_analyzer = IntelligentPolicyAnalyzer()
        await policy_analyzer.initialize()
        
        document_processor = DocumentProcessor()
        document_processor.set_llm_analyzer(policy_analyzer)
        
        compliance_engine = IntelligentComplianceEngine()
        
        report_generator = IntelligentReportGenerator()
        
        app.state.document_processor = document_processor
        app.state.compliance_engine = compliance_engine
        app.state.report_generator = report_generator
        app.state.policy_analyzer = policy_analyzer
        
        os.makedirs("temp_files", exist_ok=True)
        os.makedirs("reports", exist_ok=True)
        os.makedirs("static", exist_ok=True)
        
        logger.info("✅ RAIA system initialized successfully")
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAIA system: {e}")
        yield
    
    finally:
        logger.info("🔄 Shutting down RAIA system...")
        if policy_analyzer:
            await policy_analyzer.close()
        executor.shutdown(wait=True)

app = FastAPI(
    title="RAIA - Intelligent Policy Analysis System",
    description="AI-Powered Intelligent Policy Review and Compliance Analysis",
    version="5.0.0",
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
    <title>RAIA - Rewards AI Assistant</title>
    <link rel="stylesheet" href="/static/styles.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div id="loadingScreen" class="loading-screen">
        <div class="loading-content">
            <div class="loading-spinner"></div>
            <h2>Initializing RAIA - Rewards AI Assistant</h2>
            <p>Preparing intelligent rewards analysis...</p>
        </div>
    </div>

    <header class="header">
        <div class="container">
            <div class="header-content">
                <div class="logo">
                    <i class="fas fa-brain"></i>
                    <span>RAIA - Rewards AI Assistant</span>
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
                        <h1>100% AI-Powered Rewards Analysis</h1>
                        <p class="hero-subtitle">Meet RAIA — your smart assistant for Total Rewards. It intelligently analyzes policies, detects key compensation elements, and delivers deep insights without predefined templates.</p>
                        <div class="hero-features">
                            <div class="feature-item">
                                <i class="fas fa-robot"></i>
                                <span>Fully Adaptive to Any Rewards Policy</span>
                            </div>
                            <div class="feature-item">
                                <i class="fas fa-magic"></i>
                                <span>Compatible with All Compensation Documents</span>
                            </div>
                            <div class="feature-item">
                                <i class="fas fa-lightning-bolt"></i>
                                <span>Insightful, Context-Aware Rewards Evaluation</span>
                            </div>
                        </div>
                        <button class="btn-primary hero-cta" onclick="scrollToUpload()">
                            <i class="fas fa-rocket"></i> Start Rewards Evaluation
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
                    <h2>RAIA's Smart Capabilities</h2>
                    <p>Advanced AI tailored to understand any rewards, compensation, or benefits document</p>
                </div>
                <div class="features-grid">
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-eye"></i>
                        </div>
                        <h3>Smart Policy Detection</h3>
                        <p>Recognizes salary structures, incentive plans, and benefits from diverse document formats.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-search-plus"></i>
                        </div>
                        <h3>Dynamic Rewards Identification</h3>
                        <p>Pinpoints key reward elements like base pay, bonuses, equity grants, and allowances.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-balance-scale"></i>
                        </div>
                        <h3>Flexible Rewards Evaluation</h3>
                        <p>Adapts to multiple frameworks, job families, grades, markets, and internal reward policies.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-chart-line"></i>
                        </div>
                        <h3>Actionable Rewards Insights</h3>
                        <p>Provides deep analytics on fairness, competitiveness, and alignment with strategy.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-globe"></i>
                        </div>
                        <h3>Supports All Reward Formats</h3>
                        <p>Works with any document — salary guides, HR policies, bonus plans, or benefits handbooks.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">
                            <i class="fas fa-shield-alt"></i>
                        </div>
                        <h3>Enterprise-Level Confidence</h3>
                        <p>Precision-level analysis with full traceability, ideal for audits and executive reviews.</p>
                    </div>
                </div>
            </div>
        </section>

        <section id="how-it-works" class="how-it-works">
            <div class="container">
                <div class="section-header">
                    <h2>How RAIA Analysis Works</h2>
                    <p>5-Phase Smart Evaluation for Rewards Strategy Optimization</p>
                </div>
                <div class="process-steps">
                    <div class="step">
                        <div class="step-number">1</div>
                        <div class="step-content">
                            <h3><i class="fas fa-file-search"></i> Policy Recognition</h3>
                            <p>RAIA understands document types and compensation-related structures to define what's being assessed.</p>
                        </div>
                    </div>
                    <div class="step">
                        <div class="step-number">2</div>
                        <div class="step-content">
                            <h3><i class="fas fa-route"></i> Reward Framework Mapping</h3>
                            <p>Identifies the ideal evaluation method based on compensation elements, policy types, and industry practices.</p>
                        </div>
                    </div>
                    <div class="step">
                        <div class="step-number">3</div>
                        <div class="step-content">
                            <h3><i class="fas fa-tasks"></i> Rewards Component Extraction</h3>
                            <p>Extracts salary bands, bonus structures, allowances, benefits, and key compliance indicators.</p>
                        </div>
                    </div>
                    <div class="step">
                        <div class="step-number">4</div>
                        <div class="step-content">
                            <h3><i class="fas fa-check-double"></i> Equity & Benchmark Analysis</h3>
                            <p>Checks internal consistency, equity, and alignment with benchmarking data or internal grading systems.</p>
                        </div>
                    </div>
                    <div class="step">
                        <div class="step-number">5</div>
                        <div class="step-content">
                            <h3><i class="fas fa-chart-pie"></i> Rewards Insights & Actions</h3>
                            <p>Delivers clear insights, red flags, and recommended optimizations to support better decisions.</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <section id="upload" class="upload-section">
            <div class="container">
                <div class="upload-container">
                    <div class="upload-header">
                        <h2><i class="fas fa-cloud-upload-alt"></i> Start Your Rewards Analysis</h2>
                        <p>Upload reward policies and compensation documents for intelligent analysis</p>
                    </div>
                    
                    <div class="upload-area">
                        <div class="upload-box" id="uploadBoxLegal">
                            <div class="upload-content">
                                <i class="fas fa-file-pdf"></i>
                                <h3>Reward Framework Documents</h3>
                                <p>Upload reward policies (salary guides, bonus plans, benefits handbooks, etc.)</p>
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
                                <h3>Compensation Document</h3>
                                <p>Upload compensation document to analyze (employee contract, pay structure, etc.)</p>
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
                            <span>Start Rewards Analysis</span>
                        </button>
                        <p class="analysis-note">
                            <i class="fas fa-info-circle"></i>
                            RAIA will automatically detect document types and determine optimal analysis strategy
                        </p>
                    </div>
                </div>
            </div>
        </section>

        <section id="results" class="results-section" style="display: none;">
            <div class="container">
                <div class="results-container">
                    <div class="results-header">
                        <h2><i class="fas fa-chart-line"></i> Rewards Analysis Results</h2>
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
                            RAIA is analyzing your rewards documents...
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
                                    <h4>Rewards Alignment Score</h4>
                                    <p id="complianceScore">--</p>
                                </div>
                            </div>
                            <div class="summary-card">
                                <div class="summary-icon">
                                    <i class="fas fa-tasks"></i>
                                </div>
                                <div class="summary-content">
                                    <h4>Components Analyzed</h4>
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
                                <span>Download Rewards Analysis Report</span>
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
                        <span>RAIA - Rewards AI Assistant</span>
                    </div>
                    <p>Powered by advanced artificial intelligence for intelligent rewards and compensation analysis.</p>
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
                <p>&copy; 2025 RAIA - Rewards AI Assistant. Advanced AI Technology.</p>
            </div>
        </div>

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
        <title>RAIA - Intelligent Policy Analysis</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #005C4D; text-align: center; }
            .status { background: #eff6ff; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .endpoint { background: #f8fafc; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .endpoint code { background: #e2e8f0; padding: 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>RAIA - Intelligent Policy Analysis System</h1>
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
                <strong>Policy Analysis:</strong><br>
                <code>POST /analyze</code> - Start intelligent policy analysis
            </div>
            <div class="endpoint">
                <strong>Analysis Status:</strong><br>
                <code>GET /status/{task_id}</code> - Check analysis progress
            </div>
            <div class="endpoint">
                <strong>Download Report:</strong><br>
                <code>GET /download/{task_id}</code> - Download analysis report
            </div>
            <div class="endpoint">
                <strong>9-Point Framework:</strong><br>
                <code>GET /criteria-framework</code> - View analysis criteria
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
        "system": "RAIA - Rewards AI Assistant",
        "version": "4.0.0",
        "ai_powered": True,
        "capabilities": [
            "Smart policy detection and recognition",
            "Dynamic rewards identification",
            "Flexible rewards evaluation",
            "Equity and benchmark analysis",
            "Actionable rewards insights"
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
            "document_understanding": "Automatic detection of any compensation document type",
            "rewards_extraction": "Dynamic extraction from any rewards/benefits document", 
            "equity_analysis": "Intelligent assessment of compensation fairness",
            "benchmark_identification": "AI-powered benchmarking and market analysis"
        },
        "analysis_features": [
            "Smart policy detection",
            "Dynamic rewards identification", 
            "Flexible rewards evaluation",
            "Equity and benchmark analysis",
            "Actionable rewards insights",
            "Context-aware compensation assessment"
        ],
        "ai_capabilities": [
            "Zero hardcoded rules or templates",
            "Universal compensation document compatibility",
            "Contextual understanding of rewards",
            "Intelligent reasoning for fairness",
            "Adaptive analysis strategies"
        ]
    }

@app.get("/supported-document-types")
async def get_supported_document_types():
    return {
        "rewards_documents": {
            "salary_guides": ["Salary Bands", "Pay Scales", "Grade Structures", "Compensation Frameworks"],
            "bonus_plans": ["Incentive Plans", "Performance Bonuses", "Variable Pay", "Commission Structures"],
            "benefits": ["Benefits Handbooks", "Benefit Summaries", "Pension Plans", "Health Insurance"],
            "equity_plans": ["Stock Options", "Equity Grants", "Share Plans", "Long-term Incentives"]
        },
        "compensation_documents": {
            "contracts": ["Employment Contracts", "Executive Agreements", "Offer Letters", "Compensation Letters"],
            "policies": ["HR Policies", "Compensation Policies", "Reward Policies", "Pay Equity Policies"],
            "benchmarks": ["Market Data", "Survey Results", "Benchmark Reports", "Peer Comparisons"],
            "structures": ["Job Families", "Career Ladders", "Grading Systems", "Leveling Guides"]
        },
        "analysis_note": "RAIA automatically detects document types and adapts analysis accordingly. No predefined templates required."
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_documents(
    background_tasks: BackgroundTasks,
    legal_documents: List[UploadFile] = File(..., description="Reward framework documents"),
    policy_document: UploadFile = File(..., description="Compensation document for analysis")
):
    if not legal_documents or len(legal_documents) == 0:
        raise HTTPException(status_code=400, detail="At least one reward framework document must be uploaded")
    
    if not policy_document:
        raise HTTPException(status_code=400, detail="Compensation document must be uploaded")
    
    for doc in legal_documents:
        if not doc.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"All files must be PDF format. Invalid file: {doc.filename}")
    
    if not policy_document.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Compensation document must be PDF format")
    
    task_id = str(uuid.uuid4())
    logger.info(f"🎯 Starting rewards analysis task: {task_id}")
    
    try:
        regulatory_doc_paths = []
        regulatory_doc_names = []
        
        for doc in legal_documents:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                doc_content = await doc.read()
                temp_file.write(doc_content)
                regulatory_doc_paths.append(temp_file.name)
                regulatory_doc_names.append(doc.filename)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_policy:
            policy_content = await policy_document.read()
            temp_policy.write(policy_content)
            policy_path = temp_policy.name
        
        background_tasks.add_task(
            rewards_analysis_pipeline,
            task_id, regulatory_doc_paths, policy_path, regulatory_doc_names, policy_document.filename
        )
        
        return AnalysisResponse(
            task_id=task_id,
            status="processing",
            message="AI-powered rewards analysis started. Processing time: 3-7 minutes depending on document complexity."
        )
        
    except Exception as e:
        logger.error(f"❌ Analysis request failed: {e}")
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
            "message": "Intelligent policy analysis completed successfully",
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
        "message": "Intelligent analysis in progress...",
        "download_ready": False
    }

@app.get("/download/{task_id}")
async def download_report(task_id: str):
    report_path = f"reports/{task_id}.pdf"
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report not found or still processing")
    
    return FileResponse(
        path=report_path,
        filename=f"raia_policy_analysis_{task_id}.pdf",
        media_type="application/pdf"
    )

async def rewards_analysis_pipeline(task_id: str, regulatory_doc_paths: List[str], policy_path: str, 
                                      regulatory_doc_names: List[str], policy_filename: str):
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
            logger.warning(f"⚠️ Could not update progress: {e}")
    
    try:
        logger.info(f"🚀 Starting rewards analysis pipeline for task: {task_id}")
        
        doc_processor = getattr(app.state, 'document_processor', None)
        compliance_engine = getattr(app.state, 'compliance_engine', None)
        report_gen = getattr(app.state, 'report_generator', None)
        policy_analyzer = getattr(app.state, 'policy_analyzer', None)
        
        if not doc_processor:
            doc_processor = DocumentProcessor()
            if policy_analyzer:
                doc_processor.set_llm_analyzer(policy_analyzer)
            app.state.document_processor = doc_processor
            
        if not compliance_engine:
            compliance_engine = IntelligentComplianceEngine()
            app.state.compliance_engine = compliance_engine
            
        if not report_gen:
            report_gen = IntelligentReportGenerator()
            app.state.report_generator = report_gen
        
        await update_progress("Phase 1: Document Processing", "Extracting and analyzing document content")
        
        regulatory_texts = []
        for i, doc_path in enumerate(regulatory_doc_paths):
            extraction = await doc_processor.intelligent_extract_text(doc_path)
            text = extraction["extracted_text"]
            
            if len(text) < 200:
                raise Exception(f"Reward framework document {i+1} ({regulatory_doc_names[i]}) contains insufficient readable text")
            
            regulatory_texts.append(text)
        
        policy_extraction = await doc_processor.intelligent_extract_text(policy_path)
        policy_text = policy_extraction["extracted_text"]
        
        if len(policy_text) < 200:
            raise Exception(f"Compensation document ({policy_filename}) contains insufficient readable text")
        
        await update_progress("Phase 2: Document Understanding", "RAIA analyzing document types and content")
        
        regulatory_docs_summary = f"{len(regulatory_doc_names)} Reward Framework Documents: {', '.join(regulatory_doc_names)}"
        
        policy_assessment = await compliance_engine.comprehensive_policy_analysis(
            regulatory_texts, policy_text, regulatory_doc_names, policy_filename
        )
        
        await update_progress("Phase 3: Report Generation", "Creating comprehensive rewards analysis report")
        
        report_path = f"reports/{task_id}.pdf"
        
        await loop.run_in_executor(
            executor,
            report_gen.generate_professional_report,
            policy_assessment,
            regulatory_docs_summary,
            policy_filename,
            report_path
        )
        
        logger.info(f"✅ Rewards analysis completed successfully for task: {task_id}")
        
    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        logger.error(f"❌ Task {task_id}: {error_msg}")
        
        try:
            with open(error_path, 'w') as f:
                f.write(error_msg)
        except Exception as write_error:
            logger.error(f"❌ Could not write error file: {write_error}")
        
    finally:
        try:
            for doc_path in regulatory_doc_paths:
                if os.path.exists(doc_path):
                    os.unlink(doc_path)
            if os.path.exists(policy_path):
                os.unlink(policy_path)
            if os.path.exists(progress_path):
                os.unlink(progress_path)
        except Exception as cleanup_error:
            logger.warning(f"⚠️ Cleanup error: {cleanup_error}")

if __name__ == "__main__":
    print("🧠 RAIA - Rewards AI Assistant")
    print("📊 Version: 4.0.0")
    print("🎯 AI-Powered Rewards Analysis")
    print("🚀 Starting server...")
    print("🌐 Web interface: http://localhost:8010")
    print("📖 API documentation: http://localhost:8010/docs")
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8010,
        reload=False,
        log_level="info"
    )