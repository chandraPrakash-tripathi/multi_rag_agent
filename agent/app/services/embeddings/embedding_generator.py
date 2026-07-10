from typing import Union
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def generate_embedding(
    content: Union[str, list[str]],
    is_query: bool = False,
) -> Union[list[float], list[list[float]]]:
    if isinstance(content, str) and is_query:
        content = BGE_QUERY_PREFIX + content

    embedding = model.encode(content, normalize_embeddings=True, convert_to_numpy=True)
    return embedding.tolist()
