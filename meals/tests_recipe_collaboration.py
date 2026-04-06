import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from meals.models import Recipe

User = get_user_model()


class RecipeCollaborationTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password")
        self.collaborator = User.objects.create_user(
            username="collab", password="password"
        )
        self.stranger = User.objects.create_user(
            username="stranger", password="password"
        )

        self.recipe = Recipe.objects.create(
            name="Test Recipe",
            owner=self.owner,
            description="A test recipe",
            instructions="Cook it",
        )
        self.recipe.collaborators.add(self.collaborator)
        self.client = Client()

    def test_everyone_can_view(self):
        # Stranger can view
        self.client.force_login(self.stranger)
        response = self.client.get(f"/api/meals/recipes/{self.recipe.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Test Recipe")

    def test_owner_can_edit(self):
        self.client.force_login(self.owner)
        response = self.client.put(
            f"/api/meals/recipes/{self.recipe.id}",
            data=json.dumps({"name": "Updated by Owner"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.name, "Updated by Owner")

    def test_collaborator_can_edit(self):
        self.client.force_login(self.collaborator)
        response = self.client.put(
            f"/api/meals/recipes/{self.recipe.id}",
            data=json.dumps({"name": "Updated by Collab"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.name, "Updated by Collab")

    def test_stranger_cannot_edit(self):
        self.client.force_login(self.stranger)
        response = self.client.put(
            f"/api/meals/recipes/{self.recipe.id}",
            data=json.dumps({"name": "Hacked"}),
            content_type="application/json",
        )
        # Ninja might return 402 or 500 if PermissionError is raised and not handled by an exception handler
        # But usually in tests we want to see it catch it.
        # Actually default Ninja behavior for unhandled exception is 500, but let's see.
        self.assertNotEqual(response.status_code, 200)
        self.recipe.refresh_from_db()
        self.assertNotEqual(self.recipe.name, "Hacked")

    def test_invite_collaborator(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            f"/api/meals/recipes/{self.recipe.id}/collaborators",
            data=json.dumps({"username": "stranger"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("stranger", response.json()["collaborators"])

    def test_collaborator_cannot_invite(self):
        self.client.force_login(self.collaborator)
        response = self.client.post(
            f"/api/meals/recipes/{self.recipe.id}/collaborators",
            data=json.dumps({"username": "stranger"}),
            content_type="application/json",
        )
        self.assertEqual(
            response.status_code, 404
        )  # get_object_or_404(Recipe, ..., owner=request.user)

    def test_collaborator_can_remove_self(self):
        self.client.force_login(self.collaborator)
        response = self.client.delete(
            f"/api/meals/recipes/{self.recipe.id}/collaborators/collab"
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.recipe.collaborators.filter(username="collab").exists())
