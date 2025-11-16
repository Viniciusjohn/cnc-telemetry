from datetime import datetime, timedelta, timezone

from app.db import TelemetryEvents


def seed_events(session, machine_id: str = "SIM_M80_01", count: int = 5):
    base_ts = datetime(2025, 11, 14, 12, 0, tzinfo=timezone.utc)
    for offset in range(count):
        session.add(
            TelemetryEvents(
                id=offset + 1,
                machine_id=machine_id,
                timestamp_utc=base_ts - timedelta(minutes=offset),
                mode="AUTOMATIC",
                execution="EXECUTING",
                rpm=1500 + offset,
                feed_rate=250.0 + offset,
                spindle_load_pct=10.0,
                tool_id=f"T{offset:02d}",
                alarm_code=f"A{offset}",
                alarm_message=f"Alarm {offset}",
                part_count=offset,
                controller_family="MITSUBISHI_M8X",
                source="tests",
            )
        )
    session.commit()


def test_events_empty_returns_list(client):
    response = client.get('/v1/machines/SIM_M80_01/events?limit=10')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data == []


def test_events_with_data_ordered_and_limited(client, db_session):
    seed_events(db_session)

    response = client.get('/v1/machines/SIM_M80_01/events?limit=3')
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) == 3

    timestamps = [datetime.fromisoformat(item['timestamp_utc'].replace('Z', '+00:00')) for item in payload]
    assert timestamps == sorted(timestamps, reverse=True)

    for item in payload:
        for field in ('timestamp_utc', 'execution', 'mode', 'rpm', 'alarm_code', 'alarm_message'):
            assert field in item

