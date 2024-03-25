import discord, os, re

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)
    
@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=1153858189884915752))
    print(f"[bitcamper] logged in as {client.user.name}")

@tree.command(name="ping", description="Ping", guild=discord.Object(id=1153858189884915752))
async def ping_command(interaction):
    await interaction.response.send_message(
        f"**{int(client.latency*1000)}**ms"
    )

@tree.command(name="mkchannels", description="Create private channels for members with a specified role.", guild=discord.Object(id=1153858189884915752))
async def create_channels(interaction, role: discord.Role = None):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            f"Only administrators can use this command.", ephemeral=True
        )
        return
    
    guild = interaction.guild

    if role:
        members_to_process = [member for member in guild.members if role in member.roles]
    else:
        members_to_process = [member for member in guild.members if len(member.roles) == 1 and guild.default_role in member.roles]

    creating, skipping = [], []
    for member in members_to_process:
        if re.sub(r"[^\w]", "", member.name.lower()) in [channel.name for channel in member.guild.channels]:
            skipping.append(member.name)
        else:
            creating.append(member.name)
    
    message = f"Creating channels for {', '.join(creating)}."
    
    if len(creating) <= 0:
        message = "Creating channels for nobody."
    if len(skipping) > 0:
        message += f" Skipping creating channels for {', '.join(skipping)}. (Channels already exist)"
        
    await interaction.response.send_message(
        message, ephemeral=True
    )

    for member in members_to_process:
        channel_name = re.sub(r"[^\w]", "", member.name.lower())
        
        if channel_name in [channel.name for channel in member.guild.channels]:
            continue
        
        await on_member_join(member)
    
@client.event
async def on_member_join(member):
    channel_name = f"{member.name}"
    guild = member.guild
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True),
        client.user: discord.PermissionOverwrite(read_messages=True)
    }
    
    if "ახალი მოსწავლე" in [category.name for category in guild.categories]:
        category = [category for category in guild.categories if category.name == "ახალი მოსწავლე"][0]
    else:    
        category = await guild.create_category("ახალი მოსწავლე")

    new_channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category)
    
    await new_channel.send(f"გამარჯობა, {member.mention}! იმისათვის რომ მოგენიჭოთ მოსწავლის როლი და გამოგიჩნდეთ სასწავლო არხები, გთხოვთ მოგვწეროთ საიტზე რეგისტრაციისას გამოყენებული email და მოსწავლის ასაკი.")

def start():
    client.run(os.environ["DISCORD_BOT_TOKEN"])

if __name__ == "__main__":
    client.run(os.environ["DISCORD_BOT_TOKEN"])