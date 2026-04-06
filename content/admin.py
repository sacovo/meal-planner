import io

import polars as pl
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin
from unfold.decorators import action

from .models import UIText
from .tasks import translate_all_ui_texts, translate_ui_text


@admin.register(UIText)
class UITextAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ("key", "text_de", "text_fr")
    search_fields = ("key", "text_de", "text_fr")
    list_filter = ("key",)
    actions_list = [
        "export_texts_action",
        "import_texts_action",
        "translate_all_action",
    ]

    actions = ["translate_action"]

    @action(
        description="Export texts as Excel",
        url_path="export-texts",
    )
    def export_texts_action(self, request: HttpRequest):
        texts = UIText.objects.all().values("key", "text_de", "text_fr")
        df = pl.DataFrame(list(texts))

        buffer = io.BytesIO()
        df.write_excel(buffer, worksheet="UI Texts")
        buffer.seek(0)

        response = HttpResponse(
            buffer.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="ui_texts.xlsx"'
        return response

    @action(
        description="Import texts from Excel",
        url_path="import-texts",
        attrs={"enctype": "multipart/form-data"},
    )
    def import_texts_action(self, request: HttpRequest):
        if request.method == "POST" and request.FILES.get("file"):
            file = request.FILES["file"]
            df = pl.read_excel(io.BytesIO(file.read()))

            count = 0
            for row in df.iter_rows(named=True):
                key = row.get("key")
                if not key:
                    continue
                obj, created = UIText.objects.get_or_create(key=key)
                if row.get("text_de"):
                    obj.text_de = row["text_de"]
                if row.get("text_fr"):
                    obj.text_fr = row["text_fr"]
                obj.save()
                count += 1

            self.message_user(request, f"Successfully imported {count} texts.")
            return redirect(reverse_lazy("admin:content_uitext_changelist"))

        # Show a simple upload form
        html = """
        <html>
        <head><title>Import UI Texts</title></head>
        <body style="font-family: sans-serif; padding: 2rem;">
            <h2>Import UI Texts from Excel</h2>
            <p>Upload an Excel file with columns: <code>key</code>, <code>text_de</code>, <code>text_fr</code></p>
            <form method="post" enctype="multipart/form-data">
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf}">
                <input type="file" name="file" accept=".xlsx,.xls" required>
                <br><br>
                <button type="submit">Import</button>
            </form>
        </body>
        </html>
        """.replace("{csrf}", request.META.get("CSRF_COOKIE", ""))
        return HttpResponse(html)

    @action(
        description="Translate all (DE → FR) via AI",
        url_path="translate-all",
    )
    def translate_all_action(self, request: HttpRequest):
        translate_all_ui_texts.delay()
        self.message_user(
            request,
            "AI translation task started for all UI texts missing French translations.",
        )
        return redirect(reverse_lazy("admin:content_uitext_changelist"))

    @action(
        description="Translate selected texts (DE → FR) via AI",
        url_path="translate-selected",
    )
    def translate_action(self, request: HttpRequest, queryset: QuerySet[UIText]):
        for obj in queryset:
            translate_ui_text.delay(obj.id)

        self.message_user(
            request,
            f"AI translation task started for {queryset.count()} texts.",
        )
        return redirect(reverse_lazy("admin:content_uitext_changelist"))
