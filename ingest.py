from langchain_community.document_loaders import DirectoryLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

OPENAI_API_KEY = "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"

loader = DirectoryLoader("docs", glob="**/*.docx", loader_cls=Docx2txtLoader)
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)

embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="chroma_db"
)

print(f"Feito! {len(chunks)} chunks guardados.")