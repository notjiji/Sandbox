import re
import uuid


def slugify(value: str, *, fallback: str = "item") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or fallback


def unique_slug(base: str, *, suffix: uuid.UUID | None = None) -> str:
    slug = slugify(base)
    if suffix is None:
        return slug
    return f"{slug}-{str(suffix).split('-')[0]}"
