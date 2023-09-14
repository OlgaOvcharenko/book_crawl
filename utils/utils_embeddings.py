from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize
import pandas as pd
import numpy as np
import gensim
from gensim.models import Word2Vec
import pickle
import warnings
 
warnings.filterwarnings(action = 'ignore')

 
def generate__store_embeddings(data, cols: list, path_out: str):
    model = gensim.models.Word2Vec(data[cols[0]], seed=0, workers=1, sg=0, min_count=1)
    [model.train(data[c], total_examples=data[c].shape[0], epochs=model.epochs) for c in cols[1:]]
    model.save(path_out)


def preprocess(data: pd.DataFrame):    
    stop_words = set(stopwords.words('english')) 
    lemmatizer = WordNetLemmatizer()
    stemmer = PorterStemmer()

    names, descriptions = [], []
    for _, doc in data.iterrows():
        row_name = doc["name"].lower()
        row_desc = doc["description"].lower()

        name_t, desc_t = [], []
        tokens = word_tokenize(row_name)
        for word in tokens:
            # not word in stop_words
            if word.isalpha() or len(tokens) < 2:
                name_t.append(stemmer.stem(lemmatizer.lemmatize(word)))

        if len(name_t) < 1:
            print(name_t)
            print(row_name)

        names.append(name_t)
        
        for word in word_tokenize(row_desc):
            if not word in stop_words and word.isalpha():
                desc_t.append(stemmer.stem(lemmatizer.lemmatize(word)))    
        descriptions.append(' '.join(desc_t))
    data["name_clean"] = names
    data["description_clean"] = descriptions

    return data

def avg_book_embedings(model, data, col: str):
    vectors = []

    for _, doc in data.iterrows():
        vec = []
        for word in doc[col]:
            vec.append(model.wv[word])
        vectors.append(np.array(np.mean(vec, axis=0)))
    
    return vectors

def main ():
    # Preprocess data
    in_data = pd.read_csv("../data/last_update_small.csv")
    in_data.fillna(inplace=True, value="")
    res = preprocess(in_data)
    res.to_csv("data/clean_last_update_small.csv", index=False)

    # Generate embeddings
    model_path, avg_book_vec = "../embeddings/word2vec.model", 'embeddings/w2v_avg_vectors.p'
    generate__store_embeddings(res, ["name_clean"], model_path)

    # Embedd book names
    model = Word2Vec.load(model_path)
    emb = avg_book_embedings(model, res, "name_clean")

    emb_dict = {res["name"].iloc[i].lower(): emb[i] for i in range(len(emb))}
    with open(avg_book_vec, 'wb') as fp:
        pickle.dump(emb_dict, fp, protocol=pickle.HIGHEST_PROTOCOL)
    
if __name__ == "__main__":
    main()
