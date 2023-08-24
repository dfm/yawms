import re

WILDCARD_REGEX = re.compile(
    r"""
    \{
        (?=(   # This lookahead assertion emulates an 'atomic group'
               # which is required for performance
            \s*(?P<name>\w+)                    # wildcard name
            (\s*,\s*
                (?P<constraint>                 # an optional constraint
                    ([^{}]+ | \{\d+(,\d+)?\})*  # allow curly braces to nest one level
                )                               # ...  as in '{w,a{3,5}}'
            )?\s*
        ))\1
    \}
    """,
    re.VERBOSE,
)


def _get_regex_from_wildcard_pattern(pattern: str) -> tuple[re.Pattern[str], set[str]]:
    parts = []
    last = 0
    names = set()
    for match in WILDCARD_REGEX.finditer(pattern):
        parts.append(re.escape(pattern[last : match.start()]))
        name = match.group("name")
        if name in names:
            if match.group("constraint"):
                raise ValueError(
                    "Constraint regex must be defined only in the first "
                    "occurrence of the wildcard in a string."
                )
            parts.append(f"(?P={name})")
        else:
            names.add(name)
            parts.append(
                "(?P<{}>{})".format(
                    name,
                    match.group("constraint") if match.group("constraint") else ".+",
                )
            )
        last = match.end()
    parts.append(re.escape(pattern[last:]))
    parts.append("$")
    return re.compile("".join(parts)), names


class WildcardError(Exception):
    def __init__(self, name: str):
        self.name = name


def apply_wildcards(wildcards: dict[str, str], pattern: str) -> str:
    def format_match(match: re.Match[str]) -> str:
        name = match.group("name")
        try:
            return wildcards[name]
        except KeyError:
            raise WildcardError(name) from None

    return WILDCARD_REGEX.sub(format_match, pattern)


class Wildcard:
    pattern: str
    matcher: re.Pattern[str]
    names: set[str]

    def __init__(self, pattern: str) -> None:
        self.pattern = pattern
        self.matcher, self.names = _get_regex_from_wildcard_pattern(pattern)

    def __repr__(self) -> str:
        return f"<Wildcard {self.pattern}>"

    def match(self, string: str) -> dict[str, str] | None:
        match = self.matcher.match(string)
        return match.groupdict() if match is not None else None
