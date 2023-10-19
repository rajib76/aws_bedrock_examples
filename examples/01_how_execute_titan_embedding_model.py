# Author: Rajib Deb
# Date : 18-Oct-2023
import json
import os

import boto3
import botocore
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()
assumed_role = os.environ.get('ASSUMED_ROLE')


class BedRockClient():
    def __init__(self):
        self.module = "AWS Bedrock"

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

    def get_embeddings(self, text, assumed_role, modelId="amazon.titan-embed-text-v1"):
        """
        Get the embeddings of a text
        :param text: the text to embed
        :param assumed_role: the role which has access to AWS bedrock
        :param modelId: the model id of the embedding
        :return: The embedding vectors
        """
        bedrock_runtime_client = self._get_bedrock_client(assumed_role)
        body = json.dumps({"inputText": text})
        accept = "application/json"
        contentType = "application/json"
        try:

            response = bedrock_runtime_client.invoke_model(
                body=body, modelId=modelId, accept=accept, contentType=contentType
            )
            response_body = json.loads(response.get("body").read())

            embedding = response_body.get("embedding")

            return embedding


        except botocore.exceptions.ClientError as error:

            if error.response['Error']['Code'] == 'AccessDeniedException':
                print(f"\x1b[41m{error.response['Error']['Message']}\
                        \nTo troubeshoot this issue please refer to the following resources.\
                         \nhttps://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html\
                         \nhttps://docs.aws.amazon.com/bedrock/latest/userguide/security-iam.html\x1b[0m\n")

            else:
                raise error


if __name__ == "__main__":
    text = "Amazon Bedrock supports focundational models like AI21 Labs, Anthropic, Stability AI"
    bd_client = BedRockClient()
    embedding = bd_client.get_embeddings(text, assumed_role)
    print(f"The embedding vector has {len(embedding)} values\n{embedding[0:3] + ['...'] + embedding[-3:]}")
