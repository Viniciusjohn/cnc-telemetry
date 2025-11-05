# backend/app/services/alerts.py
# Alert evaluation engine with Celery + Redis

import os
import yaml
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from celery import Celery
from redis import Redis
import hashlib

# Celery configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery('alerts', broker=REDIS_URL, backend=REDIS_URL)

# Redis client for deduplication
redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

# Global config
ALERTS_CONFIG_PATH = os.getenv("ALERTS_CONFIG_PATH", "config/alerts.yaml")


def load_alert_rules() -> Dict:
    """Load alert rules from YAML configuration"""
    try:
        with open(ALERTS_CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"⚠️  Alert config not found: {ALERTS_CONFIG_PATH}")
        return {"alerts": [], "global": {}}
    except Exception as e:
        print(f"❌ Error loading alert config: {e}")
        return {"alerts": [], "global": {}}


def eval_condition(condition: str, data: Dict) -> bool:
    """
    Safely evaluate alert condition.
    
    Args:
        condition: Python expression as string (e.g., "rpm == 0 AND state == 'running'")
        data: Dictionary with current telemetry data
    
    Returns:
        True if condition is met, False otherwise
    """
    try:
        # Create safe namespace with only allowed variables
        namespace = {
            'rpm': data.get('rpm', 0),
            'feed_mm_min': data.get('feed_mm_min', 0),
            'state': data.get('state', 'unknown'),
            'duration_seconds': data.get('duration_seconds', 0),
            'duration_min': data.get('duration_seconds', 0) / 60,
        }
        
        # Replace common operators
        condition = condition.replace('AND', 'and').replace('OR', 'or')
        
        # Evaluate safely (only arithmetic and boolean operations)
        result = eval(condition, {"__builtins__": {}}, namespace)
        return bool(result)
    
    except Exception as e:
        print(f"⚠️  Error evaluating condition '{condition}': {e}")
        return False


def get_alert_key(rule_name: str, machine_id: str) -> str:
    """Generate Redis key for alert deduplication"""
    return f"alert:{rule_name}:{machine_id}"


def is_recently_fired(rule_name: str, machine_id: str, window_seconds: int = 60) -> bool:
    """
    Check if alert was recently fired (deduplication).
    
    Args:
        rule_name: Name of the alert rule
        machine_id: Machine identifier
        window_seconds: Deduplication window in seconds
    
    Returns:
        True if alert was fired within window, False otherwise
    """
    key = get_alert_key(rule_name, machine_id)
    return redis_client.exists(key) > 0


def mark_alert_fired(rule_name: str, machine_id: str, window_seconds: int = 60):
    """Mark alert as fired in Redis with TTL"""
    key = get_alert_key(rule_name, machine_id)
    redis_client.setex(key, window_seconds, "1")


def get_recent_telemetry(machine_id: str, lookback_seconds: int = 120) -> List[Dict]:
    """
    Get recent telemetry data from database.
    
    Args:
        machine_id: Machine identifier
        lookback_seconds: How many seconds to look back
    
    Returns:
        List of telemetry samples
    """
    from ..db import get_db_context, Telemetry
    from sqlalchemy import desc
    
    cutoff = datetime.utcnow() - timedelta(seconds=lookback_seconds)
    
    with get_db_context() as db:
        samples = db.query(Telemetry).filter(
            Telemetry.machine_id == machine_id,
            Telemetry.ts >= cutoff
        ).order_by(desc(Telemetry.ts)).limit(100).all()
        
        return [
            {
                'ts': sample.ts,
                'machine_id': sample.machine_id,
                'rpm': sample.rpm,
                'feed_mm_min': sample.feed_mm_min,
                'state': sample.state,
                'sequence': sample.sequence
            }
            for sample in samples
        ]


def calculate_state_duration(samples: List[Dict], target_state: str) -> int:
    """
    Calculate how long the machine has been in a specific state.
    
    Args:
        samples: List of telemetry samples (most recent first)
        target_state: State to check duration for
    
    Returns:
        Duration in seconds
    """
    if not samples:
        return 0
    
    # Check if current state matches
    if samples[0]['state'] != target_state:
        return 0
    
    # Count consecutive samples in target state
    duration_samples = 0
    for sample in samples:
        if sample['state'] == target_state:
            duration_samples += 1
        else:
            break
    
    # Assuming 2-second polling interval
    return duration_samples * 2


def format_alert_message(rule: Dict, data: Dict) -> str:
    """
    Format alert message using template.
    
    Args:
        rule: Alert rule configuration
        data: Current telemetry data
    
    Returns:
        Formatted message string
    """
    template = rule.get('channels', [{}])[0].get('template', 
                                                   "{machine_id} alert: {rule_name}")
    
    # Format template with data
    try:
        message = template.format(
            machine_id=data.get('machine_id', 'UNKNOWN'),
            rule_name=rule['name'],
            rpm=data.get('rpm', 0),
            feed_mm_min=data.get('feed_mm_min', 0),
            state=data.get('state', 'unknown'),
            duration_min=data.get('duration_seconds', 0) / 60,
            severity=rule.get('severity', 'info')
        )
        return message
    except KeyError as e:
        return f"{data.get('machine_id')} alert: {rule['name']} (template error: {e})"


def send_slack_alert(webhook_url: str, message: str):
    """Send alert to Slack webhook"""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.post(
                webhook_url,
                json={"text": message}
            )
            response.raise_for_status()
            print(f"✅ Slack alert sent: {message[:50]}...")
    except Exception as e:
        print(f"❌ Failed to send Slack alert: {e}")


def send_webhook_alert(url: str, payload: Dict):
    """Send alert to custom webhook"""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            print(f"✅ Webhook alert sent to {url}")
    except Exception as e:
        print(f"❌ Failed to send webhook alert: {e}")


@celery_app.task(name="alerts.evaluate_all")
def evaluate_all_alerts():
    """
    Main task: Evaluate all alert rules for all machines.
    Runs periodically (every 30s by default).
    """
    config = load_alert_rules()
    alerts = config.get('alerts', [])
    global_config = config.get('global', {})
    
    dedupe_window = global_config.get('dedupe_window_seconds', 60)
    lookback = global_config.get('lookback_seconds', 120)
    
    print(f"🔍 Evaluating {len(alerts)} alert rules...")
    
    # Get list of active machines (from recent telemetry)
    from ..db import get_db_context
    from sqlalchemy import text
    
    with get_db_context() as db:
        # Get machines with data in last 5 minutes
        result = db.execute(text("""
            SELECT DISTINCT machine_id 
            FROM telemetry 
            WHERE ts > NOW() - INTERVAL '5 minutes'
        """))
        active_machines = [row.machine_id for row in result]
    
    print(f"📟 Found {len(active_machines)} active machines")
    
    alerts_fired = 0
    
    # Evaluate each rule for each machine
    for machine_id in active_machines:
        samples = get_recent_telemetry(machine_id, lookback)
        
        if not samples:
            continue
        
        current_sample = samples[0]
        
        for rule in alerts:
            # Check if rule is enabled
            if not rule.get('enabled', True):
                continue
            
            # Check if rule applies to this machine
            rule_machine_id = rule.get('machine_id', '*')
            if rule_machine_id != '*' and rule_machine_id != machine_id:
                continue
            
            # Check deduplication
            if is_recently_fired(rule['name'], machine_id, dedupe_window):
                continue
            
            # Prepare data for condition evaluation
            data = {
                'machine_id': machine_id,
                'rpm': current_sample['rpm'],
                'feed_mm_min': current_sample['feed_mm_min'],
                'state': current_sample['state'],
                'duration_seconds': 0
            }
            
            # Calculate state duration if needed
            if 'duration_seconds' in rule.get('condition', ''):
                state = current_sample['state']
                data['duration_seconds'] = calculate_state_duration(samples, state)
            
            # Evaluate condition
            condition_met = eval_condition(rule['condition'], data)
            
            if condition_met:
                # Check minimum duration requirement
                min_duration = rule.get('duration_seconds', 0)
                if data['duration_seconds'] < min_duration:
                    continue
                
                # Fire alert
                print(f"🚨 Alert triggered: {rule['name']} for {machine_id}")
                
                # Format message
                message = format_alert_message(rule, data)
                
                # Send to all channels
                for channel in rule.get('channels', []):
                    if channel['type'] == 'slack':
                        webhook_url = os.path.expandvars(channel['webhook'])
                        send_slack_alert(webhook_url, message)
                    
                    elif channel['type'] == 'webhook':
                        if channel.get('enabled', True):
                            url = os.path.expandvars(channel['url'])
                            payload = {
                                'rule': rule['name'],
                                'machine_id': machine_id,
                                'severity': rule.get('severity', 'info'),
                                'data': data,
                                'message': message,
                                'timestamp': datetime.utcnow().isoformat()
                            }
                            send_webhook_alert(url, payload)
                
                # Mark as fired
                mark_alert_fired(rule['name'], machine_id, dedupe_window)
                alerts_fired += 1
    
    print(f"✅ Alert evaluation complete. {alerts_fired} alerts fired.")
    return {"alerts_fired": alerts_fired, "machines_checked": len(active_machines)}


# Celery beat schedule
celery_app.conf.beat_schedule = {
    'evaluate-alerts-every-30s': {
        'task': 'alerts.evaluate_all',
        'schedule': 30.0,  # Every 30 seconds
    },
}

celery_app.conf.timezone = 'UTC'
