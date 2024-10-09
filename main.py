import os
from pathlib import Path
import json
from syftbox.lib import ClientConfig

APP_NAME = "pairwise-keys"

class RingRunner:
    def __init__(self):
        self.client_config = ClientConfig.load(
            os.path.expanduser("~/.syftbox/client_config.json")
        )
        self.my_email = self.client_config["email"]
        self.my_home = (
            Path(self.client_config["sync_folder"])
            / self.my_email
            / "app_pipelines"
            / APP_NAME
        )
        
        self.prev_email, self.next_email = self.get_neighbors()
        self.first_folder = self.my_home / "first"
        self.second_folder = self.my_home / "second"
        self.folders = [self.first, self.second_folder]
        self.data_file = Path(os.path.abspath(__file__)).parent / "data.json"
        
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


    def setup_folders(self):
        print("Setting up the necessary folders.")
        for folder in self.folders:
            os.makedirs(folder, exist_ok=True)
            with open(folder / "dummy", "w") as f:
                pass
        with open(self.my_home / "_.syftperm", "w") as f:
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

    # def check_datafile_exists(self):
    #     files = []
    #     print(f"Please put your data files in {self.running_folder}.")
    #     for file in os.listdir(self.running_folder):
    #         if file.endswith(".json"):
    #             print("There is a file here.")
    #             files.append(os.path.join(self.running_folder, file))
    #     print(f"Found {len(files)} files in {self.running_folder}.")
    #     return files

    # def data_read_and_increment(self, file_name):
    #     with open(file_name) as f:
    #         data = json.load(f)

    #     ring_participants = data["ring"]
    #     datum = data["data"]
    #     to_send_idx = data["current_index"] + 1

    #     if to_send_idx >= len(ring_participants):
    #         print("END TRANSMISSION.")
    #         to_send_email = None
    #     else:
    #         to_send_email = ring_participants[to_send_idx]

    #     # Read the secret value from secret.txt
    #     with open(self.secret_file, 'r') as secret_file:
    #         secret_value = int(secret_file.read().strip())

    #     # Increment datum by the secret value instead of 1
    #     data["data"] = datum + secret_value
    #     data["current_index"] = to_send_idx
    #     os.remove(file_name)
    #     return data, to_send_email

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
        
        return key_file.exists()
    
    def create_secret_value(self):
        import random
        secret_value = random.randint(1, 100)
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

    # def terminate_ring(self):
    #     my_ring_runner.data_writer(self.done_folder / "data.json", datum)


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