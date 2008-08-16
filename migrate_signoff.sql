CREATE TABLE `main_signoff` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `pkg_id` integer NOT NULL,
    `pkgver` varchar(255) NOT NULL,
    `pkgrel` varchar(255) NOT NULL
);
CREATE TABLE `main_signoff_signed_off` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `signoff_id` integer NOT NULL REFERENCES `main_signoff` (`id`),
    `user_id` integer NOT NULL REFERENCES `auth_user` (`id`),
    UNIQUE (`signoff_id`, `user_id`)
);
CREATE INDEX main_signoff_pkg_id ON `main_signoff` (`pkg_id`);

