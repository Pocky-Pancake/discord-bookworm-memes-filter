import nextcord, sqlite3
from nextcord import Interaction
from nextcord.ext import commands
from math import ceil
from paging import mkpages

async def doLog(content):
    print(content)
    log_channel = await client.fetch_channel(log_channel_id)
    await log_channel.send(content=content)
    return 0

async def getPage(interaction, client, sql, page:int, setType:int) -> None:
    # TYPE:
    # 0 = filters
    # 1 = bots
    # 2 = logs
    # 3 = registered threads

    class typeSelect(nextcord.ui.Select):
        def __init__(self, client, sql, caller):
            options={
                "Filter Channels":0,
                "Bots Channels":1,
                "Logs Channels":2
            }
            super().__init__(placeholder="Select Type", options=options)
            self.sql = sql
            self.caller = caller
            self.client = client

        async def callback(self, interaction):
            if interaction.user == caller:
                await getPage(interaction, self.client, self.sql, 1, self.values[0])
            else:
                await interaction.response.send_message(f"Only {caller.mention} may do this.", ephemeral=True)

    caller = interaction.user
    nextPage = nextcord.ui.Button(label="Next", style=nextcord.ButtonStyle.blurple)
    prevPage = nextcord.ui.Button(label="Prev", style=nextcord.ButtonStyle.blurple)
    refreshPage = nextcord.ui.Button(label="Refresh", style=nextcord.ButtonStyle.blurple)
    view = nextcord.ui.View(timeout=600)
    view.add_item(prevPage)
    view.add_item(refreshPage)
    view.add_item(nextPage)
    view.add_item(typeSelect(client, sql, caller))

    if setType == 0:
        data = sql.execute(f"SELECT channel_id FROM targets WHERE type = 0 AND guild_id = {interaction.guild.id}").fetchall()
    elif setType == 1:
        data = sql.execute(f"SELECT channel_id FROM targets WHERE type = 1 AND guild_id = {interaction.guild.id}").fetchall()
    elif setType == 2:
        data = sql.execute(f"SELECT channel_id FROM targets WHERE type = 2 AND guild_id = {interaction.guild.id}").fetchall()
    elif setType == 3:
        data = sql.execute(f"SELECT thread_id FROM threads WHERE guild_id = {interaction.guild.id}").fetchall()

    pagedData = mkpages(data, 6)
    dataContent = ""
    lastPage = ceil(len(data)/6)

    async def callbackNext(interaction):
        if interaction.user == caller:
            await getPage(interaction, client, sql, page+1, setType)
        else: 
            await interaction.response.send_message(f"Only {caller.mention} may do this.", ephemeral=True)
    async def callbackRefresh(interaction):
        if interaction.user == caller:
            await getPage(interaction, client, sql, page, setType)
        else:
            await interaction.response.send_message(f"Only {caller.mention} may do this.", ephemeral=True)
    async def callbackPrev(interaction):
        if interaction.user == caller:
            await getPage(interaction, client, sql, page-1, setType)
        else:
            await interaction.response.send_message(f"Only {caller.mention} may do this.", ephemeral=True)

    nextPage.callback = callbackNext
    refreshPage.callback = callbackRefresh
    prevPage.callback = callbackPrev

    try:
        for x in pagedData[page-1]:
            dataContent += f"<#{x[0]}>\n\n"
    except:
        dataContent = "Empty" if dataContent == "" else dataContent

    info = f"""-Status: {client.status}
    -Latency: {client.latency}
    -User: {client.user.mention}
    -Total registered threads: {len(sql.execute(f"SELECT thread_id FROM threads WHERE guild_id = {interaction.guild.id}").fetchall())}"""
    embed = nextcord.Embed(title=f"{client.user.name} Stats", description=info, color=0x3366cc)
    if setType == 0:
        embed.add_field(name="Filter Channels", value=dataContent)
    elif setType == 1:
        embed.add_field(name="Bots Channels", value=dataContent)
    elif setType == 2:
        embed.add_field(name="Logs Channels", value=dataContent)
    elif setType == 3:
        embed.add_field(name="Registered Threads", value=dataContent)
    embed.set_footer(text=f"Page {page}/{lastPage}", icon_url=interaction.guild.icon)
    try:
        await interaction.response.edit_message(embed=embed, view=view)
    except:
        await interaction.response.send_message(embed=embed, view=view)

class renameModal(nextcord.ui.Modal):
    def __init__(self, thread):
        super().__init__("Rename Thread")
        self.thread = thread

        self.set_name = nextcord.ui.TextInput(label="Thread Name:", min_length=1, max_length=100, required=True, style=nextcord.TextInputStyle.short)
        self.add_item(self.set_name)

    async def callback(self, interaction:Interaction) -> None:
        set_name = self.set_name.value
        await self.thread.edit(name=set_name)
        await doLog(f"Thread ({self.thread.id}) renamed by {interaction.user.name}")
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

class threadView(nextcord.ui.View):
    def __init__(self, thread, caller):
        super().__init__(timeout=600)
        self.add_item(renameThread(thread, caller))
    async def on_error(self, error, item, interaction):
        raise error