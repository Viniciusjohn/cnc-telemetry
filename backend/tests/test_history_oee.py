from datetime import datetime, timedelta, timezone

from app.db import Telemetry


def _seed_telemetry_samples(db_session, count=5):
    base_ts = datetime.now(timezone.utc)
    for offset in range(count):
        db_session.add(
            Telemetry(
                ts=base_ts - timedelta(minutes=offset),
                machine_id='SIM_M80_01',
                rpm=2000 + offset,
                feed_mm_min=300 + offset,
                state='running',
                sequence=offset,
                src='tests'
            )
        )
    db_session.commit()


def test_history_raw_shape(client, db_session):
    _seed_telemetry_samples(db_session)
    response = client.get('/v1/machines/SIM_M80_01/history?resolution=raw&limit=10')
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    if data:
        first = data[0]
        for field in ('timestamp_utc', 'rpm', 'mode', 'execution'):
            assert field in first


def test_oee_shape(client):
    response = client.get('/v1/machines/SIM_M80_01/oee')
    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload, dict)
    for field in ('availability', 'performance', 'quality', 'oee'):
        assert field in payload
