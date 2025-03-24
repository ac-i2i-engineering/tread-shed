import requests
import os
from datetime import datetime


def fetch_rss():
    """
    Fetch the RSS feed and save it as an XML file.

    This function retrieves the RSS feed from The Hub (`https://thehub.amherst.edu/events.rss`),
    and saves the raw content of the response as an XML file. The filename is timestamped based
    on the current date and time, and the file is stored in the `rss_files` directory.

    The function uses the `requests` library to fetch the data and saves it in binary format.

    Returns
    -------
    None

    Examples
    --------
    >>> fetch_rss()
    """
    url = "https://thehub.amherst.edu/events.rss"
    response = requests.get(url)

    # Define the directory and file name
    directory = "access_amherst_algo/rss_scraper/rss_files"

    os.makedirs(directory, exist_ok=True)

    file_name = os.path.join(
        directory, "hub_" + datetime.now().strftime("%Y_%m_%d_%H") + ".xml"
    )

    # Save the content as an XML file
    with open(file_name, "wb") as file:
        file.write(response.content)
