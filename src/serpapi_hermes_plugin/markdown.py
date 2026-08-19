"""Structure-aware transformations for SerpApi Markdown responses."""

from __future__ import annotations

import re

from markdown_it import MarkdownIt

_PARSER = MarkdownIt("commonmark").enable("table")


def _normalized_heading(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _matches_heading(value: str, expected: str) -> bool:
    normalized = _normalized_heading(value)
    return normalized == expected or normalized.startswith(f"{expected} ")


def limit_result_table(markdown: str, *, heading: str, limit: int) -> str:
    """Limit table body rows under a named Markdown heading.

    Source line mappings from markdown-it-py let us remove excess rows without
    rendering the document again, so unrelated formatting remains unchanged.
    """
    tokens = _PARSER.parse(markdown)
    expected_heading = _normalized_heading(heading)
    section_level: int | None = None
    in_table_body = False
    result_count = 0
    removed_lines: set[int] = set()

    for index, token in enumerate(tokens):
        if token.type == "heading_open":
            level = int(token.tag.removeprefix("h"))
            if section_level is not None and level <= section_level:
                break

            next_token = tokens[index + 1] if index + 1 < len(tokens) else None
            if (
                section_level is None
                and next_token is not None
                and next_token.type == "inline"
                and _matches_heading(next_token.content, expected_heading)
            ):
                section_level = level
            continue

        if section_level is None:
            continue
        if token.type == "tbody_open":
            in_table_body = True
        elif token.type == "tbody_close":
            in_table_body = False
        elif token.type == "tr_open" and in_table_body and token.map is not None:
            result_count += 1
            if result_count > limit:
                removed_lines.update(range(*token.map))

    if not removed_lines:
        return markdown

    return "".join(
        line
        for line_number, line in enumerate(markdown.splitlines(keepends=True))
        if line_number not in removed_lines
    )
