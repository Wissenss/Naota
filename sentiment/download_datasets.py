import nltk

def download_datasets():
  nltk.download("stopwords")
  nltk.download("punkt")
  nltk.download("wordnet")
  nltk.download('vader_lexicon')

if __name__ == "__main__":
  download_datasets()