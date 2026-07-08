import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from meals.models import Recipe

User = get_user_model()


class RecipeImportTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password")
        self.stranger = User.objects.create_user(
            username="stranger", password="password"
        )
        self.recipe = Recipe.objects.create(
            name="Existing Recipe",
            owner=self.owner,
            description="Old description",
            instructions="Old instructions",
        )
        self.client = Client()

    @patch("meals.api.recipes.import_recipe_ai_task.delay")
    def test_import_existing_recipe_owner(self, mock_delay):
        self.client.force_login(self.owner)
        response = self.client.post(
            f"/api/meals/recipes/{self.recipe.id}/import",
            data=json.dumps({"raw_text": "New recipe text"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.recipe.refresh_from_db()
        self.assertTrue(self.recipe.is_importing)
        mock_delay.assert_called_once_with(
            self.recipe.id, "New recipe text", override_existing=True
        )

    @patch("meals.api.recipes.import_recipe_ai_task.delay")
    def test_import_existing_recipe_stranger_forbidden(self, mock_delay):
        self.client.force_login(self.stranger)
        response = self.client.post(
            f"/api/meals/recipes/{self.recipe.id}/import",
            data=json.dumps({"raw_text": "New recipe text"}),
            content_type="application/json",
        )
        self.assertNotEqual(response.status_code, 200)
        mock_delay.assert_not_called()
