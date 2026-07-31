import psycopg2
import os
from typing import Any


class DbClient:
    def __init__(self, dsn: str | None = None):
        dsn = dsn or os.getenv("DATABASE_URL")
        if not dsn:
            raise ValueError("DATABASE_URL not set")
        self.conn = psycopg2.connect(dsn=dsn)

    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()

    def fetch_one(self, query: str, params: tuple = ()) -> tuple | None:
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()

    def fetch_all(self, query: str, params: tuple = ()) -> list[tuple]:
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def get_movie_by_id(self, movie_id: int) -> tuple | None:
        return self.fetch_one(
            "SELECT id, name, price, location, genre_id FROM movies WHERE id = %s",
            (movie_id,)
        )

    def get_movies_count(self) -> int:
        row = self.fetch_one("SELECT COUNT(*) FROM movies")
        return row[0] if row else 0

    def get_genre_by_id(self, genre_id: int) -> tuple | None:
        return self.fetch_one("SELECT id, name FROM genres WHERE id = %s", (genre_id,))

    def get_movies_by_location(self, location: str) -> list[tuple]:
        return self.fetch_all(
            "SELECT id, name, location FROM movies WHERE location = %s",
            (location,)
        )

    def movie_exists_by_name(self, name: str) -> bool:
        row = self.fetch_one("SELECT 1 FROM movies WHERE name = %s", (name,))
        return row is not None