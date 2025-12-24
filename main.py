from fastapi import FastAPI, Query
import gradio as gr
from langdetect import detect
from langchain_google_genai import ChatGoogleGenerativeAI

from src.services.open_seach_insertion import OpenSearchInsertion
from src.opensearch.open_search_client import OpenSearchClient
from src.opensearch.mapping import ProjectMapping
from src.extracters.stanza_temporal_extractor import MultiLangTemporalExtractor
from src.extracters.stanza_locations_extractor import StanzaLocationsExtractor
from src.extracters.geopy_geo_location_finder import GeopyGeoLocationFinder
from src.services.an_najah_repository_search_service import (
    AnNajahRepositorySearchService,
)
from global_config import global_config
from src.queries_generation.query_generation import QueryGeneration
from src.models.chat_model import GeminiGenerativeModel


generative_model = ChatGoogleGenerativeAI(
    model=global_config.generative_model_name,
    temperature=0.0,
)


query_generation = QueryGeneration(ollama_model=global_config.ollama_model_name)
client = OpenSearchClient(True, True)
print("OpenSearch client initialized.")

project_mapping = ProjectMapping(
    model_name=global_config.embedding_model_name,
    opensearch_client=client,
)

opensearch_insertion_client = OpenSearchInsertion(
    project_mapping,
    location_extractor=StanzaLocationsExtractor(),
    temporal_extractor=MultiLangTemporalExtractor(),
    geo_location_finder=GeopyGeoLocationFinder(),
    index_name=global_config.index_name,
)

opensearch_search_service = AnNajahRepositorySearchService(
    index=global_config.index_name,
    client=client,
    query_generator=query_generation,
    mapping=project_mapping,
    generative_model=GeminiGenerativeModel(model=generative_model),
)

# print(opensearch_search_service.client_health())

# generated_query = opensearch_search_service.generate_query(
#     user_prompt="Find articles for the author hamed abdelhaq"
# )


# print("Generated Query:", generated_query[1])
# print("Generated Query:", generated_query[0])

# Initialize FastAPI app
main = FastAPI()


# autocomplete API endpoint
@main.get("/api/suggest")
def suggest(q: str = Query(..., min_length=3), limit: int = Query(8, ge=1, le=20)):
    # return a raw list[str] of suggestions
    return opensearch_search_service.suggest(prefix=q, limit=limit)


# --- UI LOGIC FUNCTIONS ---

RTL_LANGS = {"ar", "he", "fa", "ur"}


def format_answer_markdown(answer_text: str) -> str:
    """Formats the answer text into HTML with proper directionality."""
    try:
        lang = detect(answer_text)
    except Exception:
        lang = "en"

    direction = "rtl" if lang in RTL_LANGS else "ltr"
    return (
        '<div class="answer-container">\n'
        f'<div dir="{direction}" class="answer-shell">\n{answer_text}\n</div>\n'
        "</div>"
    )


def _generate_answer_ui(query):
    """Generates answer for the UI and formats it."""
    if not query:
        return "Please enter a question."
    answer_text = opensearch_search_service.generate_answer(query)
    return format_answer_markdown(answer_text)


def get_suggestions(q):
    """Hits the suggest logic every time a user types."""
    if not q or len(q) < 3:
        return gr.update(choices=[])

    # Calls your suggest logic from the service
    suggestions = opensearch_search_service.suggest(prefix=q, limit=5)
    return gr.update(choices=suggestions)


def handle_selection(current_text, selected_value):
    """Appends the selected suggestion to the current text box content."""
    if not current_text:
        return selected_value
    # If the user clicks a suggestion already in the box, don't repeat it
    if selected_value in current_text:
        return current_text
    return f"{current_text} {selected_value}".strip()


# --- GRADIO INTERFACE ---

app_theme = gr.themes.Soft()
custom_css = """
body, .gradio-container {
    font-family: 'Times New Roman', Times, serif;
}
#answer-box, .answer-shell, .gr-markdown div {
    font-family: 'Times New Roman', Times, serif;
}
#answer-box {
    font-size: 20px;
    line-height: 1.65;
    margin-top: 8px;
    margin-bottom: 12px;
}
.answer-shell {
    font-size: 20px;
    line-height: 1.65;
    padding: 12px 16px;
    margin: 8px 0 12px 0;
    border-radius: 8px;
}
.answer-container {
    margin-top: 10px;
    margin-bottom: 14px;
    padding: 6px;
    border-radius: 10px;
}
#query-box textarea {
    font-size: 18px;
    line-height: 1.5;
    min-height: 140px;
    padding: 14px;
}
"""

with gr.Blocks(title="An-Najah Assistant", css=custom_css) as demo:
    gr.Markdown("# 🏛️ An-Najah National University Repository Assistant")
    gr.Markdown("Ask questions about the university's research and documents.")

    with gr.Row():
        query_box = gr.Textbox(
            label="Type your question...",
            placeholder="Ask about papers, authors, dates, or topics...",
            lines=3,
            max_lines=6,
            interactive=True,
            container=True,
            elem_id="query-box",
            scale=4,
        )
        submit_btn = gr.Button("Generate Answer", variant="primary", scale=1)

    status_box = gr.Markdown("")
    answer_box = gr.Markdown("### Answer", elem_id="answer-box")

    # 3. Execution pipeline with UI feedback
    submit_btn.click(
        fn=lambda: (
            "⏳ Analyzing context and generating response...",
            gr.update(interactive=False),
        ),
        outputs=[status_box, submit_btn],
    ).then(fn=_generate_answer_ui, inputs=query_box, outputs=answer_box).then(
        fn=lambda: ("", gr.update(interactive=True)), outputs=[status_box, submit_btn]
    )

    # Allow Enter key to trigger generation too
    query_box.submit(
        fn=lambda: (
            "⏳ Analyzing context and generating response...",
            gr.update(interactive=False),
        ),
        outputs=[status_box, submit_btn],
    ).then(fn=_generate_answer_ui, inputs=query_box, outputs=answer_box).then(
        fn=lambda: ("", gr.update(interactive=True)), outputs=[status_box, submit_btn]
    )

if __name__ == "__main__":
    demo.queue().launch(share=True, theme=app_theme)
