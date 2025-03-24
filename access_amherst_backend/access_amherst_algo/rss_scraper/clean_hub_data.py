import json
from datetime import datetime
from access_amherst_algo.rss_scraper.parse_rss import create_events_list
import re
import os


def clean_hub_data(events_list=None):
    """
    Clean and preprocess a list of data from events.

    This function processes a list of events by performing the following steps:
    - Removes events that are marked as "Cancelled" in the title.
    - Splits the author information into separate `author_name` and `author_email` fields.
    - Assigns a unique ID to each event based on its link.
    - Saves the cleaned event data to a timestamped JSON file for later use.

    If no `events_list` is provided, the function will create one by calling `create_events_list()`.

    Parameters
    ----------
    events_list : list of dict, optional
        A list of events to be cleaned. If not provided, the function will generate 
        the list using `create_events_list()`.

    Returns
    -------
    list of dict
        A list of cleaned event dictionaries, with updated author information and 
        cancelled events removed.

    Examples
    --------
    >>> events = clean_hub_data()
    >>> print(events[0]["author_email"])
    'literature@amherst.edu'
    """
    if events_list is None:
        events_list = create_events_list()

    cleaned_events = []
    for event in events_list:
        # Remove cancelled events
        if "Cancelled" in event["title"]:
            continue

        # Split author into name and email
        if event["author"] is not None:
            author_email, author_name = event["author"].split(" (", 1)
            author_name = author_name[
                :-1
            ]  # Remove the last character which is ')'
            event["author_name"] = author_name
            event["author_email"] = author_email
            del event["author"]
        else:
            event["author_name"] = None
            event["author_email"] = None

        # Generate unique event ID
        event["id"] = (
            int(re.search(r"/(\d+)$", event["link"]).group(1)) + 500_000_000
        )

        cleaned_events.append(event)

    # Define the directory and output file name
    directory = "access_amherst_algo/rss_scraper/cleaned_json_outputs"
    os.makedirs(directory, exist_ok=True)  # Ensure the directory exists
    output_file_name = directory + "/hub_" + datetime.now().strftime("%Y_%m_%d_%H") + ".json"

    # Save the cleaned data to a JSON file
    with open(output_file_name, "w") as f:
        json.dump(cleaned_events, f, indent=4)

    return cleaned_events
