
def dec_factory(arg_type):
    def decorator(func):
        def wrapper(arg):
            if isinstance(arg, arg_type):
                result = func(arg)
            else:
                print('Bad Type')
                result = None
            return result
        return wrapper
    return decorator


int_decorator = dec_factory(int)
str_decorator = dec_factory(str)


@int_decorator
def even(number):
    return number % 2 == 0


@str_decorator
def reverse(text):
    return text[::-1]


print('Testing even(2)')
print(even(2))
print("\nTesting even('2')")
print(even('2'))

print('---')

print("Testing reverse('arthur')")
print(reverse('arthur'))
print("\nTesting reverse(3)")
print(reverse(3))
