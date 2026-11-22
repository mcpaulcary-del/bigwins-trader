-- BF-D52: the dashboard's SELECT-only role (run by the db-roles service at every start;
-- idempotent; also for a journal that existed before). psql variables: db, pw.
SELECT 'CREATE ROLE bigwins_dashboard LOGIN'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bigwins_dashboard') \gexec
ALTER ROLE bigwins_dashboard WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD :'pw';
ALTER ROLE bigwins_dashboard SET default_transaction_read_only = on;
GRANT CONNECT ON DATABASE :"db" TO bigwins_dashboard;
GRANT USAGE ON SCHEMA public TO bigwins_dashboard;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM bigwins_dashboard;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM bigwins_dashboard;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO bigwins_dashboard;
-- tables the trader creates later (new journal tables) are readable too, never writable
ALTER DEFAULT PRIVILEGES FOR ROLE trader IN SCHEMA public GRANT SELECT ON TABLES TO bigwins_dashboard;
