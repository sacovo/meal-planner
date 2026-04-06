from modeltranslation.translator import TranslationOptions, register

from .models import UIText


@register(UIText)
class UITextTranslationOptions(TranslationOptions):
    fields = ("text",)
