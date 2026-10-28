-- 1. Create the Director role
CREATE ROLE director WITH LOGIN PASSWORD 'DirectorSecure2026!';

-- 2. Grant schema usage
GRANT USAGE ON SCHEMA public TO director;

-- 3. Grant read-only access to all views and reports
GRANT SELECT ON ALL TABLES IN SCHEMA public TO director;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO director;