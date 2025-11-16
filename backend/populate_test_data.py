#!/usr/bin/env python3
# backend/populate_test_data.py
# Script para popular dados de teste (30 dias de telemetria)

import psycopg2
from datetime import datetime, timedelta
import random
import os

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cnc_user:cnc_telemetry_2025@localhost/cnc_telemetry"
)

def populate_test_data(machine_id="CNC-SIM-001", days=30):
    """
    Popula dados de teste para OEE calculation.
    
    Args:
        machine_id: Machine identifier
        days: Number of days to generate (default: 30)
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        now = datetime.now()
        total_samples = 0
        
        print(f"🚀 Populating test data for {machine_id}...")
        print(f"📅 Generating {days} days of data")
        
        for day in range(days):
            date = now - timedelta(days=day)
            
            # 8 hours of operation per day (06:00-14:00)
            # Sampling every minute for speed (in production it's every 2s)
            for hour in range(6, 14):
                for minute in range(0, 60):
                    ts = datetime(date.year, date.month, date.day, hour, minute, 0)
                    
                    # Simulate realistic states
                    # 70% running, 20% idle, 10% stopped
                    rand = random.random()
                    
                    if rand < 0.70:
                        # Running state
                        state = 'running'
                        rpm = random.randint(4000, 5000)
                        feed = random.randint(1000, 1500)
                    elif rand < 0.90:
                        # Idle state
                        state = 'idle'
                        rpm = random.randint(0, 500)
                        feed = random.randint(0, 100)
                    else:
                        # Stopped state
                        state = 'stopped'
                        rpm = 0
                        feed = 0
                    
                    try:
                        cur.execute("""
                            INSERT INTO telemetry (ts, machine_id, rpm, feed_mm_min, state)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                        """, (ts, machine_id, rpm, feed, state))
                        total_samples += 1
                    except Exception as e:
                        print(f"⚠️  Error inserting sample: {e}")
                
                # Commit every hour
                conn.commit()
            
            print(f"✅ Day {days-day}/{days} complete ({date.strftime('%Y-%m-%d')})")
        
        print(f"\n✅ Test data populated successfully!")
        print(f"📊 Total samples: {total_samples}")
        print(f"📊 Expected: {days * 8 * 60}")
        
        # Show summary
        cur.execute("""
            SELECT 
                DATE(ts) AS date,
                COUNT(*) AS samples,
                SUM(CASE WHEN state='running' THEN 1 ELSE 0 END) AS running,
                SUM(CASE WHEN state='stopped' THEN 1 ELSE 0 END) AS stopped,
                SUM(CASE WHEN state='idle' THEN 1 ELSE 0 END) AS idle,
                ROUND(SUM(CASE WHEN state='running' THEN 1 ELSE 0 END)::NUMERIC / COUNT(*) * 100, 1) AS uptime_pct
            FROM telemetry 
            WHERE machine_id = %s
            GROUP BY DATE(ts)
            ORDER BY date DESC
            LIMIT 7
        """, (machine_id,))
        
        print("\n📈 Last 7 days summary:")
        print("Date       | Samples | Running | Stopped | Idle | Uptime %")
        print("-" * 70)
        
        for row in cur:
            print(f"{row[0]} | {row[1]:7d} | {row[2]:7d} | {row[3]:7d} | {row[4]:4d} | {row[5]:6.1f}%")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Populate test telemetry data')
    parser.add_argument('--machine-id', default='CNC-SIM-001', help='Machine ID')
    parser.add_argument('--days', type=int, default=30, help='Number of days to generate')
    
    args = parser.parse_args()
    
    populate_test_data(machine_id=args.machine_id, days=args.days)
