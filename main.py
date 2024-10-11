import os
from pathlib import Path
import json
from syftbox.lib import ClientConfig

APP_NAME = "pairwise-keys"
STATISTICAL_SECURITY = 2 ** 6


# When each ring member arrives, they will create their own key in public/pairwise-keys/second/key.txt
# All app related data will be inside public/APP_NAME/
# syft_root_dir/
# ├── .config/                      <-- Hidden for better UX
# │   └── config.json
# ├── apps/                         <-- This is currently inside sync
# │   └── ring
# └── sync/                         <-- This is the datasites folder
#     ├── a@openmined.org
#         └── public
#             └── _syftperm (this folder is public)
#             └── ring/
#                 └── _syftperm (this folder is private)
#                 └── private_file.txt
#     └── b@openmined.org
#         └── public
#             └── _syftperm (this folder is public)
#             └── ring/
#                 └── _syftperm (this folder is private)
#                 └── private_file.txt


class ApplicationBase: 
    def share_folder(email_id, folder_path):
        # This method change the _syftperms inside a given folder_path and share it with the given email_id.
        # This will error out if this user does not have write access to this file.

    def create_file(email_id, file_name, folder_path):
        # This method will create a file in folder_path. This will error out if 
        # this user does not have write access to this file.

    

class RingRunner:
    def __init__(self):
        self.data_file = Path(os.path.abspath(__file__)).parent / "data.json" 
        self.client_config = ClientConfig.load(os.environ.get("SYFTBOX_CLIENT_CONFIG_PATH"))
        self.my_email = self.client_config["email"]
        self.my_home = (
            Path(self.client_config["sync_folder"])
            / self.my_email
            / "app_pipelines"
            / APP_NAME
        )

        self.prev_email, self.next_email = self.get_neighbors()
        print(f"my next: {self.next_email}, my prev: {self.prev_email}")
        self.first_folder = self.my_home / "first"
        self.second_folder = self.my_home / "second"
        self.folders = [self.my_home, self.first_folder, self.second_folder]
        
        self.syft_perm_json = {
            "admin": [self.my_email],
            "read": [self.my_email, "GLOBAL"],
            "write": [self.my_email, "GLOBAL"],
            "filepath": str(self.my_home / "_.syftperm"),
            "terminal": False,
        }

    def get_neighbors(self):
        with open(self.data_file) as f:
            data = json.load(f)

        ring_participants = data["ring"]
        try:
            index = ring_participants.index(self.my_email)
        except ValueError:
            return None, None
    
        prev_index = (index - 1) % len(ring_participants)  # Cyclic previous
        next_index = (index + 1) % len(ring_participants)  # Cyclic next
        
        return ring_participants[prev_index], ring_participants[next_index]


    # Each folder will setup with default perms
    def setup_folders(self):
        print("Setting up the necessary folders.")
        for folder in self.folders:
            os.makedirs(folder, exist_ok=True)
            with open(folder / "_.syftperm", "w") as f:
                json.dump(self.syft_perm_json, f)
            
    def setup_folder_perms(self):
        # Give write perms to the first folder for the prev ring member
        print("Setting up the permission for first folder.")
        self.syft_perm_first_json = {
            "admin": [self.my_email],
            "read": [self.my_email, self.prev_email],
            "write": [self.my_email, self.prev_email],
            "filepath": str(self.my_home / "first" / "_.syftperm"),
            "terminal": False,
        }

        with open(self.first_folder / "_.syftperm", "w") as f:
            json.dump(self.syft_perm_first_json, f)
            
        # Second folder is completely private
        print("Setting up the permission for second folder.")
        self.syft_perm_second_json = {
            "admin": [self.my_email],
            "read": [self.my_email],
            "write": [self.my_email],
            "filepath": str(self.my_home / "second" / "_.syftperm"),
            "terminal": False,
        }

        with open(self.second_folder / "_.syftperm", "w") as f:
            json.dump(self.syft_perm_second_json, f)

 
    def data_writer(self, file_name, result):
        with open(file_name, "w") as f:
            json.dump(result, f)

    def check_key_exists(self, key_type):
        if key_type == "first":
            key_file = self.first_folder / "key.txt"
        elif key_type == "second":
            key_file = self.second_folder / "key.txt"
        else:
            raise ValueError("Invalid key type.")
        
        print(f"Checking if {key_file} exists: {key_file.exists()}")
        return key_file.exists()
    
    def create_secret_value(self):
        import random
        secret_value = random.randint(1, STATISTICAL_SECURITY)
        with open(self.second_folder / "key.txt", "w") as f:
            f.write(str(secret_value))
        return secret_value

    def send_to_next_person(self, to_send_email, key_second):
        output_path = (
            Path(os.path.abspath(__file__)).parent.parent.parent
            / to_send_email
            / "app_pipelines"
            / APP_NAME
            / "first"
            / "key.txt"
        )
        print(f"Writing to {output_path}.")
        self.data_writer(output_path, key_second)


if __name__ == "__main__":
    # Start of script. Step 1. Setup any folders that may be necessary.
    my_ring_runner = RingRunner()
    my_ring_runner.setup_folders()
    my_ring_runner.setup_folder_perms()
    
    # Step 2. Check if second key already exists. If it does, proceed to Step 5.
    exists = my_ring_runner.check_key_exists("second")

    if not exists:
        print("Second key does not exist. Let's create it.")
        # Step 3. Create a random value and write it to the second folder as key.txt
        key_second = my_ring_runner.create_secret_value()
        # Step 4. Write that value to the first folder of the next person in the ring.
        my_ring_runner.send_to_next_person(my_ring_runner.next_email, key_second)
        
    # Step 5. check if first key already exists. If it does, print protocol complete.
    exists = my_ring_runner.check_key_exists("first")
    
    if exists:
        print("Key exchange complete.")
    else:
        print("Key exchange incomplete.")
