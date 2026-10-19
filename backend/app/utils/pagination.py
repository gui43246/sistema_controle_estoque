"""Helpers for validating bounded page and page-size query parameters."""


DEFAULT_PER_PAGE = 50
MAX_PER_PAGE = 200


def parse_pagination(query_args):
    """Return (page, per_page), capping page size and rejecting invalid values."""
    try:
        page = int(query_args.get("page", 1))
        per_page = int(query_args.get("per_page", DEFAULT_PER_PAGE))
    except (TypeError, ValueError) as error:
        raise ValueError("page e per_page devem ser números inteiros") from error

    if page < 1:
        raise ValueError("page deve ser maior ou igual a 1")
    if per_page < 1:
        raise ValueError("per_page deve ser maior ou igual a 1")

    return page, min(per_page, MAX_PER_PAGE)
