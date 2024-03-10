import secrets
import string

from data_helpers import get_and_update_counter

lower_bound = 0
upper_bound = 0
counter = 1


def generate_secure_unique_key():
    global counter, lower_bound, upper_bound
    print("Lower:", lower_bound)
    print("upper:", upper_bound)
    print("count:", counter)
    characters = string.ascii_letters + string.digits
    key = "".join(secrets.choice(characters) for _ in range(6))

    if counter >= upper_bound:
        lower_bound, upper_bound = get_and_update_counter()
        counter = lower_bound + 1

    counter += 1
    base_62_val = int_to_base62(counter)
    random_chars = generate_two_random_chars()

    key = base_62_val + random_chars
    return key


def generate_two_random_chars(length=2):
    characters = string.ascii_letters + string.digits
    rand_key = "".join(secrets.choice(characters) for _ in range(length))
    return rand_key


def int_to_base62(num, length=6):
    characters = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    base = 62
    result = []
    while num:
        num, remainder = divmod(num, base)
        result.append(characters[remainder])
    return "".join(reversed(result))
