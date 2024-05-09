from langchain_core.documents import Document

from retrieval.base import Retrieval


class ContextRetrieval(Retrieval):
    def __init__(self):
        super().__init__()
        self.module ="__name__"

    def get_relevant_contex(self):
        documents = Document(page_content="TajMahal is in Agra, Uttar Pradesh", metadata={"source":"wikipedia"})
        return documents