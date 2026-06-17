import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from prompt import SYSTEM_PROMPT

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

@st.cache_resource
def load_resources():
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    retriever = vectorstore.as_retriever()
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY, temperature=0.7)
    return retriever, llm

retriever, llm = load_resources()

st.title("Nexus AI Tutor")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("Escreve a tua pergunta..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        docs = retriever.invoke(prompt)
        context = "\n\n".join([doc.page_content for doc in docs])
        full_prompt = f"{SYSTEM_PROMPT}\n\nContexto dos documentos da Happy Code:\n{context}\n\nPergunta do aluno: {prompt}"
        response = llm.invoke(full_prompt)
        answer = response.content
        st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})