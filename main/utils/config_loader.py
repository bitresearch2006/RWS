# utils/config_loader.py
import os
from utils.logger import log_status

def read_external_folders(config_file, logger):
    try:
        if not os.path.exists(config_file):
            log_status(logger, f"❌ Error: Configuration file '{config_file}' not found.", "error")
            exit(1)

        valid_paths = []
        with open(config_file, "r") as file:
            for line in file:
                folder_path = os.path.abspath(line.strip())
                if os.path.exists(folder_path) and os.path.isdir(folder_path):
                    valid_paths.append(folder_path)
                else:
                    log_status(logger, f"⚠️ Invalid path in config file: {folder_path}", "warning")

        if not valid_paths:
            log_status(logger, "❌ Error: No valid external folders found in configuration file.", "error")
            exit(1)

        return valid_paths
    except Exception as e:
        log_status(logger, f"❌ Error reading configuration file: {str(e)}", "error")
        exit(1)
