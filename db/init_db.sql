CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE subforums
(
    id      SERIAL PRIMARY KEY,
    name    VARCHAR(100)
);

CREATE TABLE topics
(
    id          INT PRIMARY KEY,
    subforum_id INT REFERENCES subforums(id),
    title       VARCHAR(255),
    url         VARCHAR(255),
    is_invalid  BOOLEAN DEFAULT false,
    fetch_time  TIMESTAMP
);

CREATE TABLE pages
(
    id UUID     PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id    INT REFERENCES topics(id),
    page_number INT,
    content     TEXT
);


INSERT INTO subforums (name)
VALUES  ('aihe_vapaa'),
        ('vauvakuume'),
        ('raskaus_ja_synnytys'),
        ('vauvat_ja_taaperot'),
        ('kasvatus'),
        ('perhe_ja_arki'),
        ('lapsettomuus_ja_adoptio'),
        ('erota_vai_ei_kysy_asiantuntijat_vastaavat'),
        ('kysy_terveydenhoitajalta'),
        ('keskustele_unesta_ja_jaksamisesta'),
        ('kysy_seksuaaliterapeutilta'),
        ('erota_vai_ei_asiantuntijat_vastaavat'),
        ('keskustelu_unesta_ja_jaksamisesta'),
        ('keskustelu_nettikiusaamisesta'),
        ('seksi'),
        ('nimet');