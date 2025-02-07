# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: all,-hidden,-heading_collapsed,-run_control,-trusted
#     notebook_metadata_filter: all, -jupytext.text_representation.jupytext_version,
#       -jupytext.text_representation.format_version, -language_info.version, -language_info.codemirror_mode.version,
#       -language_info.codemirror_mode, -language_info.file_extension, -language_info.mimetype,
#       -toc
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
#   language_info:
#     name: python
#     nbconvert_exporter: python
#     pygments_lexer: ipython3
#   nbhosting:
#     title: les librairies
# ---

# %% [markdown]
# <span style="float:left;">Licence CC BY-NC-ND</span><span style="float:right;">Thierry Parmentelat<img src="media/inria-25-alpha.png" style="display:inline"></span><br/>

# %% [markdown] slideshow={"slide_type": "slide"}
# # les librairies disponibles

# %% slideshow={"slide_type": "fragment"}
import asyncio

# %% [markdown]
# à ce stade vous avez les bases pour pouvoir utiliser les parties vraiment utiles de la librairie `asyncio`, ainsi d'ailleurs que tout l'écosystème qui s'est construit autour

# %% [markdown]
# ## `asyncio`

# %% [markdown]
# Le contenu de la `asyncio` est assez hétérogène en fait, car on y trouve
#
# * la boucle d'événements dont a parlé dans la séquence précédente
# * un objet du type 'Queue' pour gérer les accès concurrents
# * mais aussi - heureusement - des outils qui adressent spécifiquement des interactions avec le système d'exploitation, notamment en ce qui concerne
#   * la gestion des sous-processus
#   * le réseau, notamment seulement les couches basses (TCP/IP)

# %% [markdown]
# ## autres

# %% [markdown]
# Pour tous usages de plus haut niveau - par exemple si vous voulez faire du HTTP, ou du SSH, ou tout autre - il vous faudra installer des librairies supplémentaires comme par exemple
#
# * `oifiles` pour accéder aux fichiers de l'ordinateur d'une façon compatible avec le paradigme qu'on étudie
# * `aiohttp` qu'on a utilisée pour nos premiers exemples
# * `asyncssh` pour contrôler plein de machines en même temps avec une seule connexion ssh
# * `asyncpg` pour dialoguer de façon asynchrone avec une base de données postgresql,
# * ...

# %% [markdown]
# ## `Queue`

# %% [markdown]
# Pour montrer un petit exemple d'utilisation de la classe `Queue`, on va implémenter un mécanisme de 'throttle' qui permet de limiter le nombre de trucs qui tournent en même temps
#
# Comme toujours je prends un exemple bidon; chaque tâche appelle notre utilitaire `sequence`

# %%
from asynchelpers import start_timer, show_timer, sequence

# %%
async def job(name):
    await sequence(name, delay=2)

# %% [markdown]
# Imaginons maintenant que j'ai plein de jobs de ce genre

# %%
# lancer n jobs indentiques en parallèle
async def hurd(nbjobs):
    await asyncio.gather(*(job(f"job #{i+1:03d}") for i in range(nbjobs)))

# %% [markdown]
# Qaudn je les lance tous ensemble, ça donne ceci

# %%
start_timer()
await hurd(8)

# %% [markdown]
# OK; maintenant disons que je veux limiter le nombre de jobs actifs à un instant t
#
# Pour ne pas devoir faire une arithmétique compliquée, je vais juste utiliser une queue

# %%
# l'objet queue s'ssure qu'il n'y a pas plus de n jetons pris à un instant t

async def job2(name, queue):
    # j'occupe une place dans la queue
    await queue.put(1)
    await sequence(name, delay=2)
    # je la libère
    await queue.get()    

# %%
# maintenant il me suffit de créer la queue avec la taille qui va bien

async def hurd2(n, throttle):
    queue = asyncio.Queue(throttle)
    await asyncio.gather(*(job2(f"job #{i+1:03d}", queue) for i in range(n)))

# %%
# et maintenant je n'ai que 'throttle' jobs qui tournent en même temps
start_timer()
await hurd2(12, 8)

# %% [markdown]
# ## réseau

# %% [markdown]
# je tire cet exemple de la doc Python ici
# https://docs.python.org/3/library/asyncio-stream.html#tcp-echo-client-using-streams
#
# ça devrait résonner par rapport au dernier cours de Basile Marchand...

# %% [markdown]
# ### serveur TCP

# %%
import asyncio

async def handle_echo(reader, writer):
    data = await reader.read(100)
    message = data.decode()
    addr = writer.get_extra_info('peername')

    print(f"server Received {message!r} from {addr!r}")
    
    # simulate a small delay
    await asyncio.sleep(1)

    print(f"server Send: {message!r}")
    writer.write(data)
    await writer.drain()

    print("server Close the connection")
    writer.close()

# %%
async def server_mainloop(port):
    server = await asyncio.start_server(
        handle_echo, '127.0.0.1', port)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()

# %%
server_task = asyncio.ensure_future(server_mainloop(8080))

# %%
# comme on l'a vu, si ça se passe mal on n'a pas de retour
if server_task.done():
    print(server_task.exception())

# %%
# pour arrêter le serveur
# server_task.cancel()

# %% [markdown]
# ### client

# %% [markdown]
# maintenant que le serveur tourne je peux lancer des clients

# %%
import asyncio

async def tcp_echo_client(port, message):
    reader, writer = await asyncio.open_connection(
        '127.0.0.1', port)

    print(f'client Send: {message!r}')
    writer.write(message.encode())

    data = await reader.read(100)
    print(f'client Received: {data.decode()!r}')

    print('Close the connection')
    writer.close()

# %%
# un seul client 
asyncio.ensure_future(tcp_echo_client(8080, "Hey"))

# %%
async def hurd(nb_clients):
    await asyncio.gather(*(tcp_echo_client(8080, f"client#{i:03d}") for i in range(nb_clients)))

# %%
client_task = asyncio.ensure_future(hurd(30))

# %% [markdown]
# ## et plus...

# %% [markdown]
# Pour ceux qui voudraient en savoir plus, je vous invite à consulter la semaine 8 du MOOC Python sur fun-mooc.fr, et notamment
#
# * la séquence 8 où on montre un exemple de gestion de sous-processus
# * pour les geeks la séquence 5 où j'explique la mécanique interne de la boucle d'événements
