from .. import loader, utils
import time # time.time() для времени. Используется для промежутков бонуса, бизнеса и др
from telethon import types

lesya = 757724042  # ID бота
init = False
@loader.tds
class AutoLesyaMod(loader.Module):
	"""Автоматизация LesyaBot"""
	strings = {"name": "LesyaBot"}
	next_bonus = 0

	async def client_ready(self, client, db):
		self._me = await client.get_me()

	async def watcher(self, message):
		if init == False:
			message.client.send_message(lesya, "Профиль")
			init = True
		if not isinstance(message, types.Message):
			return
		chat_id = utils.get_chat_id(message)
		if chat_id != lesya:
			return
		text = message.text
		if not text:
			return
		now = time.time()
		if (text.find("Ваши питомцы проиграли") != -1) or (text.find("Ваши питомцы победили") != -1): # Продолжение боя
			await utils.answer(message, "Бой") # todo: чек времени, когда нету стероидов
		if next_bonus and (now > next_bonus) and (next_bonus > 0):
			await message.client.send_message(lesya, "Бонус")
			await message.client.send_message(lesya, "Вип бонус")
			await message.client.send_message(lesya, "Премиум бонус")
			next_bonus = now + 60 * 60 * 8
