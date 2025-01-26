# Author : Rajib
# date : 26-JAN-2025
# Programmatically create topic denial guardrails
import boto3


class AWSGuardRails:
    def __init__(self):
        self.client = boto3.client('bedrock')

    def create_topic_denial(self):
        """
        programatic creation of topic denial guardrail
        :return: Response from the guardrail
        """
        name = 'political-guardrail'
        description = 'Prevents the model from providing any information related to politics'
        blockedInputMessaging = """
        I am sorry, I cannot answer any political questions. Ask me anyother question
        """
        blockedOutputsMessaging = """
        I apologize, I cannot share any political information
        """
        topicPolicyConfig = {
            'topicsConfig': [
                {
                    "name": "political-topics",
                    "definition": "requests for information related to politics",
                    "examples": [
                        "can you tell me who is going to win the next Indian election?",
                        "Who will be the next president of India",
                        "Who will win the Assembly elections"
                    ],
                    "type": "DENY"
                }
            ]
        }
        tags = [
            {'key': 'scope', 'value': 'political-guardrail'},
            {'key': 'environment', 'value': 'production'}
        ]

        GUARDRAIL_RESPONSE = self.client.create_guardrail(name=name,
                                                          description=description,
                                                          topicPolicyConfig=topicPolicyConfig,
                                                          blockedInputMessaging=blockedInputMessaging,
                                                          blockedOutputsMessaging=blockedOutputsMessaging,
                                                          tags=tags)

        return GUARDRAIL_RESPONSE


if __name__ == "__main__":
    guard = AWSGuardRails()
    RESPONSE = guard.create_topic_denial()
    print(RESPONSE)
