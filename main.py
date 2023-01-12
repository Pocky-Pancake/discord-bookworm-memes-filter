import nextcord, os, re, sqlite3
from nextcord import Interaction
from nextcord.ext import commands
from dotenv import load_dotenv
from random import randint

load_dotenv()

intents = nextcord.Intents.all()
client = nextcord.Client(intents=intents)

filter_channels_ids = [1062211727527247932]

conn = sqlite3.connect("bot.sqlite3")
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS threads (
    user_id integer,
    thread_id integer
)""")

class renameModal(nextcord.ui.Modal):
    def __init__(self, thread):
        super().__init__("Rename Thread")
        self.thread = thread

        self.set_name = nextcord.ui.TextInput(label="Thread Name:", min_length=1, max_length=100, required=True, style=nextcord.TextInputStyle.short)
        self.add_item(self.set_name)

    async def callback(self, interaction:Interaction) -> None:
        set_name = self.set_name.value
        await self.thread.edit(name=set_name)
        return 0

class renameThread(nextcord.ui.Button):
    def __init__(self, thread, caller):
        super().__init__(emoji="📝", style=nextcord.ButtonStyle.blurple)
        self.thread = thread
        self.caller = caller

    async def callback(self, interaction:Interaction):
        if self.caller == interaction.user.id:
            await interaction.response.send_modal(renameModal(self.thread))
        else:
            await interaction.response.send_message(f"Only <@{self.caller}> may do this.", ephemeral=True)

class rejectThread(nextcord.ui.Button):
    def __init__(self, thread, caller):
        super().__init__(emoji="🚮", style=nextcord.ButtonStyle.red)
        self.thread = thread
        self.caller = caller
    
    async def callback(self, interaction:Interaction):
        if self.caller == interaction.user.id:
            await self.thread.delete()
        else:
            await interaction.response.send_message(f"Only <@{self.caller}> may do this.", ephemeral=True)

class threadView(nextcord.ui.View):
    def __init__(self, thread, caller):
        super().__init__(timeout=600)
        self.add_item(rejectThread(thread, caller))
        self.add_item(renameThread(thread, caller))
    async def on_error(self, error, item, interaction):
        print(error)
        print(item)

@client.event
async def on_ready():
    print("Bot ready")

URL_REGEX = re.compile(r".*\shttps?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)")
URL_REGEX2 = re.compile(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)")
URL_REGEX3 = re.compile(r".*https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)")

@client.event
async def on_message(message):
    for x in filter_channels_ids:
        if message.channel.id == x:
            if message.attachments or (message.content and URL_REGEX.match(message.content)) or (message.content and URL_REGEX2.match(message.content)) or (message.content and URL_REGEX3.match(message.content)):
                thread = await message.create_thread(name=f"{message.author.name}'s meme discussion")
                embed = nextcord.Embed(title="Edit thread?", description="Use 🚮 button to delete it\n *or*\nUse 📝 button to rename it.", color=randint(0,16777215))
                embed.set_footer(text="This will only be valid for the first 10 minutes. To rename the thread afterwards use </rename:1062906458523586620> instead.")
                await thread.send(embed=embed, view=threadView(thread, message.author.id), delete_after=600)
                sql = "INSERT INTO threads (user_id, thread_id) VALUES (?, ?)"
                val = (message.author.id, thread.id)
                c.execute(sql,val)
                conn.commit()
            elif message.author.bot or message.author.guild_permissions.manage_channels:
                pass
            else:
                await message.author.send(f"In order to keep {message.channel.mention} as organized as possible, it is only possible to discuss memes via threads.")
                await message.delete()

@client.slash_command(description="Rename a thread")
async def rename(interaction:Interaction):
    try:
        thread_id = c.execute(f"SELECT thread_id FROM threads WHERE thread_id = {interaction.channel.id}").fetchone()[0]
        user_id = c.execute(f"SELECT user_id FROM threads WHERE thread_id = {thread_id}").fetchone()[0]
    except:
        thread_id = None
        user_id = None
    if interaction.channel.id == thread_id and interaction.user.id == user_id:
        thread = await client.fetch_channel(thread_id)
        await interaction.response.send_modal(renameModal(thread))
        await interaction.response.send_message("Done.", ephemeral=True)
    else:
        await interaction.response.send_message("This channel is either not a thread, not a registered thread or you don't own this thread.", ephemeral=True)

# @client.slash_command(description="Set specific slowmode to the channel you are in. Set 0 to disable slowmode.")
# async def slowmode(interaction:Interaction, delay:int = nextcord.SlashOption(max_value=21600, min_value=0, description="Delay time in seconds.")):
#     if interaction.user.guild_permissions.manage_channels:
#         try:
#             await interaction.channel.edit(slowmode_delay=delay, reason=f"{interaction.user.name} used /set_slowmode.")
#         except:
#             await interaction.channel.edit(slowmode_delay=delay)
#         await interaction.response.send_message(f"Slowmode set to {delay} seconds.")
#     else:
#         await interaction.response.send_message("The \"manage channels\" permission is required to use this command", ephemeral=True)

client.run(os.getenv('TOKEN'))


