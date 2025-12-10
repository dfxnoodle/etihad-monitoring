"""
Health monitor for Odoo platform.
Checks Odoo health status and sends email notifications if offline or in error state.
Run this script via cron job every 15 minutes.
"""
import os
import time
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv
from email_notifier import send_odoo_alert

# Load environment variables
load_dotenv()


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


def run_health_check():
    """
    Run health check and send notification if Odoo is offline or in error.
    """
    odoo_url = os.getenv("ODOO_MONITOR_URL")
    if not odoo_url:
        print("Error: ODOO_MONITOR_URL not set in environment")
        return
    
    print(f"[{datetime.now().isoformat()}] Checking Odoo health at: {odoo_url}")
    
    result = check_odoo_health(odoo_url)
    status = result["status"]
    
    print(f"Status: {status} - {result['message']}")
    
    # Send notification only if status is offline or error
    if status in ("offline", "error"):
        print("Sending alert notification...")
        try:
            msg_id = send_odoo_alert(
                status=status,
                message=result["message"],
                url=result["url"],
                checked_at=result["checked_at"]
            )
            print(f"Alert sent! Message ID: {msg_id}")
        except Exception as e:
            print(f"Failed to send alert: {e}")
    else:
        print("Odoo is online. No notification needed.")


if __name__ == "__main__":
    run_health_check()
