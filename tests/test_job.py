def test_post_jobs(client_client):
    response = client_client.post("/jobs", json={"title": "example", "description": "test", "budget": 200})

    assert response.status_code == 200

def test_apply_job( create_job, professional_client):
    response = professional_client.post(f"/jobs/{create_job}/apply", json={
        "abilities_description": "example", "proposal": "example"
    },)

    assert response.status_code == 200

def test_delete_job(admin_client, create_job):
    response = admin_client.delete(f"/jobs/{create_job}/delete")

    assert response.status_code == 200

def test_update_job(client_client, create_job):
    response = client_client.patch(f"jobs/{create_job}/update", json = {
        "title": "modify", "description": "modify_description", "budget": 500
    })

    assert response.status_code == 200

def test_update_job_forbidden_other_client(create_job, client_2_client):
    response = client_2_client.patch(f"jobs/{create_job}/update", json = {
        "title": "modify", "description": "modify_description", "budget": 500
    })

    assert response.status_code == 409

def test_delete_job_forbidden_other_client(create_job, client_2_client):
    response = client_2_client.delete(f"jobs/{create_job}/delete")

    assert response.status_code == 409
def test_apply_job_twice_forbidden(create_job, professional_client):
    first_response =professional_client.post(f"/jobs/{create_job}/apply", json={
        "abilities_description": "example", "proposal": "example"
    },)
    assert first_response.status_code == 200
    response = professional_client.post(f"/jobs/{create_job}/apply", json={
        "abilities_description": "example", "proposal": "example"
    },)

    assert response.status_code == 409
def test_apply_job_as_client_forbidden(create_job, client_client):
    response = client_client.post(f"/jobs/{create_job}/apply", json={
        "abilities_description": "example", "proposal": "example"
    },)

    assert response.status_code == 403
def test_update_job_as_professional_forbidden(create_job, professional_client):
    response = professional_client.patch(f"jobs/{create_job}/update", json = {
        "title": "modify", "description": "modify_description", "budget": 500
    })

    assert response.status_code == 403
