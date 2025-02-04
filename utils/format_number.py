from decimal import Decimal

def format_number(number):
    number = Decimal(str(number))
    integer_part = number // 1
    fractional_part = number - integer_part

    formatted_integer = '{:,.0f}'.format(integer_part).replace(',', ' ')

    if fractional_part == 0:
        return formatted_integer

    fractional_str = f"{fractional_part:.30f}".split('.')[1]
    first_non_zero = next((i for i, char in enumerate(fractional_str) if char != '0'), len(fractional_str))
    result_fractional = fractional_str[:first_non_zero + 3]
    result_fractional = result_fractional.rstrip('0')

    if not result_fractional:
        return formatted_integer

    return f"{formatted_integer}.{result_fractional}"
