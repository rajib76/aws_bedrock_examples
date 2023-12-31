# The trust relation and all the permission policies for the role used in this program
# is provided in the readme
import logging

import boto3
from botocore.client import BaseClient

logger = logging.getLogger(__name__)


class BedrockKBAgent():
    def __init__(self, region_name="us-east-1"):
        """
        Initializes the region for the service
        :param region_name: The region name of the service. Defaulted to us-east-1
        """
        self.region_name = region_name

    def _return_aws_service_client(self, resource_name='bedrock', run_time=True) -> BaseClient:
        """
        This funtion returns the appropriate aws service client
        :param resource_name: the resource name for which the client needs to be created
        :param run_time: If resource is 'bedrock' and the value is true, returns the
        run time client, else the normal client
        :return: Returns the appropriate client for the resource
        """
        if resource_name == "bedrock":
            if run_time:
                service_client = boto3.client(
                    service_name="bedrock-agent-runtime",
                    region_name=self.region_name)
            else:
                service_client = boto3.client(
                    service_name="bedrock-agent",
                    region_name=self.region_name)
        elif resource_name == "iam":
            service_client = boto3.resource("iam")

        return service_client

    def create_kb(self,
                  kb_name,
                  role_arn,
                  collection_arn,
                  index_name,
                  model_arn="arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1"):
        """
        This module creates the knowledge base
        :param kb_name: the name of the knowledge base
        :param role_arn: The arn of the role to create the knowledge base
        :param collection_arn: the arn of the oepn search collection
        :param index_name: The name of the vector index
        :param model_arn: The arn of the titan embedding model
        :return: The response after calling the API
        """

        client = self._return_aws_service_client(run_time=False)
        response = client.create_knowledge_base(
            name=kb_name,
            description='This is a KB created through python',
            roleArn=role_arn,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': model_arn
                }
            },
            storageConfiguration={
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': collection_arn,
                    'vectorIndexName': index_name,
                    'fieldMapping': {
                        'vectorField': 'embedding',
                        'textField': 'AMAZON_BEDROCK_TEXT_CHUNK',
                        'metadataField': 'AMAZON_BEDROCK_METADATA'
                    }
                }
            },
            tags={
                'bedrockb': 'kbforloan'
            }
        )

        return response

    def create_ds(self,
                  knowledge_base_id,
                  bucket_arn):
        """
        This module creates the data source and attached to the knowledge base
        :param knowledge_base_id: The id of the created knowledge base
        :param bucket_arn: The arn of the bucket which has the source data
        :return: Returns the response from the API
        """
        client = self._return_aws_service_client(run_time=False)
        response = client.create_data_source(
            knowledgeBaseId=knowledge_base_id,
            name='bedrock-ds',
            description='data source for kb',
            dataSourceConfiguration={
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': bucket_arn,
                    'inclusionPrefixes': [
                        'loan_estimate.pdf'
                    ]
                }
            },
            vectorIngestionConfiguration={
                'chunkingConfiguration': {
                    'chunkingStrategy': 'FIXED_SIZE',
                    'fixedSizeChunkingConfiguration': {
                        'maxTokens': 200,
                        'overlapPercentage': 50
                    }
                }
            }
        )

        return response


if __name__ == "__main__":
    kb = BedrockKBAgent()
    response_kb = kb.create_kb(kb_name="bedrock-ra-01",
                  role_arn="arn:aws:iam::643045476917:role/AmazonBedrockExecutionRoleForKnowledgeBase_123023",
                  collection_arn="arn:aws:aoss:us-east-1:643045476917:collection/anddc4hozkwk6bnbzkd5",
                  index_name="bedrock-index-01")

    print(response_kb)

    kb_id = response_kb["knowledgeBase"]["knowledgeBaseId"]

    response_ds = kb.create_ds(knowledge_base_id=kb_id,
                               bucket_arn="arn:aws:s3:::bedrock-agent01")
    print(response_ds)

