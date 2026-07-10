from typing import Union

from sentence_transformers import SentenceTransformer

# Load once when the application starts
model = SentenceTransformer("BAAI/bge-small-en-v1.5")


def generate_embedding(
    content: Union[str, list[str]],
) -> Union[list[float], list[list[float]]]:
    """
    Generate embeddings using the local BGE model.

    Supports:
        - Single string -> list[float]
        - List[str] -> list[list[float]]
    """

    if isinstance(content, str):
        return model.encode(
            content,
            normalize_embeddings=True,
            convert_to_numpy=False,
        )

    elif isinstance(content, list):
        return model.encode(
            content,
            normalize_embeddings=True,
            convert_to_numpy=False,
        )

    raise ValueError("Content must be either a string or list[str]")
