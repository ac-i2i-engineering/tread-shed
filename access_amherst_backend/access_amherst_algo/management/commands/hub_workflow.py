import os
import shutil
from django.core.management.base import BaseCommand
from access_amherst_algo.rss_scraper.fetch_rss import fetch_rss
from access_amherst_algo.rss_scraper.parse_rss import (
    create_events_list,
    save_json,
    save_to_db,
)


class Command(BaseCommand):
    help = "Fetches the RSS feed from the Amherst Hub into DB"

    def handle(self, *args, **kwargs):
        rss_dir = "access_amherst_algo/rss_scraper/rss_files"
        json_dir = "access_amherst_algo/rss_scraper/cleaned_json_outputs"

        try:
            # Perform the RSS fetch and saving to DB
            fetch_rss()
            create_events_list()
            save_json()
            save_to_db()

            self.stdout.write(
                self.style.SUCCESS(
                    "Successfully fetched the RSS feed and saved to the database."
                )
            )

            # Clear directories
            self._clear_directory(rss_dir)
            self._clear_directory(json_dir)
            self._clear_directory(
                "access_amherst_algo/rss_scraper/json_outputs"
            )

            self.stdout.write(
                self.style.SUCCESS("Successfully cleaned up files.")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))

            # Clear directories even on failure
            self._clear_directory(rss_dir)
            self._clear_directory(json_dir)

            # Raise exception to signal failure
            raise e

    @staticmethod
    def _clear_directory(directory):
        """Clears all files in the specified directory."""
        if os.path.exists(directory):
            for file_name in os.listdir(directory):
                file_path = os.path.join(directory, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
