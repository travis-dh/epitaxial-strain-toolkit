"""config.py: Management of persistent user configurations and toolkit settings."""
from pathlib import Path
import tomllib
import tomli_w


CONFIG_DIR = Path.home() / ".config" / "estk"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def load_config() -> dict:
    """Load ESTK user configuration."""

    if not CONFIG_FILE.exists():
        return {}

    with open(CONFIG_FILE, "rb") as f:
        return tomllib.load(f)


def save_config(config: dict) -> None:
    """Save ESTK user configuration."""

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    with open(CONFIG_FILE, "wb") as f:
        tomli_w.dump(config, f)


def set_config_value(key: str, value: str) -> None:
    """Set a configuration value."""

    config = load_config()
    config[key] = value
    save_config(config)


def get_config_value(key: str, default=None):
    """Retrieve a configuration value."""

    config = load_config()
    return config.get(key, default)