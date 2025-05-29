from kivy.storage.jsonstore import JsonStore
import os

class CacheManager:
    def __init__(self, file_path="./cache.json"):
        self.file_path = os.path.expanduser(file_path)
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        self.store = JsonStore(self.file_path)

    def save_selections(self, selections):
        """Save spinner selections to JSON file."""
        for key, value in selections.items():
            self.store.put(key, value=value)

    def load_selections(self, defaults, valid_options):
        """Load selections, validate against valid_options, and return valid values."""
        selections = {}
        for dropdown, default_value in defaults.items():
            try:
                if self.store.exists(dropdown):
                    stored_value = self.store.get(dropdown)["value"]
                    if stored_value in valid_options[dropdown]:
                        selections[dropdown] = stored_value
                    else:
                        selections[dropdown] = default_value
                else:
                    selections[dropdown] = default_value
            except (KeyError, FileNotFoundError, OSError):
                selections[dropdown] = default_value
        return selections