"""Scenario CRUD + projection/solve API tests — FR-SCN-*, FR-AUTH-5, and the /project & /solve
happy paths.
"""
import pytest


@pytest.fixture()
def auth_client(client):
    client.post("/api/auth/register", json={"email": "owner@example.com", "password": "correcthorse1"})
    return client


def test_create_scenario_with_defaults(auth_client):
    resp = auth_client.post("/api/scenarios", json={"name": "Base case"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Base case"
    assert body["inputs"]["current_age"] == 43
    assert body["inputs"]["current_corpus"] == "15000000.00"
    assert len(body["dependents"]) == 2


def test_create_scenario_rejects_duplicate_name(auth_client):
    auth_client.post("/api/scenarios", json={"name": "Base case"})
    resp = auth_client.post("/api/scenarios", json={"name": "Base case"})
    assert resp.status_code == 409


def test_create_scenario_validates_age_ordering(auth_client):
    resp = auth_client.post(
        "/api/scenarios",
        json={
            "name": "Bad ages",
            "inputs": {
                "current_age": 50,
                "retirement_age": 40,  # before current_age -> invalid
                "life_expectancy": 80,
                "current_corpus": "1000000",
                "annual_expense_today": "500000",
                "expense_inflation": "0.07",
                "pre_retirement_return": "0.10",
                "post_retirement_return": "0.10",
            },
        },
    )
    assert resp.status_code == 422


def test_list_scenarios_includes_verdict(auth_client):
    auth_client.post("/api/scenarios", json={"name": "Base case"})
    resp = auth_client.get("/api/scenarios")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["verdict"] in ("sustainable", "shortfall")
    assert items[0]["verdict"] == "shortfall"  # sample defaults are known to fall short
    assert items[0]["exhaustion_age"] == 67  # matches PRD.md's documented monthly-mode result


def test_get_scenario_requires_auth(client):
    resp = client.get("/api/scenarios/1")
    assert resp.status_code == 401


def test_cross_user_scenario_returns_404_not_403(client):
    client.post("/api/auth/register", json={"email": "u1@example.com", "password": "correcthorse1"})
    created = client.post("/api/scenarios", json={"name": "Mine"})
    scenario_id = created.json()["id"]

    client.post("/api/auth/logout")
    client.cookies.clear()
    client.post("/api/auth/register", json={"email": "u2@example.com", "password": "correcthorse1"})

    resp = client.get(f"/api/scenarios/{scenario_id}")
    assert resp.status_code == 404  # not 403 (FR-AUTH-5)


def test_patch_updates_a_single_field(auth_client):
    created = auth_client.post("/api/scenarios", json={"name": "Base case"})
    scenario_id = created.json()["id"]

    resp = auth_client.patch(f"/api/scenarios/{scenario_id}", json={"inputs": {"retirement_age": 60}})
    assert resp.status_code == 200
    assert resp.json()["inputs"]["retirement_age"] == 60
    assert resp.json()["inputs"]["current_age"] == 43  # unrelated fields untouched


def test_duplicate_scenario_deep_copies_and_renames(auth_client):
    created = auth_client.post("/api/scenarios", json={"name": "Base case"})
    scenario_id = created.json()["id"]

    dup = auth_client.post(f"/api/scenarios/{scenario_id}/duplicate")
    assert dup.status_code == 201
    body = dup.json()
    assert body["name"] == "Base case (copy)"
    assert len(body["dependents"]) == 2
    assert body["id"] != scenario_id


def test_delete_scenario_removes_it(auth_client):
    created = auth_client.post("/api/scenarios", json={"name": "Base case"})
    scenario_id = created.json()["id"]

    resp = auth_client.delete(f"/api/scenarios/{scenario_id}")
    assert resp.status_code == 204
    resp2 = auth_client.get(f"/api/scenarios/{scenario_id}")
    assert resp2.status_code == 404


def test_project_returns_expected_shape_and_matches_golden_summary(auth_client):
    created = auth_client.post("/api/scenarios", json={"name": "Base case"})
    scenario_id = created.json()["id"]

    resp = auth_client.post(f"/api/scenarios/{scenario_id}/project", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "monthly"
    assert body["summary"]["verdict"] == "shortfall"
    assert body["summary"]["exhaustion_age"] == 67
    assert len(body["rows"]) == body["meta"]["months"]
    assert body["rows"][0]["corpus_start"] == "15000000.00"


def test_project_with_transient_overrides_does_not_persist(auth_client):
    created = auth_client.post("/api/scenarios", json={"name": "Base case"})
    scenario_id = created.json()["id"]

    resp = auth_client.post(
        f"/api/scenarios/{scenario_id}/project",
        json={"inputs": {"retirement_age": 60}},
    )
    assert resp.status_code == 200
    assert resp.json()["meta"]["retirement_age"] == 60

    saved = auth_client.get(f"/api/scenarios/{scenario_id}")
    assert saved.json()["inputs"]["retirement_age"] == 43  # unchanged on disk


def test_solve_required_corpus(auth_client):
    created = auth_client.post("/api/scenarios", json={"name": "Base case"})
    scenario_id = created.json()["id"]

    resp = auth_client.post(f"/api/scenarios/{scenario_id}/solve", json={"target": "required_corpus"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["feasible"] is True
    assert float(body["value"]) > 15_000_000


def test_solve_longevity(auth_client):
    created = auth_client.post("/api/scenarios", json={"name": "Base case"})
    scenario_id = created.json()["id"]

    resp = auth_client.post(f"/api/scenarios/{scenario_id}/solve", json={"target": "longevity"})
    assert resp.status_code == 200
    assert resp.json()["value"] == "67"


def test_anonymous_projection_requires_no_login(client):
    resp = client.post(
        "/api/project/anonymous",
        json={
            "inputs": {
                "current_age": 30,
                "retirement_age": 60,
                "life_expectancy": 85,
                "current_corpus": "1000000",
                "annual_expense_today": "400000",
                "expense_inflation": "0.06",
                "pre_retirement_return": "0.12",
                "post_retirement_return": "0.08",
            }
        },
    )
    assert resp.status_code == 200
    assert resp.json()["summary"]["verdict"] in ("sustainable", "shortfall")
