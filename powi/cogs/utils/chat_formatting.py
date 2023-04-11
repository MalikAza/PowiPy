from typing import Optional, SupportsInt
import datetime

def humanize_timedelta(*, timedelta: Optional[datetime.timedelta] = None, seconds: Optional[SupportsInt] = None) -> str:
    try:
        obj = seconds if seconds is not None else timedelta.total_seconds()
    except AttributeError:
        raise ValueError("You must provide either a timedelta or a number of seconds")

    seconds = int(obj)
    periods = [
        ("année", "années", 60 * 60 * 24 * 365),
        ("mois", "mois", 60 * 60 * 24 * 30),
        ("jour", "jours", 60 * 60 * 24),
        ("heure", "heures", 60 * 60),
        ("minute", "minutes", 60),
        ("seconde", "secondes", 1)
    ]

    string = []
    for period_name, plural_period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            if period_value == 0:
                continue
            unit = plural_period_name if period_value > 1 else period_name
            string.append(f"{period_value} {unit}")

    return ", ".join(string)