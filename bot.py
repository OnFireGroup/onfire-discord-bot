import discord
from discord.ext import commands, tasks
from datetime import datetime
import requests
import socket
import os
import itertools
import asyncio

if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configurações
TOKEN = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
DATA_INICIAL = '2025-01-28'
INTERVALO_MINUTOS = 10  # Intervalo de atualização

# Mensagens de presença do bot
STATUS_MENSAGENS = itertools.cycle([
    "🌐 OnFire Datacenter | onfiregroup.com.br 🔥",
    "💻 Os melhores preços em servidores!",
    "🔐 Segurança DDoS garantida 🚀"
])

# Lista de servidores, canais, serviços monitorados e propaganda
SERVIDORES_DISCORD = {
    000000000000000: {
        "canal_ddos": 000000000000000,
        "canal_status": 000000000000000,
        "servicos": {
            "Site Principal": "xxx.xxx.xxx.xxx:xxxx",
            "E-mail Corporativo": "xxx.xxx.xxx.xxx:xxxx",
            "Hospedagem de sites": "xxx.xxx.xxx.xxx:xxxx",
            "Servidores de jogos": "xxx.xxx.xxx.xxx:xxxx",
            "VPS": "xxx.xxx.xxx.xxx:xxxx",
            "Dedicados": "xxx.xxx.xxx.xxx:xxxx"
        },
        "propaganda_status": None,
        "propaganda_ddos": None
    },
    000000000000000: {
        "canal_ddos": 000000000000000,
        "canal_status": 000000000000000,
        "servicos": {
            "Servidor Arma Reforger": ""xxx.xxx.xxx.xxx:xxxx",
            "Servidor dedicado": ""xxx.xxx.xxx.xxx:xxxx",
            "Painel": ""xxx.xxx.xxx.xxx:xxxxr"
        },
        "propaganda_status": "🌐 **OnFire Datacenter:** Os melhores preços e máquinas! 🔥",
        "propaganda_ddos": "🚀 **OnFire:** Proteção DDoS garantida!"
    },
    000000000000000: {
        "canal_ddos": 000000000000000,
        "canal_status": 000000000000000,
        "servicos": {
            "Servidor dedicado": "xxx.xxx.xxx.xxx:xxxx",
            "Servidor DayZ": "steamquery:xxx.xxx.xxx.xxx:xxxx"  # Indicação de serviço Steam Query
        },
        "propaganda_status": "🌐 **OnFire Datacenter:** Os melhores preços e máquinas! 🔥",
        "propaganda_ddos": "🚀 **OnFire:** Proteção DDoS garantida!"
    }
}

INCIDENTES = {}

# Configuração do bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

def calcular_dias_sem_ataque():
    data_inicial = datetime.strptime(DATA_INICIAL, '%Y-%m-%d')
    dias_passados = (datetime.now() - data_inicial).days
    return dias_passados

def verificar_ping(endereco):
    return os.system(f"ping -n 1 {endereco} > nul") == 0

def verificar_http(url):
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def verificar_tcp(endereco_porta):
    try:
        endereco, porta = endereco_porta.split(":")
        porta = int(porta)
        with socket.create_connection((endereco, porta), timeout=5):
            return True
    except (socket.timeout, socket.error, ValueError):
        return False

def verificar_udp(endereco_porta):
    try:
        endereco, porta = endereco_porta.split(":")
        porta = int(porta)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        sock.sendto(b"ping", (endereco, porta))
        return True
    except (socket.timeout, socket.error, ValueError):
        return False
    finally:
        sock.close()

def verificar_steam_query(endereco_porta):
    try:
        endereco, porta = endereco_porta.split(":")
        porta = int(porta)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        
        # Pacote A2S_INFO para consulta Steam
        packet = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
        sock.sendto(packet, (endereco, porta))
        
        # Tenta receber a resposta
        response, _ = sock.recvfrom(4096)
        return response.startswith(b'\xFF\xFF\xFF\xFF')  # Verifica o cabeçalho padrão da resposta Steam
    except (socket.timeout, socket.error, ValueError):
        return False
    finally:
        sock.close()

async def verificar_servicos(servicos):
    status_servicos = {}
    for nome, endereco in servicos.items():
        if endereco.startswith("steamquery:"):
            endereco = endereco.replace("steamquery:", "")
            status = "🟢 Online" if verificar_steam_query(endereco) else "🔴 Offline"
        elif endereco.startswith("udp:"):
            endereco = endereco.replace("udp:", "")
            status = "🟢 Online" if verificar_udp(endereco) else "🔴 Offline"
        elif ":" in endereco:
            status = "🟢 Online" if verificar_tcp(endereco) else "🔴 Offline"
        elif endereco.startswith("http"):
            status = "🟢 Online" if verificar_http(endereco) else "🔴 Offline"
        else:
            status = "🟢 Online" if verificar_ping(endereco) else "🔴 Offline"

        if nome not in INCIDENTES:
            INCIDENTES[nome] = 0

        if status == "🔴 Offline":
            INCIDENTES[nome] += 1

        status_servicos[nome] = status
    return status_servicos

async def enviar_status_para_servidor(guild, servicos):
    canais = SERVIDORES_DISCORD.get(guild.id)
    if not canais:
        print(f"Servidor {guild.name} não está configurado.")
        return

    canal_status = guild.get_channel(canais["canal_status"])
    if not canal_status:
        print(f"Canal 'Status' não encontrado no servidor {guild.name}.")
        return

    ultima_verificacao = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    status_servicos = await verificar_servicos(servicos)

    mensagem_status = (
        "```\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 Status dos serviços 📊\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
    )

    for nome, status in status_servicos.items():
        mensagem_status += f"{nome.ljust(30)} {status}\n"
        mensagem_status += f"Incidentes: {INCIDENTES[nome]}\n\n"

    mensagem_status += (
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔄 Última verificação: {ultima_verificacao}\n"
        "```"
    )

    propaganda = canais.get("propaganda_status")
    if propaganda:
        mensagem_status += f"\n{propaganda}"

    async for msg in canal_status.history(limit=10):
        if msg.author == bot.user:
            try:
                await msg.delete()
            except discord.NotFound:
                print(f"Mensagem {msg.id} não encontrada, possivelmente já foi excluída.")
            except discord.Forbidden:
                print(f"Permissão negada para excluir a mensagem {msg.id}.")

    await canal_status.send(content=mensagem_status)

async def enviar_ddos_para_servidor(guild):
    canais = SERVIDORES_DISCORD.get(guild.id)
    if not canais:
        print(f"Servidor {guild.name} não está configurado.")
        return

    canal_ddos = guild.get_channel(canais["canal_ddos"])
    if not canal_ddos:
        print(f"Canal 'Dias sem DDoS' não encontrado no servidor {guild.name}.")
        return

    dias_sem_ataque = calcular_dias_sem_ataque()
    ultima_verificacao = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    mensagem_ddos = (
        "```\n"
        f"🌐 Estamos há {dias_sem_ataque} dias sem sofrer um ataque DDoS! 🚀\n"
        f"🔄 Última verificação: {ultima_verificacao}\n"
        "```"
    )

    propaganda = canais.get("propaganda_ddos")
    if propaganda:
        mensagem_ddos += f"\n{propaganda}"

    async for msg in canal_ddos.history(limit=10):
        if msg.author == bot.user:
            try:
                await msg.delete()
            except discord.NotFound:
                print(f"Mensagem {msg.id} não encontrada, possivelmente já foi excluída.")
            except discord.Forbidden:
                print(f"Permissão negada para excluir a mensagem {msg.id}.")

    await canal_ddos.send(content=mensagem_ddos)

@tasks.loop(minutes=INTERVALO_MINUTOS)
async def atualizar_status_servicos():
    for guild in bot.guilds:
        canais = SERVIDORES_DISCORD.get(guild.id)
        if not canais:
            continue

        servicos = canais.get("servicos", {})
        await enviar_status_para_servidor(guild, servicos)

@tasks.loop(minutes=INTERVALO_MINUTOS)
async def atualizar_dias_sem_ddos():
    for guild in bot.guilds:
        await enviar_ddos_para_servidor(guild)

@tasks.loop(minutes=5)
async def atualizar_presenca():
    mensagem = next(STATUS_MENSAGENS)
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name=mensagem
    ))

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

    atualizar_presenca.start()
    atualizar_status_servicos.start()
    atualizar_dias_sem_ddos.start()

bot.run(TOKEN)
