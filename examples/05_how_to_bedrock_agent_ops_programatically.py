# This programs does the below functions
# 1. Createa an agent role with access to claude model from Anthropic
# 2. Creates an agent with the created agent role. Also overrides the base prompt template
# 3. Prepares the agent for taking any question from user

import json
import logging
import sys
import time

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

logger = logging.getLogger("lifecycle")


class BedrockAgentLifeCycle():
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

    def _create_agent_role(self,
                          role_name="AmazonBedrockExecutionRoleForAgents_1226",
                          model_arn="arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-v2"):
        """
        This function creates the agent role with access to claude v2 of Anthropic
        :param role_name: The name of the role for the agent. This is hard coded now, can be changed while creating
        the role.
        :param model_arn: The arn of the model id, hard coded for now, but can be made dynamic
        :return: Returns the created role object
        """
        ROLE_POLICY_NAME = "bedrock_agent_role"
        iam_resource = self._return_aws_service_client(resource_name='iam')

        print("Creating an an execution role for the agent...")

        try:
            role = iam_resource.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"Service": "bedrock.amazonaws.com"},
                                "Action": "sts:AssumeRole",
                            }
                        ],
                    }
                ),
            )

            role.Policy(ROLE_POLICY_NAME).put(
                PolicyDocument=json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": "bedrock:InvokeModel",
                                "Resource": model_arn,
                            }
                        ],
                    }
                )
            )
        except ClientError as e:
            logger.error(f"Couldn't create role {role_name}. Here's why: {e}")
            raise

        print("Execution role for the agent has been created")
        return role

    def get_prompt_override_config(self):
        """
        This function returns the value for the key promptOverrideConfiguration which will be used
        while creating the agent
        :return: value for the key promptOverrideConfiguration
        """

        PRE_PROCESSING_PROMPT="""
Human: 
You are a classifying agent that filters user inputs into categories. Your job is to sort these inputs before they are passed along to the next stage.

Here is how you should classify the input:

-Category M:If the input is harmful and/or malicious even if it is fictional
-Category N:If the input is not harmful and/or malicious

<input>$question$</input>

Please think hard about the input in <thinking> XML tags and provide the category letter to sort the input into within <category> XML tags.Please also share the rationale for categorization.

Assistant:
        """

        ORCHESTRATION_PROMPT = """
Human:
You are a helpful chat assistant which answers based on the context provided below. Please only answer based on the provided context. If the answer is not there in the context, please politely say that you cannot answer the question. 

Use the following format:

<question>the input question you must answer</question>
<thought>you should always think about what to do</thought>
<action>the action to take, should be based on $instruction$
</action>
<action_input>the input to the action</action_input>
<observation>the result of the action</observation>
... (this <thought></thought>/<action></action>/<action_input></action_input>/<observation></observation> can repeat N times)
<thought>I now know the final answer</thought>
<answer>the final answer to the original input question</answer>

<context>$instruction$</context>
<question>$question$</question>

Assistant:
"""

        POST_PROCESSING_PROMPT="""
Human: 
You are an agent tasked with providing more context to an answer that a function calling agent outputs. The function calling agent takes in a user’s question and calls the appropriate functions (a function call is equivalent to an API call) that it has been provided with in order to take actions in the real-world and gather more information to help answer the user’s question.

At times, the function calling agent produces responses that may seem confusing to the user because the user lacks context of the actions the function calling agent has taken. Here’s an example:
<example>
    The user tells the function calling agent: “Acknowledge all policy engine violations under me. My alias is jsmith, start date is 09/09/2023 and end date is 10/10/2023.”

    After calling a few API’s and gathering information, the function calling agent responds, “What is the expected date of resolution for policy violation POL-001?”

    This is problematic because the user did not see that the function calling agent called API’s due to it being hidden in the UI of our application. Thus, we need to provide the user with more context in this response. This is where you augment the response and provide more information.

    Here’s an example of how you would transform the function calling agent response into our ideal response to the user. This is the ideal final response that is produced from this specific scenario: “Based on the provided data, there are 2 policy violations that need to be acknowledged - POL-001 with high risk level created on 2023-06-01, and POL-002 with medium risk level created on 2023-06-02. What is the expected date of resolution date to acknowledge the policy violation POL-001?”
</example>

It’s important to note that the ideal answer does not expose any underlying implementation details that we are trying to conceal from the user like the actual names of the functions.

Do not ever include any API or function names or references to these names in any form within the final response you create. An example of a violation of this policy would look like this: “To update the order, I called the order management APIs to change the shoe color to black and the shoe size to 10.” The final response in this example should instead look like this: “I checked our order management system and changed the shoe color to black and the shoe size to 10.”

Now you will try creating a final response. Here’s the original user input <user_input>$question$</user_input>.

Here is the latest raw response from the function calling agent that you should translate to bengali: <latest_response>$latest_response$</latest_response>.

And here is the history of the actions the function calling agent has taken so far in this conversation: <history>$responses$</history>.

Please output your transformed response within <final_response></final_response> XML tags. 

Assistant:
        """

        config = {
            "overrideLambda": "arn:aws:lambda:us-east-1:643045476917:function:preprocess-lambda",
            "promptConfigurations": [
                {
                    "basePromptTemplate": PRE_PROCESSING_PROMPT,
                    "inferenceConfiguration": {
                        "maximumLength": 2048,
                        "stopSequences": ["Human:"],
                        "temperature": 0,
                        "topK": 1,
                        "topP": 1
                    },
                    "parserMode": "OVERRIDDEN",
                    "promptCreationMode": "OVERRIDDEN",
                    "promptState": "ENABLED",
                    "promptType": "PRE_PROCESSING"
                },
                {
                    "basePromptTemplate": ORCHESTRATION_PROMPT,
                    "inferenceConfiguration": {
                        "maximumLength": 2048,
                        "stopSequences": ["Human:"],
                        "temperature": 0,
                        "topK": 1,
                        "topP": 1
                    },
                    "parserMode": "OVERRIDDEN",
                    "promptCreationMode": "OVERRIDDEN",
                    "promptState": "ENABLED",
                    "promptType": "ORCHESTRATION"
                },
                {
                    "basePromptTemplate": POST_PROCESSING_PROMPT,
                    "inferenceConfiguration": {
                        "maximumLength": 2048,
                        "stopSequences": ["Human:"],
                        "temperature": 0,
                        "topK": 1,
                        "topP": 1
                    },
                    "parserMode": "OVERRIDDEN",
                    "promptCreationMode": "OVERRIDDEN",
                    "promptState": "ENABLED",
                    "promptType": "POST_PROCESSING"
                }
            ]
        }

        return config

    def create_bedrock_agent(self, name, model_id, agent_role_arn=None):
        """
        This function creates the agent in AWS Bedrock
        :param name: Name of the agent
        :param model_id: The model id which can be found under model Foundation models -> Base Models in Bedrock
        :param agent_role_arn:The arn of the agent role
        :return: returns the agent object and its version
        """
        print("Agent creation in progress...")

        instruction = """The Taj Mahal is an ivory-white marble mausoleum on the right bank of the river Yamuna in 
        Agra, Uttar Pradesh, India. It was commissioned in 1631 by the fifth Mughal emperor, Shah Jahan to house the 
        tomb of his beloved wife, Mumtaz Mahal; it also houses the tomb of Shah Jahan himself. The tomb is the 
        centrepiece of a 17-hectare (42-acre) complex, which includes a mosque and a guest house, and is set in 
        formal gardens bounded on three sides by a crenellated wall. """
        bedrock_client = self._return_aws_service_client(resource_name='bedrock', run_time=False)
        if agent_role_arn is None:
            role_name = "AmazonBedrockExecutionRoleForAgents_1226"
            model_arn = f"arn:aws:bedrock:us-east-1::foundation-model/{model_id}"
            agent_role = self._create_agent_role(role_name=role_name, model_arn=model_arn)

        agent = bedrock_client.create_agent(
            agentName=name,
            foundationModel=model_id,
            instruction=instruction,
            agentResourceRoleArn=agent_role.arn,
            promptOverrideConfiguration=self.get_prompt_override_config()
        )


        while bedrock_client.get_agent(agentId=agent["agent"]["agentId"])["agent"]["agentStatus"] != "NOT_PREPARED":
            self.sleep_for_a_while(5)

        version = self._prepare_agent(agent["agent"])

        print("Agent is now ready to take questions...")
        return agent,version

    def _prepare_agent(self,agent):
        """
        This function is called from the create agent function to prepare the agent
        :param agent: The agent object
        :return: Returns the version of the agent
        """
        print("Agent Preparation in progress...")

        agent_id = agent["agentId"]
        bedrock_client = self._return_aws_service_client(resource_name='bedrock', run_time=False)
        version = bedrock_client.prepare_agent(agentId=agent_id)["agentVersion"]
        while bedrock_client.get_agent(agentId=agent["agentId"])["agent"]["agentStatus"] != "PREPARED":
            self.sleep_for_a_while(5)

        print("Agent Preparation is done...")
        return version

    def sleep_for_a_while(self, seconds, tick=12):
        """
        This function waits for the seconds passed for the process to complete.
        While waiting, it also displays a spinner
        :param seconds: The number of seconds to wait.
        :param tick: The number of frames per second used to animate the spinner.
        """
        spinner_parts = "|/-\\"
        wait_count = 0
        while wait_count < seconds:
            for frame in range(tick):
                sys.stdout.write(f"\r{spinner_parts[frame % len(spinner_parts)]}")
                sys.stdout.flush()
                time.sleep(1 / tick)
            wait_count += 1
        sys.stdout.write("\r")
        sys.stdout.flush()


if __name__ == "__main__":
    bd = BedrockAgentLifeCycle()
    agent,version = bd.create_bedrock_agent(name="bedrock-agent-02", model_id='anthropic.claude-v2')