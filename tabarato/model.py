from .loader import Loader
from .transform.transformer import Transformer
from .utils.string_utils import get_words
import time
from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor
from gensim.models import Word2Vec, Phrases
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.models.word2vec import LineSentence
from gensim.models.phrases import Phraser
from gensim.test.utils import get_tmpfile
import nltk
from nltk.corpus import stopwords
import pandas as pd

nltk.download("stopwords")

class Model:
    PORTUGUESE_STOPWORDS = set(stopwords.words("portuguese"))

    @classmethod
    def train_model(cls) -> str:
        df = Loader.read("silver")

        titles = df["name_without_brand"].dropna().unique().tolist()

        cls._train_model(titles)

    @classmethod
    def _train_model(cls, titles: list) -> None:
        start = time.time()
        print("-" * 20)
        print("Iniciando treinamento do Word2Vec...")
        phrased_titles, phraser = cls._detect_phrases(titles)
        processed_titles = [
            [word for word in title] 
            for title in phrased_titles
        ]

        w2v = Word2Vec(
            sentences=processed_titles,
            vector_size=150,
            alpha=1e-3,
            window=5,
            min_count=3,  # IGNORES WORD WITH FREQUENCY BELLOW
            workers=cpu_count() * 2,
            sg=1,  # 0 CBOW, 1 SKIP_GRAM
            cbow_mean=0,  # 0 SUM, 1 MEAN
            hs=0,  # 1 HIERARQUICAL SOFTMAX, 0 NEGATIVE
            negative=10,
            sample=1e-5,
            epochs=50,
        )
        w2v.phraser = phraser

        w2v.save("data/model/w2v.model")
        word_vectors = w2v.wv
        fname = get_tmpfile("w2v.vectors.kv")
        word_vectors.save(fname)
        print(f"Treinamento Word2Vec demorou: {round(time.time() - start, 2)}")

        def similarity(a, b):
            tokens1 = [word for word in get_words(a.lower()) if word not in cls.PORTUGUESE_STOPWORDS]
            tokens2 = [word for word in get_words(b.lower()) if word not in cls.PORTUGUESE_STOPWORDS]
            return w2v.wv.n_similarity(w2v.phraser[tokens1], w2v.phraser[tokens2])

        # DEVE SER SIMILAR
        print(similarity('Amaciante De Roupa Ype Blue Concentrado', 'Amaciante Concentrado Ype Blue'))
        print(similarity('Refrigerante Pepsi Black', 'Refrigerante Pepsi Cola Black Zero Acucar'))
        print(similarity('Refrigerante Coca Cola + Fanta Guarana', 'Kit Refrigerante Coca Cola Original + Guarana Fanta'))

        # DEVE SER DISTANTE
        print(similarity('Refrigerante Pepsi Cola', 'Refrigerante Pepsi Cola Black Zero Acucar'))
        print(similarity('Amaciante Concentrado Comfort Frescor Intenso', 'Amaciante Concentrado Comfort Lavanda'))
        print(similarity('Sabonete Líquido Antibacteriano para as Mãos Protex Nutri Protect Vitamina E', 'Sabonete Líquido Antibacteriano para as Mãos Protex Duo Protect'))
        print()

    @classmethod
    def _detect_phrases(cls, titles: list) -> list:
        tokenized_titles = [
            [word for word in get_words(title.lower()) if word not in cls.PORTUGUESE_STOPWORDS]
            for title in titles
        ]
        
        bigram = Phrases(
            tokenized_titles,
            min_count=2,
            threshold=0.3,
            scoring='npmi'
        )
        
        phraser = Phraser(bigram)
        phrased_titles = []
        for title in phraser[tokenized_titles]:
            phrased_titles.append(title)
        
        main_product_terms = set(phraser.phrasegrams.keys())
        Loader.load(pd.DataFrame(main_product_terms), layer="model", name="products_ngrams")

        return phrased_titles, phraser
