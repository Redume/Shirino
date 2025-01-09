from decimal import Decimal

def format_number(number):
    number = Decimal(str(number))

    formatted_integer_part = '{:,.0f}'.format(number // 1).replace(',', ' ')
    fractional_part = f"{number % 1:.30f}".split('.')[1]

    if int(fractional_part) == 0:
        return formatted_integer_part + ''
    
    significant_start = next((i for i, char in enumerate(fractional_part) if char != '0'), len(fractional_part))
    result_fractional = fractional_part[:significant_start + 3]
    return formatted_integer_part + '.' + result_fractional
