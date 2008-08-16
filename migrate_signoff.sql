CREATE TABLE `main_signoff` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `pkg_id` integer NOT NULL,
    `pkgver` varchar(255) NOT NULL,
    `pkgrel` varchar(255) NOT NULL,
    `packager_id` integer NOT NULL REFERENCES `auth_user` (`id`)
);
CREATE INDEX main_signoff_pkg_id ON `main_signoff` (`pkg_id`);
CREATE INDEX main_signoff_packager_id ON `main_signoff` (`packager_id`);

