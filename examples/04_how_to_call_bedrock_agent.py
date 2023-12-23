import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError


# load_dotenv()
# agent_role = os.environ.get('AGENT_ROLE')


class BedRockClient():
    """
    This class will wrap all the operations of the bedrock agent
    """

    def __init__(self,
                 region_name="us-east-1"):
        """
        Initializes the region of the service
        :param region_name: The region name of the service
        """

        self.region_name = region_name

    def return_runtime_client(self, run_time=True) -> BaseClient:
        """
        This funtion returns the appropriate bedrock client
        :param run_time: If true, returns the run time client, else the normal client
        :return: Returns the bedrock client
        """
        if run_time:
            bedrock_client = boto3.client(
                service_name="bedrock-agent-runtime",
                region_name=self.region_name)
        else:
            bedrock_client = boto3.client(
                service_name="bedrock-agent",
                region_name=self.region_name)

        return bedrock_client

    def list_agents(self):
        """
        This module calls the list agents and returns all the available agents
        :return: All the currently deployed agents
        """
        try:
            available_agents = []
            bedrock_client = self.return_runtime_client(run_time=False)
            agents = bedrock_client.list_agents()
            for agent in agents["agentSummaries"]:
                agent_status = agent["agentStatus"]
                if agent_status == "PREPARED":
                    agent_name = agent["agentName"]
                    available_agents.append(agent_name)
        except ClientError as e:
            print(e)
            raise
        else:
            return available_agents

    def invoke_bedrock_agent(self,
                             agent_id,
                             agent_alias_id,
                             session_id,
                             prompt=None):
        """
        This function will be interacting with the agent
        :param agent_id: The agent id of the agent
        :param agent_alias_id: The agent alias id of the agent
        :param session_id: A unique id that identifies the chat session
        :param prompt: The prompt or the question that needs to be answered
        :return: Returns the response
        """

        completion = ""
        traces =[]
        try:
            bedrock_client = self.return_runtime_client(run_time=True)
            response = bedrock_client.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=prompt,
            )
            for event in response.get("completion"):
                print(event)
                try:
                    trace = event["trace"]
                    traces.append(trace['trace'])
                except KeyError:
                    chunk = event["chunk"]
                    completion = completion + chunk["bytes"].decode()
                except Exception as e:
                    print(e)

        except ClientError as e:
            print(e)

        return completion, traces


if __name__ == "__main__":
    bedrock_client = BedRockClient()
    # bedrock_runtime_client = bedrock_client.return_runtime_client()

    # agents = bedrock_client.list_agents()
    # print(agents)

    response,traces = bedrock_client.invoke_bedrock_agent(agent_id="QGNVWR64AS",
                                                   agent_alias_id="O1VQBAWZQY",
                                                   session_id="session_01",
                                                   prompt="What is the interest rate?")
    print(response)
    print("-------")
    print(traces)
