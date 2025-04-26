import discord
import requests
from discord.ext import commands, tasks
from ping3 import ping
from discord.ui import Button, View
from bs4 import BeautifulSoup

# Configurações do bot
TOKEN = "xxx.xxx.xxx.xxx"  # Substitua pelo token do seu bot
SERVER_IP = "xxx.xxx.xxx.xxx"
BATTLEMETRICS_ID = "xxx.xxx.xxx.xxx"  # ID do seu servidor no BattleMetrics

# Lista de servidores permitidos (IDs dos servidores do Discord)
GUILDS_ALLOWED = [xxx.xxx.xxx.xxx]

# Dicionário de canais permitidos por servidor (ID do servidor -> ID do canal)
CHANNELS_ALLOWED = {
    xxx.xxx.xxx.xxx: xxx.xxx.xxx.xxx
}

# Configurar intents do bot
intents = discord.Intents.default()
client = commands.Bot(command_prefix="!", intents=intents)

# Função para verificar se um IP responde ao ping
def ping_server(ip):
    try:
        response = ping(ip, timeout=2)
        if response is not None:
            return f"🟢 **Online** | Latência: {int(response * 1000)}ms"
        else:
            return "🔴 **Offline**"
    except Exception as e:
        return f"🔴 **Offline (Erro: {str(e)})**"

# Função para buscar o número de jogadores via API do BattleMetrics
def get_battlemetrics_player_count_api(server_id):
    url = f"https://api.battlemetrics.com/servers/{server_id}"
    try:
        response = requests.get(url)
        data = response.json()

        players = data['data']['attributes']['players']
        max_players = data['data']['attributes']['maxPlayers']
        return f"{players}/{max_players}"
    except Exception as e:
        print(f"Erro ao acessar API do BattleMetrics: {e}")
        return "Erro ao obter dados"

# Evento chamado quando o bot estiver online
@client.event
async def on_ready():
    print(f"Bot {client.user} está online!")
    check_players.start()

# Loop que roda a cada 2 minutos para verificar status e atualizar
@tasks.loop(minutes=2)
async def check_players():
    try:
        player_count = get_battlemetrics_player_count_api(BATTLEMETRICS_ID)
        ddos_status = ping_server("xxx.xxx.xxx.xxx")  # IP do Anti-DDoS (Mikrotik, etc.)
        server_status = ping_server(SERVER_IP)

        for guild_id, channel_id in CHANNELS_ALLOWED.items():
            guild = client.get_guild(guild_id)
            if guild:
                channel = guild.get_channel(channel_id)
                if channel:
                    # Criar embed com o status
                    embed = discord.Embed(
                        title="🎮 [BR] Terra de ninguem - PVE com areas PVP |AIRDROP |KOT |BUNKER",
                        description=f"**Jogadores Online:** {player_count}",
                        color=discord.Color.green()
                    )
                    embed.set_thumbnail(url="https://i.imgur.com/45gk10W.png")
                    embed.add_field(name="Status da Proteção Anti-DDoS", value=ddos_status, inline=False)
                    embed.add_field(name="Status do Servidor de Jogo", value=server_status, inline=False)
                    embed.set_footer(text="Atualização a cada 2 minutos • Powered by OnFire")

                    # Botões
                    view = View()
                    view.add_item(Button(label="Jogar Agora", style=discord.ButtonStyle.link, url="https://onfire.top/tdnpve.html"))
                    view.add_item(Button(label="Visitar OnFire", style=discord.ButtonStyle.link, url="https://onfiregroup.com.br"))

                    # Limpar mensagens anteriores do canal
                    await channel.purge(limit=100)

                    # Enviar nova mensagem com o embed e botão
                    await channel.send(embed=embed, view=view)

    except Exception as e:
        print(f"Erro ao consultar servidor: {e}")

# Iniciar o bot
client.run(TOKEN)
