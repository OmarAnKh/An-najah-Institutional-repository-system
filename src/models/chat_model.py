from collections import deque
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.models.abstract_classes.generative_model import ABCGenerativeModel
from prompts import system_prompt, history_prompt


class GeminiGenerativeModel(ABCGenerativeModel):
    """
    Ollama RAG Model implementation using OllamaLLM from langchain-ollama. Defines methods for generating responses,
    formulating queries, and maintaining chat history.
    """

    def __init__(self, model) -> None:
        """
        Initialize the GeminiGenerativeModel with the specified Ollama model.
        Args:
            model_name (str): The name of the Ollama model to use.
        """

        self.__model = model

        self.__prompt = ChatPromptTemplate.from_template(system_prompt)
        self.__history_prompt = ChatPromptTemplate.from_template(history_prompt)

        self.__history = deque(maxlen=2)

        self.__generation_chain = self.__prompt | self.__model | StrOutputParser()
        self.__formulate_query_chain = (
            self.__history_prompt | self.__model | StrOutputParser()
        )

    def formulate_query(self, user_input: str) -> str:
        """Formulate a self-contained query based on chat history and the latest user input.

        Args:
            user_input (str): The latest user question.

        Returns:
            str: The formulated self-contained query.
        """
        if not self.__history:
            return user_input

        history_string = "\n".join(
            [
                f"User: {item['query']}\nAssistant: {item['response']}"
                for item in self.__history
            ]
        )

        return self.__formulate_query_chain.invoke(
            {"chat_history": history_string, "latest_question": user_input}
        )

    def _add_to_history(self, query: str, response: str):
        """Save the query and response to the history queue.

        Args:
            query (str): The user's query.
            response (str): The assistant's response.
        """
        self.__history.append({"query": query, "response": response})

    def generate(self, query: str, documents: set[str]) -> str:
        """Generate an answer based on the query and retrieved documents.

        Args:
            query (str): The user's query.
            documents (set[str]): A set of retrieved documents.
        Returns:
            str: The generated answer.
        """

        retrieved_chunks = "\n\n".join(documents)
        answer = self.__generation_chain.invoke(
            {"user_query": query, "retrieved_chunks": retrieved_chunks}
        )

        self._add_to_history(query, answer)
        return answer
