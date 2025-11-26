"""Named constants for Injekt CLI."""

from pathlib import Path

# Exit codes
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_VALIDATION_ERROR = 2
EXIT_INSTALLATION_ERROR = 3
EXIT_BACKUP_ERROR = 4
EXIT_PATH_ERROR = 5
EXIT_CONFLICT_ERROR = 6

# Paths
DEFAULT_ASSETS_DIR = Path("assets")
DEFAULT_BACKUP_DIR = Path.home() / ".injekt" / "backups"
DEFAULT_STATE_FILE = Path.home() / ".injekt" / "state.json"
DEFAULT_LOG_DIR = Path.home() / ".injekt" / "logs"

# Limits
MAX_BACKUPS = 5
MIN_ITERATIONS_PBT = 100

# Standard player paths (Windows)
MPV_PATHS = [
    Path.home() / "AppData" / "Roaming" / "mpv",
    Path("C:/Program Files/mpv"),
    Path("C:/Program Files (x86)/mpv"),
]

VLC_PATHS = [
    Path.home() / "AppData" / "Roaming" / "vlc",
    Path("C:/Program Files/VideoLAN/VLC"),
    Path("C:/Program Files (x86)/VideoLAN/VLC"),
]
