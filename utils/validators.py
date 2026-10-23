"""Input validation shared by the CRUD service and the Streamlit forms."""
import config


class ValidationError(ValueError):
    """Raised when user input fails validation."""


def validate_player(full_name, country, playing_role, batting_style=None, bowling_style=None):
    """Return a cleaned dict or raise ValidationError listing every problem."""
    errors = []
    name = (full_name or "").strip()
    country = (country or "").strip()
    if len(name) < 3:
        errors.append("Full name must be at least 3 characters.")
    if not country:
        errors.append("Country is required.")
    if playing_role not in config.PLAYING_ROLES:
        errors.append(f"Playing role must be one of {', '.join(config.PLAYING_ROLES)}.")
    if errors:
        raise ValidationError(" ".join(errors))
    return {"full_name": name, "country": country, "playing_role": playing_role,
            "batting_style": (batting_style or "").strip() or None,
            "bowling_style": (bowling_style or "").strip() or None}


def validate_career_stats(match_format, matches, runs, wickets, highest_score, centuries):
    errors = []
    if match_format not in config.FORMATS:
        errors.append(f"Format must be one of {', '.join(config.FORMATS)}.")
    for label, value in (("Matches", matches), ("Runs", runs), ("Wickets", wickets),
                         ("Highest score", highest_score), ("Centuries", centuries)):
        if value is None or int(value) < 0:
            errors.append(f"{label} must be zero or more.")
    if not errors and int(highest_score) > int(runs):
        errors.append("Highest score cannot exceed total runs.")
    if errors:
        raise ValidationError(" ".join(errors))
