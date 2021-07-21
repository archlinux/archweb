# Roles
STAFF_ROLE = 'Staff'
DEVOPS_ROLE = 'DevOps'

# Groups
OIDC_TRUSTEDUSER_GROUP       = '/Arch Linux Staff/Trusted Users'
OIDC_DEVELOPER_GROUP         = '/Arch Linux Staff/Developers'
OIDC_MIRRORMAINTAINER_GROUP  = '/Arch Linux Staff/Archweb/Mirrorlist Maintainers'
OIDC_RELEASEMAINTAINER_GROUP = '/Arch Linux Staff/Archweb/Release Maintainers'
OIDC_DEVOPS_GROUP            = '/Arch Linux Staff/DevOps'
OIDC_TESTERS_GROUP           = '/External Contributors/Archweb/Testers'
OIDC_SUPPORTSTAFF_GROUPS     = ['/Arch Linux Staff/Bug Wranglers',
                           '/Arch Linux Staff/Forum/Admins',
                           '/Arch Linux Staff/Forum/Mods',
                           '/Arch Linux Staff/IRC/Ops',
                           '/Arch Linux Staff/Wiki/Admins',
                           '/Arch Linux Staff/Security Team/Admins',
                           '/Arch Linux Staff/Security Team/Members']


# TODO: Release Maintainers
OIDC_GROUP_MAPPING = {
    OIDC_DEVELOPER_GROUP: 'Developers',
    OIDC_TRUSTEDUSER_GROUP: 'Trusted Users',
    OIDC_MIRRORMAINTAINER_GROUP: 'Mirror Maintainers',
    OIDC_TESTERS_GROUP: 'Testers'
}

# Dynamically add all Support Staff groups
for key in OIDC_SUPPORTSTAFF_GROUPS:
    OIDC_GROUP_MAPPING[key] = 'Support Staff'
