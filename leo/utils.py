import re


def str_normalize(value: str) -> str:
    return re.sub(r"\W+", "", value).lower()
