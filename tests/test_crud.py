from conftest import VALID, post, token


def test_create_release_and_view(admin):
    resp = post(admin, "/releases/new", VALID)
    assert resp.status_code == 302
    page = admin.get(resp.headers["Location"]).get_data(as_text=True)
    assert "Major redesign" in page and "A substantial redesign" in page
    assert "New dashboard" in page and "Fixed crash" in page
    assert "Restart service" in page


def test_create_flash_message_shown(admin):
    resp = admin.post("/releases/new", data={**VALID, "csrf_token": token(admin, "/releases/new")},
                      follow_redirects=True)
    assert b"was created" in resp.data


def test_version_prefix_v_is_normalised(admin):
    resp = post(admin, "/releases/new", {**VALID, "version": "v3.1.0"})
    assert resp.status_code == 302
    assert "v3.1.0" in admin.get(resp.headers["Location"]).get_data(as_text=True)


def test_detail_unknown_release_is_404(client):
    assert client.get("/releases/9999").status_code == 404


def test_edit_prepopulated_and_updates(admin, seeded):
    page = admin.get("/releases/1/edit").get_data(as_text=True)
    assert 'value="1.6.0"' in page and "Release workspace launch" in page
    resp = post(admin, "/releases/1/edit", {**VALID, "version": "1.6.0", "title": "Renamed release"})
    assert resp.status_code == 302
    assert "Renamed release" in admin.get("/releases/1").get_data(as_text=True)


def test_edit_keeps_own_version_but_rejects_taken_one(admin, seeded):
    ok = post(admin, "/releases/2/edit", {**VALID, "version": "1.6.1"})
    assert ok.status_code == 302
    clash = post(admin, "/releases/2/edit", {**VALID, "version": "1.6.0"})
    assert clash.status_code == 422 and b"already exists" in clash.data


def test_edit_unknown_release_is_404(admin):
    assert admin.get("/releases/777/edit").status_code == 404
    assert post(admin, "/releases/777/edit", VALID, token_from="/releases/new").status_code == 404


def test_delete_requires_confirmation_then_deletes(admin, seeded):
    confirm = admin.get("/releases/3/delete")
    assert confirm.status_code == 200 and b"cannot be undone" in confirm.data
    assert admin.get("/releases/3").status_code == 200       # GET did not delete
    resp = post(admin, "/releases/3/delete")
    assert resp.status_code == 302
    assert admin.get("/releases/3").status_code == 404


def test_delete_unknown_release_is_404(admin):
    assert admin.get("/releases/4242/delete").status_code == 404


def test_detail_navigation_links(client, seeded):
    page = client.get("/releases/3").get_data(as_text=True)
    assert "v1.6.1" in page and "v1.7.0" in page     # previous and next releases


def test_create_release_after_seeded_demo_data(admin, seeded):
    resp = post(admin, "/releases/new", VALID)
    assert resp.status_code == 302
    page = admin.get("/releases").get_data(as_text=True)
    assert "Showing 1 to 8 of 26 releases" in page
