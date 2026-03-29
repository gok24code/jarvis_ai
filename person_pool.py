import json
import os
from config import log

class PersonPool:
    def __init__(self, pool_file="persons.json"):
        self.pool_file = pool_file
        self.persons = []
        self.load_pool()

    def load_pool(self):
        """Loads the person pool from the JSON file."""
        if os.path.exists(self.pool_file):
            try:
                with open(self.pool_file, "r", encoding="utf-8") as f:
                    self.persons = json.load(f)
            except Exception as e:
                log(f"Error loading person pool: {e}")
                self.persons = []
        else:
            # Create an empty file if it doesn't exist
            self.save_pool()

    def save_pool(self):
        """Saves the person pool to the JSON file."""
        try:
            with open(self.pool_file, "w", encoding="utf-8") as f:
                json.dump(self.persons, f, indent=4, ensure_ascii=False)
        except Exception as e:
            log(f"Error saving person pool: {e}")

    def find_person(self, name_or_alias):
        """Searches for a person by name or alias."""
        search_term = name_or_alias.lower()
        for person in self.persons:
            if search_term == person["name"].lower() or search_term in [alias.lower() for alias in person.get("aliases", [])]:
                return person
        return None

    def get_phone_number(self, name_or_alias):
        """Retrieves the phone number for a person by name or alias."""
        person = self.find_person(name_or_alias)
        if person:
            return person.get("phone")
        return None

    def add_person(self, name, phone, aliases=None):
        """Adds a new person to the pool."""
        if aliases is None:
            aliases = []
        new_person = {
            "name": name,
            "phone": phone,
            "aliases": aliases
        }
        self.persons.append(new_person)
        self.save_pool()
        return True
