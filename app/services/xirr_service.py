from datetime import datetime, timezone
import math

class CashFlow:
    def __init__(self, amount: float, date: datetime):
        self.amount = amount
        self.date = date

class XirrService:
    MAX_ITERATIONS = 100
    TOLERANCE = 1e-7
    GUESSES = [0.1, 0.05, -0.05, 0.2, -0.2, 0.5, -0.5, 1.0, -0.8]

    @staticmethod
    def calculate_xirr(cash_flows: list) -> float:
        """
        Calculate XIRR rate percentage using Newton-Raphson method with multi-start guesses.
        Returns float percentage (e.g. 14.52 for 14.52%) or None if un-convergent.
        """
        if not cash_flows:
            return None

        sorted_cf = sorted(cash_flows, key=lambda cf: cf.date)
        if not sorted_cf:
            return None

        first_date = sorted_cf[0].date
        mapped = []
        for cf in sorted_cf:
            days = float((cf.date - first_date).days)
            mapped.append((days, cf.amount))

        has_positive = any(amount > 0 for _, amount in mapped)
        has_negative = any(amount < 0 for _, amount in mapped)
        if not (has_positive and has_negative):
            return None

        for initial_guess in XirrService.GUESSES:
            rate = XirrService._solve_xirr(mapped, initial_guess)
            if rate is not None:
                return rate * 100.0

        return None

    @staticmethod
    def _solve_xirr(mapped_cfs: list, guess: float) -> float:
        rate = guess
        for _ in range(XirrService.MAX_ITERATIONS):
            if 1.0 + rate <= 0.0001:
                return None

            f = XirrService._calculate_npv(mapped_cfs, rate)
            df = XirrService._calculate_derivative_npv(mapped_cfs, rate)

            if df == 0.0 or math.isnan(df) or math.isnan(f):
                return None

            new_rate = rate - (f / df)
            if new_rate <= -0.9999:
                new_rate = -0.99

            if abs(new_rate - rate) < XirrService.TOLERANCE:
                return new_rate

            rate = new_rate

        return None

    @staticmethod
    def _calculate_npv(mapped_cfs: list, rate: float) -> float:
        if 1.0 + rate <= 0.0001:
            return float('nan')
        npv = 0.0
        try:
            for days, amount in mapped_cfs:
                years = days / 365.0
                npv += amount / math.pow(1.0 + rate, years)
            return npv
        except (OverflowError, ValueError, ZeroDivisionError):
            return float('nan')

    @staticmethod
    def _calculate_derivative_npv(mapped_cfs: list, rate: float) -> float:
        if 1.0 + rate <= 0.0001:
            return float('nan')
        df = 0.0
        try:
            for days, amount in mapped_cfs:
                years = days / 365.0
                if years != 0.0:
                    df -= years * amount / math.pow(1.0 + rate, years + 1.0)
            return df
        except (OverflowError, ValueError, ZeroDivisionError):
            return float('nan')
