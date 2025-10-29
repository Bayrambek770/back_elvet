"""Clinic middlewares for cross-request housekeeping.

DailyNurseSalaryResetMiddleware resets Nurse.salary_per_day to 0 at the first
request of each day so that daily earnings start from zero and are rebuilt from
completed tasks.
"""

from django.core.cache import cache
from django.utils import timezone

from users.models import Nurse


class DailyNurseSalaryResetMiddleware:
    """Reset nurse salary_per_day to 0 once per calendar day.

    This runs on the first incoming request for a new day based on server
    timezone. It relies on Django's cache to store the last reset date.
    """

    CACHE_KEY = "nurse_salary_daily_reset_date"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        today = timezone.localdate()
        last_reset = cache.get(self.CACHE_KEY)
        if str(last_reset) != str(today):
            # Reset today's salary snapshots; totals remain intact
            Nurse.objects.update(salary_per_day=0)
            cache.set(self.CACHE_KEY, str(today), timeout=60 * 60 * 24)  # 24 hours TTL
        return self.get_response(request)
