import pytest
from unittest.mock import patch, MagicMock, mock_open, call
from datetime import datetime
import json
import os
from email.message import EmailMessage

# Import specific functions from email_parser_script
from access_amherst_algo.email_scraper.email_parser import (
    connect_and_fetch_latest_email,
    extract_email_body,
    extract_event_info_using_llama,
    save_to_json_file,
    parse_email,
)

# Mock data for testing
email_content = "This is a test email with event information."
mock_response_json = [
    {
        "title": "Sample Event",
        "pub_date": "2024-11-07",
        "starttime": "09:00:00",
        "endtime": "10:00:00",
        "location": "Main Hall",
        "event_description": "Sample description",
        "host": ["Sample Host"],
        "link": "https://sample.com",
        "picture_link": "https://sample.com/image.jpg",
        "categories": ["Category 1"],
        "author_name": "John Doe",
        "author_email": "john.doe@example.com",
    }
]


@pytest.fixture
def mock_email():
    """Create a mock email message with a body."""
    msg = EmailMessage()
    msg.set_content(email_content)
    return msg


@pytest.fixture
def setup_mock_env_vars(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
    monkeypatch.setenv("EMAIL_PASSWORD", "test-password")
    monkeypatch.setenv("EMAIL_ADDRESS", "test@example.com")


def test_connect_and_fetch_latest_email(setup_mock_env_vars, mock_email):
    """Test connecting to Gmail and fetching the latest email."""
    with patch(
        "access_amherst_algo.email_scraper.email_parser.imaplib.IMAP4_SSL"
    ) as mock_imap:
        mock_instance = mock_imap.return_value
        mock_instance.login.return_value = "OK"
        mock_instance.select.return_value = ("OK", None)
        mock_instance.search.return_value = ("OK", [b"1"])
        mock_instance.fetch.return_value = (
            "OK",
            [(None, mock_email.as_bytes())],
        )

        email = connect_and_fetch_latest_email(
            app_password="test-password", subject_filter="Test Subject"
        )
        assert email is not None
        assert email.get_payload().strip() == email_content.strip()


def test_extract_email_body(mock_email):
    """Test extracting the email body from a message."""
    body = extract_email_body(mock_email)
    assert body.strip() == email_content.strip()


@patch("access_amherst_algo.email_scraper.email_parser.requests.post")
def test_extract_event_info_using_llama(mock_post, setup_mock_env_vars):
    """Test extracting event information using the LLaMA API."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "choices": [{"message": {"content": json.dumps(mock_response_json)}}]
    }

    extracted_events = extract_event_info_using_llama(email_content)
    assert extracted_events == mock_response_json


@patch(
    "access_amherst_algo.email_scraper.email_parser.open",
    new_callable=mock_open,
)
@patch(
    "access_amherst_algo.email_scraper.email_parser.os.path.exists",
    return_value=True,
)
@patch("access_amherst_algo.email_scraper.email_parser.os.makedirs")
def test_save_to_json_file(mock_makedirs, mock_exists, mock_open):
    """Test saving extracted events to a JSON file."""
    filename = "test_events.json"
    folder = "json_outputs"
    file_path = folder + "/" + filename

    # Call the function to save data to a JSON file
    save_to_json_file(mock_response_json, filename, folder)

    # Check if file open was called with the correct path and mode
    mock_open.assert_called_once_with(file_path, "w")

    # Get the actual written content
    handle = mock_open()
    written_content = "".join(
        call.args[0] for call in handle.write.call_args_list
    )

    # Create expected content and normalize both strings
    expected_content = json.dumps(mock_response_json, indent=4) + "\n"
    assert json.loads(written_content) == json.loads(expected_content)


@patch(
    "access_amherst_algo.email_scraper.email_parser.connect_and_fetch_latest_email"
)
@patch(
    "access_amherst_algo.email_scraper.email_parser.extract_email_body",
    return_value=email_content,
)
@patch(
    "access_amherst_algo.email_scraper.email_parser.extract_event_info_using_llama",
    return_value=mock_response_json,
)
@patch("access_amherst_algo.email_scraper.email_parser.save_to_json_file")
def test_parse_email(
    mock_save_to_json_file,
    mock_extract_event_info_using_llama,
    mock_extract_email_body,
    mock_connect_and_fetch_latest_email,
    setup_mock_env_vars,
    mock_email,
):
    """Test the main parse_email function."""
    mock_connect_and_fetch_latest_email.return_value = mock_email

    with patch(
        "access_amherst_algo.email_scraper.email_parser.datetime"
    ) as mock_datetime:
        mock_datetime.now.return_value = datetime(2024, 11, 7, 12, 0, 0)

        # Run parse_email with a subject filter
        parse_email("Test Subject")

        # Assertions to check if functions were called
        mock_connect_and_fetch_latest_email.assert_called_once()
        mock_extract_email_body.assert_called_once()
        mock_extract_event_info_using_llama.assert_called_once_with(
            email_content
        )
        mock_save_to_json_file.assert_called_once()


def test_connect_and_fetch_latest_email_search_failure(setup_mock_env_vars):
    """Test search failure in connect_and_fetch_latest_email."""
    with patch(
        "access_amherst_algo.email_scraper.email_parser.imaplib.IMAP4_SSL"
    ) as mock_imap:
        mock_instance = mock_imap.return_value
        mock_instance.login.return_value = "OK"
        mock_instance.select.return_value = ("OK", None)
        mock_instance.search.side_effect = Exception("Search failed")

        email = connect_and_fetch_latest_email(
            app_password="test-password", subject_filter="Test Subject"
        )
        assert email is None


def test_extract_email_body_exception_handling():
    """Test exception handling in extract_email_body."""
    mock_msg = MagicMock()
    mock_msg.is_multipart.side_effect = Exception("Unexpected error")

    body = extract_email_body(mock_msg)
    assert body is None


@patch("access_amherst_algo.email_scraper.email_parser.requests.post")
@patch("access_amherst_algo.email_scraper.email_parser.sys.exit")
def test_extract_event_info_using_llama_api_error(
    mock_exit, mock_post, setup_mock_env_vars
):
    """Test API error handling in extract_event_info_using_llama."""
    mock_post.return_value.status_code = 400
    mock_post.return_value.json.return_value = {
        "error": {"message": "Invalid request"}
    }

    extracted_events = extract_event_info_using_llama(email_content)
    # Assert that no events are extracted
    assert extracted_events == []
    # Ensure sys.exit was called with 1
    mock_exit.assert_called_once_with(1)


@patch(
    "access_amherst_algo.email_scraper.email_parser.open",
    side_effect=PermissionError("Permission denied"),
)
@patch("access_amherst_algo.email_scraper.email_parser.logging.error")
def test_save_to_json_file_permission_error(mock_logging_error, mock_open):
    """Test permission error handling in save_to_json_file."""
    save_to_json_file(mock_response_json, "test.json", "json_outputs")
    # Ensure that logging.error was called with the appropriate message
    mock_logging_error.assert_called_once_with(
        "Failed to save data to json_outputs/test.json: Permission denied"
    )


@patch(
    "access_amherst_algo.email_scraper.email_parser.connect_and_fetch_latest_email",
    side_effect=Exception("Error connecting to email"),
)
def test_parse_email_connect_exception(mock_connect_and_fetch_latest_email):
    """Test exception handling in parse_email."""
    with pytest.raises(Exception):
        parse_email("Test Subject")

@patch("access_amherst_algo.email_scraper.email_parser.requests.post")
def test_extract_event_info_using_llama_success(mock_post, setup_mock_env_vars):
    """Test successful extraction of event information using the LLaMA API."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "choices": [{"message": {"content": json.dumps(mock_response_json)}}]
    }

    extracted_events = extract_event_info_using_llama(email_content)
    assert extracted_events == mock_response_json


@patch("access_amherst_algo.email_scraper.email_parser.requests.post")
def test_extract_event_info_using_llama_api_failure(mock_post, setup_mock_env_vars):
    """Test API failure in extract_event_info_using_llama."""
    mock_post.return_value.status_code = 500
    mock_post.return_value.json.return_value = {}

    extracted_events = extract_event_info_using_llama(email_content)
    assert extracted_events == []


@patch("access_amherst_algo.email_scraper.email_parser.requests.post")
def test_extract_event_info_using_llama_invalid_json(mock_post, setup_mock_env_vars):
    """Test invalid JSON response handling in extract_event_info_using_llama."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "choices": [{"message": {"content": "invalid json"}}]
    }

    extracted_events = extract_event_info_using_llama(email_content)
    assert extracted_events == []


@patch("access_amherst_algo.email_scraper.email_parser.requests.post")
def test_extract_event_info_using_llama_key_error(mock_post, setup_mock_env_vars):
    """Test KeyError handling in extract_event_info_using_llama."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "choices": [{"message": {}}]
    }

    extracted_events = extract_event_info_using_llama(email_content)
    assert extracted_events == []

if __name__ == "__main__":
    pytest.main()
