class CashDirection:
    OUTFLOW = "outflow"            # Cash leaves user's pocket into asset (Deposit, Buy, Premium)
    INFLOW = "inflow"              # Cash enters user's pocket from asset (Withdrawal, Maturity, Dividend)
    INTERNAL_ACCRUAL = "internalAccrual" # Interest credited directly, no external cash movement

class TransactionTypeConfig:
    def __init__(
        self,
        id_str: str,
        raw_type: str,
        display_name: str,
        icon_name: str = "dollarsign.circle",
        cash_direction: str = CashDirection.OUTFLOW,
        affects_invested_amount: bool = True,
        affects_asset_value: bool = True,
        affects_profit: bool = False,
        closes_asset: bool = False,
        is_unit_based: bool = False,
        notes_prompt: str = None
    ):
        self.id = id_str
        self.raw_type = raw_type
        self.display_name = display_name
        self.icon_name = icon_name
        self.cash_direction = cash_direction
        self.affects_invested_amount = affects_invested_amount
        self.affects_asset_value = affects_asset_value
        self.affects_profit = affects_profit
        self.closes_asset = closes_asset
        self.is_unit_based = is_unit_based
        self.notes_prompt = notes_prompt

class InvestmentTypeConfig:
    def __init__(self, holding_type: str, display_name: str, default_transaction_type: str, is_unitized: bool, allowed_transactions: list):
        self.holding_type = holding_type
        self.display_name = display_name
        self.default_transaction_type = default_transaction_type
        self.is_unitized = is_unitized
        self.allowed_transactions = allowed_transactions

class TransactionTypeRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TransactionTypeRegistry, cls).__new__(cls)
            cls._instance._register_defaults()
        return cls._instance

    @staticmethod
    def config(raw_type: str, holding_type: str = "investment") -> TransactionTypeConfig:
        registry = TransactionTypeRegistry()
        actual_holding = holding_type if holding_type else "investment"
        investment_cfg = registry.get_holding_config(actual_holding)

        for cfg in investment_cfg.allowed_transactions:
            if cfg.raw_type.lower() == raw_type.lower():
                return cfg

        clean_type = raw_type.upper()
        if clean_type in ["BUY", "DEPOSIT", "CONTRIBUTION", "PREMIUM", "PURCHASE", "EMPLOYEE_CONTRIBUTION"]:
            return TransactionTypeConfig(
                id_str="fallback_buy", raw_type=clean_type, display_name=clean_type.capitalize(),
                icon_name="plus-circle", cash_direction=CashDirection.OUTFLOW,
                affects_invested_amount=True, affects_asset_value=True, affects_profit=False,
                closes_asset=False, is_unit_based=(actual_holding == "investment")
            )
        elif clean_type in ["SELL", "WITHDRAWAL", "REDEMPTION", "SURRENDER", "MATURITY"]:
            return TransactionTypeConfig(
                id_str="fallback_sell", raw_type=clean_type, display_name=clean_type.capitalize(),
                icon_name="minus-circle", cash_direction=CashDirection.INFLOW,
                affects_invested_amount=True, affects_asset_value=True, affects_profit=True,
                closes_asset=(clean_type in ["MATURITY", "SURRENDER"]), is_unit_based=(actual_holding == "investment")
            )
        elif clean_type in ["DIVIDEND", "INTEREST", "COUPON", "BONUS", "SURVIVAL_BENEFIT"]:
            is_inflow = clean_type in ["DIVIDEND", "COUPON", "SURVIVAL_BENEFIT"]
            return TransactionTypeConfig(
                id_str="fallback_dividend", raw_type=clean_type, display_name=clean_type.capitalize(),
                icon_name="gift", cash_direction=CashDirection.INFLOW if is_inflow else CashDirection.INTERNAL_ACCRUAL,
                affects_invested_amount=False, affects_asset_value=(clean_type in ["INTEREST", "BONUS"]),
                affects_profit=True, closes_asset=False, is_unit_based=False
            )
        else:
            return TransactionTypeConfig(
                id_str="fallback_generic", raw_type=clean_type, display_name=clean_type.capitalize(),
                icon_name="dollar-sign", cash_direction=CashDirection.OUTFLOW,
                affects_invested_amount=True, affects_asset_value=True, affects_profit=False,
                closes_asset=False, is_unit_based=(actual_holding == "investment")
            )

    def get_holding_config(self, holding_type: str) -> InvestmentTypeConfig:
        return self._configs.get(holding_type, self._default_market_config())

    def _register_defaults(self):
        self._configs = {}

        # 1. Market Investments (Stocks / Mutual Funds)
        self._configs["investment"] = self._default_market_config()

        # 2. Fixed Deposit / RD
        self._configs["fixedDeposit"] = InvestmentTypeConfig(
            holding_type="fixedDeposit", display_name="Fixed Deposit / RD", default_transaction_type="DEPOSIT", is_unitized=False,
            allowed_transactions=[
                TransactionTypeConfig("fd_deposit", "DEPOSIT", "Deposit / Installment", "arrow-down-right", CashDirection.OUTFLOW, True, True, False, False, False, "FD Receipt / Account Ref"),
                TransactionTypeConfig("fd_interest_reinvest", "INTEREST", "Interest Credited (Reinvested)", "percent", CashDirection.INTERNAL_ACCRUAL, False, True, True, False, False, "Compounded interest amount"),
                TransactionTypeConfig("fd_interest_payout", "INTEREST_PAYOUT", "Interest Payout (to Bank)", "banknote", CashDirection.INFLOW, False, False, True, False, False, "Payout credit ref"),
                TransactionTypeConfig("fd_withdrawal", "WITHDRAWAL", "Partial Withdrawal", "arrow-up-left", CashDirection.INFLOW, True, True, False, False, False, "Premature partial withdrawal"),
                TransactionTypeConfig("fd_maturity", "MATURITY", "FD Maturity / Full Payout", "flag", CashDirection.INFLOW, True, True, True, True, False, "Final payout amount")
            ]
        )

        # 3. EPF / Provident Fund
        self._configs["epf"] = InvestmentTypeConfig(
            holding_type="epf", display_name="EPF / Provident Fund", default_transaction_type="EMPLOYEE_CONTRIBUTION", is_unitized=False,
            allowed_transactions=[
                TransactionTypeConfig("epf_employee", "EMPLOYEE_CONTRIBUTION", "Employee Contribution", "user-plus", CashDirection.OUTFLOW, True, True, False, False, False, "Deducted from salary"),
                TransactionTypeConfig("epf_employer", "EMPLOYER_CONTRIBUTION", "Employer Contribution", "building", CashDirection.INTERNAL_ACCRUAL, True, True, False, False, False, "Employer match contribution"),
                TransactionTypeConfig("epf_interest", "INTEREST", "Annual Interest Credited", "percent", CashDirection.INTERNAL_ACCRUAL, False, True, True, False, False, "EPFO annual interest rate credit"),
                TransactionTypeConfig("epf_withdrawal", "WITHDRAWAL", "EPF Advance / Withdrawal", "arrow-up-right", CashDirection.INFLOW, True, True, False, False, False, "Partial claim / advance"),
                TransactionTypeConfig("epf_settlement", "MATURITY", "Full EPF Transfer / Settlement", "check-circle", CashDirection.INFLOW, True, True, True, True, False, "Final settlement")
            ]
        )

        # 4. LIC / Insurance / Annuity
        self._configs["insuranceAnnuity"] = InvestmentTypeConfig(
            holding_type="insuranceAnnuity", display_name="LIC / Insurance / Annuity", default_transaction_type="PREMIUM", is_unitized=False,
            allowed_transactions=[
                TransactionTypeConfig("lic_premium", "PREMIUM", "Premium Payment", "file-text", CashDirection.OUTFLOW, True, True, False, False, False, "Policy premium receipt #"),
                TransactionTypeConfig("lic_bonus", "BONUS", "Accrued Reversionary Bonus", "star", CashDirection.INTERNAL_ACCRUAL, False, True, True, False, False, "Declared annual bonus"),
                TransactionTypeConfig("lic_survival_benefit", "SURVIVAL_BENEFIT", "Survival / Money-Back Benefit", "gift", CashDirection.INFLOW, False, True, True, False, False, "Periodic money-back payout"),
                TransactionTypeConfig("lic_maturity", "MATURITY", "Policy Maturity Payout", "flag", CashDirection.INFLOW, True, True, True, True, False, "Sum assured + total bonus"),
                TransactionTypeConfig("lic_surrender", "SURRENDER", "Policy Surrender Value", "x-circle", CashDirection.INFLOW, True, True, True, True, False, "Surrender payout")
            ]
        )

        # 5. Post Office Scheme
        self._configs["postOffice"] = InvestmentTypeConfig(
            holding_type="postOffice", display_name="Post Office / PPF / NSC / SSY", default_transaction_type="CONTRIBUTION", is_unitized=False,
            allowed_transactions=[
                TransactionTypeConfig("po_deposit", "CONTRIBUTION", "Deposit / Contribution", "arrow-down-circle", CashDirection.OUTFLOW, True, True, False, False, False, "Deposit transaction ref"),
                TransactionTypeConfig("po_interest", "INTEREST", "Annual Interest Credited", "percent", CashDirection.INTERNAL_ACCRUAL, False, True, True, False, False, "Fiscal year interest"),
                TransactionTypeConfig("po_withdrawal", "WITHDRAWAL", "Partial Withdrawal", "arrow-up-circle", CashDirection.INFLOW, True, True, False, False, False, "Eligible withdrawal"),
                TransactionTypeConfig("po_maturity", "MATURITY", "Scheme Maturity / Full Closure", "flag", CashDirection.INFLOW, True, True, True, True, False, "Final payout amount")
            ]
        )

        # 6. Bank Balance
        self._configs["bankBalance"] = InvestmentTypeConfig(
            holding_type="bankBalance", display_name="Bank Account Balance", default_transaction_type="DEPOSIT", is_unitized=False,
            allowed_transactions=[
                TransactionTypeConfig("bank_deposit", "DEPOSIT", "Money Added / Savings", "plus-circle", CashDirection.OUTFLOW, True, True, False, False, False),
                TransactionTypeConfig("bank_interest", "INTEREST", "Savings Interest Credited", "percent", CashDirection.INTERNAL_ACCRUAL, False, True, True, False, False),
                TransactionTypeConfig("bank_withdrawal", "WITHDRAWAL", "Money Withdrawn / Spent", "minus-circle", CashDirection.INFLOW, True, True, False, False, False)
            ]
        )

    def _default_market_config(self) -> InvestmentTypeConfig:
        return InvestmentTypeConfig(
            holding_type="investment", display_name="Stocks / Mutual Funds", default_transaction_type="BUY", is_unitized=True,
            allowed_transactions=[
                TransactionTypeConfig("market_buy", "BUY", "Buy Units", "shopping-cart", CashDirection.OUTFLOW, True, True, False, False, True, "Order # / Strategy"),
                TransactionTypeConfig("market_sell", "SELL", "Sell Units", "minus-circle", CashDirection.INFLOW, True, True, True, False, True, "Sell Order #"),
                TransactionTypeConfig("market_dividend", "DIVIDEND", "Dividend Received", "gift", CashDirection.INFLOW, False, False, True, False, False, "Dividend Per Share or Total Payout")
            ]
        )
