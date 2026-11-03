"""
Financial & Pricing Helper Functions.

Note:
These are pure helper functions without any side-effects, database access, or FastAPI dependencies.
This makes them easily testable with unit tests.
"""


def round_to_two_decimals(value: float) -> float:
    """Helper: Rounds float values to 2 decimal places representing currency cents."""
    return round(value, 2)


def compute_discount_amount(gross_amount: float, discount_percentage: float) -> float:
    """
    Helper: Computes the monetary discount amount from a gross price and discount percentage.

    :param gross_amount: Base amount before discount.
    :param discount_percentage: Value between 0.0 and 100.0.
    :return: Discount amount in currency.
    """
    if discount_percentage <= 0:
        return 0.0
    discount = (gross_amount * discount_percentage) / 100.0
    return round_to_two_decimals(discount)


def compute_sales_tax(taxable_amount: float, tax_rate_percentage: float) -> float:
    """
    Helper: Computes the sales tax for an amount given a tax rate percentage.

    :param taxable_amount: Amount after discount.
    :param tax_rate_percentage: Tax rate e.g., 8.5 for 8.5%.
    :return: Calculated tax amount.
    """
    if tax_rate_percentage <= 0:
        return 0.0
    tax = (taxable_amount * tax_rate_percentage) / 100.0
    return round_to_two_decimals(tax)

