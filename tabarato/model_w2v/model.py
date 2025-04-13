import os
import sys
import time
import pickle
import argparse
import re
from itertools import chain
from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
from gensim.models import Word2Vec
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.test.utils import get_tmpfile
from gensim.models.word2vec import LineSentence

def train_model(title: LineSentence, model_type: int) -> None:
    parser = argparse.ArgumentParser(description="Run word embedding models")
    parser.add_argument(
        "--model",
        dest="model_type",
        default=model_type,
        help="Word Embedding model to run: 0 = Word2Vec ; 1 = Doc2Vec ; 2 = Both",
    )
    args = parser.parse_args()
    model_type = int(args.model_type)

    if model_type == 0 or model_type == 2:
        start = time.time()
        print("-" * 20)
        print("Iniciando treinamento do Word2Vec...")
        w2v = Word2Vec(
            sentences=title,
            # corpus_file=title,
            vector_size=300,
            alpha=1e-3,
            window=10,
            min_count=2,  # IGNORES WORD WITH FREQUENCY BELLOW
            workers=cpu_count() * 2,
            sg=1,  # 0 CBOW, 1 SKIP_GRAM
            cbow_mean=0,  # 0 SUM, 1 MEAN
            hs=0,  # 1 HIERARQUICAL SOFTMAX, 0 NEGATIVE
            negative=7,
            sample=1e-4,
            epochs=25,
        )
        # Save model
        w2v.save("w2v.model")
        # Save only word vectors
        word_vectors = w2v.wv
        fname = get_tmpfile("w2v.vectors.kv")
        word_vectors.save(fname)
        print(f"Treinamento Word2Vec demorou: {round(time.time() - start, 2)}")
        print()

    if model_type == 1 or model_type == 2:
        start = time.time()
        print("-" * 20)
        print("Iniciando treinamento do Doc2Vec...")
        d2v = Doc2Vec(
            # documents=[
            #     TaggedDocument(sentence, [k])
            #     for k, sentence in enumerate(
            #         LoadCorpus(f"{os.getcwd()}/data/embedding/corpus.txt")
            #     )
            # ],
            corpus_file=title,
            vector_size=300,
            alpha=1e-3,
            window=10,
            min_count=2,
            workers=cpu_count() * 2,
            dm=1,
            hs=0,
            negative=7,
            sample=1e-4,
            dbow_words=1,
            epochs=25,
        )
        d2v.save(f"{os.getcwd()}/models/d2v.model")
        print(f"Treinamento Doc2Vec demorou: {round(time.time() - start, 2)}")




if __name__ == "__main__":
    sentences = LineSentence('corpus.txt')
    train_model(sentences, 0)
