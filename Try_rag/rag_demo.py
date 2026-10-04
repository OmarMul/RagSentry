"""
Simple RAG Demo (OpenRouter Edition)
=====================================
Pipeline:
  LLM      : OpenRouter  (any model, e.g. openai/gpt-4o-mini)
  Embeddings: HuggingFace sentence-transformers (local, no API key needed)
  Vector DB : LangChain InMemoryVectorStore

Requirements (.env):
  OPENROUTER_API_KEY=sk-or-...
  OPENROUTER_MODEL=openai/gpt-4o-mini   # optional, defaults to gpt-4o-mini

Run:
  python rag_demo.py
"""

import os
import textwrap
import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Local embeddings (no API key required)
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from langchain_community.embeddings import HuggingFaceEmbeddings

# ── Config ─────────────────────────────────────────────────────────────────────
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL   = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

# Local embedding model (~90 MB, downloaded once to ~/.cache)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

if not OPENROUTER_API_KEY:
    raise EnvironmentError(
        "OPENROUTER_API_KEY is not set.\n"
        "Add it to a .env file:\n"
        "  OPENROUTER_API_KEY=sk-or-..."
    )

# ── Sample knowledge base ──────────────────────────────────────────────────────
SAMPLE_DOCS = [
    Document(
        page_content="""
        Retrieval-Augmented Generation (RAG) is an AI framework that enhances Large Language
        Models (LLMs) by retrieving relevant information from an external knowledge base before
        generating a response. Unlike pure LLMs that rely solely on their training data, RAG
        systems can access up-to-date, domain-specific information at inference time.
        The core idea is to ground the LLM answer in real retrieved context, significantly
        reducing hallucinations and improving factual accuracy.
        """,
        metadata={"source": "rag_overview.txt", "topic": "RAG Basics"},
    ),
    Document(
        page_content="""
        A typical RAG pipeline has three main stages:
        1. Indexing: Documents are loaded, split into chunks, converted to vector embeddings,
           and stored in a vector database.
        2. Retrieval: When a user asks a question, the query is embedded and a similarity
           search finds the top-k most relevant chunks.
        3. Generation: The retrieved chunks are injected into the LLM prompt as context,
           and the LLM generates a grounded, accurate answer.
        Popular vector stores include FAISS, Chroma, Pinecone, Weaviate, and Qdrant.
        """,
        metadata={"source": "rag_pipeline.txt", "topic": "RAG Pipeline"},
    ),
    Document(
        page_content="""
        Vector embeddings are numerical representations of text that capture semantic meaning.
        Similar sentences produce vectors that are close together in high-dimensional space.
        The all-MiniLM-L6-v2 model is a lightweight sentence-transformer that produces
        384-dimensional vectors and runs fully locally without any API key.
        Cosine similarity is commonly used to measure how close two embeddings are,
        with values ranging from -1 (opposite) to 1 (identical meaning).
        """,
        metadata={"source": "embeddings.txt", "topic": "Embeddings"},
    ),
    Document(
        page_content="""
        LangChain is an open-source framework for building LLM-powered applications.
        It provides abstractions for chains, agents, memory, and retrieval. Key components:
        - ChatModels: Wrappers around LLMs like GPT-4o, Claude, Gemini, and OpenRouter.
        - VectorStores: Integrations with FAISS, Chroma, Pinecone, and many more.
        - Retrievers: Components that fetch relevant documents given a query.
        - Chains: Composable sequences of LLM calls and tool uses.
        - LCEL (LangChain Expression Language): A declarative way to compose chains using
          the pipe operator for clean, readable pipelines.
        """,
        metadata={"source": "langchain_intro.txt", "topic": "LangChain"},
    ),
    Document(
        page_content="""
        OpenRouter is a unified API gateway that gives access to hundreds of LLMs
        (GPT-4o, Claude, Gemini, Mistral, LLaMA, etc.) through a single OpenAI-compatible
        endpoint at https://openrouter.ai/api/v1. You only need one API key.
        It supports model routing, fallbacks, and cost tracking.
        Because OpenRouter uses the same API format as OpenAI, you can use it with any
        OpenAI-compatible client by changing the base_url and api_key parameters.
        """,
        metadata={"source": "openrouter.txt", "topic": "OpenRouter"},
    ),
    Document(
        page_content="""
        RAG evaluation is critical to ensure your pipeline is working correctly.
        Key metrics include:
        - Faithfulness: Does the answer stay true to the retrieved context?
        - Answer Relevancy: Is the answer relevant to the original question?
        - Context Recall: Were the right documents retrieved?
        - Context Precision: What fraction of retrieved docs were actually useful?
        Tools like RAGAS, TruLens, and RagSentry help automate this evaluation.
        Without proper evaluation, RAG systems can silently degrade in quality.
        """,
        metadata={"source": "rag_evaluation.txt", "topic": "RAG Evaluation"},
    ),
    Document(
        page_content="""
        Advanced RAG techniques beyond naive retrieval include:
        - HyDE (Hypothetical Document Embeddings): Generate a hypothetical answer first,
          then embed that for retrieval instead of the raw question.
        - Multi-query retrieval: Generate multiple rephrased versions of the question
          and merge retrieved results.
        - Re-ranking: Use a cross-encoder to re-score retrieved docs for better precision.
        - Parent-document retrieval: Embed small chunks but return their larger parent
          documents for richer context.
        - Self-RAG: The LLM decides whether retrieval is needed and critiques its own answer.
        """,
        metadata={"source": "advanced_rag.txt", "topic": "Advanced RAG"},
    ),
]


# ══════════════════════════════════════════════════════════════════════════════
# 1. BUILD THE INDEX
# ══════════════════════════════════════════════════════════════════════════════

def build_index(docs):
    """Split documents into chunks and index them in an in-memory vector store."""
    print(f"Building index with local embeddings ({EMBEDDING_MODEL})...")
    print("  (First run will download ~90 MB model to ~/.cache — subsequent runs are instant)")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=60,
        separators=["\n\n", "\n", ".", " "],
    )
    chunks = splitter.split_documents(docs)
    print(f"  Split {len(docs)} documents into {len(chunks)} chunks")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    vectorstore = InMemoryVectorStore.from_documents(chunks, embeddings)
    print(f"  Indexed {len(chunks)} chunks successfully\n")
    return vectorstore, embeddings


# ══════════════════════════════════════════════════════════════════════════════
# 2. BUILD THE RAG CHAIN
# ══════════════════════════════════════════════════════════════════════════════

RAG_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a helpful assistant that answers questions based ONLY on the
provided context. If the context does not contain enough information to answer
the question, say so clearly instead of making things up.

Context:
{context}""",
    ),
    ("human", "{question}"),
])


def format_docs(docs):
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[{i}] Source: {source}\n{doc.page_content.strip()}")
    return "\n\n---\n\n".join(parts)


def build_rag_chain(vectorstore):
    """Build the RAG chain using OpenRouter as the LLM backend."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # OpenRouter is OpenAI-compatible — just swap base_url and api_key
    llm = ChatOpenAI(
        model=OPENROUTER_MODEL,
        temperature=0,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": "https://github.com/rag-demo",  # optional but recommended by OpenRouter
            "X-Title": "RAG Demo",
        },
    )

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )
    return chain, retriever


# ══════════════════════════════════════════════════════════════════════════════
# 3. Q&A HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def sep(char="-", width=70):
    print(char * width)


def ask(chain, retriever, question):
    """Run a single RAG query and pretty-print the answer + sources."""
    sep()
    print(f"Question: {question}")
    sep(".")

    retrieved_docs = retriever.invoke(question)
    answer = chain.invoke(question)

    print("Answer:\n")
    for line in textwrap.wrap(answer, width=68):
        print(f"  {line}")

    print()
    print("Sources used:")
    for doc in retrieved_docs:
        src   = doc.metadata.get("source", "unknown")
        topic = doc.metadata.get("topic", "")
        snippet = doc.page_content.strip()[:80].replace("\n", " ")
        print(f"  [{topic}] {src}: \"{snippet}...\"")
    print()


def interactive_mode(chain, retriever):
    """Run an interactive Q&A REPL."""
    sep("=")
    print(f"  RAG Demo (model: {OPENROUTER_MODEL}) -- Interactive Mode")
    print("  Type your question and press Enter. Type 'quit' to exit.")
    sep("=")
    print()

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            continue
        if question.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break

        ask(chain, retriever, question)


# ══════════════════════════════════════════════════════════════════════════════
# 4. MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"LLM  : OpenRouter -> {OPENROUTER_MODEL}")
    print(f"Embed: {EMBEDDING_MODEL} (local)")
    print()

    vectorstore, _ = build_index(SAMPLE_DOCS)
    chain, retriever = build_rag_chain(vectorstore)

    demo_questions = [
        "What is RAG and why is it useful?",
        "What are the three stages of a RAG pipeline?",
        "How does OpenRouter differ from calling OpenAI directly?",
    ]

    sep("=")
    print("  RAG Demo -- Sample Questions")
    sep("=")
    print()

    for q in demo_questions:
        ask(chain, retriever, q)

    interactive_mode(chain, retriever)
