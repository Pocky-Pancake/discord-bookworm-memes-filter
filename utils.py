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
    # 1 = forums
    # 3 = registered threads

    class typeSelect(nextcord.ui.Select):
        def __init__(self, bot):
            options=[
                nextcord.SelectOption(label="Filter Channels", value=0, emoji="🧹"),
                nextcord.SelectOption(label="Fake forum Channels", value=1, emoji="🗨️"),
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
        data = bot.c.execute(f"SELECT channel_id FROM channels WHERE type = 0 AND guild_id = {interaction.guild.id}").fetchall()
    if setType == 1:
        data = bot.c.execute(f"SELECT channel_id FROM channels WHERE type = 1 AND guild_id = {interaction.guild.id}").fetchall()
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
    if setType == 1:
        embed.add_field(name="Fake forum Channels", value=dataContent)
    elif setType == 3:
        embed.add_field(name="Registered Threads", value=dataContent)
    embed.set_footer(text=f"Page {page}/{lastPage}", icon_url=interaction.guild.icon)
    try:
        await interaction.response.edit_message(embed=embed, view=view)
    except:
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class postModal(nextcord.ui.Modal):
    def __init__(self, bot):
        super().__init__("Create Post", auto_defer=True)
        self.bot = bot

        self.set_name = nextcord.ui.TextInput(label="Post Name:", placeholder="Topic", min_length=5, max_length=100, required=True, style=nextcord.TextInputStyle.short)
        self.add_item(self.set_name)

    async def callback(self, interaction:Interaction):
        thread = await interaction.channel.create_thread(name=self.set_name.value, type=nextcord.ChannelType.public_thread, reason="Waschen Post Thread")
        sql = "INSERT INTO threads (user_id, thread_id, guild_id, embedmsg_id) VALUES (?, ?, ?, ?)"
        val = (interaction.user.id, thread.id, interaction.guild.id, None)
        self.bot.c.execute(sql,val)
        self.bot.conn.commit()

    async def on_error(self, error, interaction):
        await doLog(self.bot, f"⚠ Error: `{error}`")
        raise error

async def stickyMsg(bot, channel):
    check = bot.c.execute(f"SELECT int_val1 FROM channels WHERE type = 1 AND channel_id = {channel.id}").fetchone()[0]
    view = nextcord.ui.View(timeout=None)
    postButton = nextcord.ui.Button(label="Start a Post", style=nextcord.ButtonStyle.blurple)
    async def postButtonCallback(interaction:Interaction):
        embedTitle = bot.c.execute(f"SELECT str_val3 FROM channels WHERE type = 1 AND channel_id = {channel.id}").fetchone()[0]
        ruleMsg = bot.c.execute(f"SELECT str_val1 FROM channels WHERE type = 1 AND channel_id = {channel.id}").fetchone()[0]
        embed = nextcord.Embed(title=embedTitle, description=ruleMsg, color=0x3366cc)
        agreeButton = nextcord.ui.Button(label="I understand", style=nextcord.ButtonStyle.green)
        async def agreeButtonCallback(interaction:Interaction):
            await interaction.response.send_modal(postModal(bot))
        agreeButton.callback = agreeButtonCallback
        view2 = nextcord.ui.View(timeout=300)
        view2.add_item(agreeButton)
        await interaction.response.send_message(embed=embed, view=view2, ephemeral=True)
    postButton.callback = postButtonCallback
    view.add_item(postButton)
    msgText = bot.c.execute(f"SELECT str_val2 FROM channels WHERE type = 1 AND channel_id = {channel.id}").fetchone()[0]
    if check:
        message = await channel.fetch_message(check)
        await message.delete()
        message = await channel.send(msgText, view=view)
        bot.c.execute(f"UPDATE channels SET int_val1 = {message.id} WHERE channel_id = {channel.id} AND type = 1")
        bot.conn.commit()
    else:
        message = await channel.send(msgText, view=view)
        bot.c.execute(f"UPDATE channels SET int_val1 = {message.id} WHERE channel_id = {channel.id} AND type = 1")
        bot.conn.commit()

class forumModal(nextcord.ui.Modal):
    def __init__(self, bot, channel, edit:bool):
        modalTitle = "Edit Fake Forum Channel" if edit else "Setup Fake Forum Channel"
        super().__init__(modalTitle, auto_defer=True)
        self.channel = channel
        self.bot = bot
        self.edit = edit

        default_rule = bot.c.execute(f"SELECT str_val1 FROM channels WHERE channel_id = {channel.id}").fetchone()[0] if edit else ""
        default_text = bot.c.execute(f"SELECT str_val2 FROM channels WHERE channel_id = {channel.id}").fetchone()[0] if edit else ""
        default_title = bot.c.execute(f"SELECT str_val3 FROM channels WHERE channel_id = {channel.id}").fetchone()[0] if edit else ""

        self.embedTitle = nextcord.ui.TextInput(label="Embed Title:", min_length=1, max_length=50, default_value=default_title, required=True, style=nextcord.TextInputStyle.short)
        self.add_item(self.embedTitle)
        self.ruleMsg = nextcord.ui.TextInput(label="Rules:", min_length=10, max_length=2000, default_value=default_rule, required=True, style=nextcord.TextInputStyle.paragraph)
        self.add_item(self.ruleMsg)
        self.msgText = nextcord.ui.TextInput(label="Message Text:", min_length=10, max_length=2000, default_value=default_text, required=True, style=nextcord.TextInputStyle.paragraph)
        self.add_item(self.msgText)

    async def callback(self, interaction:Interaction) -> None:
        if self.edit:
            self.bot.c.execute(f"UPDATE channels SET str_val1 = '{self.ruleMsg.value}' WHERE channel_id = {self.channel.id}")
            self.bot.conn.commit()
            self.bot.c.execute(f"UPDATE channels SET str_val2 = '{self.msgText.value}' WHERE channel_id = {self.channel.id}")
            self.bot.conn.commit()
            self.bot.c.execute(f"UPDATE channels SET str_val3 = '{self.embedTitle.value}' WHERE channel_id = {self.channel.id}")
            self.bot.conn.commit()
            await interaction.send_message(f"{self.channel.mention}'s fake forum settings has been updated.", ephemeral=True)
        else:
            sql = "INSERT INTO channels (channel_id, guild_id, type, int_val1, str_val1, str_val2, str_val3) VALUES (?, ?, ?, ?, ?, ?, ?)"
            val = (self.channel.id, interaction.guild.id, 1, None, self.ruleMsg.value, self.msgText.value, self.embedTitle.value)
            self.bot.c.execute(sql,val)
            self.bot.conn.commit()
            await interaction.response.send_message(f"{self.channel.mention} has been added as fake forum channel.", ephemeral=True)
            await stickyMsg(self.bot, self.channel)
        return 0

    async def on_error(self, error, interaction):
        await doLog(self.bot, f"⚠ Error: `{error}`")
        raise error

class filterModal(nextcord.ui.Modal):
    def __init__(self, bot, channel, edit:bool):
        modalTitle = "Edit Filter Channel" if edit else "Setup Filter Channel"
        super().__init__(modalTitle, auto_defer=True)
        self.channel = channel
        self.bot = bot
        self.edit = edit

        default_name = bot.c.execute(f"SELECT str_val2 FROM channels WHERE channel_id = {channel.id}").fetchone()[0] if edit else ""
        default_warn = bot.c.execute(f"SELECT str_val1 FROM channels WHERE channel_id = {channel.id}").fetchone()[0] if edit else ""

        self.defaultThreadName = nextcord.ui.TextInput(label="Default Thread Name:", min_length=5, max_length=100, default_value=default_name, required=True, style=nextcord.TextInputStyle.short)
        self.add_item(self.defaultThreadName)
        self.warnMsg = nextcord.ui.TextInput(label="Warning Message:", min_length=5, max_length=1900, default_value=default_warn, required=True, style=nextcord.TextInputStyle.paragraph)
        self.add_item(self.warnMsg)

    async def callback(self, interaction:Interaction) -> None:
        if self.edit:
            self.bot.c.execute(f"UPDATE channels SET str_val1 = '{self.warnMsg.value}' WHERE channel_id = {self.channel.id}")
            self.bot.conn.commit()
            self.bot.c.execute(f"UPDATE channels SET str_val2 = '{self.defaultThreadName.value}' WHERE channel_id = {self.channel.id}")
            self.bot.conn.commit()
            await interaction.send_message(f"{self.channel.mention}'s filter settings has been updated.", ephemeral=True)
        else:
            sql = "INSERT INTO channels (channel_id, guild_id, type, int_val1, str_val1, str_val2, str_val3) VALUES (?, ?, ?, ?, ?, ?, ?)"
            val = (self.channel.id, interaction.guild.id, 0, None, self.warnMsg.value, self.defaultThreadName.value, None)
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

