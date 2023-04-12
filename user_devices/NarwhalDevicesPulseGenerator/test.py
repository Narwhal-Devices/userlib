from pylab import *



def stepBy(steps, value):






    new_val = value + steps
    return new_val



def least_significant_digit_position(value):
    value_str = f"{value:.9f}".rstrip('0')
    print(value_str)
    dot_position = value_str.find('.')
    print(dot_position)
    
    for i, char in enumerate(reversed(value_str)):
        if char != '.' and char != '0':
            break

    position_from_right = i
    position_from_left = len(value_str) - 1 - position_from_right

    if dot_position >= 0:
        position_from_left -= 1

    return position_from_left


def least_significant_digit_unit(value):
    num_string = f'{value:.9f}'.rstrip('0')
    if num_string[-1] == '.':
        for idx, char in enumerate(reversed(num_string)):
            if char != '.' and char != '0':
                break
        lsf_position = idx - 1
    else:
        lsf_position = -(len(num_string) - num_string.index('.') - 1)
    step = 10**lsf_position
    return step 

print(least_significant_digit_unit(100))
print(least_significant_digit_unit(160.000))
print(least_significant_digit_unit(111.000))
print(least_significant_digit_unit(111.100))
print(least_significant_digit_unit(111.110))
print(least_significant_digit_unit(111.111))

    # if '.' in num_string:
    #     # There's a decimal point. Figure out how many digits are to the right
    #     # of the decimal point and negate that.
    #     return -len(num_string.partition('.')[2])
    # else:
    #     # No decimal point. Count trailing zeros.
    #     return len(num_string) - len(num_string.rstrip('0'))


# def least_significant_digit_number(value):
#     value_str = f"{value:.10f}".rstrip('0')
#     dot_position = value_str.find('.')
    
#     for i, char in enumerate(reversed(value_str)):
#         if char != '.' and char != '0':
#             break

#     position_from_right = i
#     position_from_left = len(value_str) - 1 - position_from_right

#     if dot_position >= 0:
#         position_from_left -= 1

#     # Create a number with all zeros except a 1 at the least significant digit position
#     number_str = '1' + '0' * (position_from_left - 1)
#     if dot_position >= 0:
#         number_str = number_str[:-dot_position] + '.' + number_str[-dot_position:]
    
#     return float(number_str)

# print(least_significant_digit_power(100.000))
# print(least_significant_digit_power(110.000))
# print(least_significant_digit_power(111.000))
# print(least_significant_digit_power(111.100))
# print(least_significant_digit_power(111.110))
# print(least_significant_digit_power(111.111))



# print(least_significant_digit_number(100))
# print(least_significant_digit_number(110.000))
# print(least_significant_digit_number(111.000))
# print(least_significant_digit_number(111.100))
# print(least_significant_digit_number(111.110))
# print(least_significant_digit_number(111.111))


# print(least_significant_digit_power(11.111))
# print(least_significant_digit_position(100))
# print(least_significant_digit_position(110.000))
# print(least_significant_digit_position(111.000))
# print(least_significant_digit_position(111.100))
# print(least_significant_digit_position(111.110))
# print(least_significant_digit_position(111.111))
# print(least_significant_digit_position(111.000))



    def stepBy(self, steps):
        value = self.value()
        step = self.least_significant_digit_unit(value)
        new_value = value + (steps * step)
        new_value = max(min(new_value, self.maximum()), self.minimum())
        self.setValue(new_value)

    def least_significant_digit_unit(self, value):
        num_string = f'{value:.9f}'.rstrip('0')
        if num_string[-1] == '.':
            for idx, char in enumerate(reversed(num_string)):
                if char != '.' and char != '0':
                    break
            lsf_position = idx - 1
        else:
            lsf_position = -(len(num_string) - num_string.index('.') - 1)
        step = 10**lsf_position
        return step 