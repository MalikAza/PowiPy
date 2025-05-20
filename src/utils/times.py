import datetime
from datetime import timedelta
import math
import re
from typing import Dict, List, Optional
import pytz
from discord.ext import commands

from .chat_formatting import humanize_timedelta


TIME_RE = re.compile(
    r"""
        (\s?(  # match deliminators here to make word border below unambiguous
            (?P<years>[\+-]?\d+)\s?(years?|y)
          | (?P<months>[\+-]?\d+)\s?(months?|mo)
          | (?P<weeks>[\+-]?\d+)\s?(weeks?|w)
          | (?P<days>[\+-]?\d+)\s?(days?|d)
          | (?P<hours>[\+-]?\d+)\s?(hours?|hrs|hr?)
          | (?P<minutes>[\+-]?\d+)\s?(minutes?|mins?|min|mn)
          | (?P<seconds>[\+-]?\d+)\s?(seconds?|secs?|s)
        ))+\b
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)

class TimeUtils:
    @staticmethod
    def get_paris_current_datetime() -> datetime.datetime:
        """
        Returns the current date and time in the timezone of Paris in Europe.
        """
        return datetime.datetime.now(pytz.timezone('Europe/Paris'))
    
    @classmethod
    def get_next_alarm_timestamp(cls, hours: int, minutes: int) -> int:
        """
        Get the next possible timestamp for the given hours and minutes.
        If the time has already passed today, returns tomorrow's timestamp.
        
        Args:
            hours (int): Hours in 24-hour format (0-23)
            minutes (int): Minutes (0-59)
        """
        now = cls.get_paris_current_datetime()
        target = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)

        if now.timestamp() >= target.timestamp():
            target = target = datetime.timedelta(days=1)

        return int(target.timestamp())

    @staticmethod
    def _parse_and_match(string_to_match: str, allowed_units: List[str]) -> Optional[Dict[str, int]]:
        """
        Local utility function to match TIME_RE string above to user input for both parse_timedelta and parse_relativedelta
        """
        matches = TIME_RE.fullmatch(string_to_match)
        if matches:
            params = {k: int(v) for k, v in matches.groupdict().items() if v is not None}
            for k in params.keys():
                if k not in allowed_units:
                    raise commands.BadArgument(
                        "`{unit}` is not a valid unit of time for this command".format(unit=k)
                    )
            return params
        return None

    @classmethod
    def parse_timedelta(
        cls,
        argument: str,
        *,
        maximum: Optional[timedelta] = None,
        minimum: Optional[timedelta] = timedelta(seconds=0),
        allowed_units: Optional[List[str]] = None,
    ) -> Optional[timedelta]:
        """
        This converts a user provided string into a timedelta

        If a unit is specified multiple times, only the last is considered.
        This works with or without whitespace.

        Parameters
        ----------
        argument : str
            The user provided input
        maximum : Optional[datetime.timedelta]
            If provided, any parsed value higher than this will raise an exception
        minimum : Optional[datetime.timedelta]
            If provided, any parsed value lower than this will raise an exception
            Defaults to 0 seconds, pass `datetime.timedelta.min` explicitly to allow negative values
        allowed_units : Optional[List[str]]
            If provided, you can constrain a user to expressing the amount of time
            in specific units. The units you can chose to provide are the same as the
            parser understands. (``months``, ``weeks``, ``days``, ``hours``, ``minutes``, ``seconds``)

        Returns
        -------
        Optional[datetime.timedelta]
            If matched, the timedelta which was parsed. This can return `None`

        Raises
        ------
        BadArgument
            If the argument passed uses a unit not allowed, but understood
            or if the value is out of bounds.
        """
        allowed_units = allowed_units or [
            "months",
            "weeks",
            "days",
            "hours",
            "minutes",
            "seconds",
        ]
        if minimum is None:
            minimum = timedelta(seconds=0)
        if maximum is None:
            maximum = timedelta.max
        params = cls._parse_and_match(argument, allowed_units)
        if params:
            if "months" in params:
                months_in_days = params['months'] * 30 # arbitrary value
                if "days" in params:
                    params["days"] += months_in_days
                else:
                    params["days"] = months_in_days
                del params["months"]

            try:
                delta = timedelta(**params)
            except OverflowError:
                raise commands.BadArgument(
                    "The time set is way too high, consider setting something reasonable."
                )
            except TypeError as e:
                raise commands.BadArgument(
                    f"Invalid time parameters: {str(e)}"
                )
            if maximum < delta:
                raise commands.BadArgument(
                    ("This amount of time is too large for this command. (Maximum: {maximum})"
                    ).format(
                        maximum=humanize_timedelta(seconds=math.floor(maximum.total_seconds()))
                        or "0 seconds"
                    )
                )
            if delta < minimum:
                raise commands.BadArgument(
                    ("This amount of time is too small for this command. (Minimum: {minimum})"
                    ).format(
                        minimum=humanize_timedelta(seconds=math.ceil(minimum.total_seconds()))
                        or "0 seconds"
                    )
                )
            return delta
        return None