def titles(resp):
    return resp.get_data(as_text=True)


def test_list_shows_all(client, seeded):
    page = titles(client.get("/releases"))
    assert "Showing 1 to 8 of 25 releases" in page
    assert "2.5.0" in page and "2.4.3" in page


def test_search_by_version_with_v_prefix(client, seeded):
    page = titles(client.get("/releases?q=v2.1"))
    assert "Release report exports" in page and "Session handling hardening" in page
    assert "Release workspace launch" not in page


def test_search_by_title_case_insensitive(client, seeded):
    page = titles(client.get("/releases?q=ACCESSIBLE"))
    assert "Accessible navigation and labels" in page
    assert "Release workspace launch" not in page


def test_filter_by_status_and_category(client, seeded):
    assert "Deployment backup verification" in titles(client.get("/releases?status=Scheduled"))
    page = titles(client.get("/releases?category=Patch"))
    assert "Release history performance tuning" in page
    assert "Release integrations and audit insights" not in page


def test_combined_filters(client, seeded):
    page = titles(client.get("/releases?status=Released&category=Minor&q=External+API"))
    assert "External API integration framework" in page
    assert "Release insights dashboard" not in page


def test_sort_order(client, seeded):
    newest = titles(client.get("/releases?sort=newest"))
    oldest = titles(client.get("/releases?sort=oldest"))
    assert newest.index("Release integrations and audit insights") < newest.index("Deployment backup verification")
    assert oldest.index("Release workspace launch") < oldest.index("Dashboard layout refinement")


def test_no_results_empty_state(client, seeded):
    assert "No releases match these filters" in titles(client.get("/releases?q=zzzz"))


def test_pagination(app, client, seeded):
    app.config["PER_PAGE"] = 4
    first = titles(client.get("/releases"))
    assert "Page 1 of 7" in first and "Showing 1 to 4 of 25" in first
    assert "Page 2 of 7" in titles(client.get("/releases?page=2"))
    assert "Page 7 of 7" in titles(client.get("/releases?page=99"))     # clamped
    assert "Page 1 of 7" in titles(client.get("/releases?page=abc"))    # bad input tolerated


def test_sql_wildcards_are_literal(client, seeded):
    assert "No releases match" in titles(client.get("/releases?q=%25"))
    assert "No releases match" in titles(client.get("/releases?q=_"))
