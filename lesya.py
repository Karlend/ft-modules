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
	"bonus2": "бонус будет доступен через",
	"work": "Вы сможете работать через"
}

@loader.tds
class AutoLesyaMod(loader.Module):
	"""Автоматизация LesyaBot"""
	strings = {"name": "LesyaBot"}

	async def client_ready(self, client, db):
		self._me = await client.get_me()	
		# await client(GetStateRequest())
		await client.send_message(lesya, "Профиль")

	def convert(self, str):
		arr = str.split(":")
		last = len(arr)
		if last == 3: # H:M:S
			return int(arr[0]) * 3600 + int(arr[1]) * 60 + int(arr[2][:2])
		elif last == 2:
			return int(arr[0]) * 60 + int(arr[1][:2])
		else:
			return int(arr[0][:2])
			

	async def watcher(self, message):
		global init
		global times
		global stats
		now = time.time()
		# Автосбор бонусов
		if stats.get("has") and (now > times.get("bonus")):
			times["bonus"] = now + 60 * 60 * 8 + 60
			await message.client.send_message(lesya, "Бонус")
			if stats.get("vip"):
				await message.client.send_message(lesya, "Вип бонус")
			if stats.get("premium"):
				await message.client.send_message(lesya, "Премиум бонус")
		if stats.get("work") and (now > times.get("work")): # todo: Получение времени для следующей работы
			for i in range(7):
				if now > times.get("work"):
					await message.client.send_message(lesya, "Работать")
		# Приём сообщений от бота
		if not isinstance(message, types.Message):
			return
		chat_id = utils.get_chat_id(message)
		if chat_id != lesya:
			return
		text = message.text
		if not text:
			return
		if (text.find("Ваш профиль:") != -1): # Инфа по профилю привет
			stats["has"] = True
			stats["premium"] = text.find("Статус: Premium") != 1
			stats["vip"] = (text.find("Статус: Premium") != 1) or (text.find("Статус: VIP") != 1)
			stats["work"] = text.find("Работа: ") != 1
			stats["clan"] = text.find("Клан: ") != 1
		# Начало для бонуса
		text_normal = text.replace("станет", "будет")
		str_f = formats.get("bonus2")
		bonus = text_normal.find(str_f)
		if (bonus == -1):
			str_f = formats.get("bonus")
			bonus = text_normal.find(str_f)
		if (bonus != -1) and (text_normal.find("VIP") == -1 and text_normal.find("PREMIUM") == -1): # Бонус будет через n период времени
			pos = bonus + len(str_f) + 1 # позиция + длина + пробел
			need = self.convert(text_normal[pos:])
			times["bonus"] = now + need + 60
		# Время для работы
		str_f = formats.get("work")
		work = text.find(str_f)
		if (work != -1):
			pos = work + len(str_f) + 1 # позиция + длина + пробел	
			need = self.convert(text[pos:])
			times["work"] = now + need + 10
		# Автобой питомцев
		if (text.find("Ваши питомцы проиграли") != -1) or (text.find("Ваши питомцы победили") != -1): # Продолжение боя
			await utils.answer(message, "Бой") # todo: чек времени, когда нету стероидов
