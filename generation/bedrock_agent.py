import os

from dotenv import load_dotenv
from langchain_aws import BedrockLLM
from langchain_core.prompts import PromptTemplate

from callbacks.bedrock_callback import BedRockTokenCounter
from generation.base import Generation
from retrieval.base import Retrieval
from retrieval.context_retrieval import ContextRetrieval


load_dotenv()

# assumed_role = os.environ.get('CLAUDE_ASSUMED_ROLE')
assumed_role = os.environ.get('LLAMA_ASSUMED_ROLE')
# assumed_role = os.environ.get("MISTRAL_ASSUMED_ROLE")

prompt_template = """
Answer based on the provided context only.
{context}
{question}
answer:
"""


class BedrockGeneration(Generation):

    def __init__(self):
        super().__init__()
        self.module = "BEDROCKGEN"

    def get_prompt(self, template=prompt_template):
        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )

        return prompt

    def generate(self,
                 model_id,
                 retriever:Retrieval):

        context = retriever.get_relevant_contex()

        question = """ Where is tajmAHAL?
        """
        bedrock_client = self.get_bedrock_client(assume_role=assumed_role)
        llm = BedrockLLM(
            client=bedrock_client, model_id=model_id
        )

        prompt = self.get_prompt()

        chain = prompt | llm
        token_counter = BedRockTokenCounter(llm)
        print(chain.invoke({"context": context, "question": question}, config={"callbacks": [token_counter]}))
        print(token_counter.input_tokens)
        print(token_counter.output_tokens)


if __name__ == "__main__":
    retriever = ContextRetrieval()
    bg = BedrockGeneration()
    # model_id ="mistral.mixtral-8x7b-instruct-v0:1"
    # model_id = "anthropic.claude-v2"
    model_id="meta.llama2-13b-chat-v1"
    bg.generate(retriever=retriever,model_id=model_id)
