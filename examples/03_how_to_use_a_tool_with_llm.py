import os

from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.llms.bedrock import Bedrock
from langchain.tools import StructuredTool

load_dotenv()
llama_assumed_role = os.environ.get('LLAMA_ASSUMED_ROLE')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')


# def setup_bedrock():
#     """Initialize the Bedrock runtime."""
#     return boto3.client(
#         service_name="bedrock-runtime",
#         region_name="us-east-1",
#     )
#
#
# def initialize_llm(client):
#     """Initialize the language model."""
#     llm = Bedrock(client=client, model_id="cohere.command-text-v14")
#     llm.model_kwargs = {"temperature": 0.0}
#     return llm


#
# # Setup bedrock
# bedrock_runtime = boto3.client(
#     service_name="bedrock-runtime",
#     region_name="us-east-1",
# )


def get_llm_instance():
    # initialize LLM (we use ChatOpenAI because we'll later define a `chat` agent)
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        temperature=0,
        model_name='gpt-3.5-turbo'
    )

    # llm = Bedrock(
    #     credentials_profile_name="default", model_id="cohere.command-text-v14"
    # )
    #
    # llm = Bedrock(
    #     credentials_profile_name="default", model_id="anthropic.claude-v2"
    # )


    #
    # Initialize bedrock and llm
    # bedrock_runtime = setup_bedrock()
    # llm = initialize_llm(bedrock_runtime)

    return llm


def mortgage_calculator(loan_amount, interest_rate, loan_term) -> float:
    """Formula to calculate monthly mortgage payments"""
    interest_rate = float(interest_rate) / 100 / 12
    months = float(loan_term) * 12
    mortgagePayment = float(loan_amount) * (interest_rate * (1 + interest_rate)
                                     ** months) / ((1 + interest_rate) ** months - 1)

    return mortgagePayment


def get_mortgage_agent():
    tool = StructuredTool.from_function(mortgage_calculator)
    agent_executor = initialize_agent(
        [tool],
        llm=get_llm_instance(),
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
    )

    return agent_executor


if __name__ == "__main__":
    print("Get the result by directly calling the python script")
    loan_amount = 800000
    interest_rate = 6.75
    loan_term = 15
    value = mortgage_calculator(loan_amount, interest_rate, loan_term)
    print("Value from python script ", value)
    print("--------------------------------")

    # Structured tools are compatible with the STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION agent type.

    print("Get the result by calling the LLM enabled with the python script tool")
    agent_executor = get_mortgage_agent()
    response = agent_executor.run(
        "My mortgage interest rate is 6.75% per annum and my loan amount is 800,000 USD.I would like to pay "
        "off in 15 years. What will be my monthly payment?")

    # response = agent_executor.invoke(
    #     {"input": "My mortgage interest rate is 6.75% per annum and my loan amount is 800,000 USD.I would like to pay "
    #               "off in 15 years. What will be my monthly payment?", })

    print(response)
