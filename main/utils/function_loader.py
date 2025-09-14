# utils/function_loader.py
import os
import importlib.util
import sys
import traceback
from utils.logger import log_status

function_map = {}

def preload_functions(external_folders, logger):
    def load_functions_from_directory(directory):
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py") and file not in ["__init__.py"]:
                    module_path = os.path.join(root, file)
                    module_name = os.path.splitext(os.path.basename(file))[0]
                    try:
                        spec = importlib.util.spec_from_file_location(module_name, module_path)
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = module
                        spec.loader.exec_module(module)
                        for attr in dir(module):
                            if callable(getattr(module, attr)) and not attr.startswith("_"):
                                function_map[attr] = getattr(module, attr)
                        log_status(logger, f"✅ Loaded module: {module_name}, functions: {list(function_map.keys())}")
                    except Exception:
                        log_status(logger, f"⚠️ Error loading module {module_name}: {traceback.format_exc()}", "error")

    for folder in external_folders:
        log_status(logger, f"🔍 Scanning folder: {folder}")
        load_functions_from_directory(folder)
