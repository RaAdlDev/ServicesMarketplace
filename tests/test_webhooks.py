
from unittest.mock import patch
from services.webhooks_services import guarantee_contract, contract_failed
import pytest

@patch("services.webhooks_services.LocalSession") 
@patch("services.webhooks_services.get_conversation", return_value="conv_123")
def test_guarantee_payment_success(mock_get_conv, mock_local_session, db_session, mock_background, create_contract, create_conversation):

    mock_local_session.return_value.__enter__.return_value = db_session

    guarantee_contract(mock_background, contract_id=create_contract.contract_id, charge_id="ch_test_999")
    db_session.add(create_contract)
    db_session.flush()
    db_session.refresh(create_contract)

    assert create_contract.status == "GUARANTEED"
    assert create_contract.charge_id == "ch_test_999"

    mock_background.add_task.assert_called_once()

@patch("services.webhooks_services.LocalSession") 
@patch("services.webhooks_services.get_conversation", return_value="conv_123")
def test_contract_failed_execution(mock_get_conv, mock_local_session, db_session, mock_background,  create_contract, create_conversation):
    mock_local_session.return_value.__enter__.return_value = db_session

    contract_failed(mock_background, contract_id=create_contract.contract_id)
    db_session.add(create_contract)
    db_session.flush()
    db_session.refresh(create_contract)


    db_session.refresh(create_contract)
    assert create_contract.status == "FAILED"
    mock_background.add_task.assert_called_once()


@patch("services.webhooks_services.LocalSession")
def test_webhook_service_contract_not_found( mock_background):

    try:
        guarantee_contract(mock_background, contract_id="non_existent", charge_id="ch_1")
    except Exception as e:
        pytest.fail(f"La función se rompió con la excepción: {e}")
        
    mock_background.add_task.assert_not_called()