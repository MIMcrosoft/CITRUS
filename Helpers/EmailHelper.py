from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from CitrusApp.NOTPUBLIC import EMAIL_PSWD, TEMP_PSWD
from pathlib import Path
from django.conf import settings
from premailer import transform
import smtplib

from CitrusApp.models import Coach


class EmailTemplate(Enum):
    INVITATION = "../CitrusApp/templates/templatesCourriel/email_invitation_coach.html"
    RESETPASSWORD = "../CitrusApp/templates/templatesCourriel/email_reinitialisation.html"
    VALIDATION = "../CitrusApp/templates/templatesCourriel/email_validation_mdp.html"
    REPORTMATCH = "../CitrusApp/templates/templatesCourriel/email_report_match.html"

class EmailHelper:
    def __init__(self):
        self.smtpServer = 'node38-ca.n0c.com'
        self.smtpPort = 465
        self.senderEmail = 'citrus@liguedespamplemousses.com'
        self.password = EMAIL_PSWD
        self.domaine = "http://localhost:8000" if settings.DEBUG else "https://citrus.liguedespamplemousses.com"
        self.baseDirectory = Path(__file__).parent

    def envoieCourriel(self,listReceveurCourriel,sujet,body):

        for receveurCourriel in listReceveurCourriel:
            courriel = MIMEMultipart("alternative")
            courriel["From"] = self.senderEmail
            courriel["To"] = receveurCourriel
            courriel["subject"] = sujet
            courriel.attach(MIMEText(body,'html'))

            try:
                with smtplib.SMTP_SSL(self.smtpServer, self.smtpPort) as server:
                    server.login(self.senderEmail, self.password)
                    server.sendmail(self.senderEmail, receveurCourriel, courriel.as_string())
                print('Le courriel à été envoyé avec succès')
            except Exception as e:
                print(f"Le courriel n'a pas été envoyé : {e}")

    def courrielInvitation(self,courrielCoach):
        receveurs = []
        receveurs.append(courrielCoach)

        coachTemp = Coach.createCoach("tempCoach","tempCoach",courrielCoach,TEMP_PSWD)
        urlSignIn = f"{self.domaine}/Citrus/CoachSignIn/{coachTemp.coach_id}"

        with open(EmailTemplate.INVITATION.value, 'r',encoding="utf-8") as file:
            htmlBody = file.read()
        htmlBodyParam = htmlBody.replace("urlSignIn",urlSignIn)
        htmlBodyParamStyle = transform(htmlBodyParam)

        sujet = "Invitation à la plateforme CITRUS"

        self.envoieCourriel(receveurs, sujet, htmlBodyParamStyle)

    def courrielResetPwd(self,courrielCoach):
        receveurs = []
        receveurs.append(courrielCoach)

        urlResetPwd = f"{self.domaine}/Citrus/ResetPassword/{hash}"

        with open(EmailTemplate.RESETPASSWORD.value, 'r',encoding="utf-8") as file:
            htmlBody = file.read()
        htmlBodyParam = htmlBody.replace("{urlResetPassword}",urlResetPwd)
        htmlBodyParamStyle = transform(htmlBodyParam)

        sujet = "Réinitialisation de ton mot de passe CITRUS"

        self.envoieCourriel(receveurs, sujet, htmlBodyParamStyle)

    def courrielValidation(self, courrielCoach):
        receveurs = []
        receveurs.append(courrielCoach)

        urlValidation = f"{self.domaine}/Citrus/Validation/{hash}"

        with open(EmailTemplate.VALIDATION.value, 'r',encoding="utf-8") as file:
            htmlBody = file.read()
        htmlBodyParam = htmlBody.replace("{urlValidation}",urlValidation)
        htmlBodyParamStyle = transform(htmlBodyParam)

        sujet = "Votre compte CITRUS a été accepté par l'organisation"

        self.envoieCourriel(receveurs, sujet, htmlBodyParamStyle)

    def courrielReportMatch(self, courrielCoachEq1, courrielCoachEq2, courrielAdmin):
        receveurs = []
        receveurs.append(courrielCoachEq1)
        receveurs.append(courrielCoachEq2)
        receveurs.append(courrielAdmin)

        urlReportMatch = f"{self.domaine}/Citrus/Report/{hash}"

        with open(EmailTemplate.REPORTMATCH.value, 'r',encoding="utf-8") as file:
            htmlBody = file.read()
        htmlBodyParam = htmlBody.replace("{urlValidation}", urlReportMatch)
        htmlBodyParamStyle = transform(htmlBodyParam)

        sujet = "Demande de report de match"
        self.envoieCourriel(receveurs, sujet, htmlBodyParamStyle)