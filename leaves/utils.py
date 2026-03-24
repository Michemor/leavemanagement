"""Utility functions for leave management system."""
import datetime

def calculate_working_days(start_date, end_date):
    """Calculate the number of working days between two dates."""
    working_days = 0

    if start_date > end_date:
        raise ValueError("Start date cannot be after end date.")
        return 0

    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5:
            working_days += 1
        current_date += datetime.timedelta(days=1)
    return working_days