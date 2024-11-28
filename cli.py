import keyboard
import sys

key = sys.argv[1]

if key == "space":
  print("pressing space")

  keyboard.press_and_release("space")

# import settings
# import connectionPool
# import csv

# #source_csv = "./test.csv"
# source_csv = "./lichess_db_puzzle.csv"

# conn = connectionPool.get_connection()

# try:
#   curs = conn.cursor()

#   with open(source_csv, "r") as file:
#     csv_file = csv.reader(file)

#     is_header = True

#     for lines in csv_file:
#       if is_header:
#         is_header = False
#         continue

#       lichess_puzzle_id = lines[0]
#       fen = lines[1]
#       moves = lines[2]
#       rating = lines[3]
#       rating_deviation = lines[4]
#       popularity = lines[5]
#       nb_plays = lines[6]
#       themes = lines[7]
#       game_url = lines[8]
#       opening_tags = lines[9]

#       params = [
#         lichess_puzzle_id,
#         fen,
#         moves,
#         rating,
#         rating_deviation,
#         popularity,
#         nb_plays,
#         themes,
#         game_url, 
#         opening_tags,
#         0,
#         len(moves.split(" "))
#       ]

#       print(f"processsing line {csv_file.line_num}...")

#       curs.execute("INSERT INTO puzzles(lichess_puzzle_id, fen, moves, rating, rating_deviation, popularity, nb_plays, themes, game_url, opening_tags, status, no_moves) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", params)

#     conn.commit()

# except Exception as e:
#   print(f"unhandled exception: {repr(e)}")

# finally:
#   connectionPool.release_connection(conn)
