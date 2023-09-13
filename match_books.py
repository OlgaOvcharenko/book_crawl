from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize
import pandas as pd
import numpy as np
from numpy import dot
from numpy.linalg import norm
from gensim.models import Word2Vec


class Matcher():
    def __init__(self) -> None:
        self.emb_model = self.get_or_train_fast_text()
        self.data_embeddings = self.get_data_embeddings()

    @staticmethod
    def get_or_train_fast_text(path_in: str = "data/clean_last_update_small.csv", model_path:str = "embeddings/word2vec.model"):
        model = Word2Vec.load(model_path)
        return model
    
    @staticmethod
    def get_data_embeddings(path_in: str = "data/clean_last_update_small.csv"):
        return pd.read_csv(path_in)
    
    @staticmethod
    def jaccard_distance(set1:set, set2:set):
        symm_diff = set1.symmetric_difference(set2)
        union = set1.union(set2)
        return len(symm_diff)/len(union)
    
    @staticmethod
    def cosine_similarity(a, b):
        return np.dot(a, b)/(norm(a) * norm(b))
    
    @staticmethod
    def euclidian_dist(a, b):
        return np.linalg.norm(a - b)
    
    def preprocess_query(self, query: str, only_lower: bool): 
        if only_lower:
            return query.lower()
         
        stop_words = set(stopwords.words('english')) 
        lemmatizer = WordNetLemmatizer()
        stemmer = PorterStemmer()

        words = []    
        tokens = word_tokenize(query)
        for word in tokens:
            # not word in stop_words
            if word.isalpha() or len(tokens) < 2:
                words.append(stemmer.stem(lemmatizer.lemmatize(word)))
        return words
    
    def get_embedding_vector(self, query):
        vec = []
        for word in query:
            vec.append(self.emb_model.wv[word])
        return np.mean(vec, axis=0)
        
    def get_matches_emb(self, query: str, candidate: list) -> bool|list:
        a = self.get_embedding_vector(self.preprocess_query(query, False))
        b = self.get_embedding_vector(self.preprocess_query(candidate, False))
        sim = self.cosine_similarity(a, b)
        return [sim] if sim > 0.8 or sim < -0.8 else False
  
    def get_matches(self, query, candidate) -> bool|list:
        return [q for q in query.split(" ")if q in candidate] if query in candidate else False
    