DROP TRIGGER IF EXISTS packages_insert;
CREATE TRIGGER packages_insert
	AFTER INSERT ON packages
	FOR EACH ROW
	BEGIN
		INSERT INTO packages_update
			(action_flag, created, package_id, arch_id, repo_id, pkgname, pkgbase, new_pkgver, new_pkgrel, new_epoch) 
			VALUES (1, strftime('%Y-%m-%d %H:%M:%f', 'now'), NEW.id, NEW.arch_id, NEW.repo_id, NEW.pkgname, NEW.pkgbase, NEW.pkgver, NEW.pkgrel, NEW.epoch);
	END;

DROP TRIGGER IF EXISTS packages_update;
CREATE TRIGGER packages_update
	AFTER UPDATE ON packages
	FOR EACH ROW
	WHEN (OLD.pkgver != NEW.pkgver OR OLD.pkgrel != NEW.pkgrel OR OLD.epoch != NEW.epoch)
	BEGIN
		INSERT INTO packages_update
			(action_flag, created, package_id, arch_id, repo_id, pkgname, pkgbase, old_pkgver, old_pkgrel, old_epoch, new_pkgver, new_pkgrel, new_epoch)
			VALUES (2, strftime('%Y-%m-%d %H:%M:%f', 'now'), NEW.id, NEW.arch_id, NEW.repo_id, NEW.pkgname, NEW.pkgbase, OLD.pkgver, OLD.pkgrel, OLD.epoch, NEW.pkgver, NEW.pkgrel, NEW.epoch);
	END;

DROP TRIGGER IF EXISTS packages_delete;
CREATE TRIGGER packages_delete
	AFTER DELETE ON packages
	FOR EACH ROW
	BEGIN
		INSERT INTO packages_update
			(action_flag, created, arch_id, repo_id, pkgname, pkgbase, old_pkgver, old_pkgrel, old_epoch)
			VALUES (3, strftime('%Y-%m-%d %H:%M:%f', 'now'), OLD.arch_id, OLD.repo_id, OLD.pkgname, OLD.pkgbase, OLD.pkgver, OLD.pkgrel, OLD.epoch);
	END;
