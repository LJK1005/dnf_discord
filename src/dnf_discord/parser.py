import re


def parse_korean_number(value: str) -> int:
    if not value:
        return 0

    text = value.strip()

    eok_match = re.search(r"(\d+)억", text)
    man_match = re.search(r"(\d+)만", text)

    eok = int(eok_match.group(1)) if eok_match else 0
    man = int(man_match.group(1)) if man_match else 0

    remain_part = text
    if man_match:
        remain_part = text[man_match.end():]
    elif eok_match:
        remain_part = text[eok_match.end():]

    remain = int(remain_part) if remain_part.isdigit() else 0

    return eok * 100_000_000 + man * 10_000 + remain


def format_korean_number(value: int) -> str:
    if value == 0:
        return "0"

    parts = []

    eok = value // 100_000_000
    if eok:
        parts.append(f"{eok}억")
    value %= 100_000_000

    man = value // 10_000
    if man:
        parts.append(f"{man}만")
    value %= 10_000

    if value:
        parts.append(str(value))

    return "".join(parts)
