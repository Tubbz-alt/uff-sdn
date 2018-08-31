global_list = []


def append_to_list(func):
    def wrapper(*args, **kwargs):
        global global_list
        answer = func(*args, **kwargs)
        global_list.append(answer)
        return answer
    return wrapper


@append_to_list
def sum(a, b, c):
    return a + b + c


def multiply(a, b, c):
    return a * b * c


multiply = append_to_list(multiply)

sum(1, 2, 3)
print(global_list)
multiply(2, 2, 2)
print(global_list)
