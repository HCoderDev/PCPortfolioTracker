from datetime import datetime, timezone, timedelta
import math

class FIMilestone:
    def __init__(self, percentage: float, label: str, target_amount: float, months_needed: int, target_date: datetime, age_at_milestone: float, is_achieved: bool):
        self.percentage = percentage
        self.label = label
        self.target_amount = target_amount
        self.months_needed = months_needed
        self.target_date = target_date
        self.age_at_milestone = age_at_milestone
        self.is_achieved = is_achieved

class FIProjectionResult:
    def __init__(
        self,
        current_net_worth: float,
        target_goal: float,
        progress_percentage: float,
        current_age: int,
        months_needed: int,
        years_needed: float,
        target_date: datetime,
        age_at_fi: float,
        monthly_sip: float,
        return_rate: float,
        inflation_rate: float,
        safe_withdrawal_rate: float,
        annual_passive_income_at_fi: float,
        monthly_passive_income_at_fi: float,
        milestones: list
    ):
        self.current_net_worth = current_net_worth
        self.target_goal = target_goal
        self.progress_percentage = progress_percentage
        self.current_age = current_age
        self.months_needed = months_needed
        self.years_needed = years_needed
        self.target_date = target_date
        self.age_at_fi = age_at_fi
        self.monthly_sip = monthly_sip
        self.return_rate = return_rate
        self.inflation_rate = inflation_rate
        self.safe_withdrawal_rate = safe_withdrawal_rate
        self.annual_passive_income_at_fi = annual_passive_income_at_fi
        self.monthly_passive_income_at_fi = monthly_passive_income_at_fi
        self.milestones = milestones

class FiService:
    DEFAULT_TARGET_GOAL = 70000000.0  # 7 Crore INR
    DEFAULT_MONTHLY_SIP = 50000.0
    DEFAULT_RETURN_RATE = 12.0
    DEFAULT_INFLATION_RATE = 6.0
    DEFAULT_SWR = 4.0

    @staticmethod
    def calculate_current_age(birth_date: datetime, as_of_date: datetime = None) -> int:
        ref = as_of_date or datetime.now(timezone.utc)
        if birth_date is None:
            return 30
        years = ref.year - birth_date.year
        if (ref.month, ref.day) < (birth_date.month, birth_date.day):
            years -= 1
        return max(0, years)

    @staticmethod
    def project_fi(
        current_net_worth: float,
        target_goal: float,
        birth_date: datetime,
        monthly_sip: float,
        return_rate: float,
        inflation_rate: float,
        safe_withdrawal_rate: float = 4.0,
        as_of_date: datetime = None
    ) -> FIProjectionResult:
        ref = as_of_date or datetime.now(timezone.utc)
        clean_target = max(1.0, target_goal)
        clean_sip = max(0.0, monthly_sip)
        clean_return = max(0.0, return_rate)
        progress_pct = min(100.0, (current_net_worth / clean_target) * 100.0)
        current_age_years = FiService.calculate_current_age(birth_date, ref)

        monthly_return_rate = math.pow(1.0 + (clean_return / 100.0), 1.0 / 12.0) - 1.0 if clean_return > 0 else 0.0

        balance = current_net_worth
        months_needed = 0
        max_months = 1200  # Cap at 100 years

        if balance < clean_target:
            while balance < clean_target and months_needed < max_months:
                balance = (balance * (1.0 + monthly_return_rate)) + clean_sip
                months_needed += 1

        # Calculate target date by adding months
        target_date = ref + timedelta(days=int(months_needed * 30.4375))
        if birth_date:
            birth_age_double = (ref - birth_date).days / 365.25
        else:
            birth_age_double = 30.0

        age_at_fi = birth_age_double + (months_needed / 12.0)
        years_needed = months_needed / 12.0

        annual_passive_income = clean_target * (safe_withdrawal_rate / 100.0)
        monthly_passive_income = annual_passive_income / 12.0

        milestone_pcts = [
            (25.0, "25% FI (Quarter FI)"),
            (50.0, "50% FI (Half FI)"),
            (75.0, "75% FI (Three-Quarter FI)"),
            (100.0, "100% FI (Full Freedom)")
        ]

        milestones = []
        for pct, label in milestone_pcts:
            m_goal = clean_target * (pct / 100.0)
            is_achieved = current_net_worth >= m_goal
            m_balance = current_net_worth
            m_months = 0

            if not is_achieved:
                while m_balance < m_goal and m_months < max_months:
                    m_balance = (m_balance * (1.0 + monthly_return_rate)) + clean_sip
                    m_months += 1

            m_date = ref + timedelta(days=int(m_months * 30.4375))
            m_age = birth_age_double + (m_months / 12.0)

            milestones.append(FIMilestone(
                percentage=pct,
                label=label,
                target_amount=m_goal,
                months_needed=m_months,
                target_date=m_date,
                age_at_milestone=m_age,
                is_achieved=is_achieved
            ))

        return FIProjectionResult(
            current_net_worth=current_net_worth,
            target_goal=clean_target,
            progress_percentage=progress_pct,
            current_age=current_age_years,
            months_needed=months_needed,
            years_needed=years_needed,
            target_date=target_date,
            age_at_fi=age_at_fi,
            monthly_sip=clean_sip,
            return_rate=clean_return,
            inflation_rate=inflation_rate,
            safe_withdrawal_rate=safe_withdrawal_rate,
            annual_passive_income_at_fi=annual_passive_income,
            monthly_passive_income_at_fi=monthly_passive_income,
            milestones=milestones
        )
