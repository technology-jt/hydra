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
                 interest_rate,  # per annum mortgage rate
                 discount_rate,  # general risk free rate
                 tax_proj_rate,  # general projection rate for tax liabilities
                 carry_proj_rate,  # general projection rate for carry income
                 property_proj_rate,  # general projection rate for property value
                 tax_rate,  # per annum tax rate
                 tax_pay_freq,  # tax payment frequency
                 tenor,  # tenor of the loan
                 down_percent,  # down payment percentage on the mortgage == initial equity in the property
                 down_pay_freq):  # frequency of down payment installations

        self.list_value = listvalue
        self.interest_rate = interest_rate
        self.discount_rate = discount_rate
        self.tax_rate = tax_rate
        self.tax_pay_freq = tax_pay_freq
        self.tax_projection_rate = tax_proj_rate
        self.carry_proj_rate = carry_proj_rate
        self.property_proj_rate = property_proj_rate
        self.tenor = tenor
        self.down_percent = down_percent
        self.down_pay_freq = down_pay_freq
        self.loan_amount = self.list_value * self.down_percent
        self.tax_df = self.get_cf_dataframe(self.generic_df_curve(self.discount_rate),
                                            self.generic_proj_curve(self.tax_projection_rate),
                                            self.vanilla_cf(frequency=self.tax_pay_freq,
                                                            period_cf=self.tax_rate * self.list_value * self.tax_pay_freq / 12))

        self.mortgage_payments = self.vanilla_cf(frequency=self.down_pay_freq,
                                                 period_cf=self.down_percent * self.list_value / (-12 * self.down_pay_freq * self.tenor))

        self.mortgage_schedule = self.get_mortgage_schedule()

    def generic_cf_dict(self, frequency=12):
        length = range(int(frequency / 12), self.tenor * frequency + 1)
        cf_library = {
            i: 0 for i in length
        }
        return cf_library

    def generic_df_curve(self, generic_discount_rate):
        dfcurve_ = self.generic_cf_dict()
        for period in dfcurve_:
            dfcurve_[period] = 1 / (1 + generic_discount_rate / 12) ** period
        return dfcurve_

    def generic_proj_curve(self, generic_projection_rate):
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

    def calc_proj(self, cashflows, projection_curve):
        projected_cashflows = {
            cf_event: cashflows[cf_event] * projection_curve[cf_event] for cf_event in cashflows
        }
        return projected_cashflows

    def calc_disc(self, cashflows, discount_curve):
        discounted_cashflows = {
            cf_event: cashflows[cf_event] * discount_curve[cf_event] for cf_event in cashflows
        }
        return discounted_cashflows

    def get_cf_dataframe(self, discount_curve, projection_curve, cash_flows):
        df = pd.DataFrame(
            {
                'DF Curve': discount_curve,
                'Proj Curve': projection_curve,
                'Cashflows': cash_flows,
                'Fwd Cashflows': self.calc_proj(cash_flows, projection_curve),
                'Disc Fwd Cashflows': self.calc_disc(self.calc_proj(cash_flows, projection_curve), discount_curve)
            })
        return df

    def get_mortgage_schedule(self):
        df = pd.DataFrame(
            {
                'DF Curve': self.generic_df_curve(self.discount_rate),
                'Mortgage Payments': self.mortgage_payments,
            }
        )
        df['Accumulated Payments'] = df.index.values * df['Mortgage Payments']
        df['Remaining Loan'] = df['Accumulated Payments'] + self.loan_amount
        df['Interest Payments'] = df['Remaining Loan'] * self.interest_rate / 12
        df['Total Payments'] = df['Interest Payments'] + df['Mortgage Payments']
        return df


parameters = {
    'listvalue': 100000,
    'interest_rate': -0.05,
    'discount_rate': 0.016,
    'tax_rate': -0.05,
    'tax_pay_freq': 1,
    'tax_proj_rate': 0.025,
    'carry_proj_rate': 0.05,
    'property_proj_rate': 0.07,
    'tenor': 10,
    'down_percent': 0.5,
    'down_pay_freq': 1
}

NewProperty = HomeModel(**parameters)
print(NewProperty.tax_df)
print(NewProperty.mortgage_schedule)
print(NewProperty.mortgage_schedule['Total Payments'].sum())
