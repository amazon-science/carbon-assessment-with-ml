import ast
import json
import logging
import os
from typing import Any, Dict, Optional

import boto3
import numpy as np
import rich.traceback
from botocore.config import Config
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_community.llms import Bedrock
from langchain_core.prompts import PromptTemplate
from prompts import lca_assistant_prompt, system_lca_assistant_prompt

rich.traceback.install(show_locals=False)

logger = logging.getLogger("eifmap")


# taken from https://github.com/ClickHouse/bedrock_rag/blob/main/bedrock.py
def get_bedrock_client(
    assumed_role: Optional[str] = None,
    region: Optional[str] = None,
    runtime: Optional[bool] = True,
):
    """Create a boto3 client for Amazon Bedrock, with optional configuration overrides.

    Parameters
    ----------
    assumed_role : str, optional
        Optional ARN of an AWS IAM role to assume for calling the Bedrock service. If not
        specified, the current active credentials will be used.
    region : str, optional
        Optional name of the AWS Region in which the service should be called (e.g. "us-east-1").
        If not specified, AWS_REGION or AWS_DEFAULT_REGION environment variable will be used.
    runtime : bool, optional
        Optional choice of getting different client to perform operations with the Amazon Bedrock service.
    """

    if region is None:
        target_region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION"))
    else:
        target_region = region

    logger.info(f"Create new client\n  Using region: {target_region}")
    session_kwargs = {"region_name": target_region}
    client_kwargs = {**session_kwargs}

    profile_name = os.environ.get("AWS_PROFILE")
    if profile_name:
        logger.info(f"  Using profile: {profile_name}")
        session_kwargs["profile_name"] = profile_name

    retry_config = Config(
        region_name=target_region,
        retries={
            "max_attempts": 10,
            "mode": "standard",
        },
    )
    session = boto3.Session(**session_kwargs)

    if assumed_role:
        logger.info(f"  Using role: {assumed_role}", end="")
        sts = session.client("sts")
        response = sts.assume_role(RoleArn=str(assumed_role), RoleSessionName="langchain-llm-1")
        logger.info(" ... successful!")
        client_kwargs["aws_access_key_id"] = response["Credentials"]["AccessKeyId"]
        client_kwargs["aws_secret_access_key"] = response["Credentials"]["SecretAccessKey"]
        client_kwargs["aws_session_token"] = response["Credentials"]["SessionToken"]

    if runtime:
        service_name = "bedrock-runtime"
    else:
        service_name = "bedrock"

    bedrock_client = session.client(service_name=service_name, config=retry_config, **client_kwargs)

    logger.info("boto3 Bedrock client successfully created!")
    logger.info(bedrock_client._endpoint)
    return bedrock_client


class LCAAssistant:
    def __init__(self, llm_model="anthropic.claude-3-sonnet-20240229-v1:0"):
        self.model_list = [
            "anthropic.claude-3-sonnet-20240229-v1:0"
        ]

        self.llm_model = llm_model
        self.boto3_bedrock = get_bedrock_client()
        if self.llm_model in self.model_list:
            self.history = []
        else:
            assistant_model = Bedrock(
                model_id=llm_model,
                client=self.boto3_bedrock,
                model_kwargs={"temperature": 0},
            )
            memory = ConversationBufferMemory(ai_prefix="Assistant")
            self.conversation = ConversationChain(llm=assistant_model, verbose=False, memory=memory)
            self.conversation.prompt = PromptTemplate.from_template(lca_assistant_prompt)
        logger.info("LCA Assistant initialized")

    def reset_mem(self):
        if self.llm_model in self.model_list:
            self.history = []
        else:
            self.memory.clear()
            self.conversation.prompt = PromptTemplate.from_template(lca_assistant_prompt)
    
    def chat(self, text, temperature=0.0):
        if self.llm_model in self.model_list:
            input_body = dict()
            input_body["messages"] = [{"role": "user", "content": text}]
            self.history += input_body["messages"]

            try:
                response = self.boto3_bedrock.invoke_model(
                    body=json.dumps(
                        {
                            "anthropic_version": "bedrock-2023-05-31",
                            "temperature": temperature,
                            "max_tokens": 4096,
                            "system": system_lca_assistant_prompt,
                            "messages": self.history,
                        }
                    ),
                    modelId=self.llm_model,
                )
            except Exception as e:
                logger.exception(e)
                logger.exception("Returning empty string")
                return ""
            response_body = json.loads(response.get("body").read())
            self.history.append({key: response_body[key] for key in ["role", "content"]})
            return response_body.get("content")[0]["text"]

        return self.conversation.invoke(text)["response"].strip()

    def __call__(
        self,
        text,
        format="text",
        reset_mem=False,
        retries=1,
        temperature=0.0,
        validation_fn=None,
    ):
        if reset_mem:
            self.reset_mem()
        if format == "python":
            while retries > 0:
                try:  
                    response = self.chat(text, temperature=temperature)
                    parsed = ast.literal_eval(response)
                    if validation_fn:
                        validation_fn(parsed)
                except Exception as e:  
                    logger.exception(e)
                    logger.warning("Retrying again")
                    text = f"Your previous response, when parsed with a python code interpreter, caused this python exception: {e!r}\n. This time generate a response that doesn't cause this exception. ### ORIGINAL INSTRUCTIONS ###\n" + text
                    retries -= 1
                else:
                    return parsed
            return ast.literal_eval(self.chat(text, temperature=temperature))
        return self.chat(text, temperature=temperature) 
