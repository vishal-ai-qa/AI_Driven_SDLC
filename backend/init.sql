-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Full-text search configuration
CREATE TEXT SEARCH CONFIGURATION IF NOT EXISTS english_unaccent (COPY = english);
