__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from prompt import SYSTEM_PROMPT
import os


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")


@st.cache_resource
def load_resources():
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    retriever = vectorstore.as_retriever()
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY, temperature=0.7)
    return retriever, llm

retriever, llm = load_resources()

st.title("Tutor EDruptiva - Happy Code")

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