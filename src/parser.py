def parse_numbers(text):
    """Convert comma-separated numbers into integers."""
    return [int(x.strip()) for x in text.split(",")]