from collections.abc import Iterator


def fibonacci(limit: int) -> Iterator[int]:
    a, b = 0, 1
    while a < limit:
        yield a
        a, b = b, a + b


def main() -> None:
    for num in fibonacci(100):
        print(num)


if __name__ == "__main__":
    main()
