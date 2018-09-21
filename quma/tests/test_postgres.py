from unittest.mock import Mock

import psycopg2
import pytest

from . import util
from ..exc import (
    DoesNotExistError,
    FetchError,
    MultipleRecordsError,
)
from ..mapper import Cursor
from ..provider.postgresql import Connection


def setup_function(function):
    util.setup_pg_db()


@pytest.mark.postgres
def test_cursor(pgdb):
    with pgdb().cursor as cursor:
        assert type(cursor) is Cursor
        assert len(pgdb.users.all(cursor)) == 4


@pytest.mark.postgres
def test_cursor_call(pgdb):
    cursor = pgdb.cursor()
    try:
        pgdb.user.add(cursor,
                      name='Test User',
                      email='test.user@example.com',
                      city='Test City')
        cursor.commit()
        pgdb.user.remove(cursor, name='Test User')
        cursor.commit()
    finally:
        cursor.close()


@pytest.mark.postgres
def test_conn_attr(pgdb):
    with pgdb.cursor as c:
        assert c.raw_conn.autocommit is False
        assert c.get_conn_attr('autocommit') is c.raw_conn.autocommit
        c.set_conn_attr('autocommit', True)
        assert c.raw_conn.autocommit is True
        assert c.get_conn_attr('autocommit') is c.raw_conn.autocommit
        pgdb.user.add(c,
                      name='Test User',
                      email='test.user@example.com',
                      city='Test City')
        # no explicit commit
    with pgdb.cursor as cursor:
        assert cursor.get_conn_attr('autocommit') is False
        user = pgdb.user.by_name.get(cursor, name='Test User')
    assert user.email == 'test.user@example.com'


@pytest.mark.postgres
def test_rollback(pgdb):
    cursor = pgdb.cursor()
    pgdb.user.add(cursor,
                  name='Test User',
                  email='test.user@example.com',
                  city='Test City')
    pgdb.user.by_name.get(cursor, name='Test User')
    cursor.rollback()
    with pytest.raises(DoesNotExistError):
        pgdb.user.by_name.get(cursor, name='Test User')
    cursor.close()


@pytest.mark.postgres
def test_changeling_cursor(pgdb):
    with pgdb.cursor as cursor:
        user = pgdb.user.by_name.get(cursor, name='User 3')
        assert user[0] == 'user.3@example.com'
        assert user['email'] == 'user.3@example.com'
        assert user.email == 'user.3@example.com'
        user.email = 'test@example.com'
        assert user.email == 'test@example.com'
        with pytest.raises(AttributeError):
            user.wrong_attr
        assert 'email' in user.keys()


@pytest.mark.postgres
def test_no_changeling_cursor(pgdb_persist):
    # pgdb_persist does not use the changeling factory
    with pgdb_persist.cursor as cursor:
        user = pgdb_persist.user.by_name.get(cursor, name='User 3')
        assert user[0] == 'user.3@example.com'
        assert user['email'] == 'user.3@example.com'
        with pytest.raises(AttributeError):
            user.email
        cursor.rollback()


@pytest.mark.postgres
def test_multiple_records(pgdb):
    with pgdb.cursor as cursor:
        users = pgdb.users.by_city(cursor, city='City A')
        assert len(users) == 2
        for user in users:
            assert user.name in ('User 1', 'User 2')


@pytest.mark.postgres
def test_multiple_records_error(pgdb):
    with pgdb.cursor as cursor:
        with pytest.raises(MultipleRecordsError):
            pgdb.user.by_city.get(cursor, city='City A')


@pytest.mark.postgres
def test_faulty_fetch(dburl):
    cursor = type('C', (), {})
    cn = Connection(dburl)

    def fetch():
        raise psycopg2.ProgrammingError('test error')

    cursor.fetchall = fetch
    cursor.fetchmany = fetch
    with pytest.raises(FetchError) as e:
        cn.get_cursor_attr(cursor, 'fetchall')()
    assert str(e.value.error) == 'test error'
    with pytest.raises(FetchError) as e:
        cn.get_cursor_attr(cursor, 'fetchmany')()


@pytest.mark.postgres
def test_get_cursor_attr(pgdb):
    conn = pgdb.conn
    cursor = Mock
    cursor.fetchall = Mock()
    cursor.fetchall.side_effect = psycopg2.ProgrammingError(
        'no results to fetch')
    assert conn.get_cursor_attr(cursor, 'fetchall')() == ()
    cursor.fetchall.side_effect = psycopg2.ProgrammingError('test')
    with pytest.raises(FetchError) as e:
        conn.get_cursor_attr(cursor, 'fetchall')()
    assert str(e.value.error) == 'test'

    # Test Query._fetch except
    with pgdb.cursor as cursor:
        cursor.raw_cursor.fetchall = Mock()
        cursor.raw_cursor.fetchall.side_effect = FetchError(
                psycopg2.ProgrammingError('pg-exc-test'))
        with pytest.raises(psycopg2.ProgrammingError) as e:
            pgdb.users.all(cursor)
        assert str(e.value) == 'pg-exc-test'


@pytest.mark.postgres
def test_many(pgdb):
    with pgdb.cursor as cursor:
        users = pgdb.users.all.many(cursor, 2)
        assert len(users) == 2
        users = pgdb.users.all.next(cursor, 1)
        assert len(users) == 1
        users = pgdb.users.all.next(cursor, 1)
        assert len(users) == 1
        users = pgdb.users.all.next(cursor, 1)
        assert len(users) == 0


@pytest.mark.postgres
def test_many_default(pgdb):
    with pgdb.cursor as cursor:
        users = pgdb.users.all.many(cursor)
        assert len(users) == 1
        users = pgdb.users.all.next(cursor)
        assert len(users) == 1

        users = pgdb.users.all.many(cursor, 2, test='test')
        assert len(users) == 2
        users = pgdb.users.all.next(cursor, 2)
        assert len(users) == 2

        users = pgdb.users.all.many(cursor, test='test', size=2)
        assert len(users) == 2
        users = pgdb.users.all.next(cursor, size=2)
        assert len(users) == 2

        users = pgdb.users.all.many(cursor, 2, 'test')
        assert len(users) == 2
        users = pgdb.users.all.next(cursor)
        assert len(users) == 1
