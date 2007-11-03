from django.db import backend, connection, transaction
""" Daily cleanup file
    This purges the session data that is old from the session table.
"""
def clean_up():
    # Clean up old database records
    cursor = connection.cursor()
    cursor.execute("DELETE FROM %s WHERE %s < NOW()" % \
        (backend.quote_name('django_session'), backend.quote_name('expire_date')))
    cursor.execute("OPTIMIZE TABLE %s" % backend.quote_name('django_session'))
    transaction.commit_unless_managed()

if __name__ == "__main__":
    clean_up()
