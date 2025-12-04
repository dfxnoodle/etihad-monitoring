import asyncio
import psutil
import aiosqlite
import json
from database import DB_PATH

async def collect_metrics():
    while True:
        try:
            cpu = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            net = psutil.net_io_counters()
            
            # Collect per-partition disk usage
            disk_details = []
            for part in psutil.disk_partitions():
                if part.mountpoint.startswith('/snap'):
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disk_details.append({
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent
                    })
                except PermissionError:
                    continue
            
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "INSERT INTO metrics (cpu_percent, memory_percent, disk_percent, disk_details, net_sent, net_recv) VALUES (?, ?, ?, ?, ?, ?)",
                    (cpu, memory, disk, json.dumps(disk_details), net.bytes_sent, net.bytes_recv)
                )
                await db.commit()
                
                # Retention policy: delete older than 7 days
                await db.execute("DELETE FROM metrics WHERE timestamp < datetime('now', '-7 days')")
                await db.commit()
                
        except Exception as e:
            print(f"Error collecting metrics: {e}")
            
        await asyncio.sleep(5) # Collect every 5 seconds
