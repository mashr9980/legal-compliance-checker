from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import uvicorn
from contextlib import asynccontextmanager
import os
from services.document_processor import DocumentProcessor
from services.compliance_checker import IntelligentComplianceEngine
from services.report_generator import IntelligentReportGenerator
from models.schemas import AnalysisResponse
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid
import tempfile
import traceback

executor = ThreadPoolExecutor(max_workers=4)

document_processor = None
compliance_engine = None
report_generator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global document_processor, compliance_engine, report_generator
    
    print("🚀 Initializing Intelligent Legal Compliance System...")
    
    document_processor = DocumentProcessor()
    compliance_engine = IntelligentComplianceEngine()
    report_generator = IntelligentReportGenerator()
    
    app.state.document_processor = document_processor
    app.state.compliance_engine = compliance_engine
    app.state.report_generator = report_generator
    
    os.makedirs("temp_files", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    print("✅ System initialized successfully")
    yield
    
    print("🔄 Shutting down system...")
    executor.shutdown(wait=True)

app = FastAPI(
    title="Intelligent Legal Compliance System",
    description="AI-Powered Dynamic Policy Compliance Analysis",
    version="2.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "system": "Intelligent Legal Compliance System",
        "version": "2.0.0",
        "capabilities": [
            "Dynamic document analysis",
            "Intelligent requirement extraction",
            "Adaptive compliance checking",
            "Strategic recommendations"
        ]
    }

@app.get("/capabilities")
async def get_capabilities():
    return {
        "supported_document_types": [
            "Policies", "Laws", "Regulations", "Standards", 
            "Contracts", "Guidelines", "Procedures"
        ],
        "analysis_types": [
            "Compliance checking", "Gap analysis", 
            "Policy comparison", "Regulatory alignment"
        ],
        "intelligence_features": [
            "Automatic document type detection",
            "Dynamic requirement extraction",
            "Contextual compliance assessment",
            "Strategic recommendation generation"
        ]
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def intelligent_analysis(
    background_tasks: BackgroundTasks,
    document1: UploadFile = File(..., description="First document (any policy/legal document)"),
    document2: UploadFile = File(..., description="Second document (any policy/legal document)")
):
    print(f"📄 Received documents: {document1.filename}, {document2.filename}")
    
    if not all(doc.filename.endswith('.pdf') for doc in [document1, document2]):
        raise HTTPException(status_code=400, detail="Both files must be PDF format")
    
    task_id = str(uuid.uuid4())
    print(f"🆔 Created analysis task: {task_id}")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp1:
            content1 = await document1.read()
            temp1.write(content1)
            path1 = temp1.name
            print(f"📂 Document 1 saved: {len(content1)} bytes")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp2:
            content2 = await document2.read()
            temp2.write(content2)
            path2 = temp2.name
            print(f"📂 Document 2 saved: {len(content2)} bytes")
        
        background_tasks.add_task(
            intelligent_analysis_pipeline,
            task_id, path1, path2, document1.filename, document2.filename
        )
        
        return AnalysisResponse(
            task_id=task_id,
            status="processing",
            message="Documents are being analyzed using intelligent AI systems. The system will automatically determine document types, extract requirements, and generate comprehensive compliance analysis."
        )
        
    except Exception as e:
        print(f"❌ Error in document upload: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/status/{task_id}")
async def get_analysis_status(task_id: str):
    report_path = f"reports/{task_id}.pdf"
    error_path = f"reports/{task_id}.error"
    
    if os.path.exists(report_path):
        file_size = os.path.getsize(report_path)
        return {
            "status": "completed", 
            "task_id": task_id,
            "report_size": file_size,
            "message": "Analysis completed successfully"
        }
    elif os.path.exists(error_path):
        with open(error_path, 'r') as f:
            error_msg = f.read()
        return {
            "status": "error", 
            "task_id": task_id, 
            "error": error_msg,
            "message": "Analysis failed - check error details"
        }
    else:
        return {
            "status": "processing", 
            "task_id": task_id,
            "message": "Analysis in progress - intelligent systems are working"
        }

@app.get("/download/{task_id}")
async def download_intelligent_report(task_id: str):
    report_path = f"reports/{task_id}.pdf"
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report not found or still processing")
    
    return FileResponse(
        path=report_path,
        filename=f"intelligent_compliance_report_{task_id}.pdf",
        media_type="application/pdf"
    )

async def intelligent_analysis_pipeline(task_id: str, doc1_path: str, doc2_path: str, doc1_filename: str, doc2_filename: str):
    loop = asyncio.get_event_loop()
    error_path = f"reports/{task_id}.error"
    
    try:
        print(f"🧠 Starting intelligent analysis pipeline for task: {task_id}")
        
        print("📖 Phase 1: Document text extraction...")
        doc1_text = await loop.run_in_executor(
            executor, document_processor.extract_text, doc1_path
        )
        doc2_text = await loop.run_in_executor(
            executor, document_processor.extract_text, doc2_path
        )
        
        print(f"✅ Extracted - Doc1: {len(doc1_text)} chars, Doc2: {len(doc2_text)} chars")
        
        if len(doc1_text) < 100 or len(doc2_text) < 100:
            raise Exception("One or both documents contain insufficient text for analysis")
        
        print("🔍 Phase 2: Intelligent document analysis...")
        analysis_context = await compliance_engine.analyze_documents(doc1_text, doc2_text)
        
        doc1_type = analysis_context["doc1_analysis"].get("document_type", "Unknown")
        doc2_type = analysis_context["doc2_analysis"].get("document_type", "Unknown")
        comparison_type = analysis_context["comparison_context"].get("analysis_type", "comparison")
        
        print(f"📋 Document types identified - Doc1: {doc1_type}, Doc2: {doc2_type}")
        print(f"🎯 Analysis type: {comparison_type}")
        
        print("⚙️ Phase 3: Generating intelligent policy checklist...")
        policy_checklist = await compliance_engine.generate_intelligent_checklist(
            doc1_text, doc2_text, analysis_context
        )
        
        checklist_items = len(policy_checklist.items)
        aligned_items = len([item for item in policy_checklist.items if item.status.value == "ALIGNED"])
        
        print(f"📊 Generated checklist with {checklist_items} items ({aligned_items} aligned)")
        
        print("📄 Phase 4: Generating intelligent report...")
        report_path = f"reports/{task_id}.pdf"
        await loop.run_in_executor(
            executor,
            report_generator.generate_intelligent_report,
            policy_checklist,
            doc1_filename,
            doc2_filename,
            report_path
        )
        
        file_size = os.path.getsize(report_path)
        print(f"✅ Report generated successfully: {file_size} bytes")
        
    except Exception as e:
        error_msg = f"Intelligent analysis failed: {str(e)}\n\nFull traceback:\n{traceback.format_exc()}"
        print(f"❌ {error_msg}")
        
        with open(error_path, 'w') as f:
            f.write(error_msg)
        
        try:
            from models.schemas import PolicyChecklist, PolicyItem, PolicyStatus
            
            fallback_item = PolicyItem(
                chapter="System Error",
                item="Analysis Failed",
                requirement="Automated analysis could not be completed",
                status=PolicyStatus.UNALIGNED,
                feedback=f"System encountered an error: {str(e)}",
                comments="Manual analysis recommended",
                suggested_amendments="Review documents manually and retry analysis",
                source_reference="System Error",
                category="error"
            )
            
            fallback_checklist = PolicyChecklist(
                document_analysis={
                    "error": True,
                    "message": str(e)
                },
                items=[fallback_item],
                overall_feedback={
                    "statistics": {
                        "aligned": 0,
                        "moderate": 0,
                        "unaligned": 1,
                        "total": 1,
                        "alignment_percentage": 0,
                        "moderate_percentage": 0,
                        "unaligned_percentage": 100
                    },
                    "assessment": "Analysis failed due to system error",
                    "key_strengths": [],
                    "critical_gaps": ["System analysis failure"],
                    "compliance_maturity": "UNKNOWN"
                },
                recommendations=["Retry analysis with different documents", "Contact system administrator"],
                additional_considerations=["Ensure documents are readable PDFs", "Check document file integrity"]
            )
            
            report_path = f"reports/{task_id}.pdf"
            await loop.run_in_executor(
                executor,
                report_generator.generate_intelligent_report,
                fallback_checklist,
                doc1_filename,
                doc2_filename,
                report_path
            )
            
        except Exception as fallback_error:
            print(f"❌ Even fallback report generation failed: {fallback_error}")
        
    finally:
        try:
            if os.path.exists(doc1_path):
                os.unlink(doc1_path)
            if os.path.exists(doc2_path):
                os.unlink(doc2_path)
        except Exception as cleanup_error:
            print(f"⚠️ Cleanup error: {cleanup_error}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001)