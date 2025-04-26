import discord
import requests
from discord.ext import commands, tasks
from ping3 import ping
from discord.ui import Button, View

# Token e IP base
TOKEN = "xxx.xxx.xxx.xxx"
DDOS_PROTECT_IP = "xxx.xxx.xxx.xxx"

# Lista de servidores permitidos
GUILDS_ALLOWED = [xxx.xxx.xxx.xxx]
CHANNELS_ALLOWED = {
    xxx.xxx.xxx.xxx: xxx.xxx.xxx.xxx
}
# Canal onde será postado o resumo com total de jogadores
SUMMARY_CHANNEL = {
    xxx.xxx.xxx.xxx: xxx.xxx.xxx.xxx  # <-- Substitua pelo ID real do canal de resumo
}

intents = discord.Intents.default()
client = commands.Bot(command_prefix="!", intents=intents)

# Lista de servidores com apelido, ID BM, IP, imagem (editável)
SERVERS = [
    {"apelido": "SaS Modded",             "id": "xxx.xxx.xxx.xxx", "ip": "xxx.xxx.xxx.xxx", "img": "https://i.imgur.com/I4CzqIa.jpeg"},
    {"apelido": "SaS Hardcore",           "id": "xxx.xxx.xxx.xxx", "ip": "xxx.xxx.xxx.xxx", "img": "https://i.imgur.com/I4CzqIa.jpeg"},
    {"apelido": "Evolution Z",            "id": "xxx.xxx.xxx.xxx", "ip": "xxx.xxx.xxx.xxx",   "img": "https://i.imgur.com/INYdCbe.jpeg"},
    {"apelido": "Terra de Ninguém",       "id": "xxx.xxx.xxx.xxx", "ip": "xxx.xxx.xxx.xxx",   "img": "https://i.imgur.com/45gk10W.png"},
    {"apelido": "Squad FEB",              "id": "xxx.xxx.xxx.xxx", "ip": "xxx.xxx.xxx.xxx",   "img": "https://i.imgur.com/k7b5ca1.png"},
    {"apelido": "Servidor 31518561",      "id": "xxx.xxx.xxx.xxx", "ip": "xxx.xxx.xxx.xxx",   "img": "https://i.imgur.com/k7b5ca1.png"},
    {"apelido": "Servidor 28601902",      "id": "xxx.xxx.xxx.xxx", "ip": "xxx.xxx.xxx.xxx",   "img": "https://i.imgur.com/k7b5ca1.png"},
    {"apelido": "Servidor 32805592",      "id": "xxx.xxx.xxx.xxx", "ip": "xxx.xxx.xxx.xxx",   "img": "https://i.imgur.com/k7b5ca1.png"},
    {"apelido": "Arma Reforger FEB",      "id": "xxx.xxx.xxx.xxx", "ip": "xxx.xxx.xxx.xxx",   "img": "https://i.imgur.com/k7b5ca1.png"},
    {"apelido": "Programado pra Matar",   "id": "xxx.xxx.xxx.xxx", "ip": "xxx.xxx.xxx.xxx",   "img": "https://i.imgur.com/3bJY8u3.png"}
]

# Função de ping
def ping_server(ip):
    try:
        response = ping(ip, timeout=2)
        return f"🟢 **Online** | Latência: {int(response * 1000)}ms" if response else "🔴 **Offline**"
    except:
        return "🔴 **Offline**"

# Função para obter nome, players e jogo via API
def get_battlemetrics_data(server_id):
    url = f"https://api.battlemetrics.com/servers/{server_id}"
    try:
        response = requests.get(url)
        data = response.json()

        name = data['data']['attributes']['name']
        players = data['data']['attributes']['players']
        max_players = data['data']['attributes']['maxPlayers']

        game_raw = data['data']['relationships']['game']['data']['id']
        game_name = game_raw.replace("-", " ").title()

        return name, f"{players}/{max_players}", game_name
    except Exception as e:
        print(f"[Erro] API BM ({server_id}): {e}")
        return "Desconhecido", "Erro ao obter dados", "Jogo Desconhecido"

# Evento de inicialização
@client.event
async def on_ready():
    print(f"Bot {client.user} está online!")
    check_players.start()

# Loop de verificação
@tasks.loop(minutes=2)
async def check_players():
    try:
        ddos_status = ping_server(DDOS_PROTECT_IP)
        embeds = []

        for srv in SERVERS:
            nome_bm, player_count, game_name = get_battlemetrics_data(srv["id"])
            server_status = ping_server(srv["ip"])

            embed = discord.Embed(
                title=f"🎮 {srv['apelido']} - {nome_bm}",
                description=f"**Jogadores Online:** {player_count}",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=srv["img"])
            embed.add_field(name="Status do Servidor", value=server_status, inline=False)
            embed.add_field(name="Proteção Anti-DDoS", value=ddos_status, inline=False)
            embed.add_field(name="Jogo", value=f"🎮 {game_name}", inline=False)
            embed.set_footer(text="Atualização a cada 2 minutos • Powered by OnFire")

            embeds.append(embed)

        for guild_id, channel_id in CHANNELS_ALLOWED.items():
            guild = client.get_guild(guild_id)
            if guild:
                channel = guild.get_channel(channel_id)
                if channel:
                    await channel.purge(limit=100)

                    view = View()
                    view.add_item(Button(label="Visitar OnFire", style=discord.ButtonStyle.link, url="https://onfiregroup.com.br"))

                    await channel.send(embeds=embeds, view=view)

        # Total de jogadores
        total_players = 0
        for srv in SERVERS:
            try:
                _, player_count_str, _ = get_battlemetrics_data(srv["id"])
                players_online = int(player_count_str.split('/')[0])
                total_players += players_online
            except:
                continue

        # Enviar no canal de resumo
        for guild_id, summary_channel_id in SUMMARY_CHANNEL.items():
            guild = client.get_guild(guild_id)
            if guild:
                summary_channel = guild.get_channel(summary_channel_id)
                if summary_channel:
                    await summary_channel.purge(limit=10)
                    embed_summary = discord.Embed(
                        title="🔥 Clientes online na OnFire Datacenter!",
                        description=f"Atualmente temos **{total_players} usuários online** nos servidores da OnFire! 🎮\n\n🚀 Hospede seus servidores com proteção DDoS, suporte 24/7 e estabilidade garantida.\n\n🌐 [onfiregroup.com.br](https://onfiregroup.com.br)",
                        color=discord.Color.orange()
                    )
                    embed_summary.set_image(url="https://i.imgur.com/gzgva1G.png")
                    embed_summary.set_footer(text="OnFire Datacenter • Performance sem limites")

                    view = View()
                    view.add_item(Button(label="Acesse agora", style=discord.ButtonStyle.link, url="https://onfiregroup.com.br"))

                    await summary_channel.send(embed=embed_summary, view=view)

    except Exception as e:
        print(f"[Erro geral]: {e}")

# Iniciar o bot
client.run(TOKEN)
