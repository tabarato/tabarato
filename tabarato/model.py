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
            vector_size=300,
            alpha=1e-3,
            window=10,
            min_count=3,  # IGNORES WORD WITH FREQUENCY BELLOW
            workers=cpu_count() * 2,
            sg=1,  # 0 CBOW, 1 SKIP_GRAM
            cbow_mean=0,  # 0 SUM, 1 MEAN
            hs=0,  # 1 HIERARQUICAL SOFTMAX, 0 NEGATIVE
            negative=10,
            sample=1e-5,
            epochs=30,
        )
        w2v.phraser = phraser

        w2v.save("data/model/w2v.model")
        word_vectors = w2v.wv
        fname = get_tmpfile("w2v.vectors.kv")
        word_vectors.save(fname)
        print(f"Treinamento Word2Vec demorou: {round(time.time() - start, 2)}")

        # DEVE SER SIMILAR
        print(w2v.wv.n_similarity('Amaciante Conc Comfort Lavanda'.lower().split(), 'Amaciante Concentrado Comfort Lavanda'.lower().split()))
        print(w2v.wv.n_similarity('Amaciante De Roupa Ype Blue Concentrado'.lower().split(), 'Amaciante Conc. Ype Blue'.lower().split()))
        print(w2v.wv.n_similarity('Refrigerante Pepsi Black'.lower().split(), 'Refrigerante Pepsi Cola Black Zero Acucar'.lower().split()))
        print(w2v.wv.n_similarity('Refrigerante Coca Cola + Fanta Guarana'.lower().split(), 'Kit Refrigerante Coca Cola Original + Guarana Fanta'.lower().split()))

        # DEVE SER DISTANTE
        print(w2v.wv.n_similarity('Refrigerante Pepsi Cola'.lower().split(), 'Refrigerante Pepsi Cola Black Zero Acucar'.lower().split()))
        print(w2v.wv.n_similarity('Amaciante Conc Comfort Fiber'.lower().split(), 'Amaciante Conc Comfort Lavanda'.lower().split()))
        print(w2v.wv.n_similarity('Sabonete Líquido Antibacteriano para as Mãos Protex Nutri Protect Vitamina E'.lower().split(), 'Sabonete Líquido Antibacteriano para as Mãos Protex Duo Protect'.lower().split()))
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
            threshold=0.2,
            scoring='npmi'
        )
        trigram = Phrases(
            bigram[tokenized_titles],
            min_count=2,
            threshold=0.1,
            scoring='npmi'
        )
        
        phraser = Phraser(trigram)
        phrased_titles = []
        for title in phraser[tokenized_titles]:
            phrased_titles.append(title)
        
        main_product_terms = set(phraser.phrasegrams.keys())
        Loader.load(pd.DataFrame(main_product_terms), layer="model", name="products_ngrams")

        return phrased_titles, phraser
