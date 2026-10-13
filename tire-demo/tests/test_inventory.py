def event(settings, **updates):
    return {
        "event_id": "new-event",
        "product_id": "T0001",
        "store_id": "S01",
        "quantity": 7,
        "observed_epoch": int(settings.now().timestamp()) - 10,
    } | updates


def test_inventory_replays_conflicts_and_out_of_order_events(client, headers, settings):
    first = event(settings)
    assert (
        client.post("/api/tire/inventory", headers=headers, json=first).json()["outcome"]
        == "applied"
    )
    assert (
        client.post("/api/tire/inventory", headers=headers, json=first).json()["outcome"]
        == "duplicate"
    )
    assert (
        client.post(
            "/api/tire/inventory", headers=headers, json=first | {"quantity": 1}
        ).status_code
        == 409
    )
    older = event(
        settings, event_id="old-event", quantity=1, observed_epoch=first["observed_epoch"] - 1
    )
    assert (
        client.post("/api/tire/inventory", headers=headers, json=older).json()["outcome"]
        == "older_ignored"
    )
    record = client.app.state.store.query(
        "SELECT quantity FROM inventory WHERE product_id='T0001' AND store_id='S01'"
    )[0]
    assert record["quantity"] == 7


def test_scope_future_and_unknown_records_are_rejected(client, headers, settings):
    assert (
        client.post(
            "/api/tire/inventory", headers=headers, json=event(settings, store_id="S05")
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/tire/inventory",
            headers=headers,
            json=event(settings, observed_epoch=int(settings.now().timestamp()) + 1),
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/tire/inventory", headers=headers, json=event(settings, product_id="T9999")
        ).status_code
        == 404
    )


def test_freshness_boundary_and_future_stock(client, headers, settings):
    store = client.app.state.store
    now = int(settings.now().timestamp())
    with store.connection() as connection, connection:
        connection.execute("DELETE FROM inventory WHERE product_id!='T0001'")
        connection.execute("UPDATE inventory SET observed_epoch=?", (now - 1800,))
    assert client.post("/api/tire/recommendations", headers=headers, json={}).json()[
        "recommendations"
    ]
    with store.connection() as connection, connection:
        connection.execute("UPDATE inventory SET observed_epoch=?", (now - 1801,))
    assert not client.post("/api/tire/recommendations", headers=headers, json={}).json()[
        "recommendations"
    ]
    with store.connection() as connection, connection:
        connection.execute("UPDATE inventory SET observed_epoch=?", (now + 1,))
    assert not client.post("/api/tire/recommendations", headers=headers, json={}).json()[
        "recommendations"
    ]
