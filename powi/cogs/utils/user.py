import discord

def handle_custom(user):
    a = [c for c in user.activities if c.type == discord.ActivityType.custom]
    if not a:
        return None, discord.ActivityType.custom
    a = a[0]
    c_status = None
    if not a.name and not a.emoji:
        return None, discord.ActivityType.custom
    elif a.name and a.emoji:
        c_status = ("{emoji} {name}").format(emoji=a.emoji, name=a.name)
    elif a.emoji:
        c_status = ("{emoji}").format(emoji=a.emoji)
    elif a.name:
        c_status = ("{name}").format(name=a.name)
    return c_status, discord.ActivityType.custom

def handle_playing(user):
    p_acts = [c for c in user.activities if c.type == discord.ActivityType.playing]
    if not p_acts:
        return None, discord.ActivityType.playing
    p_act = p_acts[0]
    act = ("Joue à : {name}").format(name=p_act.name)
    return act, discord.ActivityType.playing

def handle_streaming(user):
    s_acts = [c for c in user.activities if c.type == discord.ActivityType.streaming]
    if not s_acts:
        return None, discord.ActivityType.streaming
    s_act = s_acts[0]
    if isinstance(s_act, discord.Streaming):
        act = ("Stream : [{name}{sep}{game}]({url})").format(
            name=discord.utils.escape_markdown(s_act.name),
            sep=" | " if s_act.game else "",
            game=discord.utils.escape_markdown(s_act.game) if s_act.game else "",
            url=s_act.url,
        )
    else:
        act = ("Stream : {name}").format(name=s_act.name)
    return act, discord.ActivityType.streaming

def handle_listening(user):
    l_acts = [c for c in user.activities if c.type == discord.ActivityType.listening]
    if not l_acts:
        return None, discord.ActivityType.listening
    l_act = l_acts[0]
    if isinstance(l_act, discord.Spotify):
        act = ("Ecoute : [{title}{sep}{artist}]({url})").format(
            title=discord.utils.escape_markdown(l_act.title),
            sep=" | " if l_act.artist else "",
            artist=discord.utils.escape_markdown(l_act.artist) if l_act.artist else "",
            url=f"https://open.spotify.com/track/{l_act.track_id}",
        )
    else:
        act = ("Ecoute : {title}").format(title=l_act.name)
    return act, discord.ActivityType.listening

def handle_watching(user):
    w_acts = [c for c in user.activities if c.type == discord.ActivityType.watching]
    if not w_acts:
        return None, discord.ActivityType.watching
    w_act = w_acts[0]
    act = ("Regarde : {name}").format(name=w_act.name)
    return act, discord.ActivityType.watching

def get_status_string(user):
        string = ""
        for a in [
            handle_custom(user),
            handle_playing(user),
            handle_listening(user),
            handle_streaming(user),
            handle_watching(user),
        ]:
            status_string, status_type = a
            if status_string is None:
                continue
            string += f"{status_string}\n"
        return string

def get_status_emoji(user):
    if any(a.type is discord.ActivityType.streaming for a in user.activities):
        statusemoji = "\N{LARGE PURPLE CIRCLE}"
    elif user.status.name == "online":
        statusemoji = "\N{LARGE GREEN CIRCLE}"
    elif user.status.name == "offline":
        statusemoji = "\N{MEDIUM WHITE CIRCLE}"
    elif user.status.name == "dnd":
        statusemoji = "\N{LARGE RED CIRCLE}"
    elif user.status.name == "idle":
        statusemoji = "\N{LARGE ORANGE CIRCLE}"

    return statusemoji

def get_status(user):
    return get_status_string(user), get_status_emoji(user)

def get_roles_string(user):
    roles = user.roles[-1:0:-1]
    if roles:
        role_str = ", ".join([x.mention for x in roles])

        if len(role_str) > 1024:
            continuation_string = (
                "and {numeric_number} more roles not displayed due to embed limits."
            )
            available_length = 1024 - len(continuation_string)
            role_chunks = []
            remaining_roles = 0

            for r in roles:
                chunk = f"{r.mention}, "
                chunk_size = len(chunk)

                if chunk_size < available_length:
                    available_length -= chunk_size
                    role_chunks.append(chunk)
                else:
                    remaining_roles += 1

            role_chunks.append(continuation_string.format(numeric_number=remaining_roles))
            role_str = "".join(role_chunks)

        return role_str

    return None