# 1) This code imports LangChain's RecursiveCharacterTextSplitter and defines a reusable function recursive_character_splitting()
# that breaks a large text into smaller, overlapping chunks suitable for embedding and Retrieval-Augmented Generation (RAG).
# 2) The function accepts the input text along with optional parameters chunk_size (default 300 characters) and chunk_overlap (default 20 characters)
# to control the size of each chunk and preserve context between consecutive chunks.
# 3)Inside the function, a RecursiveCharacterTextSplitter object is created with length_function=len, meaning chunk sizes are measured by the number of characters,
# and a hierarchy of separators=["\n\n", "\n", " ", ""], which tells the splitter to first try splitting at paragraph boundaries (\n\n), then line breaks (\n),
# then spaces (between words), and finally, if necessary, at individual characters ("") to ensure every chunk stays within the specified size.
# The split_text(text) method then recursively applies these separators to produce clean, context-preserving chunks, which are returned as a
# list of strings and are typically passed to an embedding model before being stored in a vector database like Qdrant.

# Separators:The separators parameter sets a priority order for how to split your text.
# the  algorithm tries to split at the first separator to keep semantic units (like paragraphs) together.
# If the resulting chunk is still larger than your chunk_size, it "recursively" moves to the next separator in the list to break it down further.
# "\n\n" (Paragraphs)
# "\n" (Lines)
# " "Words
# "" (Characters)
from langchain_text_splitters import RecursiveCharacterTextSplitter


def recursive_character_splitting(text, chunk_size=300, chunk_overlap=20):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )

    chunks = text_splitter.split_text(text)
    return chunks
