from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies.auth import get_current_user
from backend.models.models import Device, MetricHistory, Alert
from backend.services.monitoring_service import monitor_devices

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/devices")
def get_devices(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    devices = db.query(Device).all()
    return devices


@router.get("/devices/{device_id}/metrics")
def get_device_metrics(
    device_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    metrics = db.query(MetricHistory).filter(MetricHistory.device_id == device_id).all()
    return metrics


@router.get("/alerts")
def get_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    alerts = db.query(Alert).all()
    return alerts


@router.post("/monitor")
def trigger_monitoring(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    monitor_devices(db)
    return {"message": "Monitoring executed successfully"}
