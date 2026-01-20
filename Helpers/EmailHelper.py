import hashlib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from CitrusApp.NOTPUBLIC import EMAIL_PSWD, TEMP_PSWD
from pathlib import Path
from django.conf import settings
from premailer import transform
import smtplib

from CitrusApp.models import Coach, hash_code, RequeteReportMatch



class EmailTemplate(Enum):
    INVITATION = "email_invitation_coach.html"
    REINIT_MDP = "email_reinitialisation_mdp.html"
    VALIDATION = "email_validation_inscription.html"
    REPORT_MATCH = "email_report_match.html"
    CONFIRMATION = "email_confirmation_inscription.html"
    RESUME = "email_resume_match.html"
    REPORT_MATCH_UPDATE = "email_report_match_update.html"
    REPORT_MATCH_ACCEPTEE = "email_report_match_accepte.html"


class EmailHelper:
    COURRIEL_ADMIN = "citrus@liguedespamplemousses.com"
    COURRIEL_RESPO_COM = "citrus@liguedespamplemousses.com"
    def __init__(self):
        self.smtpServer = 'node38-ca.n0c.com'
        self.smtpPort = 465
        self.senderEmail = 'citrus@liguedespamplemousses.com'
        self.password = EMAIL_PSWD
        self.domaine = "http://localhost:8000" if settings.DEBUG else "https://citrus.liguedespamplemousses.com"
        self.baseDirectory = Path(__file__).parent
        self.templateFolder = self.baseDirectory.parent / "CitrusApp" / "templates" / "templatesCourriel"

    def hash_code(code: str) -> str:
        # Create a SHA-256 hash object
        hash_object = hashlib.sha256()

        # Encode the string and update the hash object
        hash_object.update(code.encode('utf-8'))

        # Get the hexadecimal representation of the hash
        hash_hex = hash_object.hexdigest()

        return hash_hex

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

    def courrielConfirmationInscription(self, courrielCoach):
        receveurs = []
        receveurs.append(courrielCoach)

        template_path = self.templateFolder / EmailTemplate.CONFIRMATION.value
        with open(template_path, 'r', encoding="utf-8") as file:
            htmlBody = file.read()
        htmlBodyParam = htmlBody.replace("{currentYear}", datetime.today().strftime("%Y"))
        htmlBodyParamStyle = transform(htmlBodyParam)

        sujet = "Votre compte CITRUS est en attente de validation"

        self.envoieCourriel(receveurs, sujet, htmlBodyParamStyle)

    def courrielInvitation(self,courrielCoach):
        receveurs = []
        receveurs.append(courrielCoach)

        coachTemp = Coach.createCoach("tempCoach","tempCoach",courrielCoach,TEMP_PSWD)
        urlSignIn = f"{self.domaine}/Citrus/Inscription"

        template_path = self.templateFolder / EmailTemplate.VALIDATION.value
        with open(template_path, 'r',encoding="utf-8") as file:
            htmlBody = file.read()
        htmlBodyParam = htmlBody.replace("{urlSignIn}",urlSignIn)
        htmlBodyParam = htmlBodyParam.replace("{currentYear}", datetime.today().strftime("%Y"))
        htmlBodyParamStyle = transform(htmlBodyParam)

        sujet = "Invitation à la plateforme CITRUS"

        self.envoieCourriel(receveurs, sujet, htmlBodyParamStyle)

    def courrielResetPwd(self,courrielCoach,code):
        receveurs = []
        receveurs.append(courrielCoach)
        urlResetPwd = f"{self.domaine}/Citrus/reinitialisationMdp-{hash_code(code)}"

        template_path = self.templateFolder / EmailTemplate.REINIT_MDP.value
        with open(template_path, 'r',encoding="utf-8") as file:
            htmlBody = file.read()
        htmlBodyParam = htmlBody.replace("{urlResetPassword}",urlResetPwd)
        htmlBodyParam = htmlBodyParam.replace("{currentYear}", datetime.today().strftime("%Y"))
        htmlBodyParamStyle = transform(htmlBodyParam)

        sujet = "Réinitialisation de ton mot de passe CITRUS"

        self.envoieCourriel(receveurs, sujet, htmlBodyParamStyle)

    def courrielValidation(self, courrielCoach):
        receveurs = []
        receveurs.append(courrielCoach)

        urlConnexion = f"{self.domaine}/Citrus/Connexion"

        template_path = self.templateFolder / EmailTemplate.VALIDATION.value

        with open(template_path, 'r',encoding="utf-8") as file:
            htmlBody = file.read()
        htmlBodyParam = htmlBody.replace("{urlConnexion}",urlConnexion)
        htmlBodyParamStyle = transform(htmlBodyParam)

        sujet = "Votre compte CITRUS a été accepté par l'organisation"

        self.envoieCourriel(receveurs, sujet, htmlBodyParamStyle)

    def courrielCreationReportMatch(self, courrielCoachEq1, courrielCoachEq2, courrielAdmin, rr:RequeteReportMatch):
        receveurs = []
        receveurs.append(courrielCoachEq1)
        receveurs.append(courrielCoachEq2)
        receveurs.append(courrielAdmin)

        coach1 = Coach.objects.get(courriel=courrielCoachEq1) if courrielCoachEq1 else None
        coach2 = Coach.objects.get(courriel=courrielCoachEq2) if courrielCoachEq2 else None

        coach1Statut = "ACCEPTÉE" if rr.coach1_validation else "EN ATTENTE"
        coach2Statut = "ACCEPTÉE" if rr.coach2_validation else "EN ATTENTE"
        adminStatut = "ACCEPTÉE" if rr.admin_validation else "EN ATTENTE"

        urlReportMatch = f"{self.domaine}/Citrus/Report_Match-{rr.token}"
        template_path = self.templateFolder / EmailTemplate.REPORT_MATCH.value
        with open(template_path, 'r', encoding="utf-8") as file:
            htmlBody = file.read()

        htmlBodyParam = htmlBody.replace("{urlRequeteReport}", urlReportMatch)
        htmlBodyParam = htmlBodyParam.replace("{currentYear}", datetime.today().strftime("%Y"))
        htmlBodyParam = htmlBodyParam.replace("{matchEq1}", str(rr.match.equipe1.nom_equipe))
        htmlBodyParam = htmlBodyParam.replace("{matchEq2}", str(rr.match.equipe2.nom_equipe))
        htmlBodyParam = htmlBodyParam.replace("{ancienneDateMatch}", str(rr.match.get_dateFormatted()))
        htmlBodyParam = htmlBodyParam.replace("{nouvelleDateMatch}", str(rr.nouvelle_date))
        htmlBodyParam = htmlBodyParam.replace("{collegeRec}", str(rr.match.equipe1.college.nom_college))

        htmlBodyParam = htmlBodyParam.replace("{coachEq1}", f"{coach1.prenom_coach} {coach1.nom_coach}" if coach1 else "")
        htmlBodyParam = htmlBodyParam.replace("{coachEq1Courriel}", str(courrielCoachEq1) if courrielCoachEq1 else "")
        htmlBodyParam = htmlBodyParam.replace("{coachEq1Statut}", coach1Statut)

        htmlBodyParam = htmlBodyParam.replace("{coachEq2}", f"{coach2.prenom_coach} {coach2.nom_coach}" if coach2 else "")
        htmlBodyParam = htmlBodyParam.replace("{coachEq2Courriel}", str(courrielCoachEq2) if courrielCoachEq2 else "")
        htmlBodyParam = htmlBodyParam.replace("{coachEq2Statut}", coach2Statut)

        htmlBodyParam = htmlBodyParam.replace("{admin}", "Statisticien")
        htmlBodyParam = htmlBodyParam.replace("{adminCourriel}", courrielAdmin)
        htmlBodyParam = htmlBodyParam.replace("{adminCourrielStatut}", adminStatut)

        htmlBodyParamStyle = transform(htmlBodyParam)

        sujet = "Demande de report de match"
        self.envoieCourriel(receveurs, sujet, htmlBodyParamStyle)

    def courrielUpdateReportMatch(self, courrielCoachEq1, courrielCoachEq2, courrielAdmin, rr:RequeteReportMatch):
        receveurs = []
        receveurs.append(courrielCoachEq1)
        receveurs.append(courrielCoachEq2)
        receveurs.append(courrielAdmin)

        coach1Statut = "ACCEPTÉE" if rr.coach1_validation else "EN ATTENTE"
        coach2Statut = "ACCEPTÉE" if rr.coach2_validation else "EN ATTENTE"
        adminStatut = "ACCEPTÉE" if rr.admin_validation else "EN ATTENTE"

        urlReportMatch = f"{self.domaine}/Citrus/Report_Match-{rr.token}"
        template_path = self.templateFolder / EmailTemplate.REPORT_MATCH.value
        with open(template_path, 'r', encoding="utf-8") as file:
            htmlBody = file.read()

        htmlBodyParam = htmlBody.replace("{urlRequeteReport}", urlReportMatch)
        htmlBodyParam = htmlBodyParam.replace("{currentYear}", datetime.today().strftime("%Y"))
        htmlBodyParam = htmlBodyParam.replace("{matchEq1}", str(rr.match.equipe1.nom_equipe))
        htmlBodyParam = htmlBodyParam.replace("{matchEq2}", str(rr.match.equipe2.nom_equipe))
        htmlBodyParam = htmlBodyParam.replace("{ancienneDateMatch}", str(rr.match.get_dateFormatted()))
        htmlBodyParam = htmlBodyParam.replace("{nouvelleDateMatch}", str(rr.nouvelle_date))
        htmlBodyParam = htmlBodyParam.replace("{collegeRec}", str(rr.match.equipe1.college.nom_college))

        htmlBodyParam = htmlBodyParam.replace("{coachEq1}", f"{rr.coach_1.prenom_coach} {rr.coach_1.nom_coach}")
        htmlBodyParam = htmlBodyParam.replace("{coachEq1Courriel}", str(courrielCoachEq1))
        htmlBodyParam = htmlBodyParam.replace("{coachEq1Statut}", coach1Statut)

        htmlBodyParam = htmlBodyParam.replace("{coachEq2}", f"{rr.coach_2.prenom_coach} {rr.coach_2.nom_coach}")
        htmlBodyParam = htmlBodyParam.replace("{coachEq2Courriel}", str(courrielCoachEq2))
        htmlBodyParam = htmlBodyParam.replace("{coachEq2Statut}", coach2Statut)

        htmlBodyParam = htmlBodyParam.replace("{admin}", "Statisticien")
        htmlBodyParam = htmlBodyParam.replace("{adminCourriel}", courrielAdmin)
        htmlBodyParam = htmlBodyParam.replace("{adminCourrielStatut}", adminStatut)


        htmlBodyParamStyle = transform(htmlBodyParam)

        sujet = "Mise à jour sur une demande de report de match"
        self.envoieCourriel(receveurs, sujet, htmlBodyParamStyle)

    def courrielReportMatchAccepte(self, courrielCoachEq1, courrielCoachEq2, courrielAdmin, courrielRespoCom, rr:RequeteReportMatch):
        receveurs = []
        receveurs.append(courrielCoachEq1)
        receveurs.append(courrielCoachEq2)
        receveurs.append(courrielAdmin)
        receveurs.append(courrielRespoCom)

        template_path = self.templateFolder / EmailTemplate.REPORT_MATCH_ACCEPTEE.value
        with open(template_path, 'r', encoding="utf-8") as file:
            htmlBody = file.read()

        htmlBodyParam = htmlBody.replace("{currentYear}", datetime.today().strftime("%Y"))
        htmlBodyParam = htmlBodyParam.replace("{matchEq1}", str(rr.match.equipe1.nom_equipe))
        htmlBodyParam = htmlBodyParam.replace("{matchEq2}", str(rr.match.equipe2.nom_equipe))
        htmlBodyParam = htmlBodyParam.replace("{nouvelleDateMatch}", str(rr.match.get_dateFormatted()))
        htmlBodyParam = htmlBodyParam.replace("{collegeRec}", str(rr.match.equipe1.college.nom_college))


        htmlBodyParamStyle = transform(htmlBodyParam)

        sujet = "Votre demande de report de match à été acceptée"
        self.envoieCourriel(receveurs, sujet, htmlBodyParamStyle)

    def courrielRappelSignature(self, courrielCoach):
        pass

    def courrielResumeMatch(self, courrielCoachEq1, courrielCoachEq2, match):
        receveurs = []
        if courrielCoachEq1:
            receveurs.append(courrielCoachEq1)
        if courrielCoachEq2:
            receveurs.append(courrielCoachEq2)

        urlConnexion = f"{self.domaine}/Citrus/Connexion"
        template_path = self.templateFolder / EmailTemplate.RESUME.value
        with open(template_path, 'r',encoding="utf-8") as file:
            htmlBody = file.read()

        htmlBodyParam = htmlBody.replace("{urlConnexion}", urlConnexion)
        htmlBodyParam = htmlBodyParam.replace("{dateMatch}", match.get_dateFormattedWithYear())
        htmlBodyParam = htmlBodyParam.replace("{collegeRec}", match.equipe1.college.nom_college)
        htmlBodyParam = htmlBodyParam.replace("{equipeVis}", match.equipe2.nom_equipe)
        htmlBodyParam = htmlBodyParam.replace("{equipeVisCollege}", match.equipe2.college.nom_college)
        htmlBodyParam = htmlBodyParam.replace("{scoreVis}", match.score_eq2)
        htmlBodyParam = htmlBodyParam.replace("{equipeHote}", match.equipe1.nom_equipe)
        htmlBodyParam = htmlBodyParam.replace("{equipeHoteCollege}", match.equipe1.college.nom_college)
        htmlBodyParam = htmlBodyParam.replace("{scoreHote}", match.score_eq1)
        htmlBodyParam = htmlBodyParam.replace("{currentYear}", datetime.today().strftime("%Y"))

        htmlBodyParamStyle = transform(htmlBodyParam)

        sujet = "Résumé de match"
        self.envoieCourriel(receveurs, sujet, htmlBodyParamStyle)