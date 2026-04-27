import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import subprocess
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models.models import Alert, Device, MetricHistory

PING_TIMEOUT_MS = 1000
MONITOR_MAX_WORKERS = 16


def probe_device(ip: str) -> tuple[bool, Optional[float]]:
    start = time.perf_counter()
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", str(PING_TIMEOUT_MS), ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return False, None

    latency_ms = None
    if result.returncode == 0:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

    return result.returncode == 0, latency_ms


def _probe_device(device: Device) -> tuple[int, bool, Optional[float]]:
    is_up, latency_ms = probe_device(device.ip)
    return device.id, is_up, latency_ms

def ping_device(ip: str) -> bool:
    is_up, _ = probe_device(ip)
    return is_up


def calculerLantence(ip: str) -> Optional[float]:
    _, latency_ms = probe_device(ip)
    return latency_ms


def monitor_devices(db: Session):
    devices = db.query(Device).all()

    if not devices:
        return

    max_workers = min(MONITOR_MAX_WORKERS, len(devices))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        probe_results = {
            device_id: (is_up, latency_ms)
            for device_id, is_up, latency_ms in executor.map(_probe_device, devices)
        }

    for device in devices:
        is_up, duree = probe_results.get(device.id, (False, None))
        if is_up:
            device.status = "online"
        else:
            device.status = "offline"
        device.last_seen = datetime.utcnow()
        metric = MetricHistory(
            device_id=device.id,
            timestamp=datetime.utcnow(),
            latency_ms=duree,
            is_up=is_up
        )
        db.add(metric)
    offline_count = sum(1 for d in devices if d.status == "offline")
    if offline_count >= 3:
        alert = Alert(
            type="NETWORK_OUTAGE",
            severity="critical",
            message=f"{offline_count} appareils sont hors ligne"
        )
        db.add(alert)

    db.commit()


def scheduled_monitor():
    db = SessionLocal()
    try:
        monitor_devices(db)
    finally:
        db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_monitor, "interval", seconds=30)
scheduler.start()

def get_snmp_matrice(ip: str) -> dict:
    try:
        from pysnmp.hlapi import (
            CommunityData,
            ContextData,
            ObjectIdentity,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
            getCmd,
        )

        iterator = getCmd(
            SnmpEngine(),
            CommunityData('public', mpModel=0),
            UdpTransportTarget((ip, 161), timeout=2, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.4.1.2021.11.9.0')),
            ObjectType(ObjectIdentity('1.3.6.1.4.1.2021.4.5.0')),
            ObjectType(ObjectIdentity('1.3.6.1.4.1.2021.4.6.0'))
        )

        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
        if not errorStatus and not errorIndication:
            cpu = int(varBinds[0][1])
            ramTotal = int(varBinds[1][1])
            ramFree = int(varBinds[2][1])
            ram_percent = round((ramTotal - ramFree) / ramTotal * 100, 2)
            return {"cpu": cpu, "ram_percent": ram_percent}
    except Exception:
        return None
