import discord
from openai import OpenAI
import json
import re

price_per_token_3_5 = 0.0015/1000
price_per_token_4 = 0.03/1000


# Charger la configuration
with open('config.json') as config_file:
    config = json.load(config_file)

# Initialiser le client Discord
intents = discord.Intents.default()
intents.typing = False  # Optional: Disable typing events if not needed
intents.presences = False  # Optional: Disable presence events if not needed

client = discord.Client(intents=intents)

# Initialiser le client OpenAI
client_openai = OpenAI(
    api_key=config["openai_api_key"]
)

@client.event
async def on_ready():
    print(f'Nous sommes connectés en tant que {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    model = "gpt-3.5-turbo"
    # Regex pour détecter ?bx avec x un nombre entier
    prefix_pattern = r"\?b(\d+)"
    message_rcv = message.content
    print(f"Message reçu : {message_rcv}")
    history_messages = []  # Initialisation de la liste d'historique des messages

    if message_rcv.startswith("?"):
        cmd_match = re.match(prefix_pattern, message_rcv)
        if message_rcv[1] == "4":
            model = "gpt-4-1106-preview"
            message_rcv = message_rcv[2:]
        elif message_rcv[1] == "h":
            await message.channel.send("```?4 pour utiliser gpt-4-1106-preview\n? pour utiliser gpt-3.5-turbo\n?b[x] pour définir l'historique```")
            return
        elif cmd_match:
            history_limit = int(cmd_match.group(1))  # Convertir x en entier
            message_rcv = message_rcv[cmd_match.end():].strip()  # Supprimer la commande de l'historique
            async for hist_message in message.channel.history(limit=history_limit+1):
                # Assurez-vous de ne pas inclure le message actuel dans l'historique
                if hist_message.id != message.id:
                    history_messages.append({"role": "user", "content": hist_message.content})
            history_messages = history_messages[::-1]  # Inverser pour avoir l'ordre chronologique

    try:
        response = client_openai.chat.completions.create(
            model=model,
            messages=history_messages + [{"role": "user", "content": message_rcv}],
        )
        price = response.usage.total_tokens * (price_per_token_3_5 if model == "gpt-3.5-turbo" else price_per_token_4)
        await message.channel.send(response.choices[0].message.content + f"\n\nPrix de la réponse : {price} USD")
        print(f"Réponse générée : {response.choices[0].message.content}")
        print(f"Prix de la réponse : {price} USD")
    except Exception as e:
        print(f"Erreur lors de la génération de la réponse : {e}")
        await message.channel.send("Désolé, je ne peux pas répondre à cette question pour le moment.")


# Démarrer le bot
client.run(config["discord_token"])
