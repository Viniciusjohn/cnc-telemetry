from app.routers import status as status_router


def test_status_contract(client):
    response = client.get("/v1/machines/SIM_M80_01/status")
    assert response.status_code == 200

    data = response.json()

    required_fields = [
        "machine_id",
        "controller_family",
        "timestamp_utc",
        "mode",
        "execution",
        "rpm",
        "feed_rate",
        "update_interval_ms",
        "source",
    ]
    for field in required_fields:
        assert field in data, f"{field} não encontrado no payload"

    optional_fields = [
        "spindle_load_pct",
        "tool_id",
        "alarm_code",
        "alarm_message",
        "part_count",
    ]
    for field in optional_fields:
        assert field in data

    assert data["update_interval_ms"] == 1000


def test_status_handles_null_fields(client):
    """Garante que valores None não quebram a resposta padrão."""
    status_router.LAST_STATUS.clear()

    response = client.get("/v1/machines/SIM_M80_01/status")
    assert response.status_code == 200

    data = response.json()
    assert data["spindle_load_pct"] is None
    assert data["alarm_code"] is None
    assert data["alarm_message"] is None
