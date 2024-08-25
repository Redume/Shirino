def format_number(number):
    number_str = str(number)

    if '.' in number_str:
        integer_part, fractional_part = number_str.split('.')
    else:
        integer_part, fractional_part = number_str, ''

    formatted_integer_part = '{:,}'.format(int(integer_part)).replace(',', ' ')

    if fractional_part:
        return formatted_integer_part + '.' + fractional_part
    else:
        return formatted_integer_part
