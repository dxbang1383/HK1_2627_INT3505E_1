import base64
import json
from dataclasses import dataclass
from pathlib import Path

from flask import Blueprint, jsonify, request
from jsonschema import Draft202012Validator
from sqlalchemy import and_, asc, desc, func, or_

from models import Book, Category, db


books_bp = Blueprint("books", __name__)

DEFAULT_LIMIT = 20
MAX_LIMIT = 100
DEFAULT_SORT = "-id"

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "book.json"
BOOK_VALIDATOR = Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


@dataclass(frozen=True)
class SortSpec:
    name: str
    column: object
    descending: bool


SORT_COLUMNS = {
    "id": Book.id,
    "title": Book.title,
    "isbn": Book.isbn,
    "price": Book.price_vnd,
    "price_vnd": Book.price_vnd,
    "stock": Book.stock,
    "genre": Category.slug,
}


class QueryError(ValueError):
    pass


def _error(message):
    return jsonify({"error": message}), 400


def _parse_positive_int(name, default, maximum=None, minimum=1):
    raw_value = request.args.get(name)
    if raw_value is None or raw_value == "":
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise QueryError(f"{name} must be an integer") from exc
    if value < minimum:
        raise QueryError(f"{name} must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise QueryError(f"{name} must be <= {maximum}")
    return value


def _parse_offset():
    raw_value = request.args.get("offset", "0")
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise QueryError("offset must be an integer") from exc
    if value < 0:
        raise QueryError("offset must be >= 0")
    return value


def _parse_sort(default_sort=DEFAULT_SORT):
    raw_sort = request.args.get("sort", default_sort)
    tokens = [token.strip() for token in raw_sort.split(",") if token.strip()]
    if not tokens:
        raise QueryError("sort must contain at least one field")

    specs = []
    seen = set()
    for token in tokens:
        descending = token.startswith("-")
        field = token[1:] if token[:1] in {"-", "+"} else token
        if field not in SORT_COLUMNS:
            allowed = ", ".join(sorted(SORT_COLUMNS))
            raise QueryError(f"unsupported sort field '{field}'. Allowed: {allowed}")
        if field in seen:
            raise QueryError(f"sort field '{field}' is duplicated")
        seen.add(field)
        specs.append(SortSpec(field, SORT_COLUMNS[field], descending))
    return specs


def _sort_signature(specs):
    return ",".join(("-" if spec.descending else "") + spec.name for spec in specs)


def _ensure_category_join(query, specs, genre):
    needs_category = genre is not None or any(spec.name == "genre" for spec in specs)
    return query.join(Book.category) if needs_category else query


def _apply_filters(query, genre):
    if genre is None:
        return query
    genre = genre.strip()
    if not genre:
        raise QueryError("genre must not be empty")
    normalized = genre.casefold()
    return query.filter(
        or_(func.lower(Category.slug) == normalized, func.lower(Category.name) == normalized)
    )


def _apply_order(query, specs):
    ordering = [spec.column.desc() if spec.descending else spec.column.asc() for spec in specs]
    # ID is the deterministic tie-breaker for every sort that does not already use it.
    if specs[-1].name != "id":
        ordering.append(Book.id.desc() if specs[-1].descending else Book.id.asc())
    return query.order_by(*ordering)


def _encode_cursor(payload):
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(token):
    if not token:
        return None
    if len(token) > 4096:
        raise QueryError("cursor is too long")
    try:
        padding = "=" * (-len(token) % 4)
        raw = base64.b64decode(
            (token + padding).encode("ascii"), altchars=b"-_", validate=True
        )
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise QueryError("cursor must be a valid base64url JSON value") from exc
    if not isinstance(payload, dict) or not {"s", "v", "i"}.issubset(payload):
        raise QueryError("cursor payload must contain s, v and i")
    if not isinstance(payload["s"], str) or not isinstance(payload["i"], int):
        raise QueryError("cursor fields s and i have invalid types")
    return payload


def _cursor_values(payload, specs):
    values = payload.get("k")
    if values is None:
        values = [payload["v"]]
    if not isinstance(values, list) or len(values) != len(specs):
        raise QueryError("cursor does not match the requested sort")
    return values


def _apply_cursor(query, payload, specs):
    if payload is None:
        return query
    expected_sort = _sort_signature(specs)
    if payload["s"] != expected_sort:
        raise QueryError("cursor was created for a different sort")

    values = _cursor_values(payload, specs)
    branches = []
    equal_prefix = []
    for spec, value in zip(specs, values):
        comparison = spec.column < value if spec.descending else spec.column > value
        branches.append(and_(*equal_prefix, comparison))
        equal_prefix.append(spec.column == value)

    if specs[-1].name != "id":
        id_comparison = Book.id < payload["i"] if specs[-1].descending else Book.id > payload["i"]
        branches.append(and_(*equal_prefix, id_comparison))
    return query.filter(or_(*branches))


def _cursor_for(book, specs):
    values = []
    for spec in specs:
        if spec.name == "genre":
            value = book.category.slug if book.category else None
        else:
            value = getattr(book, "price_vnd" if spec.name == "price" else spec.name)
        values.append(value)

    payload = {
        "s": _sort_signature(specs),
        "v": values[0],
        "i": book.id,
    }
    if len(values) > 1:
        payload["k"] = values
    return _encode_cursor(payload)


def _serialize(books):
    data = [book.to_dict() for book in books]
    for item in data:
        BOOK_VALIDATOR.validate(item)
    return data


@books_bp.get("/books")
def list_books():
    try:
        strategy = request.args.get("strategy", "cursor").lower()
        if strategy not in {"offset", "cursor"}:
            raise QueryError("strategy must be either 'offset' or 'cursor'")
        limit = _parse_positive_int("limit", DEFAULT_LIMIT, MAX_LIMIT)
        offset = _parse_offset() if strategy == "offset" else None
        specs = _parse_sort("id" if strategy == "offset" else DEFAULT_SORT)
        genre = request.args.get("genre")

        query = db.session.query(Book)
        query = _ensure_category_join(query, specs, genre)
        query = _apply_filters(query, genre)

        if strategy == "offset":
            total = query.order_by(None).count()
            books = _apply_order(query, specs).offset(offset).limit(limit).all()
            return jsonify(
                {
                    "data": _serialize(books),
                    "pagination": {
                        "offset": offset,
                        "limit": limit,
                        "total": total,
                        "has_next": offset + len(books) < total,
                    },
                }
            )

        payload = _decode_cursor(request.args.get("cursor"))
        query = _apply_cursor(query, payload, specs)
        books = _apply_order(query, specs).limit(limit + 1).all()
        has_more = len(books) > limit
        if has_more:
            books = books[:limit]
        next_cursor = _cursor_for(books[-1], specs) if has_more and books else None
        return jsonify(
            {
                "data": _serialize(books),
                "page": {
                    "next": next_cursor,
                    "has_more": has_more,
                    "limit": limit,
                    "sort": _sort_signature(specs),
                },
            }
        )
    except QueryError as exc:
        return _error(str(exc))
