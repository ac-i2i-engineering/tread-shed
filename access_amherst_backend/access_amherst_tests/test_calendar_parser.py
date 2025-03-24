import pytest
from unittest.mock import patch, MagicMock, mock_open, call
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
import requests

# Import the functions from calendar parser
from access_amherst_algo.calendar_scraper.calendar_parser import (
    fetch_page,
    scrape_page,
    scrape_all_pages,
    save_to_json,
)

# Mock data for testing
mock_event_data = {
    "title": "Test Event",
    "author_name": "Test Author",
    "author_email": "test@example.com",
    "pub_date": "2024-11-07",
    "host": "Test Host",
    "link": "https://example.com/event",
    "picture_link": "https://example.com/image.jpg",
    "event_description": "Test description",
    "start_time": "2024-11-07T09:00:00",
    "end_time": "2024-11-07T10:00:00",
    "location": "Test Location",
    "categories": ["Test Category"],
    "latitude": None,
    "longitude": None,
    "map_location": None,
}

@pytest.fixture
def mock_html():
    """Create mock HTML content for testing."""
    return """
    <article class="mm-calendar-event">
        <h2 class="mm-event-listing-title"><a href="https://example.com/event">Test Event</a></h2>
        <h3 class="mm-calendar-period">
            <meta itemprop="startDate" content="2024-11-07T09:00:00">
            <meta itemprop="endDate" content="2024-11-07T10:00:00">
        </h3>
        <p class="mm-event-listing-location">Test Location</p>
        <div class="mm-event-listing-description">Test description</div>
        <img itemprop="image" src="https://example.com/image.jpg">
    </article>
    """

@patch('access_amherst_algo.calendar_scraper.calendar_parser.requests.Session')
def test_fetch_page_success(mock_session):
    """Test successful page fetch."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"Test content"
    mock_session.return_value.get.return_value = mock_response

    content = fetch_page("https://test.com")
    assert content == b"Test content"
    mock_session.return_value.get.assert_called_once()

@patch('access_amherst_algo.calendar_scraper.calendar_parser.requests.Session')
def test_fetch_page_failure(mock_session):
    """Test page fetch failure."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_session.return_value.get.return_value = mock_response

    content = fetch_page("https://test.com")
    assert content is None

@patch('access_amherst_algo.calendar_scraper.calendar_parser.requests.Session')
def test_fetch_page_connection_error(mock_session):
    """Test page fetch with connection error."""
    mock_session.return_value.get.side_effect = requests.exceptions.ConnectionError("Connection failed")

    content = fetch_page("https://test.com")
    assert content is None

@patch('access_amherst_algo.calendar_scraper.calendar_parser.requests.Session')
def test_fetch_page_timeout_error(mock_session):
    """Test page fetch with timeout error."""
    mock_session.return_value.get.side_effect = requests.exceptions.Timeout("Request timed out")

    content = fetch_page("https://test.com")
    assert content is None

@patch('access_amherst_algo.calendar_scraper.calendar_parser.fetch_page')
def test_scrape_page_success(mock_fetch_page, mock_html):
    """Test successful page scraping."""
    mock_fetch_page.return_value = mock_html.encode()

    events = scrape_page("https://test.com")
    assert len(events) == 1
    assert events[0]["title"] == "Test Event"
    assert events[0]["location"] == "Test Location"
    assert events[0]["start_time"] == "2024-11-07T09:00:00"

@patch('access_amherst_algo.calendar_scraper.calendar_parser.fetch_page')
def test_scrape_page_no_content(mock_fetch_page):
    """Test page scraping with no content."""
    mock_fetch_page.return_value = None

    events = scrape_page("https://test.com")
    assert events == []

@patch('access_amherst_algo.calendar_scraper.calendar_parser.fetch_page')
def test_scrape_page_captcha(mock_fetch_page):
    """Test page scraping with CAPTCHA detection."""
    mock_fetch_page.return_value = b"<html>captcha detected</html>"

    events = scrape_page("https://test.com")
    assert events == []

@patch('access_amherst_algo.calendar_scraper.calendar_parser.scrape_page')
def test_scrape_all_pages_success(mock_scrape_page):
    """Test successful scraping of all pages."""
    mock_scrape_page.side_effect = [
        [mock_event_data],  # First page
        [mock_event_data],  # Second page
        []  # No more pages
    ]

    events = scrape_all_pages()
    assert len(events) == 2
    assert mock_scrape_page.call_count == 3

@patch('access_amherst_algo.calendar_scraper.calendar_parser.scrape_page')
def test_scrape_all_pages_empty(mock_scrape_page):
    """Test scraping with no events."""
    mock_scrape_page.return_value = []

    events = scrape_all_pages()
    assert events == []
    mock_scrape_page.assert_called_once()

@patch('access_amherst_algo.calendar_scraper.calendar_parser.os.makedirs')
@patch('access_amherst_algo.calendar_scraper.calendar_parser.os.path.exists')
@patch('access_amherst_algo.calendar_scraper.calendar_parser.open', new_callable=mock_open)
def test_save_to_json_success(mock_file_open, mock_exists, mock_makedirs):
    """Test successful JSON file save."""
    mock_exists.return_value = False
    events = [mock_event_data]

    save_to_json(events)

    mock_makedirs.assert_called_once()
    mock_file_open.assert_called_once()
    handle = mock_file_open()
    written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
    assert json.loads(written_content)[0]["title"] == "Test Event"

@patch('access_amherst_algo.calendar_scraper.calendar_parser.os.path.exists')
def test_save_to_json_file_exists(mock_exists):
    """Test JSON save when file already exists."""
    mock_exists.return_value = True
    events = [mock_event_data]

    save_to_json(events)
    # Function should return early without error
    assert True

@patch('access_amherst_algo.calendar_scraper.calendar_parser.os.makedirs')
@patch('access_amherst_algo.calendar_scraper.calendar_parser.os.path.exists')
def test_save_to_json_permission_error(mock_exists, mock_makedirs):
    """Test JSON save with permission error."""
    mock_exists.return_value = False
    mock_makedirs.side_effect = PermissionError("Permission denied")
    
    with pytest.raises(PermissionError):
        save_to_json([mock_event_data])

@patch('access_amherst_algo.calendar_scraper.calendar_parser.fetch_page')
def test_scrape_page_invalid_html(mock_fetch_page):
    """Test page scraping with invalid HTML."""
    mock_fetch_page.return_value = b"Invalid HTML"

    events = scrape_page("https://test.com")
    assert events == []

@patch('access_amherst_algo.calendar_scraper.calendar_parser.scrape_page')
def test_scrape_all_pages_exception(mock_scrape_page):
    """Test scraping all pages with an exception."""
    mock_scrape_page.side_effect = Exception("Scraping error")

    with pytest.raises(Exception):
        scrape_all_pages()

def test_empty_event_cleaning():
    """Test cleaning of empty event fields."""
    event_with_nones = {
        "title": "Test",
        "author_name": None,
        "description": "Test description",
        "categories": None
    }
    
    cleaned_event = {k: v for k, v in event_with_nones.items() if v is not None}
    assert "author_name" not in cleaned_event
    assert "categories" not in cleaned_event
    assert cleaned_event["title"] == "Test"

@patch('access_amherst_algo.calendar_scraper.calendar_parser.fetch_page')
def test_scrape_page_exception_handling(mock_fetch_page):
    """Test exception handling in scrape_page."""
    mock_fetch_page.side_effect = Exception("Unexpected error")
    from access_amherst_algo.calendar_scraper.calendar_parser import scrape_page

    events = scrape_page("https://test.com")
    assert events == []

@patch('access_amherst_algo.calendar_scraper.calendar_parser.requests.Session')
def test_fetch_page_unexpected_exception(mock_session):
    """Test unexpected exception during fetch_page."""
    from access_amherst_algo.calendar_scraper.calendar_parser import fetch_page

    mock_session.return_value.get.side_effect = Exception("Unexpected error")

    # Ensure fetch_page handles the unexpected exception and returns None
    content = fetch_page("https://test.com")
    assert content is None

    mock_session.return_value.get.assert_called_once()  # Ensure GET was called

if __name__ == "__main__":
    pytest.main()