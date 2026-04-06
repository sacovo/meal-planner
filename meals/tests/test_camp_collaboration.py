import datetime
import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

from meals.models import Camp

User = get_user_model()


class CampCollaborationTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password")
        self.collaborator = User.objects.create_user(
            username="collab", password="password"
        )
        self.stranger = User.objects.create_user(
            username="stranger", password="password"
        )

        self.camp = Camp.objects.create(
            name="Test Camp",
            owner=self.owner,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + datetime.timedelta(days=5),
        )
        self.camp.collaborators.add(self.collaborator)
        self.client = Client()

    def test_owner_access(self):
        self.client.force_login(self.owner)
        response = self.client.get(f"/api/meals/camps/{self.camp.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Test Camp")

    def test_collaborator_access(self):
        self.client.force_login(self.collaborator)
        response = self.client.get(f"/api/meals/camps/{self.camp.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Test Camp")

    def test_stranger_no_access(self):
        self.client.force_login(self.stranger)
        response = self.client.get(f"/api/meals/camps/{self.camp.id}")
        self.assertEqual(response.status_code, 404)

    def test_invite_collaborator(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            f"/api/meals/camps/{self.camp.id}/collaborators",
            data=json.dumps({"username": "stranger"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("stranger", response.json()["collaborators"])

    def test_collaborator_cannot_invite(self):
        self.client.force_login(self.collaborator)
        response = self.client.post(
            f"/api/meals/camps/{self.camp.id}/collaborators",
            data=json.dumps({"username": "stranger"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_collaborator_can_remove_self(self):
        self.client.force_login(self.collaborator)
        response = self.client.delete(
            f"/api/meals/camps/{self.camp.id}/collaborators/collab"
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.camp.collaborators.filter(username="collab").exists())
