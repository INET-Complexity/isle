use_abce = False
oneriskmodel = False
replicating = False
force_foreground = False
verbose = False
showprogress = False

simulation_parameters={"no_categories": 4,
                       "no_insurancefirms": 20,
                       "no_reinsurancefirms": 4,
                       "no_riskmodels": 2,
                       "riskmodel_inaccuracy_parameter": 2, # values >=1; inaccuracy higher with higher values
                       "riskmodel_margin_of_safety": 2, # values >=1; factor of additional liquidity beyond value at risk
                       "value_at_risk_tail_probability": 0.005, # values <1, >0, usually close to 0; tail probability at which the value at risk is taken by the risk models
                       "norm_profit_markup": 0.15,
                       "rein_norm_profit_markup": 0.15,
                       "dividend_share_of_profits": 0.4,
                       "mean_contract_runtime": 36,
                       "contract_runtime_halfspread": 10,
                       "default_contract_payment_period": 12,
                       "max_time": 1000,
                       "money_supply": 2000000000,
                       "event_time_mean_separation": 100 / 3.,
                       "expire_immediately": False,
                       "risk_factors_present": False,
                       "risk_factor_lower_bound": 0.4,
                       "risk_factor_upper_bound": 0.6,
                       "initial_acceptance_threshold": 0.5,
                       "acceptance_threshold_friction": 0.9,
                       "insurance_firm_market_entry_probability": 0.15,#0.02,
                       "reinsurance_firm_market_entry_probability": 0.005,#0.004,
                       "simulation_reinsurance_type": 'non-proportional',
                       "default_non-proportional_reinsurance_deductible": 0.3,
                       "default_non-proportional_reinsurance_excess": 1.0,
                       "default_non-proportional_reinsurance_premium_share": 0.3,
                       "static_non-proportional_reinsurance_levels": False,
                       "catbonds_off": False,
                       "reinsurance_off": False,
                       "capacity_target_decrement_threshold": 1.8,
                       "capacity_target_increment_threshold": 1.2,
                       "capacity_target_decrement_factor": 24/25.,
                       "capacity_target_increment_factor": 25/24.,
                       "insurance_reinsurance_levels_lower_bound": 0.35,
                       "insurance_reinsurance_levels_upper_bound": 0.7,
                       "reinsurance_reinsurance_levels_lower_bound": 0.5,
                       "reinsurance_reinsurance_levels_upper_bound": 0.95,
                       "initial_agent_cash": 20000,
                       "initial_reinagent_cash": 200000,
                       "interest_rate": 0.001,
                       "reinsurance_limit": 0.1,
                       "upper_price_limit": 1.2,
                       "lower_price_limit": 0.85,
                       "no_risks": 20000}


