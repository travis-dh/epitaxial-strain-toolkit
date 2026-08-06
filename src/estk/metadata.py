import json
from pathlib import Path
from datetime import datetime, timezone

class MetadataManager:
    def __init__(self, output_path: Path, input_file: str = None):
        """
        Initializes the MetadataManager.
        
        Args:
            output_path: The directory where the metadata JSON will live.
            input_file: The name of the source material file (e.g., BaTiO3_mp-5933.cif).
        """
        self.path = output_path / "setup_metadata.json"
        self.data = self._load()

        if input_file:
            self.data["input_file"] = input_file
        elif not self.data.get("input_file"):
            # Fallback to directory name if no file is specified and JSON is new
            self.data["input_file"] = output_path.name

    def _get_timestamp(self) -> str:
        """Returns a UTC ISO 8601 timestamp with seconds precision."""
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _load(self) -> dict:
        """Loads existing metadata or returns a fresh template if none exists."""
        if self.path.exists():
            try:
                with open(self.path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print(f"Warning: Could not read {self.path}. Creating new manifest.")
        
        now = self._get_timestamp()
        return {
            "input_file": "",
            "created_at": now,
            "last_updated": now,
            "orientations": {}
        }

    def _save(self):
        """Writes the current metadata state to the JSON file."""
        self.data["last_updated"] = self._get_timestamp()
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=4)

    def get_orientation_metadata(self, miller_label: str) -> dict:
        """Returns the metadata for a specific orientation, if it exists."""
        return self.data["orientations"].get(miller_label)

    def upsert_orientation(self, miller_label: str, params: dict):
        """
        Adds or updates an orientation entry. 
        Records 'created_at' on the first run and 'updated_at' on every change.
        """
        now = self._get_timestamp()
        
        if miller_label not in self.data["orientations"]:
            self.data["orientations"][miller_label] = {
                "created_at": now,
                "updated_at": now,
                "strains": {},
                **params
            }
        else:
            entry = self.data["orientations"][miller_label]
            entry["updated_at"] = now
            for key, value in params.items():
                entry[key] = value

        self._save()

    def upsert_strain(
        self,
        miller_label: str,
        strain_name: str,
        strain_value: float,
        status: str | None = None,
    ):
        """Adds or updates a strain entry under a specific orientation."""
        if miller_label not in self.data["orientations"]:
            raise ValueError(f"Cannot add strain to unknown orientation: {miller_label}")

        now = self._get_timestamp()
        strains_dict = self.data["orientations"][miller_label]["strains"]

        if strain_name not in strains_dict:
            strains_dict[strain_name] = {
                "value": strain_value,
                "status": status or "Initialized",
                "created_at": now,
                "updated_at": now
            }
        else:
            strains_dict[strain_name]["updated_at"] = now
            strains_dict[strain_name]["value"] = strain_value
            if status is not None:
                strains_dict[strain_name]["status"] = status

        self.data["orientations"][miller_label]["updated_at"] = now
        self._save()