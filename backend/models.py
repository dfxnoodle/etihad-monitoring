from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SystemInfo(BaseModel):
    hostname: str
    platform: str
    uptime_seconds: float
    cpu_count: int
    memory_total: int

class DiskPartition(BaseModel):
    device: str
    mountpoint: str
    total: int
    used: int
    free: int
    percent: float

class MetricData(BaseModel):
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    disk_details: List[DiskPartition] = []
    net_sent: int
    net_recv: int

class HistoricalData(BaseModel):
    metrics: List[MetricData]
