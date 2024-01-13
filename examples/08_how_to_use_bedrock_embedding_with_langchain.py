# Author: Rajib Deb
# Description: This module shows how you can use AWS Bedrock, faiss and Langchain
# to embed and query from a pdf
import os

import boto3
from botocore.config import Config
from dotenv import load_dotenv
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.llms.bedrock import Bedrock
from langchain_community.vectorstores.faiss import FAISS

load_dotenv()
# First ensure that you have created a IAM role with the below permissions
# {
#     "Version": "2012-10-17",
#     "Statement": [
#         {
#             "Sid": "Statement1",
#             "Effect": "Allow",
#             "Action": "bedrock:InvokeModel",
#             "Resource": "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v1"
#         },
#         {
#             "Sid": "Statement2",
#             "Effect": "Allow",
#             "Action": [
#                 "bedrock:InvokeModel"
#             ],
#             "Resource": [
#                 "arn:aws:bedrock:*::foundation-model/amazon.titan-text-express-v1"
#             ]
#         }
#     ]
# }

# Now get that role arn
# arn:aws:iam::<your_account_id>:role/<role_name>
# I am getting the arn from environment variables as I did not want to expose it
assumed_role = os.environ.get('ASSUMED_ROLE')


class VectorSearchWithBedrock():
    """
    This class wraps all the required functions to embed and than later query using Bedrock
    """
    def __init__(self, index_store="./index/faiss_index"):
        """
        In the init method, I am initializing with the index store to localy save the vecrtors.
        In addition, also initialzing the embedding model that will be used to embed the content.
        Note, that I have used the BedrockEmbeddings wrapper of Langchain and passing the client.
        We could have also used credentials_profile_name to pass the aws credentials, but I prefer
        to do it with client

        :param index_store: The default location of the index store
        """
        self.module = "__name__"
        self.bedrock_client = self._get_bedrock_client(assume_role=assumed_role)

        self.embeddings = BedrockEmbeddings(
            client=self.bedrock_client, region_name="us-east-1")

        self.index_store = "./index/faiss_index"

    def _get_bedrock_client(self, assume_role, profile_name='default', runtime=True):
        """
        Get the runtime client
        :param assume_role: The role which has access to bedrock service
        :param profile_name: default
        :param runtime: True is default
        :return: Bedrock client
        """

        client_kwargs = {}
        session_kwargs = {}

        if profile_name:
            print(f"  Using profile: {profile_name}")
            session_kwargs["profile_name"] = profile_name

        session = boto3.Session(**session_kwargs)
        print("profile used is ", profile_name)
        sts = session.client("sts")
        response = sts.assume_role(
            RoleArn=str(assume_role),
            RoleSessionName="bedrock-session"
        )

        retry_config = Config(
            retries={
                "max_attempts": 10,
                "mode": "standard",
            },
        )

        client_kwargs["aws_access_key_id"] = response["Credentials"]["AccessKeyId"]
        client_kwargs["aws_secret_access_key"] = response["Credentials"]["SecretAccessKey"]
        client_kwargs["aws_session_token"] = response["Credentials"]["SessionToken"]

        if runtime:
            service_name = 'bedrock-runtime'
        else:
            service_name = 'bedrock'

        bedrock_client = session.client(
            service_name=service_name,
            config=retry_config,
            **client_kwargs
        )

        return bedrock_client

    def save_into_vector(self, docs):
        """
        In this function I am saving the vectors locally using FAISS
        :param docs: The documents I need to embed, this is in langchain Document schema
        :return: None
        """

        vectorstore_faiss = FAISS.from_documents(
            docs, self.embeddings, )

        # Here I am storing the embeddings locally
        vectorstore_faiss.save_local(self.index_store)

    def load_vector(self):
        """
        This function loads the embedding vectors from the previously stored embedding
        store
        :return: It returns the previously stored embedding vectors
        """
        faiss_vectorstore = FAISS.load_local(self.index_store, self.embeddings)

        return faiss_vectorstore

    def return_bedrock_llm(self,model_id="amazon.titan-text-express-v1"):
        """
        This function returns the bedrock mode that will be used to generate the response.
        By default, it uses amazon.titan-text-express-v1
        :return: Returns the LLM required to respond to the query
        """
        llm = Bedrock(
            client=self.bedrock_client, model_id=model_id
        )

        return llm


if __name__ == "__main__":
    # The PDF content that I want to embed
    loader = PyPDFLoader("./data/impact_of_covid.pdf")
    documents = loader.load()
    # Splitting the document using Langchain text splitte. This is just a training example.
    # To make a production grade application, we need to experiment with more advanced
    # chunking and retrieval patterns
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50, separator="\n")
    docs = text_splitter.split_documents(documents=documents)

    # The next two lines of code are saving the vectors locally
    faiss_chat_bot = VectorSearchWithBedrock()
    faiss_chat_bot.save_into_vector(docs)

    # Here i am creating the vector store index wrapper by loading the stored vectors from the local file
    wrapper_faiss_chat = VectorStoreIndexWrapper(vectorstore=faiss_chat_bot.load_vector())

    # Now returning the LLM which will answer the query
    llm = faiss_chat_bot.return_bedrock_llm()

    # We are now ready to pass the query and get the answer
    query = "How many students were surveyed to understand the impact of the COVID-19 pandemic on higher education?"
    answer = wrapper_faiss_chat.query_with_sources(question=query, llm=llm)

    print(answer)
