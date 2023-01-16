# discord-bookworm-memes-filter

This is server specific discord bot.

## How it works

This bot deletes every messages with no valid links or attachments. Users sending such messages will be DM'd a message.
If the user has the "manage-messages" permission, their messages will bypass the restriction.

If a message has a valid link or an attachment, a thread will be autogenerated.
Users may delete and rename the thread (using the embed & buttons the bot sended) on the 10 first minutes as long as they are the one who started the thread.
The /rename command can be used after the 10 minutes as an alternative.

This bot allows keeping the meme channel as moderated as possible while keeping the ability of discussing memes via threads.
