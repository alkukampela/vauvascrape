CREATE TABLE normalized_topics
(
    id                INT PRIMARY KEY REFERENCES topics(id),
    content           TEXT[]
);