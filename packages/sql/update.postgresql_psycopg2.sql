CREATE OR REPLACE FUNCTION packages_on_insert() RETURNS trigger AS $body$
BEGIN
	INSERT INTO packages_update
		(action_flag, created, package_id, arch_id, repo_id, pkgname, pkgbase, new_pkgver, new_pkgrel, new_epoch) 
		VALUES (1, now(), NEW.id, NEW.arch_id, NEW.repo_id, NEW.pkgname, NEW.pkgbase, NEW.pkgver, NEW.pkgrel, NEW.epoch);
	RETURN NULL;
END;
$body$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION packages_on_update() RETURNS trigger AS $body$
BEGIN
	INSERT INTO packages_update
		(action_flag, created, package_id, arch_id, repo_id, pkgname, pkgbase, old_pkgver, old_pkgrel, old_epoch, new_pkgver, new_pkgrel, new_epoch)
		VALUES (2, now(), NEW.id, NEW.arch_id, NEW.repo_id, NEW.pkgname, NEW.pkgbase, OLD.pkgver, OLD.pkgrel, OLD.epoch, NEW.pkgver, NEW.pkgrel, NEW.epoch);
	RETURN NULL;
END;
$body$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION packages_on_delete() RETURNS trigger AS $body$
BEGIN
	INSERT INTO packages_update
		(action_flag, created, arch_id, repo_id, pkgname, pkgbase, old_pkgver, old_pkgrel, old_epoch)
		VALUES (3, now(), OLD.arch_id, OLD.repo_id, OLD.pkgname, OLD.pkgbase, OLD.pkgver, OLD.pkgrel, OLD.epoch);
	RETURN NULL;
END;
$body$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS packages_insert ON packages;
CREATE TRIGGER packages_insert
	AFTER INSERT ON packages
	FOR EACH ROW
	EXECUTE PROCEDURE packages_on_insert();

DROP TRIGGER IF EXISTS packages_update ON packages;
CREATE TRIGGER packages_update
	AFTER UPDATE ON packages
	FOR EACH ROW
	WHEN (OLD.pkgver != NEW.pkgver OR OLD.pkgrel != NEW.pkgrel OR OLD.epoch != NEW.epoch)
	EXECUTE PROCEDURE packages_on_update();

DROP TRIGGER IF EXISTS packages_delete ON packages;
CREATE TRIGGER packages_delete
	AFTER DELETE ON packages
	FOR EACH ROW
	EXECUTE PROCEDURE packages_on_delete();
