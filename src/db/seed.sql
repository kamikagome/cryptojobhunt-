-- Seed data: SQL-related skills
-- Run this after schema.sql to populate initial skills

INSERT OR IGNORE INTO skills (name, category) VALUES
('SQL', 'SQL'),
('PostgreSQL', 'SQL'),
('MySQL', 'SQL'),
('BigQuery', 'SQL'),
('Snowflake', 'SQL'),
('SQLite', 'SQL'),
('Redshift', 'SQL');
