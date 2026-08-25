__import__('pysqlite3')
import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except (ImportError, KeyError):
    pass
import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from azure.storage.blob import BlobServiceClient
from prompt import SYSTEM_PROMPT
from openai import OpenAI
import os


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
AZURE_STORAGE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING") or st.secrets.get("AZURE_STORAGE_CONNECTION_STRING")


@st.cache_resource
def ensure_chroma_db():
    if os.path.exists("chroma_db") and os.listdir("chroma_db"):
        return
    blob_service = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    container = blob_service.get_container_client("chroma-db")
    for blob in container.list_blobs():
        local_path = os.path.join("chroma_db", blob.name)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(container.download_blob(blob.name).readall())

ensure_chroma_db()


@st.cache_resource
def load_resources():
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    retriever = vectorstore.as_retriever()
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY, temperature=0.7)
    return retriever, llm

moderation_client = OpenAI(api_key=OPENAI_API_KEY)

MENSAGEM_CONTEUDO_PREOCUPANTE = (
    "Não consigo ajudar com isso por aqui. Se estás a passar por um momento difícil, "
    "fala com um professor, um adulto de confiança ou alguém da tua família — é importante "
    "que não fiques sozinho/a com isto."
)

def conteudo_sinalizado(texto):
    resultado = moderation_client.moderations.create(input=texto)
    return resultado.results[0].flagged

retriever, llm = load_resources()

with open("kobe.css") as f:
    kobe_css = f.read()

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
{kobe_css}


html, body, .stMarkdown, .stChatInput textarea,
p, div, span, label, button {{
    font-family: 'Roboto', sans-serif !important;
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: 'Kobe', 'Roboto', sans-serif !important;
    font-weight: 700 !important;
}}

[data-testid="stIconMaterial"], .material-icons, [class*="material-symbols"] {{
    font-family: 'Material Symbols Rounded' !important;
}}

[data-testid="stHeaderActionElements"] {{
    display: none !important;
}}

[data-testid="stChatMessageAvatarUser"] {{
    background-color: #e66468 !important;
}}
[data-testid="stChatMessageAvatarAssistant"] {{
    background-color: #aecc53 !important;
}}
[data-testid="stChatMessageAvatarUser"] svg,
[data-testid="stChatMessageAvatarAssistant"] svg {{
    fill: #ffffff !important;
}}

.stMainBlockContainer, [data-testid="stMainBlockContainer"] {{
    padding-top: 0 !important;
    padding-left: 0.75rem !important;
    padding-right: 0.75rem !important;
}}

[data-testid="stChatMessage"] {{
    padding-top: 0.25rem !important;
    padding-bottom: 0.25rem !important;
}}

</style>
""", unsafe_allow_html=True)


if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Olá! Sou o Coddy. Em que posso ajudar-te hoje?"}
    ]

for message in st.session_state.messages:
    avatar = "coddy_icon.png" if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar):
        st.write(message["content"])

if prompt := st.chat_input("Escreve a tua pergunta..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant", avatar="coddy_icon.png"):
        if conteudo_sinalizado(prompt):
            answer = MENSAGEM_CONTEUDO_PREOCUPANTE
            st.write(answer)
        else:
            docs = retriever.invoke(prompt)
            context = "\n\n".join([doc.page_content for doc in docs])

            messages_for_llm = [
                SystemMessage(content=f"{SYSTEM_PROMPT}\n\nContexto dos documentos da Happy Code:\n{context}")
            ]
            for msg in st.session_state.messages[:-1]:
                if msg["role"] == "user":
                    messages_for_llm.append(HumanMessage(content=msg["content"]))
                else:
                    messages_for_llm.append(AIMessage(content=msg["content"]))
            messages_for_llm.append(HumanMessage(content=prompt))

            response = llm.invoke(messages_for_llm)
            answer = response.content
            st.write(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})