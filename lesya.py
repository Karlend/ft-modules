from .. import loader, utils
import time # time.time() для времени. Используется для промежутков бонуса, бизнеса и др
from telethon import types
# from telethon.tl.functions.updates import GetStateRequest

lesya = 757724042  # ID бота
init = False
times = {
	"bonus": 0,
	"work": 0
}
stats = {}

formats = {
	"bonus": "Вы сможете получить бонус через",
	"bonus2": "бонус будет доступен через"
}

@loader.tds
class AutoLesyaMod(loader.Module):
	"""Автоматизация LesyaBot"""
	strings = {"name": "LesyaBot"}

	async def client_ready(self, client, db):
		self._me = await client.get_me()
		# await client(GetStateRequest())
		await client.send_message(lesya, "Профиль")

	async def watcher(self, message):
		global init
		global times
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
		# Начало для бонуса
		text_normal = text.replace("станет", "будет")
		str_f = formats.get("bonus2")
		bonus = text_normal.find(str)
		if bonus == -1:
			str_f = formats.get("bonus")
			bonus = text_normal.find(str_f)
		if (bonus != -1): # Бонус будет через n период времени
			pos = bonus + len(str_f)
			need = "Это:" + text_normal[pos:]
			await utils.answer(message, need)
		# Автобой питомцев
		if (text.find("Ваши питомцы проиграли") != -1) or (text.find("Ваши питомцы победили") != -1): # Продолжение боя
			await utils.answer(message, "Бой") # todo: чек времени, когда нету стероидов
		# Автосбор бонусов
		if stats.get("has") and (now > times.get("bonus")): # todo: Получение времени для следующего бонуса из сообщения
			times["bonus"] = now + 60 * 60 * 8
			await message.client.send_message(lesya, "Бонус")
			if stats.get("vip"):
				await message.client.send_message(lesya, "Вип бонус")
			if stats.get("premium"):
				await message.client.send_message(lesya, "Премиум бонус")
		if stats.get("work") and (now > times.get("work")): # todo: Получение времени для следующей работы
			times["work"] = now + 60 * 13 # раз в 13 минут
			for i in range(3):
				await message.client.send_message(lesya, "Работать")
