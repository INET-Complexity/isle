use_abce = False
oneriskmodel = False
replicating = False
force_foreground = False
verbose = False
showprogress = False
show_network = False                   # Should network be visualized? This should be False by default, to be overridden by commandline arguments
slim_log = True                        # Should logs be small in ensemble runs (only aggregated level data)?
                       
simulation_parameters={"no_categories": 4,
                       "no_insurancefirms": 20,
                       "no_reinsurancefirms": 4,
                       "no_riskmodels": 2,
                       "riskmodel_inaccuracy_parameter": 2,  # values >=1; inaccuracy higher with higher values
                       "riskmodel_margin_of_safety": 2,  # values >=1; factor of additional liquidity beyond value at risk
                       "margin_increase": 0, # This parameter modifies the margin of safety depending on the number of risks models available in the market. When is 0 all risk models have the same margin of safety.
                       "value_at_risk_tail_probability": 0.005,  # values <1, >0, usually close to 0; tail probability at which the value at risk is taken by the risk models
                       "norm_profit_markup": 0.15,
                       "rein_norm_profit_markup": 0.15,
                       "dividend_share_of_profits": 0.4,
                       "mean_contract_runtime": 12,
                       "contract_runtime_halfspread": 2,
                       "default_contract_payment_period": 3,
                       "max_time": 1000,
                       "money_supply": 2000000000,
                       "event_time_mean_separation": 100 / 3.,
                       "expire_immediately": False,
                       "risk_factors_present": False,
                       "risk_factor_lower_bound": 0.4,
                       "risk_factor_upper_bound": 0.6,
                       "initial_acceptance_threshold": 0.5,
                       "acceptance_threshold_friction": 0.9,
                       "insurance_firm_market_entry_probability": 0.3,  #0.02,
                       "reinsurance_firm_market_entry_probability": 0.05,  #0.004,
                       "simulation_reinsurance_type": 'non-proportional',
                       "default_non-proportional_reinsurance_deductible": 0.3,
                       "default_non-proportional_reinsurance_excess": 1.0,
                       "default_non-proportional_reinsurance_premium_share": 0.3,
                       "static_non-proportional_reinsurance_levels": False,
                       "catbonds_off": True,
                       "reinsurance_off": False,
                       "capacity_target_decrement_threshold": 1.8,
                       "capacity_target_increment_threshold": 1.2,
                       "capacity_target_decrement_factor": 24/25.,
                       "capacity_target_increment_factor": 25/24.,
                       # Retention parameters
                       "insurance_retention": 0.85, # Ratio of insurance contracts retained every iteration.
                       "reinsurance_retention": 1, # Ratio of reinsurance contracts retained every iteration.
                       #Premium sensitivity parameters
                       "premium_sensitivity": 5,  # This parameter represents how sensitive is the variation of the insurance premium with respect of the capital of the market. Higher means more sensitive.
                       "reinpremium_sensitivity": 6,  # This parameter represents how sensitive is the variation of the reinsurance premium with respect of the capital of the market. Higher means more sensitive.
                       #Balanced portfolio parameters
                       "insurers_balance_ratio": 0.1,  # This ratio represents how low we want to keep the standard deviation of the cash reserved below the mean for insurers. Lower means more balanced.
                       "reinsurers_balance_ratio": 20,  # This ratio represents how low we want to keep the standard deviation of the cash reserved below the mean for reinsurers. Lower means more balanced. (Deactivated for the moment)
                       "insurers_recursion_limit": 50,  # Intensity of the recursion algorithm to balance the portfolio of risks for insurers.
                       "reinsurers_recursion_limit": 10,  # Intensity of the recursion algorithm to balance the portfolio of risks for reinsurers.
                       #Market permanency parameters
                       "market_permanency_off": False,  # This parameter activates (deactivates) the following market permanency constraints.
                       "cash_permanency_limit": 100,  # This parameter enforces the limit under which the firms leave the market because they cannot underwrite anything.
                       "insurance_permanency_contracts_limit": 4,  # If insurers stay for too long under this limit of contracts they deccide to leave the market.
                       "insurance_permanency_ratio_limit": 0.6,  # If insurers stay for too long under this limit they deccide to leave the market because they have too much capital.
                       "insurance_permanency_time_constraint": 24,  # This parameter defines the period that the insurers wait if they have few capital or few contract before leaving the market.
                       "reinsurance_permanency_contracts_limit": 2,  # If reinsurers stay for too long under this limit of contracts they deccide to leave the market.
                       "reinsurance_permanency_ratio_limit": 0.8,  # If reinsurers stay for too long under this limit they deccide to leave the market because they have too much capital.
                       "reinsurance_permanency_time_constraint": 48,  # This parameter defines the period that the reinsurers wait if they have few capital or few contract before leaving the market.
                       #Insurance and Reinsurance deductibles
                       "insurance_reinsurance_levels_lower_bound": 0.25,
                       "insurance_reinsurance_levels_upper_bound": 0.30,
                       "reinsurance_reinsurance_levels_lower_bound": 0.5,
                       "reinsurance_reinsurance_levels_upper_bound": 0.95,
                       "initial_agent_cash": 80000,
                       "initial_reinagent_cash": 2000000,
                       "interest_rate": 0.001,
                       "reinsurance_limit": 0.1,
                       "upper_price_limit": 1.2,
                       "lower_price_limit": 0.85,
                       "no_risks": 20000}


