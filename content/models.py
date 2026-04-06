from django.db import models


class UIText(models.Model):
    key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique key like 'nav.camps', 'btn.save'",
    )
    text = models.TextField(help_text="The UI text content")

    class Meta:
        ordering = ["key"]
        verbose_name = "UI Text"
        verbose_name_plural = "UI Texts"

    def __str__(self):
        return self.key
