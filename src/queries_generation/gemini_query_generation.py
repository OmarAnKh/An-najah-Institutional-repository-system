from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import json

from src.queries_generation.abstract_classes import ABCQueryGeneration
from prompts import query_generation_prompt


class GeminiQueryGeneration(ABCQueryGeneration):
    """
    Query generation implementation using a Gemini chat model.
    """

    def __init__(self, model):
        """
        Initializes the GeminiQueryGeneration with the specified chat model.

        Args:
            model: A LangChain chat model instance (e.g., ChatGoogleGenerativeAI).
        """
        self.__model = model
        self.__prompt = ChatPromptTemplate.from_template(
            "{system_part}\n\nUser: {user_prompt}\nAssistant:"
        )
        self.__generation_chain = self.__prompt | self.__model | StrOutputParser()

    def generate_opensearch_query(self, user_prompt: str, mapping):
        """
        Generates an OpenSearch query using the Gemini chat model.

        Args:
            user_prompt: The user input for query generation.
            mapping: The OpenSearch index mapping/configuration.

        Returns:
            str: The generated OpenSearch query as a string.
        """
        system_part = (
            query_generation_prompt
            + "\n\nINDEX MAPPING:\n"
            + json.dumps(mapping, ensure_ascii=False)
        )
        return self.__generation_chain.invoke(
            {"system_part": system_part, "user_prompt": user_prompt}
        )
