-- CitrusApp/sql/ipp_equipe.sql
WITH base AS (
    SELECT
        e.id_equipe,
        e.nom_equipe,

        CASE
            WHEN m.equipe1_id = e.id_equipe AND m.score_eq2 > 0
                THEN LN(1.0 * m.score_eq1 / m.score_eq2)
            WHEN m.equipe2_id = e.id_equipe AND m.score_eq1 > 0
                THEN LN(1.0 * m.score_eq2 / m.score_eq1)
        END AS log_ratio_global,

        CASE
            WHEN m.equipe1_id = e.id_equipe AND m.score_eq2 > 0
                THEN LN(1.0 * m.score_eq1 / m.score_eq2)
        END AS log_ratio_home,

        CASE
            WHEN m.equipe2_id = e.id_equipe AND m.score_eq1 > 0
                THEN LN(1.0 * m.score_eq2 / m.score_eq1)
        END AS log_ratio_away

    FROM CitrusApp_equipe e
    LEFT JOIN CitrusApp_match m
        ON (
            (m.equipe1_id = e.id_equipe OR m.equipe2_id = e.id_equipe)
            AND m.saison_id = %s
        )
),

par_equipe AS (
    SELECT
        id_equipe,
        nom_equipe,
        ROUND(AVG(log_ratio_global), 3) AS force,
        ROUND(AVG(log_ratio_home), 3) AS avantageMaison,
        ROUND(AVG(log_ratio_away), 3) AS performanceExterieur,
        ROUND(AVG(log_ratio_home) - AVG(log_ratio_away), 3) AS ipp,
        COUNT(log_ratio_home) AS nb_domicile,
        COUNT(log_ratio_away) AS nb_exterieur
    FROM base
    GROUP BY id_equipe, nom_equipe
),

stats_ligue AS (
    SELECT
        AVG(ipp) AS ipp_moyen,
        SQRT(
            AVG(ipp * ipp) - AVG(ipp) * AVG(ipp)
        ) AS ipp_ecart_type
    FROM par_equipe
    WHERE nb_domicile >= 4 AND nb_exterieur >= 4
),

classement AS (
    SELECT
        id_equipe,
        RANK() OVER (ORDER BY ipp DESC) AS rang_ipp,
        (SELECT COUNT(*) FROM par_equipe) AS nb_equipes_ligue
    FROM par_equipe
)

SELECT
    p.id_equipe AS equipe_id,
    p.nom_equipe,
    p.force,
    p.avantageMaison,
    p.performanceExterieur,
    p.ipp,
    p.nb_domicile,
    p.nb_exterieur,

    ROUND(
        (p.ipp - s.ipp_moyen) / NULLIF(s.ipp_ecart_type, 0),
        3
    ) AS z_score,

    c.rang_ipp,
    c.nb_equipes_ligue,

    ROUND(s.ipp_moyen, 3) AS ipp_moyen_ligue,
    ROUND(s.ipp_ecart_type, 3) AS ipp_ecart_type_ligue

FROM par_equipe p
CROSS JOIN stats_ligue s
JOIN classement c ON c.id_equipe = p.id_equipe
WHERE p.id_equipe = %s;