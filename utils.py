import nextcord, sqlite3, os
from nextcord import Interaction
from nextcord.ext import commands
from math import ceil
from paging import mkpages

async def doLog(bot, content):
    try:
        globalLog = await bot.client.fetch_channel(int(os.getenv('LOG')))
        await globalLog.send(content=content)
    except:
        pass
    print(content)
    return 0

async def getPage(interaction, bot, page:int, setType:int) -> None:
    # TYPE:
    # 0 = filters
    # 3 = registered threads

    class typeSelect(nextcord.ui.Select):
        def __init__(self, bot):
            options=[
                nextcord.SelectOption(label="Filter Channels", value=0, emoji="🧹"),
                nextcord.SelectOption(label="Registered Threads", value=3, emoji="🧵")
            ]
            super().__init__(placeholder="Select Type", options=options)
            self.bot = bot

        async def callback(self, interaction):
            await getPage(interaction, self.bot, 1, int(self.values[0]))

    nextPage = nextcord.ui.Button(label=" Next", style=nextcord.ButtonStyle.blurple, emoji="➡️")
    prevPage = nextcord.ui.Button(label=" Previous", style=nextcord.ButtonStyle.blurple, emoji="⬅️")
    refreshPage = nextcord.ui.Button(label=" Refresh", style=nextcord.ButtonStyle.blurple, emoji="🔄")
    view = nextcord.ui.View(timeout=600)
    view.add_item(prevPage)
    view.add_item(refreshPage)
    view.add_item(nextPage)
    view.add_item(typeSelect(bot))

    data = []
    if setType == 0:
        data = bot.c.execute(f"SELECT channel_id FROM filters WHERE guild_id = {interaction.guild.id}").fetchall()
    elif setType == 3:
        data = bot.c.execute(f"SELECT thread_id FROM threads WHERE guild_id = {interaction.guild.id}").fetchall()

    pagedData = mkpages(data, 6)
    dataContent = ""
    lastPage = ceil(len(data)/6)

    if page <= 0:
        page = lastPage
    elif page > lastPage:
        page = 1

    async def callbackNext(interaction):
        await getPage(interaction, bot, page+1, setType)
    async def callbackRefresh(interaction):
        await getPage(interaction, bot, page, setType)
    async def callbackPrev(interaction):
        await getPage(interaction, bot, page-1, setType)

    nextPage.callback = callbackNext
    refreshPage.callback = callbackRefresh
    prevPage.callback = callbackPrev

    try:
        for x in pagedData[page-1]:
            dataContent += f"• <#{x[0]}>\n\n"
    except:
        dataContent = "Empty" if dataContent == "" else dataContent
        page = 0

    info = f"""
    -Status: {bot.client.status}
    -Latency: {bot.client.latency}
    -User: {bot.client.user.mention}
    -Total registered threads: {len(bot.c.execute(f"SELECT thread_id FROM threads WHERE guild_id = {interaction.guild.id}").fetchall())}"""
    embed = nextcord.Embed(title=f"{bot.client.user.name} Stats", description=info, color=0x3366cc)
    if setType == 0:
        embed.add_field(name="Filter Channels", value=dataContent)
    elif setType == 3:
        embed.add_field(name="Registered Threads", value=dataContent)
    embed.set_footer(text=f"Page {page}/{lastPage}", icon_url=interaction.guild.icon)
    try:
        await interaction.response.edit_message(embed=embed, view=view)
    except:
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class filterModal(nextcord.ui.Modal):
    def __init__(self, bot, channel, edit:bool):
        modalTitle = "Edit Filter Channel" if edit else "Setup Filter Channel"
        super().__init__(modalTitle, auto_defer=True)
        self.channel = channel
        self.bot = bot
        self.edit = edit

        default_name = bot.c.execute(f"SELECT default_thread_name FROM filters WHERE channel_id = {channel.id}").fetchone()[0] if edit else ""
        default_warn = bot.c.execute(f"SELECT warn_msg FROM filters WHERE channel_id = {channel.id}").fetchone()[0] if edit else ""

        self.defaultThreadName = nextcord.ui.TextInput(label="Default Thread Name:", min_length=5, max_length=100, default_value=default_name, required=True, style=nextcord.TextInputStyle.short)
        self.add_item(self.defaultThreadName)
        self.warnMsg = nextcord.ui.TextInput(label="Warning Message:", min_length=5, max_length=1900, default_value=default_warn, required=True, style=nextcord.TextInputStyle.paragraph)
        self.add_item(self.warnMsg)

    async def callback(self, interaction:Interaction) -> None:
        if self.edit:
            self.bot.c.execute(f"UPDATE filters SET warn_msg = '{self.warnMsg.value}' WHERE channel_id = {self.channel.id}")
            self.bot.conn.commit()
            self.bot.c.execute(f"UPDATE filters SET default_thread_name = '{self.defaultThreadName.value}' WHERE channel_id = {self.channel.id}")
            self.bot.conn.commit()
            await interaction.send_message(f"{self.channel.mention}'s filter settings has been updated.", ephemeral=True)
        else:
            sql = "INSERT INTO filters (channel_id, guild_id, warn_msg, default_thread_name) VALUES (?, ?, ?, ?)"
            val = (self.channel.id, interaction.guild.id, self.warnMsg.value, self.defaultThreadName.value)
            self.bot.c.execute(sql,val)
            self.bot.conn.commit()
            await interaction.response.send_message(f"{self.channel.mention} has been added as filter channel.", ephemeral=True)
        return 0

    async def on_error(self, error, interaction):
        await doLog(self.bot, f"⚠ Error: `{error}`")
        raise error

class renameModal(nextcord.ui.Modal):
    def __init__(self, bot, thread):
        super().__init__("Rename Thread")
        self.bot = bot
        self.thread = thread

        self.set_name = nextcord.ui.TextInput(label="Thread Name:", min_length=1, max_length=100, required=True, style=nextcord.TextInputStyle.short)
        self.add_item(self.set_name)

    async def callback(self, interaction:Interaction) -> None:
        await self.thread.edit(name=self.set_name.value)
        return 0

    async def on_error(self, error, interaction):
        await doLog(self.bot, f"⚠ Error: `{error}`")
        raise error

class renameThread(nextcord.ui.Button):
    def __init__(self, bot, thread, caller):
        super().__init__(emoji="📝", style=nextcord.ButtonStyle.blurple)
        self.bot = bot
        self.thread = thread
        self.caller = caller

    async def callback(self, interaction:Interaction):
        if self.caller == interaction.user.id:
            await interaction.response.send_modal(renameModal(self.bot, self.thread))
        else:
            await interaction.response.send_message(f"Only <@{self.caller}> may do this.", ephemeral=True)

class threadView(nextcord.ui.View):
    def __init__(self, bot, thread, caller):
        super().__init__(timeout=600)
        self.bot = bot
        self.add_item(renameThread(bot, thread, caller))

    async def on_error(self, error, item, interaction):
        await doLog(self.bot, f"⚠ Error: `{error}`", 0)
        raise error
