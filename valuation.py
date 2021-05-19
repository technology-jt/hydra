import pandas as pd
import numpy as np
import numpy_financial as npf

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)


class HomeModel:
    def __init__(self,
                 listvalue,  # total property value
                 interestrate,  # per annum mortgage rate
                 discount_rate,  # general risk free rate
                 tax_proj_rate,  # general projection rate for tax liabilities
                 carry_proj_rate,  # general projection rate for carry income
                 property_proj_rate,  # general projection rate for property value
                 tax_rate,  # per annum tax rate
                 tax_pay_freq,
                 tenor,  # tenor of the model in years
                 sqft):

        self.listvalue = listvalue
        self.interestrate = interestrate
        self.discount_rate = discount_rate
        self.tax_rate = tax_rate
        self.tax_pay_freq = tax_pay_freq
        self.tax_projection_rate = tax_proj_rate
        self.carry_proj_rate = carry_proj_rate
        self.property_proj_rate = property_proj_rate
        self.tenor = tenor
        self.sqft = sqft

    def generic_cf_dict(self, frequency=12):
        length = range(int(frequency / 12), self.tenor * frequency + 1)  # create a vector schedule of every month
        cf_library = {
            i: 0 for i in length
        }

        return cf_library

    def generic_df_curve(self, generic_discount_rate):
        dfcurve_ = self.generic_cf_dict()
        for period in dfcurve_:
            dfcurve_[period] = 1 / (1 + generic_discount_rate / 12) ** period

        return dfcurve_

    def generic_projection_curve(self, generic_projection_rate):
        projection_curve = self.generic_cf_dict()
        for period in projection_curve:
            projection_curve[period] = (1 + generic_projection_rate / 12) ** period

        return projection_curve

    def vanilla_cf(self, frequency=12, period_cf=0):
        vanilla_cf_ = self.generic_cf_dict()
        for period in vanilla_cf_.keys():
            if period % frequency == 0:
                vanilla_cf_[period] = period_cf

        return vanilla_cf_

    def calculate_projection(self, cashflows, projection_curve):
        projected_cashflows = {
            cf_event: cashflows[cf_event] * projection_curve[cf_event] for cf_event in cashflows
        }

        return projected_cashflows

    def calculate_discount(self, cashflows, discount_curve):
        discounted_cashflows = {
            cf_event: cashflows[cf_event] * discount_curve[cf_event] for cf_event in cashflows
        }

        return discounted_cashflows

    def carry_income(self, multiplier):
        income_schedule = self.generic_cf_dict()
        for payment in income_schedule:
            income_schedule[payment] = self.sqft * multiplier
        fwd_inc_schedule = self.calculate_projection(income_schedule,
                                                     self.generic_projection_curve(
                                                         self.carry_proj_rate
                                                     ))
        disc_fwd_inc_schedule = self.calculate_discount(fwd_inc_schedule,
                                                        self.generic_df_curve(self.discount_rate))

        return disc_fwd_inc_schedule

    def pricepersqft(self):
        pricepersqft_ = self.listvalue / self.sqft

        return pricepersqft_


newproperty = HomeModel(listvalue=400000,
                        interestrate=-0.050,
                        discount_rate=.0160,
                        tax_rate=-0.05,
                        tax_pay_freq=1,
                        tax_proj_rate=0.025,
                        carry_proj_rate=0.05,
                        property_proj_rate=0.07,
                        sqft=1000,
                        tenor=10)


# Assembling the various dataframes which are inherent to specific cash flows. They may require specific discount and
# projection curves that are based on assumptions defined in the new property class.

# TAX LIABILITY CASH FLOWS
tax_df = pd.DataFrame(
    {
        'DF Curve': newproperty.generic_df_curve(newproperty.discount_rate),
        'Projection Curve': newproperty.generic_projection_curve(newproperty.tax_projection_rate),
        'Cashflows': newproperty.vanilla_cf(
            frequency=newproperty.tax_pay_freq,
            period_cf=newproperty.tax_rate * newproperty.listvalue * newproperty.tax_pay_freq / 12),
    })

tax_df['Fwd Cashflows'] = tax_df['Cashflows'] * tax_df['Projection Curve']
tax_df['PV Fwd Cashflows'] = tax_df['Fwd Cashflows'] * tax_df['DF Curve']

carry_df = pd.DataFrame(
    {
        'DF Curve': newproperty.generic_df_curve(newproperty.discount_rate),
        'Projection Curve': newproperty.generic_projection_curve(newproperty.carry_proj_rate),
        'Cashflows': 0,
        'Fwd Cashflows': 0,
        'PV Fwd Cashflows': 0
    })

# PRINCIPAL PAYMENT CASHFLOWS
principal_df = pd.DataFrame(
    {
        'DF Curve': newproperty.generic_df_curve(newproperty.discount_rate),
        'Projection Curve': newproperty.generic_projection_curve(0.00),
        'Cashflows': 0,
        'Fwd Cashflows': 0,
        'PV Fwd Cashflows': 0
    })

# INTEREST PAYMENT CASHFLOWS
interest_df = pd.DataFrame(
    {
        'DF Curve': newproperty.generic_df_curve(newproperty.discount_rate),
        'Projection Curve': newproperty.generic_projection_curve(0.00),
        'Cashflows': 0,
        'Fwd Cashflows': 0,
        'PV Fwd Cashflows': 0
    })

# PROPERTY VALUE CASHFLOWS
property_df = pd.DataFrame(
    {
        'DF Curve': newproperty.generic_df_curve(newproperty.discount_rate),
        'Projection Curve': newproperty.generic_projection_curve(newproperty.property_proj_rate),
        'Cashflows': 0,
        'Fwd Cashflows': 0,
        'PV Fwd Cashflows:': 0
    })

master_cf = pd.DataFrame(index=range(1, newproperty.tenor * 12 + 1))
master_cf['Tax CF'] = tax_df['PV Fwd Cashflows']
master_cf.describe()
