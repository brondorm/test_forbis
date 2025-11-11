"""Database module for storing users, activities, bookings, and polls."""
import aiosqlite
from typing import List, Dict, Optional
from datetime import datetime
import json


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init_db(self):
        """Initialize database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_admin INTEGER DEFAULT 0,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Activities table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    date_time TEXT,
                    max_capacity INTEGER DEFAULT 50,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Bookings table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    activity_id INTEGER,
                    booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (activity_id) REFERENCES activities(activity_id),
                    UNIQUE(user_id, activity_id)
                )
            """)

            # Polls table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS polls (
                    poll_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    options TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Poll votes table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS poll_votes (
                    vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    poll_id INTEGER,
                    user_id INTEGER,
                    option_index INTEGER,
                    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (poll_id) REFERENCES polls(poll_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(poll_id, user_id)
                )
            """)

            await db.commit()

    # User methods
    async def add_user(self, user_id: int, username: str = None,
                       first_name: str = None, last_name: str = None, is_admin: bool = False):
        """Add or update user."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, is_admin)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, first_name, last_name, int(is_admin)))
            await db.commit()

    async def get_all_users(self) -> List[Dict]:
        """Get all registered users."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    # Activity methods
    async def add_activity(self, name: str, description: str = "",
                          date_time: str = "", max_capacity: int = 50) -> int:
        """Add new activity."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO activities (name, description, date_time, max_capacity)
                VALUES (?, ?, ?, ?)
            """, (name, description, date_time, max_capacity))
            await db.commit()
            return cursor.lastrowid

    async def get_activities(self, active_only: bool = True) -> List[Dict]:
        """Get all activities."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM activities"
            if active_only:
                query += " WHERE is_active = 1"
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_activity(self, activity_id: int) -> Optional[Dict]:
        """Get single activity."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM activities WHERE activity_id = ?", (activity_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    # Booking methods
    async def create_booking(self, user_id: int, activity_id: int) -> bool:
        """Create a booking if capacity allows."""
        async with aiosqlite.connect(self.db_path) as db:
            # Check current bookings count
            async with db.execute("""
                SELECT COUNT(*) as count FROM bookings WHERE activity_id = ?
            """, (activity_id,)) as cursor:
                row = await cursor.fetchone()
                current_count = row[0]

            # Check max capacity
            async with db.execute("""
                SELECT max_capacity FROM activities WHERE activity_id = ?
            """, (activity_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return False
                max_capacity = row[0]

            if current_count >= max_capacity:
                return False

            # Create booking
            try:
                await db.execute("""
                    INSERT INTO bookings (user_id, activity_id)
                    VALUES (?, ?)
                """, (user_id, activity_id))
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                # Already booked
                return False

    async def cancel_booking(self, user_id: int, activity_id: int) -> bool:
        """Cancel a booking."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                DELETE FROM bookings WHERE user_id = ? AND activity_id = ?
            """, (user_id, activity_id))
            await db.commit()
            return cursor.rowcount > 0

    async def get_user_bookings(self, user_id: int) -> List[Dict]:
        """Get all bookings for a user."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT b.*, a.name, a.description, a.date_time
                FROM bookings b
                JOIN activities a ON b.activity_id = a.activity_id
                WHERE b.user_id = ?
            """, (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_activity_bookings(self, activity_id: int) -> List[Dict]:
        """Get all bookings for an activity."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT b.*, u.username, u.first_name, u.last_name
                FROM bookings b
                JOIN users u ON b.user_id = u.user_id
                WHERE b.activity_id = ?
            """, (activity_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_booking_count(self, activity_id: int) -> int:
        """Get booking count for an activity."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT COUNT(*) FROM bookings WHERE activity_id = ?
            """, (activity_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0]

    async def is_user_booked(self, user_id: int, activity_id: int) -> bool:
        """Check if user has booked an activity."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT 1 FROM bookings WHERE user_id = ? AND activity_id = ?
            """, (user_id, activity_id)) as cursor:
                row = await cursor.fetchone()
                return row is not None

    # Poll methods
    async def create_poll(self, question: str, options: List[str]) -> int:
        """Create a new poll."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO polls (question, options)
                VALUES (?, ?)
            """, (question, json.dumps(options)))
            await db.commit()
            return cursor.lastrowid

    async def get_active_polls(self) -> List[Dict]:
        """Get all active polls."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM polls WHERE is_active = 1
            """) as cursor:
                rows = await cursor.fetchall()
                polls = []
                for row in rows:
                    poll_dict = dict(row)
                    poll_dict['options'] = json.loads(poll_dict['options'])
                    polls.append(poll_dict)
                return polls

    async def get_poll(self, poll_id: int) -> Optional[Dict]:
        """Get single poll."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM polls WHERE poll_id = ?
            """, (poll_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    poll_dict = dict(row)
                    poll_dict['options'] = json.loads(poll_dict['options'])
                    return poll_dict
                return None

    async def vote_poll(self, poll_id: int, user_id: int, option_index: int) -> bool:
        """Vote in a poll."""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute("""
                    INSERT INTO poll_votes (poll_id, user_id, option_index)
                    VALUES (?, ?, ?)
                """, (poll_id, user_id, option_index))
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def get_poll_results(self, poll_id: int) -> Dict[int, int]:
        """Get poll results (option_index -> vote count)."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT option_index, COUNT(*) as count
                FROM poll_votes
                WHERE poll_id = ?
                GROUP BY option_index
            """, (poll_id,)) as cursor:
                rows = await cursor.fetchall()
                return {row[0]: row[1] for row in rows}

    async def close_poll(self, poll_id: int):
        """Close a poll."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE polls SET is_active = 0 WHERE poll_id = ?
            """, (poll_id,))
            await db.commit()
