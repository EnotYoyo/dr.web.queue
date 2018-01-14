import time
import random


def main():
    time.sleep(random.randint(0, 10))
    if random.random() < 0.1:
        raise ArithmeticError


if __name__ == '__main__':
    main()