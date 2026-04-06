from ninja import Router

from .models import UIText

router = Router(tags=["content"])


@router.get("/texts/", auth=None)
def get_texts(request, lang: str = "de"):
    """Return all UI texts as a flat key→value dict for the given language."""
    if lang not in ("de", "fr"):
        lang = "de"

    field = f"text_{lang}"
    fallback = "text_de"

    texts = UIText.objects.all().values("key", field, fallback)
    result = {}
    for t in texts:
        value = t.get(field) or t.get(fallback) or ""
        result[t["key"]] = value

    return result
