from decimal import Decimal

def format_number(number):
    number = Decimal(str(number))
    
    formatted_integer_part = '{:,.0f}'.format(number).replace(',', ' ')
    
    if '.' in str(number):
        fractional_part = str(number).split('.')[1]
        return formatted_integer_part + '.' + fractional_part
    else:
        return formatted_integer_part
