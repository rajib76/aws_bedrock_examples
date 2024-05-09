from abc import abstractmethod

import boto3
from botocore.config import Config

from retrieval.base import Retrieval


class Generation():

    def __init__(self):
        self.module = "Bedrock"

    @abstractmethod
    def generate(self,
                 model_id,
                 retriever:Retrieval):
        pass

    def get_bedrock_client(self,assume_role, profile_name='default', runtime=True):
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