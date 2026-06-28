def test_deactivate_user(create_admin_professional_client, admin_client):
    user = create_admin_professional_client["client"]
    user_id = user.user_id

    response = admin_client.delete(f"/users/{user_id}/deactivate")

    assert response.status_code == 200

def test_get_professionals(client_client, professional_profile):
    response = client_client.get("/users/professionals")

    assert response.status_code == 200

def test_get_clients(client_client):
    response = client_client.get("/users/clients")

    assert response.status_code == 200

def test_update_profile(professional_client, professional_profile):
    response = professional_client.patch("/users/me", json = {"description" : "example"})

    assert response.status_code == 200


    