# This is not complete yet. DO NOT USE as of now.
import asyncio
import json
import logging
import sys
import time

import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
logger = logging.getLogger(__name__)
ROLE_POLICY_NAME = "agent_permissions"


def _create_agent_alias():
    bedrock_agent_client = boto3.client(
        service_name="bedrock-agent", region_name=REGION
    )
    print("Creating an agent alias...")

    agent_alias_name = "test_agent_alias"
    agent_alias = bedrock_agent_client.create_agent_alias(
        agentAliasName=agent_alias_name, agentId="AHELISDNHY"
    )

    while bedrock_agent_client.get_agent(agentId="AHELISDNHY")["agent"]["agentStatus"] != "PREPARED":
        wait(2)

    return agent_alias

def _chat_with_agent():
    print("-" * 88)
    print("The agent is ready to chat.")
    print("Try asking for the date or time. Type 'exit' to quit.")

    while True:
        prompt ="Where is Taj Mahal?"

        if prompt == "exit":
            break

        response = asyncio.run(_invoke_agent(prompt))

        print(f"Agent: {response}")


async def _invoke_agent(prompt):
    runtime_client = boto3.client(
        service_name="bedrock-agent-runtime", region_name=REGION)
    response = runtime_client.invoke_agent(
        agentId="AHELISDNHY",
        agentAliasId="Y3Z63CETRE",
        sessionId="Session",
        inputText=prompt,
    )

    completion = ""

    for event in response.get("completion"):
        chunk = event["chunk"]
        completion += chunk["bytes"].decode()

    return completion

def wait(seconds, tick=12):
    """
    Waits for a specified number of seconds, while also displaying an animated
    spinner.

    :param seconds: The number of seconds to wait.
    :param tick: The number of frames per second used to animate the spinner.
    """
    progress = "|/-\\"
    waited = 0
    while waited < seconds:
        for frame in range(tick):
            sys.stdout.write(f"\r{progress[frame % len(progress)]}")
            sys.stdout.flush()
            time.sleep(1 / tick)
        waited += 1
    sys.stdout.write("\r")
    sys.stdout.flush()

def _prepare_agent():
    bedrock_agent_client = boto3.client(
        service_name="bedrock-agent", region_name=REGION
    )
    print("Preparing the agent...")

    agent_id = "AHELISDNHY"
    version = bedrock_agent_client.prepare_agent(agentId=agent_id)["agentVersion"]
    while bedrock_agent_client.get_agent(agentId=agent_id)["agent"]["agentStatus"] != "PREPARED":
        wait(2)


    return version

def _create_agent():
    bedrock_agent_client = boto3.client(
        service_name="bedrock-agent", region_name=REGION
    )
    name, model_id = "bedrock-agent", "anthropic.claude-v2"
    print("Creating the agent...")

    instruction = """
         You are a friendly chat bot. You have access to a function called that returns
         information about the current date and time. When responding with date or time,
         please make sure to add the timezone UTC.
         """
    agent = bedrock_agent_client.create_agent(
        agentName=name,
        foundationModel=model_id,
        instruction=instruction,
        agentResourceRoleArn="arn:aws:iam::643045476917:role/AmazonBedrockExecutionRoleForAgents_05"
    )

    print(agent)
    print(bedrock_agent_client.get_agent(agentId = agent["agent"]["agentId"]))
    agentid = agent["agent"]["agentId"]
    while bedrock_agent_client.get_agent(agentId=agentid)["agent"]["agentStatus"] != "NOT_PREPARED":
        wait(2)

    return agent


def create_agent_role():
    try:
        iam_resource = boto3.resource("iam")
        role_name = f"AmazonBedrockExecutionRoleForAgents_05"
        model_arn = f"arn:aws:bedrock:{REGION}::foundation-model/{model_id}*"

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


if __name__ == "__main__":
    # create_agent_role()
    # _create_agent()
    # print(_prepare_agent())
    # print(_create_agent_alias())
    print(_chat_with_agent())
    # bedrock_agent_client = boto3.client(
    #     service_name="bedrock-agent", region_name=REGION)
    # runtime_client = boto3.client(
    #     service_name="bedrock-agent-runtime", region_name=REGION)
    # iam_resource = boto3.resource("iam")
