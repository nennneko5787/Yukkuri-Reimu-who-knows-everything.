# なんでも知ってるってマジですか！？！？

import discord
from discord import app_commands
from keep_alive import keep_alive
import akinator as Aki
from akinator.async_aki import Akinator
import asyncio
import os

if os.path.isfile(".env"):
	from dotenv import load_dotenv
	load_dotenv(verbose=True)

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
	change_presence.start()
	await tree.sync()

@tree.command(name="ping", description="Ping値を確認します")
async def ping(interaction: discord.Interaction):
	await interaction.response.send_message(f"🏓Pong! **{client.latency}ms**!")

# ゲーム管理部

class AkinatorQuestionView(discord.ui.View):
	def __init__(self, akinator: Akinator):
		super().__init__(timeout=None)
		self.akinator = akinator

	@discord.ui.button(label="はい", style=discord.ButtonStyle.primary)
	async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
		await akinatorAnswer(self.akinator, interaction, "yes")

	@discord.ui.button(label="わからない", style=discord.ButtonStyle.gray)
	async def idk(self, interaction: discord.Interaction, button: discord.ui.Button):
		await akinatorAnswer(self.akinator, interaction, "idk")

	@discord.ui.button(label="いいえ", style=discord.ButtonStyle.danger)
	async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
		await akinatorAnswer(self.akinator, interaction, "no")

	@discord.ui.button(label="どちらかといえばそう", style=discord.ButtonStyle.green)
	async def probably(self, interaction: discord.Interaction, button: discord.ui.Button):
		await akinatorAnswer(self.akinator, interaction, "probably")

	@discord.ui.button(label="どちらかといえば違う", style=discord.ButtonStyle.green)
	async def probably_not(self, interaction: discord.Interaction, button: discord.ui.Button):
		await akinatorAnswer(self.akinator, interaction, "probably not")

	@discord.ui.button(label="前の質問に戻る", style=discord.ButtonStyle.gray)
	async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
		await akinatorAnswer(self.akinator, interaction, "back")

class AkinatorWinView(discord.ui.View):
	def __init__(self, akinator: Akinator, guess = 1):
		super().__init__(timeout=None)
		self.akinator = akinator
		self.guess = guess

	@discord.ui.button(label="はい", style=discord.ButtonStyle.primary)
	async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.defer()
		if interaction.user.id != interaction.message.interaction.user.id:
			await interaction.followup.send("他の人は回答できません！", ephemeral=True)
			return
		self.guess = self.guess - 1
		embed = discord.Embed(title="よしあたった！！", description=f"キャラクター: {self.akinator.guesses[self.guess]['name']}\n({self.akinator.guesses[self.guess]['description']})")
		embed.set_image(url=self.akinator.guesses[self.guess]['absolute_picture_path'])
		await interaction.message.edit(embed=embed,view=None)
		await self.akinator.close()

	@discord.ui.button(label="いいえ", style=discord.ButtonStyle.danger)
	async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.defer()
		if interaction.user.id != interaction.message.interaction.user.id:
			await interaction.followup.send("他の人は回答できません！", ephemeral=True)
			return
		print(f"{self.guess} / {len(self.akinator.guesses)}")
		if self.guess == len(self.akinator.guesses):
			print("∩(・∀・)∩　ﾓｳ ｵﾃｱｹﾞﾀﾞﾈ")
			embed = discord.Embed(title="わからない。お手上げだ。", description="`∩(・∀・)∩　ﾓｳ ｵﾃｱｹﾞﾀﾞﾈ`")
			await interaction.message.edit(embed=embed,view=None)
		else:
			print("答えます")
			print(f"{self.guess}")
			embed = discord.Embed(title=f"もしかして {self.akinator.guesses[self.guess]['name']} ですか？", description=self.akinator.guesses[self.guess]['description'])
			embed.set_image(url=self.akinator.guesses[self.guess]['absolute_picture_path'])
			view = AkinatorWinView(self.akinator, self.guess + 1)
			await interaction.message.edit(embed=embed,view=view)

async def akinatorAnswer(akinator: Akinator, interaction: discord.Interaction, answer: str):
	await interaction.response.defer()
	if interaction.user.id != interaction.message.interaction.user.id:
		await interaction.followup.send("他の人は回答できません！", ephemeral=True)
		return

	if akinator.progression <= 80:
		if answer == "back":
			try:
				q = await akinator.back()
			except Aki.CantGoBackAnyFurther:
				pass
		else:
			await akinator.answer(answer)

		embed = discord.Embed(title=f"{akinator.step + 1}番目の質問", description=akinator.question)
		view = AkinatorQuestionView(akinator)
		await interaction.message.edit(embed=embed,view=view)
		return
	else:
		await akinator.win()
		embed = discord.Embed(title=f"もしかして {akinator.first_guess['name']} ですか？", description=akinator.first_guess['description'])
		embed.set_image(url=akinator.first_guess['absolute_picture_path'])
		view = AkinatorWinView(akinator)
		await interaction.message.edit(embed=embed,view=view)

@tree.command(name="game", description="ゲームを開始します")
async def game(interaction: discord.Interaction):
	await interaction.response.defer()
	akinator = Akinator()
	q = await akinator.start_game(language="jp")
	view = AkinatorQuestionView(akinator)
	embed = discord.Embed(title=f"{akinator.step + 1}番目の質問", description=akinator.question)
	await interaction.followup.send(embed=embed,view=view)

@tasks.loop(seconds=20)
async def change_presence():
	game = discord.Game(f"{len(client.guilds)} SERVERS")
	await client.change_presence(status=discord.Status.online, activity=game)

keep_alive()
client.run(os.getenv("discord"))
