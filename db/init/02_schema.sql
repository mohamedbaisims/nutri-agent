CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE users (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    age         SMALLINT     NOT NULL CHECK (age BETWEEN 14 AND 100),
    sexe        CHAR(1)      NOT NULL CHECK (sexe IN ('H', 'F')),
    taille_cm   NUMERIC(5,1) NOT NULL CHECK (taille_cm BETWEEN 150 AND 220),
    poids_kg    NUMERIC(5,1) NOT NULL CHECK (poids_kg BETWEEN 40 AND 190),
    activite    TEXT         NOT NULL CHECK (activite IN ('sedentaire', 'leger', 'modere', 'actif', 'tres_actif')),
    objectif    TEXT         NOT NULL CHECK (objectif IN ('perte', 'maintien','prise')),
    kcal_cible  INTEGER,
    prot_cible  NUMERIC(6,1),
    gluc_cible  NUMERIC(6,1),
    lip_cible   NUMERIC(6,1),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE TABLE meals (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date_heure  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    type_repas  TEXT         NOT NULL DEFAULT 'autre'
                CHECK (type_repas IN ('petit_dejeuner', 'dejeuner', 'diner', 'collation', 'autre')),
    photo_url   TEXT,
    kcal        NUMERIC(7,1) NOT NULL DEFAULT 0,
    prot        NUMERIC(6,1) NOT NULL DEFAULT 0,
    gluc        NUMERIC(6,1) NOT NULL DEFAULT 0,
    lip         NUMERIC(6,1) NOT NULL DEFAULT 0,
    confiance   NUMERIC(4,3) CHECK (confiance BETWEEN 0 AND 1),
    verdict     TEXT         CHECK (verdict IN ('vert', 'orange', 'rouge'))
);

CREATE INDEX idx_meals_user_date ON meals (user_id, date_heure);

CREATE TABLE nutrition_ref (
    aliment_id  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom_fr      TEXT          NOT NULL,
    nom_en      TEXT,
    kcal_100g   NUMERIC(6,1)  NOT NULL CHECK (kcal_100g >= 0),
    prot_100g   NUMERIC(5,1)  NOT NULL CHECK (prot_100g >= 0),
    gluc_100g   NUMERIC(5,1)  NOT NULL CHECK (gluc_100g >= 0),
    lip_100g    NUMERIC(5,1)  NOT NULL CHECK (lip_100g >= 0),
    source      TEXT          NOT NULL,
    embedding   vector(768)
);

CREATE TABLE meal_items (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    meal_id     BIGINT        NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
    aliment_id  BIGINT        REFERENCES nutrition_ref(aliment_id),
    grammes     NUMERIC(7,1)  NOT NULL CHECK (grammes >= 0),
    kcal        NUMERIC(7,1)  NOT NULL DEFAULT 0,
    prot        NUMERIC(6,1)  NOT NULL DEFAULT 0,
    gluc        NUMERIC(6,1)  NOT NULL DEFAULT 0,
    lip         NUMERIC(6,1)  NOT NULL DEFAULT 0
);
CREATE TABLE dishes_ref (
    dish_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom          TEXT         NOT NULL,
    famille      TEXT,
    kcal         NUMERIC(7,1) NOT NULL CHECK (kcal >= 0),
    prot         NUMERIC(6,1) NOT NULL CHECK (prot >= 0),
    gluc         NUMERIC(6,1) NOT NULL CHECK (gluc >= 0),
    lip          NUMERIC(6,1) NOT NULL CHECK (lip >= 0),
    score_sante  NUMERIC(4,2),
    embedding    vector(768)
);

CREATE VIEW v_daily_totals AS
SELECT
    user_id,
    (date_heure AT TIME ZONE 'Africa/Tunis')::date AS jour,
    COUNT(*)                AS nb_repas,
    COALESCE(SUM(kcal), 0)  AS kcal,
    COALESCE(SUM(prot), 0)  AS prot,
    COALESCE(SUM(gluc), 0)  AS gluc,
    COALESCE(SUM(lip), 0)   AS lip
FROM meals
GROUP BY user_id, (date_heure AT TIME ZONE 'Africa/Tunis')::date;
CREATE VIEW v_daily_remaining AS
SELECT
    u.id AS user_id,
    (now() AT TIME ZONE 'Africa/Tunis')::date          AS jour,
    COALESCE(t.nb_repas, 0)                            AS nb_repas,
    u.kcal_cible - COALESCE(t.kcal, 0)                 AS kcal_restant,
    u.prot_cible - COALESCE(t.prot, 0)                  AS prot_restant,
    u.gluc_cible - COALESCE(t.gluc, 0)                  AS gluc_restant,
    u.lip_cible  - COALESCE(t.lip, 0)                  AS lip_restant
FROM users u
LEFT JOIN v_daily_totals t
       ON t.user_id = u.id
      AND t.jour = (now() AT TIME ZONE 'Africa/Tunis')::date;