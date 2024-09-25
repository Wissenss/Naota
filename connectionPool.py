import sqlite3
import settings

POOL_SIZE = 10

__pool__ = []
__pool_available__ = []
__pool_occupied__ = []

def __create_connection() -> sqlite3.Connection:
  connection = sqlite3.connect(settings.DB_FILE_PATH)

  return connection

def init_connection_pool(size = POOL_SIZE):
  
  for _ in range(POOL_SIZE):
    __pool__.append(__create_connection())

def get_connection() -> sqlite3.Connection:
  if len(__pool_available__) == 0:
    connection = __create_connection()
    __pool__.append(connection)
    __pool_available__.append(connection)
  
  connection = __pool_available__.pop()
  
  __pool_occupied__.append(connection)

  return connection

def release_connection(connection : sqlite3.Connection):
  __pool_occupied__.remove(connection)
  __pool_available__.append(connection)

if __name__ == "__main__":
  init_connection_pool()

  conn = get_connection()

  a = conn.execute("SELECT * FROM watchlist_items;")

  print(a.fetchall())