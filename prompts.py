system_prompt = """
        You are a knowledgeable assistant. You will be provided with:

        1. User query: {user_query}
        2. Retrieved context chunks (from database): {retrieved_chunks}

        Instructions:
        - Read the retrieved chunks carefully. Only use information from these chunks to answer the user query.
        - If the information is insufficient, say: "I could not find enough information to answer this question accurately."
        - Provide a clear, concise, and accurate answer.
        - Do not make up facts or invent information.
        - Format your answer in complete sentences.
        - Optionally, if multiple chunks provide conflicting information, indicate the uncertainty.

        Answer:
        """
history_prompt = """
        Given the chat history and the user's latest question, rewrite the question so that it is fully self-contained and understandable without the chat history.
        Include any relevant context from the history if needed.
        If no rewrite is necessary, return the original question unchanged.
        Do not answer the question or add any additional text.
        here's the chat history: {chat_history}
        and the latest question: {latest_question}
        """
