import boto3

client = boto3.client(service_name="bedrock-agent")


def list_all_prompts():
    prompts = client.list_prompts()
    prompt_summaries = prompts["promptSummaries"]
    prompt_content = {}
    for prompt_summary in prompt_summaries:
        prompt_name = prompt_summary.get("name")
        prompt_id = prompt_summary.get("id")
        prompt_content[prompt_name] = prompt_id
    return prompt_content


def get_prompt_content(name: str):
    prompts = list_all_prompts()
    prompt_id = prompts.get(name)

    prompt = client.get_prompt(
        promptIdentifier=prompt_id,
    )

    return prompt.get("variants")


if __name__ == "__main__":
    prompt_variants = get_prompt_content("ChatBot")
    for prompt_variant in prompt_variants:
        print(prompt_variant)

