import pickle
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
import warnings

warnings.filterwarnings(action = 'ignore')


class Matcher():
    def __init__(self) -> None:
        self.emb_model = self.get_or_train_fast_text()
        self.data_embeddings = self.get_data_embeddings()

    @staticmethod
    def get_or_train_fast_text(path_in: str = "data/clean_last_update_small.csv", model_path:str = "embeddings/word2vec.model"):
        model = Word2Vec.load(model_path)
        return model
    
    @staticmethod
    def get_data_embeddings(path_in: str = "embeddings/w2v_avg_vectors.p"):
        with open(path_in, 'rb') as fp:
            data = pickle.load(fp)
        return data
    
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
         
        # stop_words = set(stopwords.words('english')) 
        lemmatizer = WordNetLemmatizer()
        stemmer = PorterStemmer()
        tokens = word_tokenize(query)
        return [stemmer.stem(lemmatizer.lemmatize(word)) for word in tokens if word.isalpha() or len(tokens) < 2]
    
    def get_embedding_vector(self, query):
        try:
            return np.mean([self.emb_model.wv[word] for word in query], axis=0)
        except KeyError as e:
            print("Words id not in w2v traning corpus.")
        return np.zeros((100, ))
        
    def get_matches(self, query_clean, candidate, use_simple_matching) -> bool|list:
        if use_simple_matching:
            candidate_clean = self.preprocess_query(candidate, use_simple_matching)
            return [q for q in query_clean.split(" ") if q in candidate_clean] if query_clean in candidate_clean else False
        else:
            candidate_clean = r if len(r := self.data_embeddings.get(candidate)) > 0 else self.get_embedding_vector(self.preprocess_query(candidate, False))
            sim = self.cosine_similarity(query_clean, candidate_clean)
            return [sim] if sim > 0.65 or sim < -0.65 else False
    