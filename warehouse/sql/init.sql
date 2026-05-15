CREATE TABLE IF NOT EXISTS articles (
    id VARCHAR(64) PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    author VARCHAR(255),
    published_at TIMESTAMP,
    category VARCHAR(100),
    source VARCHAR(100),
    language VARCHAR(10),
    country VARCHAR(10),
    word_count INTEGER,
    scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS articles_per_source (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    source VARCHAR(100) NOT NULL,
    count INTEGER DEFAULT 0,
    UNIQUE(date, source)
);

CREATE TABLE IF NOT EXISTS top_keywords (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    keyword VARCHAR(200) NOT NULL,
    frequency INTEGER DEFAULT 0,
    UNIQUE(date, keyword)
);

CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at);
