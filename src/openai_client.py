from utils.openai import get_azure_openai_client

client, deployment_model = get_azure_openai_client()


def create_shortDescription(message):
    """
    Function to send a message to the OpenAI API and get a summary in return.
    """
    response = client.chat.completions.create(
        model=deployment_model,
        messages=[
            {"role": "system", "content": "Lav et resume af denne tekst på maks 140 tegn som beskriver løsningen."},
            {"role": "user", "content": message}
        ]
    )
    bot_response = response.choices[0].message.content
    if len(bot_response) > 140:
        bot_response = bot_response[:137] + '...'
    return bot_response
