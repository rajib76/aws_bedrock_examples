# Author: Rajib Deb
# Date : 18-Oct-2023
import json
import os

import boto3
import botocore
from botocore.config import Config
from dotenv import load_dotenv
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import Document
import openai

load_dotenv()
llama_assumed_role = os.environ.get('LLAMA_ASSUMED_ROLE')
claude_assumed_role = os.environ.get('CLAUDE_ASSUMED_ROLE')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')


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

    def get_bedrok_model_response(self, prompt, assumed_role, model="llama"):
        """
        Get the embeddings of a text
        :param text: the text to embed
        :param assumed_role: the role which has access to AWS bedrock
        :param modelId: the model id of the embedding
        :return: The embedding vectors
        """
        modelId = ""
        body = {}
        if "llama" in model:
            modelId = "meta.llama2-13b-chat-v1"
            body = json.dumps({"prompt": prompt, "max_gen_len": 512, "temperature": 0.2, "top_p": 0.9})
        elif "anthropic" in model:
            modelId = "anthropic.claude-v2"
            body = json.dumps({"prompt": prompt, "max_tokens_to_sample": 512, "temperature": 0.2, "top_p": 0.9})

        bedrock_runtime_client = self._get_bedrock_client(assumed_role)

        accept = "*/*"
        contentType = "application/json"
        try:

            response = bedrock_runtime_client.invoke_model(
                body=body, modelId=modelId, accept=accept, contentType=contentType
            )
            response_body = json.loads(response.get("body").read())

            return response_body


        except botocore.exceptions.ClientError as error:

            if error.response['Error']['Code'] == 'AccessDeniedException':
                print(f"\x1b[41m{error.response['Error']['Message']}\
                        \nTo troubeshoot this issue please refer to the following resources.\
                         \nhttps://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html\
                         \nhttps://docs.aws.amazon.com/bedrock/latest/userguide/security-iam.html\x1b[0m\n")

            else:
                raise error

    def return_context(self):
        ## Content taken from https://www.rocketmortgage.com/learn/how-to-calculate-mortgage ##
        context = """
        There are two ways to go about calculating a monthly mortgage payment. You can go old-school and figure it out using a complicated equation, or you can use a mortgage payment calculator.

        Use The Formula
        As mentioned above, the easiest way to come to your mortgage payment is to use a mortgage calculator. However, having a basic understanding of the formula can give you an idea of how changing variables impacts the other parts of the equation. Let’s take a quick look.

        M = P*( I*(1 + I)**N ) / ((1 + I)**N − 1)

        This formula will help you calculate your mortgage payment based on the loan principal and interest before taxes, homeowners insurance and HOA fees. If it looks a little intimidating, though, you’re probably not alone – let’s break it down variable by variable so it’s easier to understand:

        M = Monthly payment: This is what you’re solving for.
        P = Principal amount: This is the loan balance, or what you’re trying to pay off.
        I = Interest rate: Remember, you’ll want to use the base interest rate and not the APR. Additionally, because the mortgage interest rate you’re charged is an annual interest rate that does represent the interest that’s supposed to be paid over the whole year, you want to divide this by 12 to get the monthly interest rate.
        N = Number of payments: This is the total number of payments in your loan term. For instance, if it’s a 30-year mortgage with monthly payments, there are 360 payments.
        There are some special situations where a spreadsheet formula might be useful. For instance, mortgage calculators tend to assume a fixed-rate mortgage. If you have an adjustable-rate mortgage (ARM) where the rate changes over time, you can set up an amortization table using the PMT function in Microsoft Excel and change the formula at a point so that the rate and time remaining reflect the new terms once the interest rate adjusts.

        Having your own formula set up also gives you the opportunity to compare different payment scenarios, including interest-only payments versus fully amortizing loans.

        As mentioned before, this covers principal and interest, but you can add in taxes and insurance once you know them to get to your total monthly payment. A lender will qualify you using these four payment factors (sometimes shortened to the acronym “PITI”. Where applicable, HOA fees are added in, and the acronym becomes “PITIA,” with the “A” standing for “association dues.”
        """

        document = Document(page_content=context, metadata={})
        return context, document

    def craft_the_prompt(self, model):

        if "anthropic" in model:
            # Prefix of the prompt
            prefix = "Human: {query}" \
                     "You are a helpful chatbot and answer questions based on provided context only. " \
                     "If the answer to the question is not there in the context, " \
                     "you can politely say that you do not have the answer"

            suffix = """
            Context: {context}
            \n\n
            Assistant: """

        else:
            # Prefix of the prompt
            prefix = "You are a helpful chatbot and answer questions based on provided context only. " \
                     "If the answer to the question is not there in the context, " \
                     "you can politely say that you do not have the answer"

            suffix = """
            Context: {context}
            User: {query}
            AI: """

        # Examples of chain of thought to be included in the prompt
        EXAMPLES = ["""Use the following format:

        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take, should be based on {context}
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat N times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question"""]

        # Template to be used
        # example_template = """
        # Context: {context}
        # User: {query}
        # AI: {answer}
        # """

        CHAT_PROMPT = PromptTemplate.from_examples(
            examples=EXAMPLES, suffix=suffix, input_variables=["context", "query"], prefix=prefix
        )
        MY_PROMPT = CHAT_PROMPT.format_prompt(context=context, query=query)
        print(MY_PROMPT)
        return CHAT_PROMPT


if __name__ == "__main__":
    bd_client = BedRockClient()
    context, document = bd_client.return_context()
    query = """
    My mortgage interest rate is 6.75% per annum and my loan amount is 800,000 USD.
    I would like to pay off in 15 years. 
    What will be my monthly payment?
    """

    model = "anthropic"

    CHAT_PROMPT = bd_client.craft_the_prompt(model)
    PROMPT = CHAT_PROMPT.format_prompt(context=context, query=query)

    response = bd_client.get_bedrok_model_response(PROMPT.text, claude_assumed_role, model=model)
    print("Response from claude....")
    print(response["completion"])

    print("------------------------")

    model = "llama"

    CHAT_PROMPT = bd_client.craft_the_prompt(model)
    PROMPT = CHAT_PROMPT.format_prompt(context=context, query=query)

    response = bd_client.get_bedrok_model_response(PROMPT.text, llama_assumed_role, model="llama")
    print("Response from llama....")
    print(response["generation"])
    print("------------------------")

    model = "gpt-4"
    CHAT_PROMPT = bd_client.craft_the_prompt(model)

    print("Response from gpt-4....")
    #
    llm = ChatOpenAI(model_name="gpt-4-1106-preview",
                     openai_api_key=OPENAI_API_KEY,
                     temperature=0,
                     max_tokens=1000)

    chain = load_qa_chain(llm, chain_type="stuff", prompt=CHAT_PROMPT, verbose=False)
    response = chain.run(input_documents=[document], query=query)

    print(response)
