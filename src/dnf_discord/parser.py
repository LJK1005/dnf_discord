import re

_JO = 1_000_000_000_000
_EOK = 100_000_000
_MAN = 10_000


def parse_korean_number(value: str) -> int:
    if not value:
        return 0

    text = value.strip()

    jo_match = re.search(r"(\d+)조", text)
    eok_match = re.search(r"(\d+)억", text)
    man_match = re.search(r"(\d+)만", text)

    jo = int(jo_match.group(1)) if jo_match else 0
    eok = int(eok_match.group(1)) if eok_match else 0
    man = int(man_match.group(1)) if man_match else 0

    unit_ends = [m.end() for m in (jo_match, eok_match, man_match) if m]
    remain_part = text[max(unit_ends) :] if unit_ends else text
    remain = int(remain_part) if remain_part.isdigit() else 0

    return jo * _JO + eok * _EOK + man * _MAN + remain


def format_korean_number(value: int) -> str:
    if value == 0:
        return "0"

    parts = []

    jo = value // _JO
    if jo:
        parts.append(f"{jo}조")
    value %= _JO

    eok = value // _EOK
    if eok:
        parts.append(f"{eok}억")
    value %= _EOK

    man = value // _MAN
    if man:
        parts.append(f"{man}만")
    value %= _MAN

    if value:
        parts.append(str(value))

    return "".join(parts)
