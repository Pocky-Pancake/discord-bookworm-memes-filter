import nextcord, os, re, sqlite3, time, datetime
from utils import *
from nextcord import Interaction
from nextcord.ext import commands, application_checks
from dotenv import load_dotenv

load_dotenv()

intents = nextcord.Intents.all()
client = nextcord.ext.commands.Bot(intents=intents)

conn = sqlite3.connect("bot_2.sqlite3")
c = conn.cursor()

class Toolkit():
    def __init__(self, client, c, conn):
        self.client = client
        self.c = c
        self.conn = conn

    def sleep(self, setTime:float):
        time.sleep(setTime)

bot = Toolkit(client, c, conn)

c.execute("""CREATE TABLE IF NOT EXISTS threads (
    user_id integer,
    thread_id integer,
    guild_id integer,
    embedmsg_id integer,
    type integer
)""")

c.execute("""CREATE TABLE IF NOT EXISTS channels (
    channel_id integer,
    guild_id integer,
    type integer,
    int_val1 integer,
    str_val1 text,
    str_val2 text,
    str_val3 text
)""")

# Values
# int_val1: msg_id
# str_val1: warn_msg. rule_msg
# str_val2: default_thread_name
# str_val3: embed_title

# Channel type
# 0 - Filter
# 1 - Forum

@client.event
async def on_ready():
    embeds_id = c.execute("SELECT embedmsg_id FROM threads").fetchall()
    for msg_id in embeds_id:
        try:
            thread = await client.fetch_channel(c.execute(f"SELECT thread_id FROM threads WHERE embedmsg_id = {msg_id[0]}").fetchone()[0])
            embedmsg = await thread.fetch_message(msg_id[0])
            await embedmsg.delete()
        except:
            pass

    forums = c.execute("SELECT channel_id FROM channels WHERE type = 1").fetchall()
    for x in forums:
        channel = await client.fetch_channel(x[0])
        await stickyMsg(bot, channel)

    print(f"{client.user.name} is ready")

@client.event
async def on_application_command_error(interaction:Interaction, error):
    error = getattr(error, "original", error)
    if isinstance(error, application_checks.ApplicationMissingPermissions):
        await interaction.response.send_message(f"{error}", ephemeral=True)
    if isinstance(error, nextcord.errors.Forbidden):
        await doLog(bot, f"⚠ Error: `{error}`")
        raise error
    else:
        await doLog(bot, f"⚠ Error: `{error}`")
        raise error

urlRegex = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
serverRegex1 = r"(server)?(.*|\s?)(mascot|mas-cot)"

@client.event
async def on_message(message):
    filters = c.execute("SELECT channel_id FROM channels WHERE type = 0").fetchall()
    forums = c.execute("SELECT channel_id FROM channels WHERE type = 1").fetchall()
    for y in client.get_all_application_commands():
                    if y.qualified_name == "rename":
                        rename_slash = y
    for x in filters:
        if message.channel.id == x[0]:
            if message.attachments or re.search(urlRegex, message.content):
                thread = await message.create_thread(name=c.execute(f"SELECT str_val2 FROM channels WHERE channel_id = {x[0]}").fetchone()[0].replace("$1", f"{message.author.name}"))
                embed = nextcord.Embed(title="New Discussion Thread", description=f"Use 📝 button to rename it.\n\nThis will only be valid for the first 10 minutes. To rename the thread afterwards use {rename_slash.get_mention(guild=None)} instead.", color=0x3366cc)
                embed.set_footer(icon_url=message.author.avatar ,text=f"This thread has been initialized and can only be renamed by {message.author.name}")
                embedmsg = await thread.send(embed=embed, view=threadView(bot, thread, message.author.id), delete_after=600)
                await thread.leave()
                sql = "INSERT INTO threads (user_id, thread_id, guild_id, embedmsg_id) VALUES (?, ?, ?, ?)"
                val = (message.author.id, thread.id, message.guild.id, embedmsg.id)
                c.execute(sql,val)
                conn.commit()
            elif message.type == nextcord.MessageType.pins_add:
                pass
            elif message.author.id == client.user.id:
                pass
            elif message.author.guild_permissions.manage_channels:
                pass
            else:
                warnMsg = c.execute(f"SELECT str_val1 FROM channels WHERE channel_id = {x[0]}").fetchone()[0].replace("$1", f"{message.channel.mention}")
                try:
                    await message.author.send(warnMsg)
                except:
                    await message.channel.send(f"{message.author.mention}\n{warnMsg}", delete_after=30)
                await message.delete()
    for x in forums:
        if message.channel.id == x[0]:
            if message.type == nextcord.MessageType.thread_created:
                try:
                    await resetSticky(bot, message.channel)
                except:
                    pass
            elif message.author.id == client.user.id:
                pass
            elif message.type == nextcord.MessageType.reply and message.author.id != client.user.id:
                await message.delete()
            elif re.search(serverRegex1, message.content.lower()) and message.author.id != client.user.id:
                if not message.author.guild_permissions.manage_channels:
                    await message.author.timeout(timeout=datetime.datetime.now()+datetime.timedelta(days=3), reason="No server mascot")
                await message.delete()
            else:
                thread = await message.create_thread(name=c.execute(f"SELECT str_val2 FROM channels WHERE channel_id = {x[0]}").fetchone()[0].replace("$1", f"{message.author.name}"))
                embed = nextcord.Embed(title="New Post Thread", description=f"Use 📝 button to rename it.\n\nThis will only be valid for the first 10 minutes. To rename the thread afterwards use {rename_slash.get_mention(guild=None)} instead.", color=0x3366cc)
                embed.set_footer(icon_url=message.author.avatar ,text=f"This thread has been initialized and can only be renamed by {message.author.name}")
                embedmsg = await thread.send(embed=embed, view=threadView(bot, thread, message.author.id), delete_after=600)
                await thread.leave()
                sql = "INSERT INTO threads (user_id, thread_id, guild_id, embedmsg_id) VALUES (?, ?, ?, ?)"
                val = (message.author.id, thread.id, message.guild.id, embedmsg.id)
                c.execute(sql,val)
                conn.commit()
                time.sleep(10)
                await resetSticky(bot, message.channel)

@client.event
async def on_message_delete(message):
    msgs_id = c.execute(f"SELECT int_val1 FROM channels WHERE type = 1").fetchall()
    for x in msgs_id:
        if x[0] == message.id:
            await stickyMsg(bot, message.channel)

@client.event
async def on_thread_delete(thread):
    check = c.execute(f"SELECT thread_id FROM threads WHERE thread_id = {thread.id}").fetchone()[0]
    if check:
        c.execute(f"DELETE FROM threads WHERE thread_id = {check}")
        conn.commit

@client.slash_command(description="Renames a registered discussion thread you started.")
async def rename(interaction:Interaction):
    try:
        thread_id = c.execute(f"SELECT thread_id FROM threads WHERE thread_id = {interaction.channel.id}").fetchone()[0]
        user_id = c.execute(f"SELECT user_id FROM threads WHERE thread_id = {thread_id}").fetchone()[0]
    except:
        thread_id = None
        user_id = None
    if interaction.channel.id == thread_id and interaction.user.id == user_id:
        thread = await client.fetch_channel(thread_id)
        if thread.locked:
            await interaction.response.send_message("This thread is locked.", ephemeral=True)
        else:
            await interaction.response.send_modal(renameModal(bot, thread))
    else:
        await interaction.response.send_message("This channel is either not a thread, not a registered thread or you don't own this thread.", ephemeral=True)

@client.slash_command(description="Check bot status, latency and data.")
async def stats(interaction:Interaction):
    await getPage(interaction, bot, 1, 3)

#type:
# 0 - filter
# 1 - forum

@client.slash_command(description="Add functionning channels.")
@application_checks.has_permissions(manage_channels=True)
async def add_channel(interaction:Interaction, channel:nextcord.TextChannel = nextcord.SlashOption(description="Target channel (Text channel only)."), asType:int = nextcord.SlashOption(description="Functioning type", name="as", choices={
    "Filter Channel":0,
    "Fake Forum Channel":1
})):
    check = c.execute(f"SELECT channel_id FROM channels WHERE channel_id = {channel.id}").fetchone()
    if not check:
        if asType == 0:
            await interaction.response.send_modal(filterModal(bot, channel, False))
        elif asType == 1:
            await interaction.response.send_modal(forumModal(bot, channel, False))
    else:
        await interaction.response.send_message(f"{channel.mention} is already used.", ephemeral=True)

@client.slash_command(description="Remove functionning channels.")
@application_checks.has_permissions(manage_channels=True)
async def rm_channel(interaction:Interaction, channel:nextcord.TextChannel = nextcord.SlashOption(description="Target channel (Text channel only).")):
    check = c.execute(f"SELECT channel_id FROM channels WHERE channel_id = {channel.id}").fetchone()
    if check:
        static = None
        if c.execute(f"SELECT type FROM channels WHERE channel_id = {check[0]}").fetchone()[0] == 1:
            static_id = c.execute(f"SELECT int_val1 FROM channels WHERE channel_id = {check[0]}").fetchone()[0]
            channel = await client.fetch_channel(check[0])
            static = await channel.fetch_message(static_id)
        c.execute(f"DELETE FROM channels WHERE channel_id = {channel.id}")
        conn.commit()
        try:
            await static.delete()
        except:
            pass
        await interaction.response.send_message(f"{channel.mention} has been removed.", ephemeral=True)
    else:
        await interaction.response.send_message(f"{channel.mention} isn't a valid channel.", ephemeral=True)

@client.slash_command(description="Configure filter channel.")
@application_checks.has_permissions(manage_channels=True)
async def conf_channel(interaction:Interaction, channel:nextcord.TextChannel = nextcord.SlashOption(description="Target channel (Text channel only).")):
    check = c.execute(f"SELECT channel_id FROM channels WHERE channel_id = {channel.id}").fetchone()
    if check:
        get_type = c.execute(f"SELECT type FROM channels WHERE channel_id = {channel.id}").fetchone()
        if get_type[0] == 0:
            await interaction.response.send_modal(filterModal(bot, channel, True))
        elif get_type[0] == 1:
            await interaction.response.send_modal(forumModal(bot, channel, True))
    else:
        await interaction.response.send_message(f"{channel.mention} isn't a valid channel.", ephemeral=True)

@client.slash_command(description="Unregister a thread from the database.")
async def unregister(interaction:Interaction, thread:nextcord.Thread):
    check = c.execute(f"SELECT thread_id FROM threads WHERE thread_id = {thread.id}").fetchone()[0]
    if check:
        if interaction.user.id == c.execute(f"SELECT user_id FROM threads WHERE thread_id = {check}").fetchone()[0]:
            c.execute(f"DELETE FROM threads WHERE thread_id = {check}")
            await interaction.response.send_message("Thread unregistered.", ephemeral=True)
        elif interaction.user.guild_permissions.manage_channels:
            c.execute(f"DELETE FROM threads WHERE thread_id = {check}")
            await interaction.response.send_message("Thread unregistered.", ephemeral=True)
        else:
            await interaction.response.send_message("You do not own this thread.", ephemeral=True)
    else:
        await interaction.response.send_message("This thread isn't registered.", ephemeral=True)

@client.slash_command(description="Create a post.")
async def post(interaction:Interaction):
    check = c.execute(f"SELECT channel_id FROM channels WHERE type = 1 AND channel_id = {interaction.channel.id}").fetchone()[0]
    if check:
        embed = postEmbed(bot, interaction.channel)
        view = postView(bot, interaction.channel)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    else:
        await interaction

@client.slash_command(description="Waschen help.")
async def help(interaction:Interaction):
    commands = client.get_all_application_commands()
    slashList = f"This is the list of commands for {client.user.mention}:\n\n"
    for x in commands:
        try:
            slashList += f"• {x.get_mention(guild=None)}\n> {x.description}\n\n"
        except:
            pass
    embed = nextcord.Embed(title="Help", description=slashList, color=0x3366cc)
    await interaction.response.send_message(embed=embed, ephemeral=True)

try:
    client.run(os.getenv('TOKEN'))
except:
    print("Failed to connect.")
