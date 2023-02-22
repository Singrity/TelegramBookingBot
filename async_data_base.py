import aiosqlite
import asyncio
from asyncio import new_event_loop, set_event_loop
from aiosqlite import Error

set_event_loop(new_event_loop())



sql_create_users_table = """ CREATE TABLE IF NOT EXISTS users (
                                        id INTEGER NOT NULL PRIMARY KEY,
                                        username TEXT,
                                        real_name TEXT,
                                        phone TEXT
                                    ); """
sql_create_booking_table = """CREATE TABLE IF NOT EXISTS booking(
    id INTEGER NOT NULL PRIMARY KEY,
    booking_type TEXT,
    amount INTEGER,
    booking_date TEXT,
    booking_time TEXT,
    duration TEXT,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);"""


async def create_user(conn, user):
    """
    Create a new project into the projects table
    :param conn:
    :param user:
    :return: user id
    """
    sql = ''' INSERT INTO users(id, username, real_name, phone)
              VALUES(?,?,?,?) '''
    cur = await conn.cursor()
    await cur.execute(sql, user)
    #await conn.commit()
    return cur.lastrowid


async def create_booking(conn, booking):
    """
    Create a new project into the projects table
    :param conn:
    :param booking:
    :return: booking id
    """
    sql = ''' INSERT INTO booking(booking_type, amount, booking_date, booking_time, duration, user_id)
              VALUES(?,?,?,?,?,?) '''
    cur = await conn.cursor()
    await cur.execute(sql, booking)
    #await conn.commit()
    return cur.lastrowid


async def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = await conn.cursor()
        await c.execute(create_table_sql)
    except Error as e:
        print(e)


async def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = await aiosqlite.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


async def show_bookings_from(conn, user_id):
    """
    shows all bookings of a user
    :param conn:
    :param user_id:
    :return:
    """
    cur = await conn.cursor()
    await cur.execute(f"SELECT real_name, phone, booking_type, amount, booking_date, duration FROM booking LEFT JOIN users ON booking.user_id = {user_id}")

    async for row in cur:
        print(row)


async def exist_in_users(conn, param):
    """
    Checs if value exists in users
    :param conn:
    :param param:
    :return: True or False
    """
    cur = await conn.cursor()
    await cur.execute("SELECT id FROM users")

    async for row in cur:
        if param == row[0]:
            return True
        else:
            return False


async def update_user(conn, user):
    """
    update name and phone
    :param conn:
    :param user:
    :return: user id
    """
    sql = '''
        UPDATE users
            SET real_name = ?,
                phone = ?
            WHERE id = ?
    '''
    cur = await conn.cursor()
    await cur.execute(sql, user)
    #await conn.commit()


async def delete_booking_by_id(conn, id):
    """
    Deleting booking by id
    :param conn:
    :param id:
    :return:
    """
    sql = 'DELETE FROM booking WHERE id = ?'
    cur = await conn.cursor()
    await cur.execute(sql, (id,))
    await conn.commit()


async def delete_booking_by_user_id(conn, id):
    """
    Deleting all bookings by user id
    :param conn:
    :param id:
    :return:
    """
    sql = 'DELETE FROM booking WHERE user_id = ?'
    cur = await conn.cursor()
    await cur.execute(sql, (id,))
    await conn.commit()


async def delete_all_bookings(conn):
    """
    Delete all rows in the booking table
    :param conn:
    :return:
    """
    sql = 'DELETE FROM booking'
    cur = await conn.cursor()
    await cur.execute(sql)
    await conn.commit()








