"""  data models  """  
class GuildStorage:
  def __init__(self, guild_id):
    self.guild_id = guild_id
    self.playing_video = None
    self.queue = SongQueue()

    self.isAutoPlay = False
    self.autoPlayExclusions = [] # we exclude previously played videos
    self.autoPlayInclusions = [] # we include a list of tags or categories

    self.sound_stream = None

class SongQueue(list):
  def __init__(self):
    super().__init__()

  def append(self, video_id : str, video_title : str) -> None:
    video_info = {
      "video_id" : video_id,
      "video_title" : video_title
    }
    
    super().append(video_info)

  def get_video_id(self, index : int):
    return super().__getitem__(index)["video_id"]

  def get_video_title(self, index : int):
    return super().__getitem__(index)["video_title"]

  # def get_video_title(self, video_id : str):
  #   for item in super().items:
  #     if item["video_id"] == video_id:
  #       return item["video_title"]

"""  private stuff  """
__storage = {}


"""  public interface  """
def get_storage_keys():
  return list(__storage.keys())

def get_storage(guild_id) -> GuildStorage:
  if guild_id not in __storage:
    __storage[guild_id] = GuildStorage(guild_id)

  return __storage[guild_id]

#################### TESTS #################### 
if __name__ == "__main__":

  """  SONG QUEUE  """  
  print("TESTING \"SongQueue\" OBJECT")
  print("\nconstructor")
  song_queue = SongQueue()
  print(song_queue)

  print("\nappend")
  song_queue.append("4eqEc-qV89s", "Some random video...")
  song_queue.append("ere2Mstl8ww", "Little Monster - Royal Blood")
  print(song_queue)

  print("\nget_video_id")
  video_id_0 = song_queue.get_video_id(0)
  print(f"video id at index 0: {video_id_0}")

  print("\nget_video_title")
  video_title_1 = song_queue.get_video_title(1)
  print(f"video title at index 1: {video_title_1}")

  # video_title_id = SongQueue.get_video_title("4eqEc-qV89s") //fail. Pending: check how to overload in python
  # print(f"video title with id 4eqEc-qV89s: {video_title_id}")

  print("\npop")
  popped_item = song_queue.pop(0)
  print(f"popped item: {popped_item}")
  print(f"song_queue: {song_queue}")
  
  """  GUILD STORAGE  """
  print("\n\nTESTING \"GuildStorage\" OBJECT")
  guild = GuildStorage("1178465444701687878")
  print("\nproperties")
  guild.queue.append("DcHKOC64KnE", "Go with the flow - Queens of the stone age")
  print(f"guild id: {guild.guild_id}")
  print(f"guild song queue: {guild.queue}")

  """  PUBLIC INTERFACE  """
  print("\n\nTESTING PUBLIC INTERFACE FUNCTIONS")
  print("\nget_storage")
  storage_1 = get_storage("1178465444701687878")
  storage_1.queue.append("DcHKOC64KnE", "Go with the flow - Queens of the stone age")
  storage_1.queue.append("ere2Mstl8ww", "Little Monster - Royal Blood")
  print(f"storage: {storage_1}")
  print(f"storage.guild_id: {storage_1.guild_id}")
  print(f"storage.queue: {storage_1.queue}")

  print("\nget_storage_keys")
  storage_2 = get_storage("638943159581147137")
  storage_keys = get_storage_keys()
  print(f"storage keys: {storage_keys}")
