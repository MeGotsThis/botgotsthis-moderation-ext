CREATE TABLE auto_ban_words (
    broadcaster VARCHAR NOT NULL,
    word VARCHAR NOT NULL,
    PRIMARY KEY (broadcaster, word)
);

CREATE TABLE url_whitelist (
    broadcaster VARCHAR NOT NULL,
    urlMatch VARCHAR NOT NULL,
    PRIMARY KEY (broadcaster, urlMatch)
);
