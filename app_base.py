# File: app_base.py

import json
from pathlib import Path
from syftbox.lib import ClientConfig

from loguru import logger

class ApplicationBase:
    """
    Base class for Syftbox applications.
    
    This class provides essential file and directory handling, as well as permission management,
    for applications built within the Syftbox ecosystem. Each application that inherits from this
    base class must define `self.app_name` to specify the application's name.

    Directory structure:
    ├── sync/
    │   ├── <user_id>
    │   │   ├── app_pipelines/
    │   │   │   └── <app_name>/   # App-specific folder set by each inherited application
    │   │   └── public/           # Public directory for shared resources
    │   │       └── _syftperm     # Permissions file for public folder access

    Attributes:
        user_id (str): Email ID of the user.
    """
    
    def __init__(self, client_config_path):
        # Load client configuration
        self.client_config = ClientConfig.load(client_config_path)
        self.user_id = self.client_config["email"]

    def app_dir(self, user_id):
        """
        Returns the application-specific directory for the given user_id.
        :param user_id: The email ID of the user.
        :return: Path object for the app directory.
        """
        return Path(self.client_config["sync_folder"]) / user_id / "app_pipelines" / self.app_name

    def public_dir(self, user_id):
        """
        Returns the public directory for the given user_id.
        :param user_id: The email ID of the user.
        :return: Path object for the public directory.
        """
        return Path(self.client_config["sync_folder"]) / user_id / "public"

    def create_directory(self, path):
        """
        Creates a directory at the given path, including any necessary parent directories.
        """
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory at: {path}")

    def create_file(self, file_path, content=""):
        """
        Creates a file at the specified path, writing the provided content to it.
        """
        with open(file_path, "w") as f:
            f.write(content)
        logger.info(f"Created file at: {file_path} with content: {content}")

    def set_permissions(self, path, read_users, write_users, admin_users=None):
        """
        Sets permissions on a directory by writing to the _.syftperm file.
        :param path: Directory for which permissions are set.
        :param read_users: List of users with read access.
        :param write_users: List of users with write access.
        :param admin_users: List of users with admin access.
        """
        self.create_directory(path)
        admin_users = admin_users if admin_users else [self.user_id]
        perm_data = {
            "admin": admin_users,
            "read": read_users,
            "write": write_users,
            "filepath": str(path / "_.syftperm"),
            "terminal": False,
        }
        with open(path / "_.syftperm", "w") as f:
            json.dump(perm_data, f)
        logger.info(f"Set permissions at {path}: admin={admin_users}, read={read_users}, write={write_users}")
