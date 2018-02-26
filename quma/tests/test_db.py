import pytest

from ..exc import DoesNotExistError
from .. import db, Namespace
from ..mapper import Cursor
from . import pg


def setup_function(function):
    pg.setup_db()


def test_init(conn, sqldirs):
    db.init(conn, sqldirs)
    assert 'addresses' in db.namespaces
    assert 'users' in db.namespaces


def test_namespace(conn, sqldirs):
    db.init(conn, sqldirs)
    assert type(db.addresses) is Namespace
    assert isinstance(db.users, Namespace)


def test_query(conn, sqldirs):
    db.init(conn, sqldirs)
    assert str(db.users.all).startswith('SELECT * FROM users')


def test_cursor(conn, sqldirs):
    db.init(conn, sqldirs)
    with db().cursor as cursor:
        assert type(cursor) is Cursor
        assert len(db.users.all(cursor)) == 4


def test_custom_namespace(conn, sqldirs):
    db.init(conn, sqldirs)
    with db.cursor as cursor:
        assert type(db.users).__module__ == 'quma.mapping.users'
        assert type(db.users).__name__ == 'Users'
        assert db.users.get_hans(cursor) == 'Hans'
        # Test the namespace alias
        assert db.user.get_hans(cursor) == 'Hans'


def test_cursor_call(conn, sqldirs):
    db.init(conn, sqldirs)
    cursor = db.cursor()
    try:
        db.user.add(cursor,
                    name='Anneliese Günthner',
                    email='anneliese.guenthner@example.com')
        cursor.commit()
        db.user.remove(cursor, name='Anneliese Günthner')
        cursor.commit()
    finally:
        cursor.close()


def test_commit(conn, sqldirs):
    db.init(conn, sqldirs)
    cursor = db.cursor()
    with db.cursor as cursor:
        db.user.add(cursor,
                    name='hans',
                    email='hans@example.com')
    with db.cursor as cursor:
        with pytest.raises(DoesNotExistError):
            db.user.by_name.get(cursor, name='hans')

    with db.cursor as cursor:
        db.user.add(cursor,
                    name='hans',
                    email='hans@example.com')
        cursor.commit()

    cursor = db.cursor()
    db.user.by_name.get(cursor, name='hans')
    db.user.remove(cursor, name='hans')
    cursor.commit()
    with pytest.raises(DoesNotExistError):
        db.user.by_name.get(cursor, name='hans')
    cursor.close()
