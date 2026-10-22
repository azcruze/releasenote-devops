def test_dashboard_api_returns_database_analytics(client, seeded):
    response = client.get("/api/dashboard")
    body = response.get_json()

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert body["total"] == 25
    assert body["status_counts"] == {
        "Draft": 1, "Scheduled": 2, "Released": 18,
        "Rolled Back": 2, "Deprecated": 2,
    }
    assert body["category_counts"] == {"Major": 2, "Minor": 9, "Patch": 11}
    assert sum(body["monthly_counts"]) == 25
    assert body["recent"][0]["version"] == "2.5.0"


def test_dashboard_api_search_status_and_release_type_filters(client, seeded):
    response = client.get("/api/dashboard?q=security&category=Security&status=Released")
    body = response.get_json()

    assert response.status_code == 200
    assert body["total"] == 1
    assert body["recent"][0]["version"] == "2.3.1"
    assert body["category_counts"] == {"Major": 0, "Minor": 0, "Patch": 0}
    assert body["status_counts"]["Released"] == 1


def test_dashboard_api_date_range_limits_analytics(client, seeded):
    response = client.get("/api/dashboard?start=2026-01-01&end=2026-12-31")
    body = response.get_json()

    assert response.status_code == 200
    assert body["total"] == 7
    assert sum(body["monthly_counts"]) == 7
    assert body["months"][0] == "2026-01"
    assert body["months"][-1] == "2026-12"


def test_dashboard_calendar_returns_scheduled_releases_for_selected_month(client, seeded):
    response = client.get("/api/dashboard?month=2026-11")
    calendar_data = response.get_json()["calendar"]

    assert response.status_code == 200
    assert calendar_data["month_name"] == "November 2026"
    assert [release["version"] for release in calendar_data["scheduled"]] == ["2.5.0"]


def test_dashboard_api_rejects_invalid_date_ranges(client):
    reversed_range = client.get("/api/dashboard?start=2026-12-01&end=2026-01-01")
    malformed_date = client.get("/api/dashboard?start=2026-13-45")
    malformed_month = client.get("/api/dashboard?month=2026-13")
    overly_wide_range = client.get("/api/dashboard?start=2000-01-01&end=2026-01-01")

    assert reversed_range.status_code == 400
    assert "start date" in reversed_range.get_json()["error"]
    assert malformed_date.status_code == 400
    assert malformed_month.status_code == 400
    assert overly_wide_range.status_code == 400


def test_empty_dashboard_analytics_has_empty_chart_and_calendar_data(client):
    body = client.get("/api/dashboard").get_json()

    assert body["total"] == 0
    assert set(body["status_counts"].values()) == {0}
    assert set(body["category_counts"].values()) == {0}
    assert set(body["monthly_counts"]) == {0}
    assert body["calendar"]["scheduled"] == []
    assert body["upcoming"] == []


def test_dashboard_renders_real_analytics_widgets(client, seeded):
    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Welcome to ReleaseNote" in html
    assert 'id="monthly-chart"' in html
    assert 'id="status-chart"' in html
    assert 'id="types-chart"' in html
    assert "Release calendar" in html
    assert "Upcoming releases" in html
    assert "Deployment backup verification" in html
