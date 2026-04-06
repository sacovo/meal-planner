from django.core.management.base import BaseCommand

from content.models import UIText

DEFAULT_TEXTS = {
    # Navigation
    "nav.camps": "Lager",
    "nav.recipes": "Rezepte",
    "nav.account": "Konto",
    "nav.app_name": "Meal Planner",
    # Dashboard
    "dashboard.title": "Deine Lager",
    "dashboard.create_camp": "+ Lager erstellen",
    "dashboard.no_camps": "Du hast noch keine Lager. Erstelle jetzt dein erstes!",
    "dashboard.open_planner": "Planer öffnen",
    "dashboard.people": "Personen",
    "dashboard.to": "bis",
    # Create Camp Modal
    "camp.create_title": "Neues Lager erstellen",
    "camp.name_label": "Lagername",
    "camp.name_placeholder": "Sommerlager 2026",
    "camp.people_count_label": "Standard-Personenzahl",
    "camp.start_date_label": "Startdatum",
    "camp.end_date_label": "Enddatum",
    # General Buttons
    "btn.create": "Erstellen",
    "btn.cancel": "Abbrechen",
    "btn.save": "Speichern",
    "btn.delete": "Löschen",
    "btn.edit": "Bearbeiten",
    "btn.close": "Schliessen",
    "btn.back": "Zurück",
    "btn.add": "Hinzufügen",
    "btn.remove": "Entfernen",
    "btn.search": "Suchen",
    "btn.loading": "Laden...",
    "btn.confirm": "Bestätigen",
    # Login
    "login.title": "Anmelden",
    "login.username": "Benutzername",
    "login.password": "Passwort",
    "login.submit": "Anmelden",
    "login.error": "Ungültige Anmeldedaten",
    "login.forgot_password": "Passwort vergessen?",
    # Account
    "account.title": "Konto-Einstellungen",
    "account.profile": "Profil",
    "account.first_name": "Vorname",
    "account.last_name": "Nachname",
    "account.update_profile": "Profil aktualisieren",
    "account.change_password": "Passwort ändern",
    "account.old_password": "Altes Passwort",
    "account.new_password": "Neues Passwort",
    "account.confirm_password": "Passwort bestätigen",
    "account.logout": "Abmelden",
    "account.profile_updated": "Profil erfolgreich aktualisiert.",
    "account.password_changed": "Passwort erfolgreich geändert.",
    # Forgot/Reset Password
    "forgot.title": "Passwort vergessen",
    "forgot.email": "E-Mail-Adresse",
    "forgot.submit": "Link senden",
    "forgot.success": "Falls ein Konto mit dieser E-Mail existiert, wurde ein Link zum Zurücksetzen gesendet.",
    "forgot.back_to_login": "Zurück zur Anmeldung",
    "reset.title": "Passwort zurücksetzen",
    "reset.new_password": "Neues Passwort",
    "reset.confirm_password": "Passwort bestätigen",
    "reset.submit": "Passwort zurücksetzen",
    "reset.success": "Dein Passwort wurde zurückgesetzt. Du kannst dich jetzt anmelden.",
    "reset.error": "Ungültiger oder abgelaufener Link.",
    # Camp Planner
    "planner.title": "Lagerplaner",
    "planner.menu_pool": "Menü-Pool",
    "planner.shopping_lists": "Einkaufslisten",
    "planner.general_items": "Allgemeine Artikel",
    "planner.collaborators": "Mitarbeiter",
    "planner.notes": "Notizen",
    "planner.inventory": "Inventar",
    "planner.settings": "Einstellungen",
    "planner.day_view": "Tagesansicht",
    "planner.filter": "Filtern",
    "planner.all_recipes": "Alle Rezepte",
    # Meal Types
    "meal.breakfast": "Frühstück",
    "meal.morning_snack": "Znüni",
    "meal.lunch": "Mittagessen",
    "meal.afternoon_snack": "Zvieri",
    "meal.dinner": "Abendessen",
    "meal.dessert": "Dessert",
    "meal.night_snack": "Nachtsnack",
    # Recipe
    "recipe.title": "Rezepte",
    "recipe.create": "Neues Rezept",
    "recipe.search_placeholder": "Rezepte suchen...",
    "recipe.ingredients": "Zutaten",
    "recipe.instructions": "Anleitung",
    "recipe.description": "Beschreibung",
    "recipe.portions": "Portionen",
    "recipe.tags": "Tags",
    "recipe.import": "Rezept importieren",
    "recipe.import_text": "Text einfügen",
    "recipe.importing": "Wird importiert...",
    "recipe.add_ingredient": "Zutat hinzufügen",
    "recipe.ingredient_name": "Zutatname",
    "recipe.amount": "Menge",
    "recipe.unit": "Einheit",
    "recipe.delete_confirm": "Möchtest du dieses Rezept wirklich löschen?",
    "recipe.collaborators": "Mitarbeiter",
    "recipe.owner": "Besitzer",
    "recipe.no_results": "Keine Rezepte gefunden.",
    # Shopping List
    "shopping.title": "Einkaufsliste",
    "shopping.generate": "Einkaufsliste generieren",
    "shopping.share": "Teilen",
    "shopping.shared_link": "Geteilter Link",
    "shopping.copy_link": "Link kopieren",
    "shopping.no_items": "Keine Artikel auf der Liste.",
    "shopping.checked": "Erledigt",
    "shopping.move_to_list": "Zur Einkaufsliste verschieben",
    # General Items
    "items.title": "Allgemeine Artikel",
    "items.add": "Artikel hinzufügen",
    "items.name": "Artikelname",
    "items.amount": "Menge",
    "items.category": "Kategorie",
    # Inventory
    "inventory.title": "Inventar",
    "inventory.bought": "Gekauft",
    "inventory.used": "Verwendet",
    "inventory.balance": "Saldo",
    "inventory.required": "Benötigt",
    # Categories
    "category.produce": "Gemüse / Obst",
    "category.meat": "Fleisch / Geflügel / Fisch",
    "category.dairy": "Milchprodukte / Kühlregal",
    "category.pantry": "Vorrat / Trockenwaren",
    "category.spices": "Gewürze / Saucen",
    "category.bread": "Bäckerei / Brot",
    "category.drinks": "Getränke",
    "category.frozen": "Tiefkühl",
    "category.non_food": "Non-Food / Allgemein",
    "category.other": "Sonstiges",
    # Collaborators
    "collab.title": "Mitarbeiter verwalten",
    "collab.invite": "Benutzer einladen",
    "collab.username_placeholder": "Benutzername eingeben",
    "collab.invite_btn": "Einladen",
    "collab.remove": "Entfernen",
    "collab.owner": "Besitzer",
    # Edit Meal Modal
    "edit_meal.title": "Mahlzeit bearbeiten",
    "edit_meal.people_count": "Personenzahl",
    "edit_meal.use_default": "Lager-Standard verwenden",
    "edit_meal.mark_done": "Als gekocht markieren",
    "edit_meal.leftovers": "Reste",
    # Misc
    "misc.people": "Personen",
    "misc.no_data": "Keine Daten verfügbar.",
    "misc.error": "Ein Fehler ist aufgetreten.",
    "misc.success": "Erfolgreich!",
    "misc.confirm_delete": "Bist du sicher, dass du das löschen möchtest?",
    "misc.language": "Sprache",
}


class Command(BaseCommand):
    help = "Load default German UI texts into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing text_de values",
        )

    def handle(self, *args, **options):
        overwrite = options["overwrite"]
        created_count = 0
        updated_count = 0

        for key, text_de in DEFAULT_TEXTS.items():
            obj, created = UIText.objects.get_or_create(
                key=key,
                defaults={"text_de": text_de},
            )
            if created:
                created_count += 1
            elif overwrite:
                obj.text_de = text_de
                obj.save()
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {created_count} created, {updated_count} updated, "
                f"{len(DEFAULT_TEXTS) - created_count - updated_count} skipped."
            )
        )
