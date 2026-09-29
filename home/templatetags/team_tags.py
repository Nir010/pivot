from django import template

register = template.Library()  # enables any function below as a filter


@register.filter
def lines(value):
    """Turn multiline text into a list, one non-empty trimmed line each.

    "A\\nB\\n\\nC"  ->  ["A", "B", "C"]
    """
    if not value:
        return []
    return [line.strip() for line in value.splitlines() if line.strip()]
