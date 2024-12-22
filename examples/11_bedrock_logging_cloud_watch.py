import json

import boto3
from botocore.exceptions import ClientError


class CloudWatchLogging:
    log_group_name: str = '/chat/amazon/bedrock/cwatch/logs'

    def create_log_group(self):
        cloudwatch_logs_client = boto3.client('logs', region_name="us-east-1")
        try:
            response = cloudwatch_logs_client.create_log_group(logGroupName=self.log_group_name)
            print("Created log group successfully")
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                print("log group {log_group_name} exists".format(log_group_name=self.log_group_name))
            else:
                print("Failed to create log group. Exception is {e}".format(e=e))


class BedrockChatAgent:

    def __init__(self):
        self.log_group_name = '/chat/amazon/bedrock/cwatch/logs'
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.bedrock_client = boto3.client('bedrock', region_name="us-east-1")
        loggingConfig = {
            'cloudWatchConfig': {
                'logGroupName': self.log_group_name,
                'roleArn': 'arn:aws:iam::643045476917:role/bedrock_cloudwatch_role',
                'largeDataDeliveryS3Config': {
                    'bucketName': 'bedrock-cloudwatch-bucket',
                    'keyPrefix': 'amazon_bedrock_large_data_delivery',
                }
            },
            's3Config': {
                'bucketName': 'bedrock-cloudwatch-bucket',
                'keyPrefix': 'amazon_bedrock_logs',
            },
            'textDataDeliveryEnabled': True,
        }
        self.bedrock_client.put_model_invocation_logging_configuration(loggingConfig=loggingConfig)
        response = self.bedrock_client.get_model_invocation_logging_configuration()
        print(response)

    def answer_chat_question(self, prompt):
        kwargs = {
            "modelId": "amazon.titan-text-express-v1",
            "contentType": "application/json",
            "accept": "*/*",
            "body": json.dumps(
                {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": 512,
                        "temperature": 0.7,
                        "topP": 0.9
                    }
                }
            )
        }
        response = self.bedrock_runtime.invoke_model(**kwargs)
        response_body = json.loads(response.get('body').read())
        generation = response_body['results'][0]['outputText']

        return generation


if __name__ == "__main__":
    cwatch = CloudWatchLogging()
    cwatch.create_log_group()

    chat_agent = BedrockChatAgent()
    prompt = "What is reflection?"
    answer = chat_agent.answer_chat_question(prompt)
    print(answer)
