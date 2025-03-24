import os
import shutil
from django.core.management.base import BaseCommand
from access_amherst_algo.calendar_scraper.calendar_parser import scrape_all_pages, save_to_json
from access_amherst_algo.calendar_scraper.calendar_saver import process_calendar_events


class Command(BaseCommand):
    help = "Scrapes calendar events and saves them to the database"

    def handle(self, *args, **kwargs):
        json_dir = "access_amherst_algo/calendar_scraper/calendar_json_outputs"

        try:
            # Scrape the calendar events and save them to JSON files
            self.stdout.write("Scraping calendar events...")
            events = scrape_all_pages()
            self.stdout.write(self.style.SUCCESS("Successfully scraped calendar events."))

            # Save to json
            self.stdout.write("Saving to JSON... ")
            save_to_json(events)
            self.stdout.write(self.style.SUCCESS("Successfully saved to JSON."))

            # Process the JSON files and save events to the database
            self.stdout.write("Processing calendar events...")
            process_calendar_events()
            self.stdout.write(
                self.style.SUCCESS("Successfully processed calendar events and saved to the database.")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))
            # Raise the exception to signal failure
            raise e

        # Step 3: Clean up the JSON files after processing is complete
        try:
            self._clear_directory(json_dir)
            self.stdout.write(self.style.SUCCESS("Successfully cleaned up JSON files."))
        except Exception as cleanup_error:
            self.stdout.write(self.style.ERROR(f"Error during cleanup: {cleanup_error}"))

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