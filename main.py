from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import uvicorn
from contextlib import asynccontextmanager
import os
from pathlib import Path
from services.document_processor import DocumentProcessor
from services.compliance_checker import ComplianceChecker
from services.report_generator import ReportGenerator
from services.ollama_client import OllamaClient
from models.schemas import AnalysisResponse, ComplianceResult
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid
import tempfile

executor = ThreadPoolExecutor(max_workers=4)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.document_processor = DocumentProcessor()
    app.state.compliance_checker = ComplianceChecker()
    app.state.report_generator = ReportGenerator()
    app.state.ollama_client = OllamaClient()
    
    await app.state.ollama_client.initialize()
    
    os.makedirs("temp_files", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    yield
    
    executor.shutdown(wait=True)

app = FastAPI(title="Legal Compliance Checker", lifespan=lifespan)

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_documents(
    background_tasks: BackgroundTasks,
    legal_doc: UploadFile = File(...),
    contract_doc: UploadFile = File(...)
):
    if not legal_doc.filename.endswith('.pdf') or not contract_doc.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    task_id = str(uuid.uuid4())
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as legal_temp:
        legal_temp.write(await legal_doc.read())
        legal_path = legal_temp.name
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as contract_temp:
        contract_temp.write(await contract_doc.read())
        contract_path = contract_temp.name
    
    background_tasks.add_task(
        process_documents_async,
        task_id,
        legal_path,
        contract_path,
        legal_doc.filename,
        contract_doc.filename
    )
    
    return AnalysisResponse(
        task_id=task_id,
        status="processing",
        message="Documents are being analyzed. Check status with task_id."
    )

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    report_path = f"reports/{task_id}.pdf"
    if os.path.exists(report_path):
        return {"status": "completed", "task_id": task_id}
    return {"status": "processing", "task_id": task_id}

@app.get("/download/{task_id}")
async def download_report(task_id: str):
    report_path = f"reports/{task_id}.pdf"
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        path=report_path,
        filename=f"compliance_report_{task_id}.pdf",
        media_type="application/pdf"
    )

async def process_documents_async(task_id: str, legal_path: str, contract_path: str, legal_filename: str, contract_filename: str):
    loop = asyncio.get_event_loop()
    
    try:
        legal_text = await loop.run_in_executor(executor, app.state.document_processor.extract_text, legal_path)
        contract_text = await loop.run_in_executor(executor, app.state.document_processor.extract_text, contract_path)
        
        legal_requirements = await app.state.compliance_checker.extract_requirements(legal_text)
        
        compliance_results = await app.state.compliance_checker.check_compliance(
            legal_requirements, contract_text
        )
        
        report_path = f"reports/{task_id}.pdf"
        await loop.run_in_executor(
            executor,
            app.state.report_generator.generate_report,
            compliance_results,
            legal_filename,
            contract_filename,
            report_path
        )
        
    finally:
        if os.path.exists(legal_path):
            os.unlink(legal_path)
        if os.path.exists(contract_path):
            os.unlink(contract_path)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001)