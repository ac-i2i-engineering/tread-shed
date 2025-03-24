import pytest
from unittest.mock import patch, call
from celery.result import EagerResult

from access_amherst_algo.tasks import (
    initiate_hub_workflow,
    initiate_daily_mammoth_workflow,
    remove_old_events,
)


@pytest.mark.django_db
class TestCeleryTasks:
    @patch("access_amherst_algo.tasks.call_command")
    def test_initiate_hub_workflow(self, mock_call_command):
        # Run the task
        result = initiate_hub_workflow.apply()

        # Assert task was executed
        assert isinstance(result, EagerResult)
        assert result.status == "SUCCESS"

        # Verify call_command was called with the correct arguments
        mock_call_command.assert_called_once_with("hub_workflow")

    @patch("access_amherst_algo.tasks.call_command")
    def test_initiate_daily_mammoth_workflow(self, mock_call_command):
        # Run the task
        result = initiate_daily_mammoth_workflow.apply()

        # Assert task was executed
        assert isinstance(result, EagerResult)
        assert result.status == "SUCCESS"

        # Verify call_command was called with the correct arguments
        mock_call_command.assert_called_once_with("daily_mammoth_workflow")

    @patch("access_amherst_algo.tasks.call_command")
    def test_remove_old_events(self, mock_call_command):
        # Run the task
        result = remove_old_events.apply()

        # Assert task was executed
        assert isinstance(result, EagerResult)
        assert result.status == "SUCCESS"

        # Verify call_command was called with the correct arguments
        mock_call_command.assert_called_once_with("remove_old_events")
