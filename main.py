# File: main.py
import os
import random
import json
import requests
from app_base import ApplicationBase

from loguru import logger
# logger.add("app.log", level="DEBUG")  # Logs to a file with debug level

STATISTICAL_SECURITY = 2**6
RING_DATA_FILE = "https://raw.githubusercontent.com/snwagh/pairwise-keys/data/data.json"


class PairwiseKeys(ApplicationBase):
    def __init__(self):
        # Define app-specific name
        self.app_name = "pairwise-keys"

        # Initialize the base class
        super().__init__(os.environ.get("SYFTBOX_CLIENT_CONFIG_PATH"))

        # Set user_id and neighbors in the ring
        self.my_user_id = self.client_config["email"]
        self.prev_user_id, self.next_user_id = self.get_neighbors()

    def get_neighbors(self):
        """
        Determine previous and next neighbors in the ring based on the data file.
        """
        data = json.loads(requests.get(RING_DATA_FILE).text)
        ring_participants = data["ring"]

        try:
            index = ring_participants.index(self.my_user_id)
        except ValueError:
            raise ValueError(f"user_id {self.my_user_id} not found in the ring.")

        prev_index = (index - 1) % len(ring_participants)  # Cyclic previous
        next_index = (index + 1) % len(ring_participants)  # Cyclic next

        logger.info(
            f"Neighbors determined: previous={ring_participants[prev_index]}, next={ring_participants[next_index]}"
        )
        return ring_participants[prev_index], ring_participants[next_index]

    def setup_folder_perms(self):
        """
        Configure specific permissions for the first and second folders.
        """
        # First folder in next ring member - writable by myself, readable by next
        next_dir_path = self.app_dir(self.next_user_id) / "first"
        self.set_permissions(next_dir_path, [self.next_user_id], [self.my_user_id])

        # Second folder - fully private
        my_dir_path = self.app_dir(self.my_user_id) / "second"
        self.set_permissions(my_dir_path, [self.my_user_id], [self.my_user_id])

        logger.info("Folder permissions set up.")

    def check_key_exists(self, key_number):
        """
        Check if the key file exists in the specified folder.
        :param key_number: The name of the folder ('first' or 'second').
        """
        assert key_number in ["first", "second"], "Invalid folder name."
        key_file = self.app_dir(self.my_user_id) / key_number / "key.txt"
        exists = key_file.exists()
        logger.debug(f"Checking if {key_file} exists: {exists}")
        return exists

    def create_secret_value(self):
        """
        Generate a random secret value and write it to the second folder.
        """
        secret_value = random.randint(1, STATISTICAL_SECURITY)
        key_file_path = self.app_dir(self.my_user_id) / "second" / "key.txt"
        self.create_file(key_file_path, str(secret_value))
        logger.info(f"Created secret value in {key_file_path}")
        return secret_value

    def write_to_next_person(self, secret_value):
        """
        Write the secret value to the 'first' folder of the next person in the ring.
        """
        output_path = self.app_dir(self.next_user_id) / "first" / "key.txt"
        self.create_file(output_path, str(secret_value))
        logger.info(f"Sent secret value to {output_path}")


if __name__ == "__main__":
    # Start of the application
    logger.info("-----------------------------")
    runner = PairwiseKeys()
        
    # Setup folder permissions
    runner.setup_folder_perms()
    logger.info("Setup complete.")

    # Check if second key exists. If not, create a new one and send it to the next person.
    if not runner.check_key_exists("second"):
        logger.info("Second key does not exist. Creating a new one.")
        secret_value = runner.create_secret_value()
        runner.write_to_next_person(secret_value)

    # Check if first key exists. If so, the key exchange is complete.
    if runner.check_key_exists("first"):
        logger.info("Key exchange complete.")
    else:
        logger.info("Key exchange incomplete.")
    logger.info("-----------------------------")

