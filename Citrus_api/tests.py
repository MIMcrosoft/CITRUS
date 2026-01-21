from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch
from unittest.mock import ANY

from rest_framework.test import APITestCase
from datetime import datetime

from CitrusApp.models import Match, Alignement, RequeteReportMatch, Coach, Saison, Equipe
from Helpers.EmailHelper import EmailHelper


# Test de l'API

# Test du classement
class ClassementTest(TestCase):
    pass

class CreerRequeteReportMatchTest(APITestCase):

    def setUp(self):
        # On initialise les mock users
        self.coach1 = Coach.objects.create_user(
            prenom_coach="Claude",
            nom_coach="Legault",
            pronom_coach="Il/Lui",
            courriel="felixrobillardWork@gmail.com",
            password="Pwd1234"
        )

        self.coach2 = Coach.objects.create_user(
            prenom_coach="Claudelle",
            nom_coach="LaGoat",
            pronom_coach="Elle",
            courriel="felixrobillard@gmail.com",
            password="Pwd1234"
        )

        #Mock saison et mock équipes
        self.saison = Saison.objects.create(nom_saison='test', est_active=False)
        self.equipe1 = Equipe.objects.create(nom_equipe='test_1', coach=self.coach1)
        self.equipe2 = Equipe.objects.create(nom_equipe='test_2', coach=self.coach2)

        #Mock Match
        self.match = Match.objects.create(
            match_id= 9999,
            equipe1=self.equipe1,
            equipe2=self.equipe2,
            saison=self.saison
        )

        #Mock Alignements
        Alignement.objects.create(
            equipe=self.equipe1,
            saison=self.saison,
            coach= self.coach1
        )

        Alignement.objects.create(
            equipe=self.equipe2,
            saison=self.saison,
            coach=self.coach2
        )

        self.url = reverse("creerRequeteReportMatch")

    def test_auth(self):
        response = self.client.post(self.url,{},format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_params(self):
        self.client.force_login(user=self.coach1)

        response = self.client.post(self.url,{},format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error",response.data)

    def test_invalid_date_format(self):
        self.client.force_login(user=self.coach1)

        response = self.client.post(self.url,{
            "match_id": self.match.match_id,
            "nouvelle_date" : "date_invalide"
        },format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("CitrusApp.views.EmailHelper.courrielCreationReportMatch")
    def test_succes_creation_coach1(self, mock_courriel):
        self.client.force_login(user=self.coach1)

        payload = {
            "match_id": self.match.match_id,
            "nouvelle_date": "2025-11-21"
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])

        rr = RequeteReportMatch.objects.first()
        self.assertIsNotNone(rr)

        mock_courriel.assert_called_once_with(
            self.coach1.courriel,
            self.coach2.courriel,
            EmailHelper.COURRIEL_ADMIN,
            rr
        )

    @patch("CitrusApp.views.EmailHelper.envoieCourriel")
    def test_email_report_contenu(self, mock_send):
        self.client.force_login(user=self.coach1)

        payload = {
            "match_id": self.match.match_id,
            "nouvelle_date": "2025-11-21"
        }

        self.client.post(self.url, payload, format="json")
        mock_send.assert_called_once()
        receveurs, sujet, html = mock_send.call_args[0]

        self.assertIn(self.coach1.courriel, receveurs)
        self.assertIn(self.coach2.courriel, receveurs)

        self.assertIn(sujet, "Demande de report de match")
        self.assertIn("Demande de report", html)
        self.assertIn("2025-11-21", html)
