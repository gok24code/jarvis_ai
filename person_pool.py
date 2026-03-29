import json
import os
from config import log

class PersonPool:
    def __init__(self, pool_file="persons.json"):
        # Dosya yolunu mutlak yol yap
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.pool_file = os.path.join(base_dir, pool_file)
        self.persons = []
        self.load_pool()

    def load_pool(self):
        """Loads the person pool from the JSON file."""
        if os.path.exists(self.pool_file):
            try:
                with open(self.pool_file, "r", encoding="utf-8") as f:
                    self.persons = json.load(f)
                # log(f"Person pool loaded: {len(self.persons)} persons found.")
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
        """Searches for a person by name or alias (case-insensitive and robust)."""
        if not name_or_alias: return None
        # Normalize input: lowercase and remove all inner spaces for extreme robustness
        search_term = "".join(name_or_alias.lower().split())
        
        for person in self.persons:
            # Check Name (Normalized comparison)
            stored_name = "".join(person.get("name", "").lower().split())
            if search_term == stored_name:
                return person
            
            # Check Aliases (Normalized comparison)
            aliases = person.get("aliases", [])
            for alias in aliases:
                stored_alias = "".join(alias.lower().split())
                if search_term == stored_alias:
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
