from .. import loader, utils
import time # time.time() для времени. Используется для промежутков бонуса, бизнеса и др
from telethon import types

lesya = 757724042  # ID бота
init = False
next_bonus = 0
stats = {}

@loader.tds
class AutoLesyaMod(loader.Module):
	"""Автоматизация LesyaBot"""
	strings = {"name": "LesyaBot"}

	async def client_ready(self, client, db):
		self._me = await client.get_me()

	async def watcher(self, message):
		global init
		global next_bonus
		if not isinstance(message, types.Message):
			return
		chat_id = utils.get_chat_id(message)
		if chat_id != lesya:
			return
		text = message.text
		if not text:
			return
		now = time.time()
		if (text.find("Ваш профиль:") != -1): # Инфа по профилю привет
			global stats
			stats["has"] = True
			stats["premium"] = text.find("Статус: Premium") != 1
			stats["vip"] = (text.find("Статус: Premium") != 1) or (text.find("Статус: VIP") != 1)
			stats["work"] = text.find("Работа: ") != 1
			stats["clan"] = text.find("Клан: ") != 1
		if (text.find("Ваши питомцы проиграли") != -1) or (text.find("Ваши питомцы победили") != -1): # Продолжение боя
			await utils.answer(message, "Бой") # todo: чек времени, когда нету стероидов
		if (now > next_bonus) and stats.get("has"):
			next_bonus = now + 60 * 60 * 8
			await message.client.send_message(lesya, "Бонус")
			if stats.get("vip"):
				await message.client.send_message(lesya, "Вип бонус")
			if stats.get("premium"):
				await message.client.send_message(lesya, "Премиум бонус")
