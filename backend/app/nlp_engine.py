"""NLP engine for Fixora (statistical, no keyword rules).

Department routing
    TF-IDF features (word 1-2 grams + character 3-5 grams) -> multinomial Logistic Regression.
    Character n-grams make it robust to typos and unseen wording. The model is trained on a
    labelled corpus and re-trained from real resolved issues at startup and after each repair.

Duplicate detection
    Cosine similarity between TF-IDF vectors (same trained feature space, so IDF weights are
    stable) of the new report and nearby open issues.
"""
import re
import threading

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import FeatureUnion, Pipeline

from .nlp_seed import SEED


def clean(text):
    text = re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())
    return re.sub(r"\s+", " ", text).strip()


def build_text(title, description):
    # The title is the strongest signal, so it is weighted by repetition.
    return clean(f"{title}. {title}. {description}")


class IssueNLP:
    def __init__(self):
        self._lock = threading.Lock()
        self._pipe = None
        self.train([])

    @staticmethod
    def _pipeline():
        features = FeatureUnion([
            ("word", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")),
            ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=2)),
        ])
        return Pipeline([("features", features),
                         ("clf", LogisticRegression(C=20, max_iter=3000, class_weight="balanced"))])

    def train(self, extra):
        """extra: iterable of (title, description, department) from resolved real issues."""
        texts, labels = [], []
        for dept, sentences in SEED.items():
            for s in sentences:
                texts.append(clean(s))
                labels.append(dept)
        for title, description, dept in extra:
            if dept in SEED and (title or description):
                texts.append(build_text(title, description))
                labels.append(dept)
        pipe = self._pipeline()
        pipe.fit(texts, labels)
        with self._lock:
            self._pipe = pipe

    def classify(self, title, description):
        with self._lock:
            pipe = self._pipe
        probs = pipe.predict_proba([build_text(title, description)])[0]
        i = int(probs.argmax())
        return str(pipe.classes_[i]), float(probs[i])

    def similarities(self, title, description, candidates):
        """candidates: list of (title, description). Returns one cosine score per candidate."""
        if not candidates:
            return []
        with self._lock:
            feats = self._pipe.named_steps["features"]
        m = feats.transform([build_text(title, description)] + [build_text(t, d) for t, d in candidates])
        return [float(x) for x in cosine_similarity(m[0], m[1:])[0]]


nlp = IssueNLP()
