class TransactionTypeRegistry:
    CONFIGS = {
        'investment': {
            'holding_type': 'investment',
            'display_name': 'Stocks / Mutual Funds',
            'default_transaction_type': 'BUY',
            'is_unitized': True,
            'allowed_transactions': [
                {
                    'id': 'market_buy',
                    'raw_type': 'BUY',
                    'display_name': 'Buy Units',
                    'icon_name': 'fa-solid fa-cart-plus',
                    'cash_direction': 'outflow',
                    'affects_invested_amount': True,
                    'affects_asset_value': True,
                    'affects_profit': False,
                    'closes_asset': False,
                    'is_unit_based': True,
                    'notes_prompt': 'Order # / Strategy'
                },
                {
                    'id': 'market_sell',
                    'raw_type': 'SELL',
                    'display_name': 'Sell Units',
                    'icon_name': 'fa-solid fa-cart-arrow-down',
                    'cash_direction': 'inflow',
                    'affects_invested_amount': True,
                    'affects_asset_value': True,
                    'affects_profit': True,
                    'closes_asset': False,
                    'is_unit_based': True,
                    'notes_prompt': 'Sell Order #'
                },
                {
                    'id': 'market_dividend',
                    'raw_type': 'DIVIDEND',
                    'display_name': 'Dividend Received',
                    'icon_name': 'fa-solid fa-gift',
                    'cash_direction': 'inflow',
                    'affects_invested_amount': False,
                    'affects_asset_value': False,
                    'affects_profit': True,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'Dividend Per Share or Total Payout'
                }
            ]
        },
        'fixedDeposit': {
            'holding_type': 'fixedDeposit',
            'display_name': 'Fixed Deposit / RD',
            'default_transaction_type': 'DEPOSIT',
            'is_unitized': False,
            'allowed_transactions': [
                {
                    'id': 'fd_deposit',
                    'raw_type': 'DEPOSIT',
                    'display_name': 'Deposit / Installment',
                    'icon_name': 'fa-solid fa-circle-arrow-down',
                    'cash_direction': 'outflow',
                    'affects_invested_amount': True,
                    'affects_asset_value': True,
                    'affects_profit': False,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'FD Receipt / Account Ref'
                },
                {
                    'id': 'fd_interest_reinvest',
                    'raw_type': 'INTEREST',
                    'display_name': 'Interest Credited (Reinvested)',
                    'icon_name': 'fa-solid fa-percent',
                    'cash_direction': 'internalAccrual',
                    'affects_invested_amount': False,
                    'affects_asset_value': True,
                    'affects_profit': True,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'Compounded interest amount'
                },
                {
                    'id': 'fd_interest_payout',
                    'raw_type': 'INTEREST_PAYOUT',
                    'display_name': 'Interest Payout (to Bank)',
                    'icon_name': 'fa-solid fa-money-bill-wave',
                    'cash_direction': 'inflow',
                    'affects_invested_amount': False,
                    'affects_asset_value': False,
                    'affects_profit': True,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'Payout credit ref'
                },
                {
                    'id': 'fd_withdrawal',
                    'raw_type': 'WITHDRAWAL',
                    'display_name': 'Partial Withdrawal',
                    'icon_name': 'fa-solid fa-circle-arrow-up',
                    'cash_direction': 'inflow',
                    'affects_invested_amount': True,
                    'affects_asset_value': True,
                    'affects_profit': False,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'Premature partial withdrawal'
                },
                {
                    'id': 'fd_maturity',
                    'raw_type': 'MATURITY',
                    'display_name': 'FD Maturity / Full Payout',
                    'icon_name': 'fa-solid fa-flag-checkered',
                    'cash_direction': 'inflow',
                    'affects_invested_amount': True,
                    'affects_asset_value': True,
                    'affects_profit': True,
                    'closes_asset': True,
                    'is_unit_based': False,
                    'notes_prompt': 'Final payout amount'
                }
            ]
        },
        'epf': {
            'holding_type': 'epf',
            'display_name': 'EPF / Provident Fund',
            'default_transaction_type': 'EMPLOYEE_CONTRIBUTION',
            'is_unitized': False,
            'allowed_transactions': [
                {
                    'id': 'epf_employee',
                    'raw_type': 'EMPLOYEE_CONTRIBUTION',
                    'display_name': 'Employee Contribution',
                    'icon_name': 'fa-solid fa-user-plus',
                    'cash_direction': 'outflow',
                    'affects_invested_amount': True,
                    'affects_asset_value': True,
                    'affects_profit': False,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'Deducted from salary'
                },
                {
                    'id': 'epf_employer',
                    'raw_type': 'EMPLOYER_CONTRIBUTION',
                    'display_name': 'Employer Contribution',
                    'icon_name': 'fa-solid fa-building',
                    'cash_direction': 'internalAccrual',
                    'affects_invested_amount': True,
                    'affects_asset_value': True,
                    'affects_profit': False,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'Employer match contribution'
                },
                {
                    'id': 'epf_interest',
                    'raw_type': 'INTEREST',
                    'display_name': 'Annual Interest Credited',
                    'icon_name': 'fa-solid fa-percent',
                    'cash_direction': 'internalAccrual',
                    'affects_invested_amount': False,
                    'affects_asset_value': True,
                    'affects_profit': True,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'EPFO annual interest rate credit'
                },
                {
                    'id': 'epf_withdrawal',
                    'raw_type': 'WITHDRAWAL',
                    'display_name': 'EPF Advance / Withdrawal',
                    'icon_name': 'fa-solid fa-arrow-up-right-from-square',
                    'cash_direction': 'inflow',
                    'affects_invested_amount': True,
                    'affects_asset_value': True,
                    'affects_profit': False,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'Partial claim / advance'
                },
                {
                    'id': 'epf_settlement',
                    'raw_type': 'MATURITY',
                    'display_name': 'Full EPF Transfer / Settlement',
                    'icon_name': 'fa-solid fa-square-check',
                    'cash_direction': 'inflow',
                    'affects_invested_amount': True,
                    'affects_asset_value': True,
                    'affects_profit': True,
                    'closes_asset': True,
                    'is_unit_based': False,
                    'notes_prompt': 'Final settlement'
                }
            ]
        },
        'insuranceAnnuity': {
            'holding_type': 'insuranceAnnuity',
            'display_name': 'LIC / Insurance / Annuity',
            'default_transaction_type': 'PREMIUM',
            'is_unitized': False,
            'allowed_transactions': [
                {
                    'id': 'lic_premium',
                    'raw_type': 'PREMIUM',
                    'display_name': 'Premium Payment',
                    'icon_name': 'fa-solid fa-file-invoice-dollar',
                    'cash_direction': 'outflow',
                    'affects_invested_amount': True,
                    'affects_asset_value': True,
                    'affects_profit': False,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'Policy premium receipt #'
                },
                {
                    'id': 'lic_bonus',
                    'raw_type': 'BONUS',
                    'display_name': 'Accrued Reversionary Bonus',
                    'icon_name': 'fa-solid fa-star',
                    'cash_direction': 'internalAccrual',
                    'affects_invested_amount': False,
                    'affects_asset_value': True,
                    'affects_profit': True,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'Declared annual bonus'
                },
                {
                    'id': 'lic_survival_benefit',
                    'raw_type': 'SURVIVAL_BENEFIT',
                    'display_name': 'Survival / Money-Back Benefit',
                    'icon_name': 'fa-solid fa-gift',
                    'cash_direction': 'inflow',
                    'affects_invested_amount': False,
                    'affects_asset_value': True,
                    'affects_profit': True,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'Periodic money-back payout'
                },
                {
                    'id': 'lic_maturity',
                    'raw_type': 'MATURITY',
                    'display_name': 'Policy Maturity Payout',
                    'icon_name': 'fa-solid fa-flag-checkered',
                    'cash_direction': 'inflow',
                    'affects_invested_amount': True,
                    'affects_asset_value': True,
                    'affects_profit': True,
                    'closes_asset': True,
                    'is_unit_based': False,
                    'notes_prompt': 'Sum assured + total bonus'
                },
                {
                    'id': 'lic_surrender',
                    'raw_type': 'SURRENDER',
                    'display_name': 'Policy Surrender Value',
                    'icon_name': 'fa-solid fa-rectangle-xmark',
                    'cash_direction': 'inflow',
                    'affects_invested_amount': True,
                    'affects_asset_value': True,
                    'affects_profit': True,
                    'closes_asset': True,
                    'is_unit_based': False,
                    'notes_prompt': 'Surrender payout'
                }
            ]
        },
        'postOffice': {
            'holding_type': 'postOffice',
            'display_name': 'Post Office / PPF / NSC / SSY',
            'default_transaction_type': 'CONTRIBUTION',
            'is_unitized': False,
            'allowed_transactions': [
                {
                    'id': 'po_deposit',
                    'raw_type': 'CONTRIBUTION',
                    'display_name': 'Deposit / Contribution',
                    'icon_name': 'fa-solid fa-circle-arrow-down',
                    'cash_direction': 'outflow',
                    'affects_invested_amount': True,
                    'affects_asset_value': True,
                    'affects_profit': False,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'Deposit transaction ref'
                },
                {
                    'id': 'po_interest',
                    'raw_type': 'INTEREST',
                    'display_name': 'Annual Interest Credited',
                    'icon_name': 'fa-solid fa-percent',
                    'cash_direction': 'internalAccrual',
                    'affects_invested_amount': False,
                    'affects_asset_value': True,
                    'affects_profit': True,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'Fiscal year interest'
                },
                {
                    'id': 'po_withdrawal',
                    'raw_type': 'WITHDRAWAL',
                    'display_name': 'Partial Withdrawal',
                    'icon_name': 'fa-solid fa-circle-arrow-up',
                    'cash_direction': 'inflow',
                    'affects_invested_amount': True,
                    'affects_asset_value': True,
                    'affects_profit': False,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'Eligible withdrawal'
                },
                {
                    'id': 'po_maturity',
                    'raw_type': 'MATURITY',
                    'display_name': 'Scheme Maturity / Full Closure',
                    'icon_name': 'fa-solid fa-flag',
                    'cash_direction': 'inflow',
                    'affects_invested_amount': True,
                    'affects_asset_value': True,
                    'affects_profit': True,
                    'closes_asset': True,
                    'is_unit_based': False,
                    'notes_prompt': 'Final payout amount'
                }
            ]
        },
        'bankBalance': {
            'holding_type': 'bankBalance',
            'display_name': 'Bank Account Balance',
            'default_transaction_type': 'DEPOSIT',
            'is_unitized': False,
            'allowed_transactions': [
                {
                    'id': 'bank_deposit',
                    'raw_type': 'DEPOSIT',
                    'display_name': 'Money Added / Savings',
                    'icon_name': 'fa-solid fa-circle-plus',
                    'cash_direction': 'outflow',
                    'affects_invested_amount': True,
                    'affects_asset_value': True,
                    'affects_profit': False,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'Savings deposit note'
                },
                {
                    'id': 'bank_interest',
                    'raw_type': 'INTEREST',
                    'display_name': 'Savings Interest Credited',
                    'icon_name': 'fa-solid fa-percent',
                    'cash_direction': 'internalAccrual',
                    'affects_invested_amount': False,
                    'affects_asset_value': True,
                    'affects_profit': True,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'Bank interest credit'
                },
                {
                    'id': 'bank_withdrawal',
                    'raw_type': 'WITHDRAWAL',
                    'display_name': 'Money Withdrawn / Spent',
                    'icon_name': 'fa-solid fa-circle-minus',
                    'cash_direction': 'inflow',
                    'affects_invested_amount': True,
                    'affects_asset_value': True,
                    'affects_profit': False,
                    'closes_asset': False,
                    'is_unit_based': False,
                    'notes_prompt': 'Withdrawal / Expense note'
                }
            ]
        }
    }

    @classmethod
    def get_config_for_holding_type(cls, holding_type: str) -> dict:
        return cls.CONFIGS.get(holding_type, cls.CONFIGS['investment'])

    @classmethod
    def get_allowed_transactions(cls, holding_type: str) -> list:
        config = cls.get_config_for_holding_type(holding_type)
        return config['allowed_transactions']
