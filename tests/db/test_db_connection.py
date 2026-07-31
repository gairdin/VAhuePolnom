class TestDbConnection:

    def test_connection_is_open(self, db_conn):
        assert db_conn.closed == 0

    def test_movies_table_exists(self, db_conn):
        cur = db_conn.cursor()
        cur.execute(
            "SELECT EXISTS (SELECT FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name='movies')"
        )
        assert cur.fetchone()[0] is True

    def test_movies_table_has_records(self, db_conn):
        cur = db_conn.cursor()
        cur.execute("SELECT COUNT(*) FROM movies")
        count = cur.fetchone()[0]
        assert count > 0