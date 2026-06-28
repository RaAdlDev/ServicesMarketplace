def test_create_abilitie(admin_client):
    response = admin_client.post("/abilities", json= {"name": "test"})

    assert response.status_code == 200

def test_get_abilities(professional_client):
    response = professional_client.get("/abilities")

    assert response.status_code == 200

def test_forbidden_create(client_client):
    response = client_client.post("/abilities", json = {"name": "test"})

    assert response.status_code == 403