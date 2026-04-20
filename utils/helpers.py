def print_banner(title: str) -> None:
    line = "=" * 70
    print("\n" + line)
    print(title.center(70))
    print(line)


def print_section(title: str) -> None:
    line = "-" * 70
    print(f"\n{line}")
    print(title)
    print(line)


def print_subsection(title: str) -> None:
    print(f"\n{title}")
    print("." * len(title))


def print_kv_block(data: dict) -> None:
    """
    Pretty-print a dictionary as key-value pairs.
    """
    print("\nResult Summary")
    print("." * 20)
    for key, value in data.items():
        print(f"{key}: {value}")