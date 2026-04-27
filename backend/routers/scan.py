import asyncio
import io
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import SessionLocal, get_db
from backend.models.models import Alert, Device, Scan, ScanResult
from backend.schemas.scan import ScanRequest
from backend.services.scanner import NetworkScanner

router = APIRouter(prefix="/scan", tags=["Scan"])
scanner = NetworkScanner()


async def run_scan(ip_range: str, scan_type: str, scan_id: int):
    db = SessionLocal()
    try:
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, scanner.scan, ip_range, scan_type)

        existing_ips = {device.ip for device in db.query(Device).all()}

        for result in results:
            result["is_new"] = result["ip"] not in existing_ips

            device = db.query(Device).filter(Device.ip == result["ip"]).first()
            if not device:
                device = Device(
                    ip=result["ip"],
                    hostname=result["hostname"],
                    os_name=result["os_name"],
                    device_type=result["device_type"],
                    status="up" if result["state"] == "up" else "down",
                )
                db.add(device)
                db.flush()
                db.add(
                    Alert(
                        type="NEW_UNKNOWN_DEVICE",
                        severity="warning",
                        message=f"Nouveau device detecte : {result['ip']} ({result['device_type']})",
                        device_id=device.id,
                    )
                )
            else:
                device.hostname = result["hostname"]
                device.os_name = result["os_name"]
                device.device_type = result["device_type"]
                device.status = "up" if result["state"] == "up" else "down"
                device.last_seen = datetime.now()

            db.add(
                ScanResult(
                    scan_id=scan_id,
                    device_ip=result["ip"],
                    hostname=result["hostname"],
                    os_name=result["os_name"],
                    device_type=result["device_type"],
                    ports=result["ports"],
                    is_new=result["is_new"],
                )
            )

        scan_obj = db.query(Scan).filter(Scan.id == scan_id).first()
        if scan_obj:
            scan_obj.finished_at = datetime.now()
            scan_obj.devices_found = len(results)
        db.commit()
    finally:
        db.close()


@router.post("/start")
async def start_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    scan = Scan(ip_range=request.ip_range, scan_type=request.scan_type)
    db.add(scan)
    db.commit()
    db.refresh(scan)
    background_tasks.add_task(run_scan, request.ip_range, request.scan_type, scan.id)
    return {"scan_id": scan.id, "status": "en cours", "ip_range": request.ip_range}


@router.get("/history")
def get_scan_history(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    scans = db.query(Scan).order_by(Scan.started_at.desc()).offset(skip).limit(limit).all()
    return scans


@router.get("/{scan_id}")
def get_scan_detail(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan introuvable")
    results = db.query(ScanResult).filter(ScanResult.scan_id == scan_id).all()
    return {"scan": scan, "devices": results}


@router.get("/{scan_id}/export")
def export_scan_csv(scan_id: int, db: Session = Depends(get_db)):
    results = db.query(ScanResult).filter(ScanResult.scan_id == scan_id).all()
    if not results:
        raise HTTPException(status_code=404, detail="Scan introuvable ou vide")
    rows = []
    for result in results:
        ports_str = ", ".join(
            [f"{port['port']}/{port['service']}" for port in (result.ports or [])]
        )
        rows.append(
            {
                "IP": result.device_ip,
                "Hostname": result.hostname,
                "OS": result.os_name,
                "Type": result.device_type,
                "Ports": ports_str,
                "Nouveau": "Oui" if result.is_new else "Non",
            }
        )
    dataframe = pd.DataFrame(rows)
    stream = io.StringIO()
    dataframe.to_csv(stream, index=False)
    stream.seek(0)
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=scan_{scan_id}.csv"},
    )
