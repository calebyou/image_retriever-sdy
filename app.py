import os
from prompts import SYSTEM_PROMPT, RETRIEVE_PROMPT
import chainlint as cl
import asyncio
import openai
import json
from datetime import datetime
from prompts import SYSTEM_PROMPT, RETRIEVE_PROMPT
from image_analyzer import read_image, format_image_info, parse_image
from langsmith.wrappers import wrap_openai
from langsmith import traceable

load_dotenv()

configurations = {
    "mistral_7B_instruct": {
        "endpoint_url": os.getenv("MISTRAL_7B_INSTRUCT_ENDPOINT"),
        "api_key": os.getenv("RUNPOD_API_KEY"),
        "model": "mistralai/Mistral-7B-Instruct-v0.2"
    },
    "mistral_7B": {
        "endpoint_url": os.getenv("MISTRAL_7B_ENDPOINT"),
        "api_key": os.getenv("RUNPOD_API_KEY"),
        "model": "mistralai/Mistral-7B-v0.1"
    },
    "openai_gpt-3.5-turbo": {
        "endpoint_url": os.getenv("OPENAI_ENDPOINT"),
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-3.5-turbo"
    }
}

# Choose configuration
config_key = "openai_gpt-3.5-turbo"
# config_key = "mistral_7B_instruct"
#config_key = "mistral_7B"

# Get selected configuration
config = configurations[config_key]

# Initialize the OpenAI async client
# client = openai.AsyncClient(api_key=config["api_key"], base_url=config["endpoint_url"])
client = wrap_openai(openai.AsyncClient(api_key=config["api_key"], base_url=config["endpoint_url"]))



gen_kwargs = {
    "model": config["model"],
    "temperature": 0.3,
    "max_tokens": 500
}

# Configuration setting to enable or disable the system prompt
ENABLE_SYSTEM_PROMPT = True
ENABLE_RATE_CONTEXT = True


@traceable
def get_latest_user_message(message_history):
    # Iterate through the message history in reverse to find the last user message
    for message in reversed(message_history):
        if message['role'] == 'user':
            return message['content']
    return None

async def assess_message(message_history):
    file_path = "document_record.md"
    markdown_content = read_document_record(file_path)
    parsed_record = parse_document_record(markdown_content)

    latest_message = get_latest_user_message(message_history)

    # Remove the original prompt from the message history for assessment
    filtered_history = [msg for msg in message_history if msg['role'] != 'system']

    # Convert message history, alerts, and title to strings
    history_str = json.dumps(filtered_history, indent=4)
    alerts_str = json.dumps(parsed_record.get("Alerts", []), indent=4)
    title_str = json.dumps(parsed_record.get("Title", {}), indent=4)
    
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Generate the sumarize prompt
    filled_prompt = SUMMARIZE_PROMPT.format(
        latest_message=latest_message,
        history=history_str,
        existing_alerts=alerts_str,
        existing_title=title_str,
        current_date=current_date
    )
    if ENABLE_RATE_CONTEXT:
        filled_prompt += "\n" + RATE_CONTEXT
    print("Filled prompt: \n\n", filled_prompt)

    response = await client.chat.completions.create(messages=[{"role": "system", "content": filled_prompt}], **gen_kwargs)

    summary_output = response.choices[0].message.content.strip()
    print("Summary Output: \n\n", summary_output)

    # Parse the summary output
    new_alerts, title_updates = parse_summary_output(summary_output)

    # Update the document record with the new alerts and Title updates
    parsed_record["Alerts"].extend(new_alerts)
    for update in title_updates:
        title = update["title"]
        rate = update["rate"]
        parsed_record["Title"][rate] = title

    # Format the updated record and write it back to the file
    updated_content = format_document_record(
        parsed_record["document Information"],
        parsed_record["Alerts"],
        parsed_record["Title"]
    )
    write_document_record(file_path, updated_content)

@traceable
def parse_summary_output(output):
    try:
        parsed_output = json.loads(output)
        new_alerts = parsed_output.get("new_alerts", [])
        title_updates = parsed_output.get("title_updates", [])
        return new_alerts, title_updates
    except json.JSONDecodeError as e:
        print("Failed to parse summary output:", e)
        return [], []

@cl.on_message
async def on_message(message: cl.Message):
    message_history = cl.user_session.get("message_history", [])

    if ENABLE_SYSTEM_PROMPT and (not message_history or message_history[0].get("role") != "system"):
        system_prompt_content = SYSTEM_PROMPT
        if ENABLE_RATE_CONTEXT:
            system_prompt_content += "\n"
        message_history.insert(0, {"role": "system", "content": system_prompt_content})

    message_history.append({"role": "user", "content": message.content})

    asyncio.create_task(assess_message(message_history))
    
    response_message = cl.Message(content="")
    await response_message.send()

    if config_key == "mistral_7B":
        stream = await client.completions.create(prompt=message.content, stream=True, **gen_kwargs)
        async for part in stream:
            if token := part.choices[0].text or "":
                await response_message.stream_token(token)
    else:
        stream = await client.chat.completions.create(messages=message_history, stream=True, **gen_kwargs)
        async for part in stream:
            if token := part.choices[0].delta.content or "":
                await response_message.stream_token(token)

    message_history.append({"role": "assistant", "content": response_message.content})
    cl.user_session.set("message_history", message_history)
    await response_message.update()


if __name__ == "__main__":
    cl.main()
