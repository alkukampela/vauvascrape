CREATE TABLE topic_words
(
    id UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id           INT REFERENCES topics(id),
    word               VARCHAR(50) NOT NULL,
    frequency          INT NOT NULL,
    scaled_frequency   NUMERIC(20, 20) NOT NULL
);
