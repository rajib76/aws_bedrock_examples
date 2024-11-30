# Author: Rajib Deb
# This example shows how to create a ChatPrompt programatically in Amazon Bedrock Prompt Management
# API reference: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_Types_Agents_for_Amazon_Bedrock.html

import boto3

# Create an Amazon Bedrock Agents client
client = boto3.client(service_name="bedrock-agent")

# User Prompt
user_prompt = """
{{context}}
{{question}}
answer:
"""

# System Prompt
system_prompt = """
You are a helpful chatbot that answers a question based on the 
provided context
"""

# Create the prompt
response = client.create_prompt(
    name="ChatBot",
    description="A chatbot that answers question based on a context",
    variants=[
        {
            "name": "claude_sonnet",
            "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
            "templateType": "CHAT",
            "inferenceConfiguration": {
                "text": {
                    "temperature": 0.8,
                    "maxTokens": 3000,
                    "stopSequences": ["Human", "End"],
                    "topP": 0.999
                }
            },
            "templateConfiguration": {
                "chat": {"messages": [{"role": "user", "content": [
                    {"text": user_prompt}]}],
                         "inputVariables": [{"name": "question"}, {"name": "context"}],
                         "system": [{"text": system_prompt}]

                         }
            }
        }
    ]
)

prompt_id = response.get("id")

print("Prompt has been created successfully for prompt id: ", prompt_id)
