from django.db import models, IntegrityError
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from googlemaps import geocoding, Client
import segno
from .NOTPUBLIC import API_KEY
from datetime import datetime, timedelta
from io import BytesIO
import base64
import hashlib
from django.conf import settings
import networkx as nx
from math import sqrt
import matplotlib.pyplot as plt
import pulp
import xlwings as xw

def hash_code(code: str) -> str:
    # Create a SHA-256 hash object
    hash_object = hashlib.sha256()

    # Encode the string and update the hash object
    hash_object.update(code.encode('utf-8'))

    # Get the hexadecimal representation of the hash
    hash_hex = hash_object.hexdigest()

    return hash_hex


DIVISION_CHOICES = [
    ("Pamplemousse", "Pamplemousse"),
    ("Tangerine", "Tangerine"),
    ("Clementine", "Clementine")
]

SESSION_CHOICES = [
    ("Automne", "Automne"),
    ("Hiver", "Hiver")
]


class Saison(models.Model):
    saison_id = models.AutoField(primary_key=True)
    nom_saison = models.CharField(max_length=255)
    est_active = models.BooleanField(default=False)

    calendrier_officiel = models.ForeignKey('Calendrier', on_delete=models.CASCADE, null=True)

    @classmethod
    def createSaison(cls, nom_saison):
        saison = cls(
            nom_saison=nom_saison
        )
        saison.save()
        for equipe in Equipe.objects.all():
            newAlignement = Alignement.create_alignement(equipe, saison)
            newAlignement.save()

        return saison

    def set_active(self):
        if self.est_active == False:
            for saison in Saison.objects.all():
                saison.est_active = False
            self.est_active = True

    def __str__(self):
        return self.nom_saison

class Session(models.Model):
    session_id = models.AutoField(primary_key=True)
    nom_session = models.CharField(max_length=50)
    type = models.CharField(max_length=25, choices=SESSION_CHOICES)
    nb_semaine = models.IntegerField(default=10)

    saison = models.ForeignKey(Saison, on_delete=models.CASCADE, null=True)
    calendrier = models.ForeignKey('Calendrier', related_name='sessions', on_delete=models.CASCADE, null=True)

    @classmethod
    def createSession(cls, nom_session, type, nb_semaine=10, calendrier_id=None):
        session = cls(
            nom_session=nom_session,
            type=type,
            nb_semaine=nb_semaine,
            calendrier_id=calendrier_id
        )
        session.save()
        return session

    def __str__(self):
        return self.calendrier_id.__str__() + " - " + self.nom_session

class Serie(models.Model):
    serie_id = models.AutoField(primary_key=True)
    division = models.CharField(max_length=50, choices=DIVISION_CHOICES)

    saison = models.ForeignKey(Saison, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.saison.nom_saison + "-SERIE-" + str(self.division)

class Calendrier(models.Model):
    calendrier_id = models.AutoField(primary_key=True)
    nom_calendrier = models.CharField(max_length=50)
    nb_match = models.IntegerField(default=0)

    @classmethod
    def createCalendrier(cls, annee, dateDepartAut, dateDepartHiv, version, nbSemaineAut, nbSemaineHiv):
        calendrier = cls(
            nom_calendrier=annee + "_V" + version
        )
        calendrier.save()

        sessionAut = Session.createSession("AUT", "Automne", nbSemaineAut, calendrier.calendrier_id)
        sessionHiv = Session.createSession("HIV", "Hiver", nbSemaineHiv, calendrier.calendrier_id)

        def next_wednesday(current_date):
            # Calculate how many days to add to reach the next Wednesday
            days_ahead = 2 - current_date.weekday()  # Wednesday is 2 (Monday is 0)
            if days_ahead <= 0:  # Target day already passed this week
                days_ahead += 7
            return current_date + timedelta(days=days_ahead)

        # Example usage
        dateAut = datetime.strptime(dateDepartAut, '%Y-%m-%d').date()
        dateHiv = datetime.strptime(dateDepartHiv, '%Y-%m-%d').date()

        # Loop for the autumn session
        for i in range(nbSemaineAut):
            semaine = Semaine.createSemaine(session_id=sessionAut.session_id, date=dateAut)
            dateAut = next_wednesday(dateAut)

        # Loop for the winter session
        for i in range(nbSemaineHiv):
            semaine = Semaine.createSemaine(session_id=sessionHiv.session_id, date=dateHiv)
            dateHiv = next_wednesday(dateHiv)

        calendrier.remplirCalendrier(datetime.strptime(dateDepartAut, '%Y-%m-%d').date(), datetime.strptime(dateDepartHiv, '%Y-%m-%d').date())

        return calendrier

    def remplirCalendrier(self, startAut, startHiver):
        def creationMatchs(division):
            # 1️⃣ Récupération des équipes de la division
            equipes = list(
                Equipe.objects.filter(division=division,est_active=True)
                .exclude(nom_equipe="EQUIPE TEST")
            )

            # 2️⃣ Réinitialisation des compteurs
            for equipe in equipes:
                equipe.nb_matchVis = 0
                equipe.nb_matchHost = 0
                equipe.save()

            # 3️⃣ Création du graphe complet
            G = nx.DiGraph()
            G.add_nodes_from(equipes)

            # 4️⃣ Fonction distance
            def calcul_distance(e1, e2):
                c1, c2 = e1.college, e2.college
                return sqrt((c1.locationX - c2.locationX) ** 2 + (c1.locationY - c2.locationY) ** 2)

            for ev in equipes:
                for er in equipes:
                    if ev == er:
                        continue
                    dist = calcul_distance(ev, er)
                    if dist <= 0:
                        dist = 1e6  # Large weight for same-college matches
                    G.add_edge(ev, er, weight=dist)

            nodes = list(G.nodes)
            edges = list(G.edges)
            weights = nx.get_edge_attributes(G, 'weight')

            # 5️⃣ Définir le problème ILP
            prob = pulp.LpProblem("DegreeConstrainedMinWeight", pulp.LpMinimize)
            x = pulp.LpVariable.dicts("x", edges, cat="Binary")
            prob += pulp.lpSum([weights[e] * x[e] for e in edges])

            # Contraintes de degré
            for i in nodes:
                prob += pulp.lpSum([x[(i, j)] for j in nodes if j != i]) == 4  # out-degree = 4
            for j in nodes:
                prob += pulp.lpSum([x[(i, j)] for i in nodes if i != j]) == 4  # in-degree = 4

            # Pas de double match entre deux équipes
            for i in nodes:
                for j in nodes:
                    if i == j:
                        continue
                    prob += x[(i, j)] + x[(j, i)] <= 1

            # Chaque équipe ne joue qu'une seule fois contre chaque college
            college_teams = {}
            for e in equipes:
                college_teams.setdefault(e.college, []).append(e)

            for team in nodes:
                for college, teams_in_college in college_teams.items():
                    if team.college == college:
                        continue
                    # Contrainte : au plus un match contre ce collège (visiteur OU receveur)
                    prob += pulp.lpSum([
                        x[(team, opp)] + x[(opp, team)]
                        for opp in teams_in_college
                        if (team, opp) in x and (opp, team) in x
                    ]) <= 1

            # 6️⃣ Résoudre
            prob.solve()

            # 7️⃣ Extraire les arêtes sélectionnées
            selected_edges = [(i, j) for (i, j) in edges if x[(i, j)].varValue == 1]

            # 8️⃣ Créer un sous-graphe pour la visualisation
            H = nx.DiGraph()
            H.add_nodes_from(G.nodes)
            H.add_edges_from(selected_edges)

            # 9️⃣ Créer des labels pour les équipes
            labels = {e: e.nom_equipe for e in H.nodes}

            # 🔟 Dessiner le graphe
            pos = nx.spring_layout(H, seed=42)
            nx.draw(H, pos, with_labels=True, labels=labels, node_color='lightblue', node_size=800, font_size=10)
            edge_labels = {(i, j): f"{G[i][j]['weight']:.1f}" for i, j in H.edges}
            nx.draw_networkx_edge_labels(H, pos, edge_labels=edge_labels)

            plt.show()
            matchs = []
            # 1️⃣1️⃣ Afficher les matchs
            for match in selected_edges:
                equipe1, equipe2 = match
                match = Match.createMatch(
                    session=None,
                    serie=None,
                    equipe1=equipe1,
                    equipe2=equipe2,
                    semaine=None,
                    division=division
                )
                matchs.append(match)

            print(f"Division {division} → {len(matchs)} matchs créés")
            for match in matchs:
                print(f"MATCH : {match.equipe2} vs {match.equipe1}")
            return matchs

        def placerMatchs(matchs, automne_start, hiver_start):
            """
            matchs: list of Match objects
            automne_start: datetime.date for week 1
            hiver_start: datetime.date for week 11
            """
            print("PLACEMENT DES MATCHS")
            # --- Input ---
            matches = list(matchs)  # ensure list

            # --- Indexing derived from MATCHES (critical!) ---
            match_ids = [int(m.match_id) for m in matches]
            host_team = {int(m.match_id): int(m.equipe1.id_equipe) for m in matches}
            visitor_team = {int(m.match_id): int(m.equipe2.id_equipe) for m in matches}
            host_college = {int(m.match_id): int(m.equipe1.college.college_id) for m in matches}

            # every team that appears in the matches gets constraints
            team_ids = sorted({host_team[m] for m in match_ids} | {visitor_team[m] for m in match_ids})
            # only colleges that actually host at least one match need a hosting constraint
            college_ids = sorted({host_college[m] for m in match_ids})

            # --- Weeks (20 = 10 autumn + 10 winter) ---
            weeks = list(range(1, 21))

            # --- Map weeks -> actual dates ---
            week_dates = {}
            for i in range(10):  # weeks 1–10
                week_dates[i + 1] = automne_start + timedelta(weeks=i)
            for i in range(10):  # weeks 11–20
                week_dates[i + 11] = hiver_start + timedelta(weeks=i)

            print(week_dates)
            # --- Build unavailable weeks per team and college ---
            team_unavail = {}
            college_unavail = {}

            for t in Equipe.objects.filter(id_equipe__in=team_ids):
                dates = set(getattr(t, "indisponibilites", {}).get("dates", []))
                weeks_blocked = {w for w, d in week_dates.items() if d.strftime("%Y-%m-%d") in dates}
                team_unavail[t.id_equipe] = weeks_blocked

            for c in College.objects.filter(college_id__in=college_ids):
                dates = set(getattr(c, "indisponibilites", {}).get("dates", []))
                weeks_blocked = {w for w, d in week_dates.items() if d.strftime("%Y-%m-%d") in dates}
                college_unavail[c.college_id] = weeks_blocked

            print(team_unavail)
            # --- Decision variables ---
            x = pulp.LpVariable.dicts("x", (match_ids, weeks), 0, 1, cat=pulp.LpBinary)  # match m in week w
            y = pulp.LpVariable.dicts("y", (team_ids, weeks), 0, 1, cat=pulp.LpBinary)  # team t plays in week w
            z = pulp.LpVariable.dicts("z", (team_ids, weeks[:-1]), 0, 1, cat=pulp.LpBinary)  # back-to-back t in w,w+1

            # --- Model ---
            prob = pulp.LpProblem("MatchScheduling", pulp.LpMinimize)

            # 1) Each match exactly once
            for m in match_ids:
                prob += pulp.lpSum(x[m][w] for w in weeks) == 1, f"match_once_m{m}"

            # 2) Team plays at most once per week (+ link to y)
            for t in team_ids:
                for w in weeks:
                    prob += pulp.lpSum(
                        x[m][w] for m in match_ids if host_team[m] == t or visitor_team[m] == t
                    ) <= 1, f"team_max_once_week_t{t}_w{w}"

                    prob += y[t][w] >= pulp.lpSum(
                        x[m][w] for m in match_ids if host_team[m] == t or visitor_team[m] == t
                    ) / 2, f"y_link_lb_t{t}_w{w}"

                    prob += y[t][w] <= pulp.lpSum(
                        x[m][w] for m in match_ids if host_team[m] == t or visitor_team[m] == t
                    ), f"y_link_ub_t{t}_w{w}"

            # 3) Each college hosts at most once per week
            for c in college_ids:
                for w in weeks:
                    prob += pulp.lpSum(x[m][w] for m in match_ids if host_college[m] == c) <= 1

            # 4) Exactly 4 per session, split 2 home / 2 away
            for t in team_ids:
                # Autumn weeks 1–10
                prob += pulp.lpSum(
                    x[m][w] for m in match_ids if (host_team[m] == t or visitor_team[m] == t) for w in range(1, 11)
                ) == 4, f"autumn_total_t{t}"
                prob += pulp.lpSum(
                    x[m][w] for m in match_ids if host_team[m] == t for w in range(1, 11)
                ) == 2, f"autumn_home_t{t}"
                prob += pulp.lpSum(
                    x[m][w] for m in match_ids if visitor_team[m] == t for w in range(1, 11)
                ) == 2, f"autumn_away_t{t}"

                # Winter weeks 11–20
                prob += pulp.lpSum(
                    x[m][w] for m in match_ids if (host_team[m] == t or visitor_team[m] == t) for w in range(11, 21)
                ) == 4, f"winter_total_t{t}"
                prob += pulp.lpSum(
                    x[m][w] for m in match_ids if host_team[m] == t for w in range(11, 21)
                ) == 2, f"winter_home_t{t}"
                prob += pulp.lpSum(
                    x[m][w] for m in match_ids if visitor_team[m] == t for w in range(11, 21)
                ) == 2, f"winter_away_t{t}"

            # 5) No more than 2 back-to-back (use y)
            for t in team_ids:
                for w in weeks[:-1]:
                    prob += z[t][w] >= y[t][w] + y[t][w + 1] - 1, f"back_to_back_t{t}_w{w}"
                prob += pulp.lpSum(z[t][w] for w in weeks[:-1]) <= 2, f"max_back_to_back_t{t}"

            # 6) No 3 consecutive weeks
            for t in team_ids:
                for w in range(1, 19):  # w, w+1, w+2
                    prob += y[t][w] + y[t][w + 1] + y[t][w + 2] <= 2, f"no_three_in_row_t{t}_w{w}"

            # 7) Not both week 1&2
            for t in team_ids:
                prob += y[t][1] + y[t][2] <= 1, f"no_two_start_fall_t{t}"

            # 8) Indisponibilités (teams + host colleges) — version robuste
            weeks_set = set(weeks)
            added_constraints = 0
            problematic_matches = []

            for m in match_ids:
                ht = host_team[m]
                vt = visitor_team[m]
                hc = host_college[m]

                # union des semaines interdites (peuvent contenir des choses inattendues)
                forbidden_weeks = (team_unavail.get(ht, set()) |
                                   team_unavail.get(vt, set()) |
                                   college_unavail.get(hc, set()))

                # Normaliser les semaines : ne garder que celles qui sont des entiers et qui existent
                # (parfois DB peut stocker des dates/strings)
                forbidden_weeks_filtered = {w for w in forbidden_weeks if isinstance(w, int) and w in weeks_set}

                # Debug : s'il y avait des valeurs non entières / hors plage, logguer-les
                bad_values = [w for w in forbidden_weeks if not (isinstance(w, int) and w in weeks_set)]
                if bad_values:
                    print(f"⚠️ Match {m}: valeurs d'indisponibilités ignorées (non-valide): {bad_values}")

                # Si le match n'a plus de semaines autorisées => impossible localement
                allowed_weeks = weeks_set - forbidden_weeks_filtered
                if not allowed_weeks:
                    print(
                        f"❌ Match {m} n'a aucune semaine possible après filtration! host={ht} visitor={vt} college={hc}")
                    problematic_matches.append(m)
                    # option: raise ici plutôt que laisser le solveur échouer plus loin
                    # raise RuntimeError(f"Match {m} has zero allowed weeks (indispos): {forbidden_weeks}")

                # Ajouter les contraintes seulement pour semaines valides
                for w in forbidden_weeks_filtered:
                    prob += x[m][w] == 0, f"indispo_m{m}_w{w}"
                    added_constraints += 1

            print(
                f"Indisponibilités : contraintes ajoutées = {added_constraints}, matchs problématiques = {problematic_matches}")

            # --- Objective (spread) ---
            prob += pulp.lpSum(z[t][w] for t in team_ids for w in weeks[:-1]), "minimize_back_to_back"

            # --- Solve (explicit CBC MILP) ---
            status = prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=180))
            print("Status:", pulp.LpStatus[prob.status])
            if pulp.LpStatus[prob.status] not in ("Optimal", "Feasible"):
                raise RuntimeError(f"Solve failed: {pulp.LpStatus[prob.status]}")

            # --- Sanity: check integrality (should be 0/1) ---
            non_int = []
            for m in match_ids:
                for w in weeks:
                    v = pulp.value(x[m][w])
                    if v is not None and abs(v - round(v)) > 1e-6:
                        non_int.append((m, w, v))
            if non_int:
                print("⚠️ Non-integer x found (solver returned fractional values):", non_int[:10])

            # --- Extract a clean schedule (strict) ---
            schedule = {}
            for m in match_ids:
                on_weeks = [w for w in weeks if pulp.value(x[m][w]) is not None and pulp.value(x[m][w]) > 0.99]
                if len(on_weeks) != 1:
                    raise ValueError(f"Match {m} assigned to {len(on_weeks)} weeks: {on_weeks}")
                schedule[m] = on_weeks[0]

            # --- Validate constraints on the extracted schedule ---
            _validate_schedule(schedule, matches)
            sessions = Session.objects.filter(calendrier_id=self.calendrier_id).all()
            match_ids = schedule.keys()
            matches = {m.match_id: m for m in Match.objects.filter(match_id__in=match_ids)}

            schedule_by_week = {}
            for m_id, week in schedule.items():
                match = matches[m_id]  # use pre-fetched dict
                schedule_by_week.setdefault(week, []).append(match)

            for s_idx, session in enumerate(sessions):  # s_idx = 0 for first session, 1 for second
                semaines = list(Semaine.objects.filter(session_id=session.session_id).order_by("semaine_id"))

                # pick the right 10 weeks from schedule_by_week
                weeks_for_session = sorted(schedule_by_week.keys())[s_idx * 10:(s_idx + 1) * 10]

                for i, semaine in enumerate(weeks_for_session):
                    for match in schedule_by_week[semaine]:
                        match.semaine = semaines[i]  # assign to the ith semaine of that session
                        match.session = session
                        match.save()

            # user display (your own function)
            display_schedule()
            return schedule

        def _validate_schedule(schedule, matches):
            """Light checker on the integer schedule produced."""
            from collections import defaultdict

            weeks_by_team = defaultdict(lambda: defaultdict(int))
            weeks_by_college = defaultdict(lambda: defaultdict(int))
            host_team = {int(m.match_id): int(m.equipe1.id_equipe) for m in matches}
            visitor_team = {int(m.match_id): int(m.equipe2.id_equipe) for m in matches}
            host_college = {int(m.match_id): int(m.equipe1.college.college_id) for m in matches}

            for m, w in schedule.items():
                t1, t2 = host_team[m], visitor_team[m]
                c = host_college[m]
                weeks_by_team[t1][w] += 1
                weeks_by_team[t2][w] += 1
                weeks_by_college[c][w] += 1

            errs = []

            # team max once per week
            for t, wk in weeks_by_team.items():
                for w, cnt in wk.items():
                    if cnt > 1:
                        errs.append(f"Team {t} plays {cnt} times in week {w}")

            # college host max once per week
            for c, wk in weeks_by_college.items():
                for w, cnt in wk.items():
                    if cnt > 1:
                        errs.append(f"College {c} hosts {cnt} matches in week {w}")

            if errs:
                print("❌ Violations detected:")
                for e in errs:
                    print("  -", e)
                raise AssertionError("Schedule violates hard constraints (see above).")
            else:
                print("✅ Schedule passes basic validation.")

        def display_schedule():
            sessions = Session.objects.filter(calendrier_id=self.calendrier_id)
            for session in sessions:
                print(session)
                semaines = Semaine.objects.filter(session_id=session.session_id)
                for semaine in semaines:
                    print(semaine)
                    matchs = Match.objects.filter(semaine_id=semaine.semaine_id)
                    for match in matchs:
                        print(match)

            self.exportCalendrierToExcel()

        matchs = []
        for division in DIVISION_CHOICES:
            print(division)
            matchs += creationMatchs(division[0])
            #print("NBMATCH : " + str(len(matchs)))
        placerMatchs(matchs, startAut, startHiver)
        for match in matchs:
            Match.deleteMatch(match.match_id)

    def exportCalendrierToExcel(self):
        BG_COLOR = (255,52,95)
        FONT_COLOR = (255,255,255)
        SEM_TITLE_COLOR = (235, 0, 129)
        HEADER_COLOR = (2,30,96)
        PAMPS_COLOR = (212,0,0)
        TANG_COLOR = (253,15,3)
        CLEMS_COLOR = (254,148,0)
        EMPTY_COLOR = (1,20,62)
        def formatCell(cell,bgColor,bold=True):
            cell.api.Font.Bold = bold
            cell.color = bgColor
            cell.api.HorizontalAlignment = -4108
            cell.api.VerticalAlignment = -4108
            #cell.api.Font.Color = FONT_COLOR

        row = 2
        col = 2
        maxMatchIndex = 0
        wb = xw.Book()
        sheet = wb.sheets[0]
        sessions = Session.objects.filter(calendrier_id=self.calendrier_id)
        for session in sessions:
            #TITLE
            sheet.range(sheet.cells(row,col), sheet.cells(row,col+12)).merge()
            cell = sheet.cells(row,col)
            cell.value = "SESSION AUTOMNE"
            formatCell(cell,BG_COLOR)
            row += 2

            semaines = Semaine.objects.filter(session_id=session.session_id)
            semIndexCol = 0
            for semaine in semaines:
                if semIndexCol % 4 == 0 and semIndexCol != 0:
                    row+=maxMatchIndex+4
                    semIndexCol = 0

                #TITRE
                sheet.range(sheet.cells(row,col+semIndexCol*3), sheet.cells(row, col+semIndexCol*3+1)).merge()
                cell = sheet.cells(row, col+semIndexCol*3)
                cell.value = f"Semaine {semIndexCol+1}"
                formatCell(cell,SEM_TITLE_COLOR)
                row += 1

                #DATE
                sheet.range(sheet.cells(row, col+semIndexCol*3), sheet.cells(row, col+semIndexCol*3 + 1)).merge()
                cell = sheet.cells(row, col+semIndexCol*3)
                cell.value = str(semaine.date)
                formatCell(cell,HEADER_COLOR)
                row+=1

                #HEADER
                cell = sheet.cells(row, col+semIndexCol*3)
                cell.value = "Visiteur"
                formatCell(cell,HEADER_COLOR)

                cell = sheet.cells(row, col + semIndexCol * 3+1)
                cell.value = "Hôtes"
                formatCell(cell,HEADER_COLOR)
                row += 1

                matchs = Match.objects.filter(semaine_id=semaine.semaine_id)
                matchIndex = 0
                for match in matchs:
                    vCell = sheet.cells(row + matchIndex, col+semIndexCol*3)
                    vCell.value = match.equipe2.nom_equipe

                    hCell = sheet.cells(row + matchIndex, col+semIndexCol*3+1)
                    hCell.value = match.equipe1.nom_equipe

                    if(match.division == "Pamplemousse"):
                        formatCell(vCell,PAMPS_COLOR,False)
                        formatCell(hCell,PAMPS_COLOR,False)
                    elif(match.division == "Tangerine"):
                        formatCell(vCell, TANG_COLOR, False)
                        formatCell(hCell, TANG_COLOR, False)
                    elif(match.division == "Clementine"):
                        formatCell(vCell, CLEMS_COLOR, False)
                        formatCell(hCell, CLEMS_COLOR, False)

                    matchIndex += 1
                maxMatchIndex = matchIndex if matchIndex > maxMatchIndex else maxMatchIndex
                row -= 3
                semIndexCol += 1
            row = 2
            col = 15

        #Analyse de la distribution des équipes
        ficheEquipeData = wb.sheets.add("Distribution Equipe")
        equipes = list(
            Equipe.objects.all()
            .exclude(nom_equipe="EQUIPE TEST")
        )
        row = 1
        col = 1
        equIndex = 0

        #Headers
        ficheEquipeData.cells(1,1).value = "Équipes"
        for semaineIndex in range(1,21):
            cell = ficheEquipeData.cells(1,semaineIndex+1)
            cell.value = f"Semaine {semaineIndex}"
            formatCell(cell,HEADER_COLOR)

        row+=1
        for equipe in equipes:
            cell = ficheEquipeData.cells(row+equIndex,1)
            cell.value = equipe.nom_equipe
            if (equipe.division == "Pamplemousse"):
                formatCell(cell, PAMPS_COLOR, False)
            elif (equipe.division == "Tangerine"):
                formatCell(cell, TANG_COLOR, False)
            elif (equipe.division == "Clementine"):
                formatCell(cell, CLEMS_COLOR, False)

            equIndex += 1
        wb.save(r"C:\Users\felix\Downloads\CalendrierPamps.xlsx")

    import xlwings as xw
    from datetime import datetime

    def importCalendrierFromExcel(calendrier_id, filepath=r"C:\Users\felix\Downloads\CalendrierPamps.xlsx"):
        wb = xw.Book(filepath)
        sheet = wb.sheets[0]

        row = 2
        col = 2

        # On suppose qu’il n’y a qu’une session par fichier
        session = Session.objects.create(
            calendrier_id=calendrier_id,
            nom="SESSION AUTOMNE"
        )

        while True:
            titre = sheet.cells(row, col).value
            if titre is None:
                break  # fin du fichier

            if "SESSION" in str(titre):
                row += 2
                semIndexCol = 0
                while True:
                    semTitre = sheet.cells(row, col + semIndexCol * 3).value
                    if semTitre is None:
                        break

                    # Lecture de la date
                    date_str = sheet.cells(row + 1, col + semIndexCol * 3).value
                    try:
                        semaine_date = datetime.strptime(str(date_str), "%Y-%m-%d").date()
                    except:
                        semaine_date = None

                    semaine = Semaine.objects.create(
                        session_id=session.session_id,
                        date=semaine_date
                    )

                    # Sauter les headers "Visiteur" / "Hôtes"
                    row_matchs = row + 3
                    while True:
                        visiteur = sheet.cells(row_matchs, col + semIndexCol * 3).value
                        hote = sheet.cells(row_matchs, col + semIndexCol * 3 + 1).value
                        if not visiteur and not hote:
                            break

                        # Récupérer les équipes
                        eq_visiteur, _ = Equipe.objects.get_or_create(nom_equipe=visiteur)
                        eq_hote, _ = Equipe.objects.get_or_create(nom_equipe=hote)

                        # Déterminer division par couleur
                        vColor = sheet.cells(row_matchs, col + semIndexCol * 3).color
                        if vColor == (212, 0, 0):
                            division = "Pamplemousse"
                        elif vColor == (253, 15, 3):
                            division = "Tangerine"
                        elif vColor == (254, 148, 0):
                            division = "Clementine"
                        else:
                            division = "Inconnue"

                        Match.objects.create(
                            semaine_id=semaine.semaine_id,
                            equipe1=eq_hote,
                            equipe2=eq_visiteur,
                            division=division
                        )

                        row_matchs += 1

                    semIndexCol += 1

            else:
                row += 1

    def __str__(self):
        return self.nom_calendrier

class Semaine(models.Model):
    semaine_id = models.AutoField(primary_key=True)
    nb_match = models.IntegerField()
    date = models.DateField(blank=True, null=True)

    session = models.ForeignKey(Session, related_name="semaines", on_delete=models.CASCADE, null=True)

    @classmethod
    def createSemaine(cls, nb_match=0, date=None, session_id=None):
        semaine = cls(
            nb_match=nb_match,
            date=date,
            session_id=session_id
        )
        semaine.save()
        return semaine

    def __str__(self):
        session = Session.objects.get(session_id=self.session_id)
        return session.__str__() + " - " + str(self.semaine_id)

class College(models.Model):
    college_id = models.AutoField(primary_key=True)
    nom_college = models.CharField(max_length=100, unique=True)
    locationX = models.FloatField()
    locationY = models.FloatField()
    adresse = models.CharField(max_length=255)
    indisponibilites = models.JSONField(null=True, blank=True)
    est_actif = models.BooleanField(default=True)

    @classmethod
    def createCollege(cls, nom_college, adresse):

        gmaps = Client(key=API_KEY)

        try:
            geocode_result = geocoding.geocode(gmaps, adresse)

            if geocode_result and geocode_result[0]["geometry"]["location"]:
                locationX = geocode_result[0]["geometry"]["location"]["lat"]
                locationY = geocode_result[0]["geometry"]["location"]["lng"]

                college = cls(
                    nom_college=nom_college,
                    locationX=locationX,
                    locationY=locationY
                )
                college.save()
                return college
        except Exception as e:
            print(f"L'adresse n'a pas été trouvé : {e}")
            return None

    def __str__(self):
        return self.nom_college

class Interprete(models.Model):
    interprete_id = models.AutoField(primary_key=True)
    nom_interprete = models.CharField(max_length=100)
    pronom_interprete = models.CharField(max_length=20, blank=True, default="")

    alignements = models.ManyToManyField(
        'Alignement',
        through="DetailsInterprete",
        related_name="interpretes"
    )

    @classmethod
    def createInterprete(cls, nom_interprete, pronom_interprete, numero_interprete, role_interprete,
                         alignement):
        interprete = cls(
            nom_interprete=nom_interprete,
            pronom_interprete=pronom_interprete,
        )
        details_interprete = DetailsInterprete()
        interprete.save()

        if alignement:
            interprete.alignements.add(alignement)
            interprete.save()
            alignement.save()

        return interprete

    def get_equipe(self, saison):

        equipes = [alignement.information_equipe for alignement in self.alignement.all() if alignement.saison == saison]

        if len(equipes) > 1:
            return None
        else:
            return equipes[0]

    def __str__(self):
        return f"{self.nom_interprete} #{self.numero_interprete} ({self.pronom_interprete})"

class Equipe(models.Model):
    id_equipe = models.AutoField(primary_key=True)
    nom_equipe = models.CharField(max_length=100, unique=True)
    logo = models.FileField(blank=True, null=True, upload_to='logos/')
    division = models.CharField(max_length=50, choices=DIVISION_CHOICES)
    last_modified = models.DateTimeField(auto_now=True)
    indisponibilites = models.JSONField(null=True, blank=True)
    est_active = models.BooleanField(default=True)

    college = models.ForeignKey(College, related_name="equipes", on_delete=models.CASCADE, null=True)
    alignement = models.ForeignKey('Alignement', related_name="Alignement", on_delete=models.SET_NULL, null=True,
                                    blank=True)
    matchs = models.ManyToManyField('Match', null=True, blank=True)

    @classmethod
    def createEquipe(cls, nomEquipe, logo=None, division=None, college=None):
        equipe = cls(
            nom_equipe=nomEquipe,
            logo=logo,
            division=division,
            college=college,
        )
        equipe.save()
        return equipe

    def getAlignement(self, saisonID):
        selectedSaison = Saison.objects.filter(saison_id=saisonID).first()
        print(Alignement.objects.filter(saison=selectedSaison, equipe=self).first().interpretes.all())
        return Alignement.objects.filter(saison=selectedSaison, equipe=self).first().interpretes.all()

    def getUrlPhoto(self):
        if settings.DEBUG:
            domain = "http://localhost:8000/Citrus"
        else:
            domain = "https://citrus.liguedespamplemousses.com"

        if self.logo and self.logo.url :
            return domain + self.logo.url
        else :
            return None



    def __str__(self):
        return self.nom_equipe

class CoachManager(BaseUserManager):
    def create_user(self, prenom_coach, nom_coach, pronom_coach, courriel, password=None, equipe=None, **extra_fields):
        if not courriel:
            raise ValueError("Le courriel est obligatoire")
        courriel = self.normalize_email(courriel)
        user = self.model(
            prenom_coach=prenom_coach,
            nom_coach=nom_coach,
            pronom_coach=pronom_coach,
            courriel=courriel,
            equipe=equipe,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, prenom_coach, nom_coach, courriel, pronom_coach=None, password=None, equipe=None,
                         **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('admin_flag', True)

        return self.create_user(
            prenom_coach=prenom_coach,
            nom_coach=nom_coach,
            pronom_coach=pronom_coach,
            courriel=courriel,
            password=password,
            equipe=equipe,
            **extra_fields
        )

class Coach(AbstractUser):
    coach_id = models.AutoField(primary_key=True)
    nom_coach = models.CharField(max_length=100)
    prenom_coach = models.CharField(max_length=100)
    pronom_coach = models.CharField(max_length=20, blank=True, null=True)
    courriel = models.EmailField(max_length=255, unique=True)
    admin_flag = models.BooleanField(default=False)
    validated_flag = models.BooleanField(default=False)
    equipe = models.ForeignKey(Equipe, on_delete=models.SET_NULL, null=True, blank=True)
    objects = CoachManager()

    username = None

    college = models.ForeignKey('College', on_delete=models.SET_NULL, null=True, blank=True, related_name='college')

    USERNAME_FIELD = 'courriel'
    REQUIRED_FIELDS = ['prenom_coach', 'nom_coach']

    @classmethod
    def createCoach(cls, nomCoach, prenomCoach, courrielCoach, coachPwd):
        """
        Creates and saves a Coach instance.
        """
        coach = cls(
            nom_coach=nomCoach,
            prenom_coach=prenomCoach,
            courriel=courrielCoach,
            admin_flag=False,
            validated_flag=False,
            equipe=None
        )

        # Proper password hashing
        coach.set_password(coachPwd)

        coach.save()

        return coach


    def __str__(self):
        return self.courriel

    @property
    def is_admin(self):
        return self.admin_flag

class Punition(models.Model):
    punition_id = models.AutoField(primary_key=True)
    nom_punition = models.CharField(max_length=50)
    est_majeure = models.BooleanField(default=False)


    equipe_punie = models.ForeignKey(Equipe, on_delete=models.DO_NOTHING, related_name='equipe_punie', null=True)
    @classmethod
    def createPunition(cls, nom_punition, est_majeure,equipePunie):
        punition = cls(
            nom_punition=nom_punition,
            est_majeure=est_majeure,
            equipe_punie=equipePunie
        )

        punition.save()
        return punition

class Match(models.Model):
    match_id = models.AutoField(primary_key=True)
    score_eq1 = models.IntegerField(default=0)
    score_eq2 = models.IntegerField(default=0)
    etoile1 = models.CharField(max_length=255, blank=True, null=True)
    etoile2 = models.CharField(max_length=255, blank=True, null=True)
    etoile3 = models.CharField(max_length=255, blank=True, null=True)
    etoile4 = models.CharField(max_length=255, blank=True, null=True)
    nom_arbitre = models.CharField(max_length=100, blank=True, null=True)
    date_match = models.DateTimeField(null=True, blank=True)
    url_photo = models.URLField(blank=True, null=True)
    division = models.CharField(max_length=50, choices=DIVISION_CHOICES, default=DIVISION_CHOICES[0][0])
    completed_flag = models.BooleanField(default=False)
    validated_flag = models.BooleanField(default=False)
    improvisations = models.JSONField(blank=True, null=True, default=list)
    cache = models.JSONField(blank=True, null=True,default=dict)

    saison = models.ForeignKey(Saison, on_delete=models.DO_NOTHING, related_name='saison_match', null=True)
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True)
    serie = models.ForeignKey(Serie, on_delete=models.CASCADE, null=True,blank=True)
    equipe1 = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name='equipe_hote', null=True)
    equipe2 = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name='equipe_visiteure', null=True)
    semaine = models.ForeignKey(Semaine, related_name="matchs", on_delete=models.SET_NULL, null=True)
    punitions = models.ManyToManyField(Punition,blank=True,related_name='punitions', null=True)

    @classmethod
    def validate_match(self):
        pass

    @classmethod
    def createMatch(cls, division, session=None, serie=None, equipe1=None, equipe2=None, semaine=None):
        match = cls(
            session=session,
            serie=serie,
            equipe1=equipe1,
            equipe2=equipe2,
            semaine=semaine,
            division=division,
            date_match=semaine.date,
        )

        equipe1.save()
        equipe2.save()

        code = str(equipe1.nom_equipe) + str(equipe2.nom_equipe) + str(match.match_id)
        match.url_match = "http://localhost:8000/Citrus/match-" + hash_code(code)

        match.save()
        return match

    @classmethod
    def deleteMatch(cls, match_id):
        try:
            match = cls.objects.get(pk=match_id)

            match.equipe1.save()
            match.equipe2.save()

            match.delete()
            return True
        except cls.DoesNotExist:
            return False

    @property
    def get_urlMatch(self):
        code = str(self.equipe1.nom_equipe) + str(self.equipe2.nom_equipe) + str(self.match_id)
        if settings.DEBUG:
            self.url_match = "http://localhost:8000/Citrus/Match-" + hash_code(code)
        else:
            self.url_match = "https://citrus.liguedespamplemousses.com/Citrus/Match-" + hash_code(code)
        self.save()
        return self.url_match
    def get_QrCode(self):
        qr = segno.make(self.get_urlMatch)

        buffer = BytesIO()
        qr.save(buffer, kind='png', scale=7)
        buffer.seek(0)

        imageBase64 = base64.b64encode(buffer.read()).decode('utf-8')

        return f"data:image/png;base64,{imageBase64}"

    def get_dateFormatted(self):
        #locale.setlocale(locale.LC_TIME, 'en_US')

        date_formatted = self.date_match.strftime("%d %b")
        return date_formatted

    def get_dateFormattedWithYear(self):
        #locale.setlocale(locale.LC_TIME, 'en_US')
        date_formatted = self.date_match.strftime("%d %b %Y")

        return date_formatted

    def __str__(self):
        if self.date_match is not None:
            date_formatted = self.date_match.strftime("%Y-%m-%d")
        else:
            date_formatted = ""
        session = self.session
        equipe1 = self.equipe1
        equipe2 = self.equipe2

        type = session.type if session else "SERIE"

        return str(self.match_id) + " - " + str(date_formatted) + " - " + type + " - " + equipe2.nom_equipe + " VS " + equipe1.nom_equipe

class Alignement(models.Model):
    id_alignement = models.AutoField(primary_key=True)
    coach = models.ForeignKey(Coach, related_name="alignements", on_delete=models.SET_NULL, null=True)
    equipe = models.ForeignKey(Equipe, related_name="equipe", on_delete=models.CASCADE, null=False)
    saison = models.ForeignKey(Saison, related_name="saison", on_delete=models.CASCADE, null=False)

    @classmethod
    def create_alignement(cls, equipe, saison):
        alignement = cls(
            equipe=equipe,
            saison=saison,
            coach_id=None
        )
        alignement.save()
        return alignement

    def ajouter_interprete(self, interprete:Interprete, role_interprete, numero_interprete):
        details_interprete = DetailsInterprete.creer_details_interprete(interprete,self,role_interprete,numero_interprete)
    def __str__(self):
        return self.saison.nom_saison + "-" + self.equipe.nom_equipe

class DetailsInterprete(models.Model):
    interprete = models.ForeignKey('Interprete', on_delete=models.CASCADE)
    alignement = models.ForeignKey('Alignement', on_delete=models.CASCADE)
    numero_interprete = models.CharField(max_length=20, blank=True, default="")
    role_interprete = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        unique_together = ('interprete', 'alignement')  # empêche doublons
        indexes = [
            models.Index(fields=['interprete']),
            models.Index(fields=['alignement']),
            models.Index(fields=['role_interprete']),
            models.Index(fields=['alignement', 'interprete']),  # accélère les jointures combinées
        ]

    @classmethod
    def creer_details_interprete(cls, interprete:Interprete, alignement:Alignement, role_interprete, numero_interprete):
        try:
            details_interprete = DetailsInterprete(
                interprete=interprete,
                alignement=alignement,
                role_interprete=role_interprete,
                numero_interprete=numero_interprete,
            )
            details_interprete.save()
            return details_interprete

        except Interprete.DoesNotExist:
            raise ValueError("Interprete not found.")
        except Alignement.DoesNotExist:
            raise ValueError("Alignement not found.")
        except IntegrityError:
            raise ValueError("This interprete is already assigned to this alignement.")


    def __str__(self):
            return f"{self.interprete.nom_interprete} - {self.alignement.equipe.nom_equipe} ({self.role_interprete})"
