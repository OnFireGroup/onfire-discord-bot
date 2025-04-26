import discord
import requests
from discord.ext import commands, tasks
from ping3 import ping
from discord.ui import Button, View

# Configurações do bot
TOKEN = "xxx.xxx.xxx.xxx"  # Substitua pelo token do seu bot
SERVER_IP = "xxx.xxx.xxx.xxx"  # IP do servidor com proteção anti DDoS
# IDs dos servidores no BattleMetrics
SERVER_1_ID = "xxx.xxx.xxx.xxx"
SERVER_2_ID = "xxx.xxx.xxx.xxx"

# Lista de servidores permitidos (IDs dos servidores do Discord)
GUILDS_ALLOWED = [xxx.xxx.xxx.xxx]
CHANNELS_ALLOWED = {
    xxx.xxx.xxx.xxx: xxx.xxx.xxx.xxx
}

# Intents e cliente
intents = discord.Intents.default()
client = commands.Bot(command_prefix="!", intents=intents)

# Ping simples
def ping_server(ip):
    try:
        response = ping(ip, timeout=2)
        return f"🟢 **Online** | Latência: {int(response * 1000)}ms" if response else "🔴 **Offline**"
    except Exception as e:
        return f"🔴 **Offline (Erro: {str(e)})**"

# Busca dados da API BattleMetrics
def get_battlemetrics_player_count(server_id):
    url = f"https://api.battlemetrics.com/servers/{server_id}"
    try:
        response = requests.get(url)
        data = response.json()
        players = data['data']['attributes']['players']
        max_players = data['data']['attributes']['maxPlayers']
        return f"{players}/{max_players}"
    except Exception as e:
        print(f"Erro ao acessar API BattleMetrics (ID {server_id}): {e}")
        return "Erro ao obter dados"

@client.event
async def on_ready():
    print(f"Bot {client.user} está online!")
    check_players.start()

@tasks.loop(minutes=2)
async def check_players():
    try:
        # Pega dados dos dois servidores
        server1_players = get_battlemetrics_player_count(SERVER_1_ID)
        server2_players = get_battlemetrics_player_count(SERVER_2_ID)

        server1_status = ping_server(SERVER_IP)
        server2_status = ping_server(SERVER_IP)
        ddos_status = ping_server("xxx.xxx.xxx.xxx")

        for guild_id, channel_id in CHANNELS_ALLOWED.items():
            guild = client.get_guild(guild_id)
            if guild:
                channel = guild.get_channel(channel_id)
                if channel:
                    # Limpa mensagens antigas
                    await channel.purge(limit=100)

                    # Embed do servidor 1
                    embed1 = discord.Embed(
                        title="🎮 Servidor Arma Reforger 1",
                        description=f"**Jogadores Online:** {server1_players}",
                        color=discord.Color.green()
                    )
                    embed1.set_thumbnail(url="https://i.imgur.com/I4CzqIa.jpeg")
                    embed1.add_field(name="Status do Servidor", value=server1_status, inline=False)
                    embed1.add_field(name="Proteção Anti-DDoS", value=ddos_status, inline=False)
                    embed1.set_footer(text="Atualização a cada 2 minutos • Powered by OnFire")

                    # Embed do servidor 2
                    embed2 = discord.Embed(
                        title="🎮 Servidor Hardcore",
                        description=f"**Jogadores Online:** {server2_players}",
                        color=discord.Color.blue()
                    )
                    embed2.set_thumbnail(url="https://i.imgur.com/I4CzqIa.jpeg")
                    embed2.add_field(name="Status do Servidor", value=server2_status, inline=False)
                    embed2.add_field(name="Proteção Anti-DDoS", value=ddos_status, inline=False)
                    embed2.set_footer(text="Atualização a cada 2 minutos • Powered by OnFire")

                    # Botões
                    view = View()
                    view.add_item(Button(label="Jogar Agora", style=discord.ButtonStyle.link, url="https://onfire.top/sas.html"))
                    view.add_item(Button(label="Visitar OnFire", style=discord.ButtonStyle.link, url="https://onfiregroup.com.br"))

                    # Envia os dois embeds
                    await channel.send(embed=embed1)
                    await channel.send(embed=embed2, view=view)

    except Exception as e:
        print(f"Erro ao consultar servidor: {e}")

client.run(TOKEN)