from django.core.exceptions import MiddlewareNotUsed
from django.db import connections


class AlwaysCommitMiddleware(object):
    """
    Ensure we always commit any possibly open transaction so we leave the
    database in a clean state. Without this, pgbouncer et al. always gives
    error messages like this for every single request:

    LOG S-0x1accfd0: db/user@unix:5432 new connection to server
    LOG C-0x1aaf620: db/user@unix:6432 closing because: client close request (age=0)
    LOG S-0x1accfd0: db/user@unix:5432 closing because: unclean server (age=0)

    We only let this middleware apply for PostgreSQL backends; other databases
    don't really require connection pooling and thus the reason for this
    middleware's use is non-existent.

    The best location of this in your middleware stack is likely the top, as
    you want to ensure it happens after any and all database activity has
    completed.
    """
    def __init__(self):
        for conn in connections.all():
            if conn.vendor == 'postgresql':
                return
        raise MiddlewareNotUsed()

    def process_response(self, request, response):
        """Commits any potentially open transactions at the underlying
        PostgreSQL database connection level."""
        for conn in connections.all():
            if conn.vendor != 'postgresql':
                continue
            db_conn = getattr(conn, 'connection', None)
            if db_conn is not None:
                db_conn.commit()
        return response

# vim: set ts=4 sw=4 et:
