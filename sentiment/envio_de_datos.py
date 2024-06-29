# Ejemplo de como funcionaria
from sentiment_analysis import process_youtube_comments

youtube_video_url = "https://www.youtube.com/watch?v=GwgNS23SiXM"
category = ['emperor', 'love', 'best']
filtered_df = process_youtube_comments(youtube_video_url, category)
print(filtered_df) 