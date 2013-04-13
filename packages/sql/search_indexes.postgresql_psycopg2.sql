CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX packages_pkgname_trgm_gist ON packages USING gist (UPPER(pkgname) gist_trgm_ops);
CREATE INDEX packages_pkgdesc_trgm_gist ON packages USING gist (UPPER(pkgdesc) gist_trgm_ops);
