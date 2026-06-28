from unittest.mock import patch, MagicMock
def test_register(client):
    response = client.post("/auth/register", json={"username": "Example",
        "email": "example@example.com", "password": "Test123*", "role": "CLIENT"})


    
    assert response.status_code == 200

def test_email_duplicated(client, create_admin_professional_client):

    response = client.post(url="/auth/register", json={
        "username": "example",
        "email": "test@test1.com",
        "password": "Example123*",
            "role": "CLIENT"
            })


    assert response.status_code == 409

def test_login(client, create_admin_professional_client):
    response = client.post(url="/auth/login", json={
   "email": "test@test2.com",
    "password": "Test123*"
        })


    assert response.status_code == 200
    assert "token" in response.json()
    assert response.json()["token_type"] == "bearer"
   
    
def test_invalid_credentials(client, create_admin_professional_client):
    user = create_admin_professional_client["client"]
    response = client.post(url="/auth/login", json={"email": user.email, "password": "bad_request"})

   
    assert response.status_code == 401

@patch("services.auth_services.stripe.AccountLink.create")
@patch("services.auth_services.stripe.Account.create")
def test_professional_register(mock_account_create, mock_link_create, client, create_admin_professional_client):
    mock_account = MagicMock()
    mock_account.id = "acct_test_123"
    mock_account_create.return_value = mock_account

    mock_link = MagicMock()
    mock_link.url = "https://stripe.com/onboarding"
    mock_link_create.return_value = mock_link

    response = client.post("/auth/register", json={
        "username": "prof_test",
        "email": "prof@test.com",
        "password": "Test123*",
        "role": "PROFESSIONAL"
    })

    assert response.status_code == 200
    assert response.json()["stripe_connect_id"] == "acct_test_123"
    assert response.json()["stripe_url"] == "https://stripe.com/onboarding"








