"""
Health monitor for Odoo platform and system metrics.
Checks Odoo health status and system CPU/RAM/Disk usage.
Sends email notifications if issues are detected.
Run this script via cron job every 15 minutes.
"""
import os
import time
import json
import sqlite3
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv
from email_notifier import send_odoo_alert, send_system_alert

# Load environment variables
load_dotenv()

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "metrics.db")


def check_odoo_health(url: str) -> dict:
    """
    Check if Odoo platform is working by verifying redirect to /web.
    
    Args:
        url: The Odoo URL to check
    
    Returns:
        Dictionary with health status information
    """
    start_time = time.time()
    
    try:
        with httpx.Client(follow_redirects=False, timeout=10.0, verify=False) as client:
            response = client.head(url)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Check if we get a redirect (301, 302, 303, 307, 308)
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("location", "")
                
                # Check if redirect is to /web
                if "/web" in location:
                    return {
                        "url": url,
                        "status": "online",
                        "redirect_location": location,
                        "response_time_ms": round(response_time, 2),
                        "checked_at": datetime.now(timezone.utc).isoformat(),
                        "message": "Odoo platform is working correctly"
                    }
                else:
                    return {
                        "url": url,
                        "status": "error",
                        "redirect_location": location,
                        "response_time_ms": round(response_time, 2),
                        "checked_at": datetime.now(timezone.utc).isoformat(),
                        "message": f"Unexpected redirect location: {location}"
                    }
            else:
                return {
                    "url": url,
                    "status": "error",
                    "response_time_ms": round(response_time, 2),
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                    "message": f"Unexpected status code: {response.status_code}"
                }
                
    except httpx.TimeoutException:
        return {
            "url": url,
            "status": "offline",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "message": "Connection timeout"
        }
    except httpx.ConnectError as e:
        return {
            "url": url,
            "status": "offline",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "message": f"Connection failed: {str(e)}"
        }
    except Exception as e:
        return {
            "url": url,
            "status": "error",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "message": f"Error: {str(e)}"
        }


def check_system_metrics() -> dict:
    """
    Check system metrics from the database over the configured duration.
    
    Returns:
        Dictionary with alerts for any metrics exceeding thresholds
    """
    # Get thresholds from environment
    cpu_threshold = float(os.getenv("CPU_THRESHOLD", "95"))
    memory_threshold = float(os.getenv("MEMORY_THRESHOLD", "90"))
    disk_threshold = float(os.getenv("DISK_THRESHOLD", "95"))
    duration_minutes = int(os.getenv("ALERT_DURATION_MINUTES", "15"))
    
    # Get monitored mountpoints
    mountpoints_str = os.getenv("DISK_MONITOR_MOUNTPOINTS", "/,/boot/efi,/mnt,/mnt/data")
    monitored_mountpoints = [mp.strip() for mp in mountpoints_str.split(",")]
    
    alerts = []
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query metrics from the last N minutes
        cursor.execute(
            """SELECT cpu_percent, memory_percent, disk_percent, disk_details, timestamp
               FROM metrics 
               WHERE timestamp > datetime('now', ? || ' minutes')
               ORDER BY timestamp ASC""",
            (f"-{duration_minutes}",)
        )
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print(f"No metrics data found for the last {duration_minutes} minutes")
            return {"alerts": [], "message": "No data available"}
        
        # Calculate averages
        cpu_values = [row["cpu_percent"] for row in rows]
        memory_values = [row["memory_percent"] for row in rows]
        
        avg_cpu = sum(cpu_values) / len(cpu_values)
        avg_memory = sum(memory_values) / len(memory_values)
        
        print(f"Metrics over last {duration_minutes} min: CPU avg={avg_cpu:.1f}%, Memory avg={avg_memory:.1f}%")
        
        # Check CPU threshold
        if avg_cpu >= cpu_threshold:
            alerts.append({
                "metric": "CPU",
                "value": avg_cpu,
                "threshold": cpu_threshold,
                "details": f"Average CPU usage: {avg_cpu:.1f}% over {len(rows)} samples"
            })
        
        # Check Memory threshold
        if avg_memory >= memory_threshold:
            alerts.append({
                "metric": "Memory",
                "value": avg_memory,
                "threshold": memory_threshold,
                "details": f"Average memory usage: {avg_memory:.1f}% over {len(rows)} samples"
            })
        
        # Check Disk thresholds for each monitored mountpoint
        # Use the latest disk_details
        latest_disk_details = rows[-1]["disk_details"]
        if latest_disk_details:
            try:
                disk_data = json.loads(latest_disk_details)
                disk_alerts = []
                
                for disk in disk_data:
                    mountpoint = disk.get("mountpoint", "")
                    if mountpoint in monitored_mountpoints:
                        percent = disk.get("percent", 0)
                        if percent >= disk_threshold:
                            disk_alerts.append(f"{mountpoint}: {percent:.1f}%")
                
                if disk_alerts:
                    alerts.append({
                        "metric": "Disk",
                        "value": max(d.get("percent", 0) for d in disk_data if d.get("mountpoint") in monitored_mountpoints),
                        "threshold": disk_threshold,
                        "details": "Mountpoints exceeding threshold:\n" + "\n".join(disk_alerts)
                    })
                    
            except json.JSONDecodeError:
                print("Warning: Could not parse disk_details JSON")
        
        return {"alerts": alerts, "samples": len(rows), "duration_minutes": duration_minutes}
        
    except Exception as e:
        print(f"Error checking system metrics: {e}")
        return {"alerts": [], "error": str(e)}


def run_odoo_health_check():
    """
    Run Odoo health check and send notification if offline or in error.
    """
    odoo_url = os.getenv("ODOO_MONITOR_URL")
    if not odoo_url:
        print("ODOO_MONITOR_URL not set - skipping Odoo health check")
        return
    
    print(f"[{datetime.now().isoformat()}] Checking Odoo health at: {odoo_url}")
    
    result = check_odoo_health(odoo_url)
    status = result["status"]
    
    print(f"Odoo Status: {status} - {result['message']}")
    
    # Send notification only if status is offline or error
    if status in ("offline", "error"):
        print("Sending Odoo alert notification...")
        try:
            msg_id = send_odoo_alert(
                status=status,
                message=result["message"],
                url=result["url"],
                checked_at=result["checked_at"]
            )
            print(f"Odoo alert sent! Message ID: {msg_id}")
        except Exception as e:
            print(f"Failed to send Odoo alert: {e}")


def run_system_metrics_check():
    """
    Run system metrics check and send notifications for any alerts.
    """
    print(f"[{datetime.now().isoformat()}] Checking system metrics...")
    
    result = check_system_metrics()
    alerts = result.get("alerts", [])
    duration = int(os.getenv("ALERT_DURATION_MINUTES", "15"))
    
    if not alerts:
        print("System metrics: All within thresholds")
        return
    
    print(f"System metrics: {len(alerts)} alert(s) detected")
    
    for alert in alerts:
        print(f"  - {alert['metric']}: {alert['value']:.1f}% (threshold: {alert['threshold']}%)")
        try:
            msg_id = send_system_alert(
                metric_name=alert["metric"],
                current_value=alert["value"],
                threshold=alert["threshold"],
                duration_minutes=duration,
                details=alert.get("details")
            )
            print(f"    Alert sent! Message ID: {msg_id}")
        except Exception as e:
            print(f"    Failed to send alert: {e}")


def run_health_check():
    """
    Run all health checks.
    """
    run_odoo_health_check()
    run_system_metrics_check()
    print("Health check complete.")


if __name__ == "__main__":
    run_health_check()

