from .. import loader, utils
import time # time.time() для времени. Используется для промежутков бонуса, бизнеса и др
from telethon import types
import asyncio

lesya = 757724042  # ID бота
lesya_chat = 1462806544

TLG_JOHNNY = 419089999

times = {
	"bonus": 0,
	"work": 0
}

stats = {}

formats = {
	"bonus": "Вы сможете получить бонус через",
	"bonus2": "бонус будет доступен через",
	"work": "Вы сможете работать через",
	"id": "ID: "
}

@loader.tds
class AutoLesyaMod(loader.Module):
	"""Автоматизация LesyaBot"""
	strings = {"name": "LesyaBot"}

	async def send_bot(self, text):
		await self._client.send_message(lesya, text)

	async def client_ready(self, client, db):
		self._me = await client.get_me()
		self._client = client
		# await client(GetStateRequest())
		await self.send_bot("Профиль")
		

	def convert(self, str):
		arr = str.split(":")
		last = len(arr)
		if last == 3: # H:M:S
			return int(arr[0]) * 3600 + int(arr[1]) * 60 + int(arr[2][:2])
		elif last == 2:
			return int(arr[0]) * 60 + int(arr[1][:2])
		else:
			return int(arr[0][:2])

	async def parseprofile(self, text):
		global stats
		stats["has"] = True
		id_format = formats.get("id")
		id_str = text.find(id_format)
		id_start = id_str + len(id_format)
		id_end = text.find("\n", id_start)
		stats["id"] = text[id_start:id_end]
		stats["premium"] = text.find("Статус: Premium") != -1
		stats["vip"] = (text.find("Статус: Premium") != -1) or (text.find("Статус: VIP") != -1)
		stats["work"] = text.find("Работа: ") != -1
		stats["clan"] = text.find("Клан: ") != -1
		stats["bitcoin"] = text.find("Ферма: ") != -1
		print("Got profile")
		if not stats.get("info"):
			await self.timer()

	def parsebonus(self, text, entry):
		if text.find("VIP") != -1 or text.find("PREMIUM") != -1:
			return
		global times

		now = time.time()
		pos = entry + 1 # позиция + длина + пробел
		need = self.convert(text[pos:])
		times["bonus"] = now + need + 60
	
	def parsejob(self, text, entry): # время для работы
		global times
		now = time.time()
		pos = entry + 1 # позиция + длина + пробел	
		need = self.convert(text[pos:])
		times["work"] = now + need + 5
		print("need to wait " + str(need))

	async def receive(self, message): # Сообщение от бота
		text = message.text
		now = time.time()
		# Инфа из профиля
		if (text.find("Ваш профиль:") != -1): # Инфа по профилю привет
			await self.parseprofile(text)
		# Ещё не получил инфу
		if not stats.get("has"):
			return
		# Расчёт действий
		global times
		text.replace("станет", "будет")
		# Время работы
		need = formats.get("work")
		entry = text.find(need)
		if entry != -1:
			self.parsejob(text, entry + len(need))
			print("Parsing job")
		# Бонус
		need = formats.get("bonus")
		entry = text.find(need)
		if entry == -1:
			need = formats.get("bonus2")
			entry = text.find(need)
		if entry != -1:
			self.parsebonus(text, entry + len(need))
		if (text.find("рабочий день закончен") != -1):
			times["work"] = now + 60
			await utils.answer(message, "Работать")
		# Автобой питомцев
		if (text.find("Ваши питомцы проиграли") != -1) or (text.find("Ваши питомцы победили") != -1): # Продолжение боя
			await utils.answer(message, "Бой") # todo: чек времени, когда нету стероидов

	async def receivechat(self, message): # сообщения в канале с ботом
		text = message.text
		user_id = message.from_id or 0

		if (text.find(", предметы для ограбления:") != -1) and user_id == lesya:
			for i in range(10):
				await self.send_bot("Предметы " + str(i + 1))
			await utils.answer(message, "Ограбление")

		if (text == "!Закуп"):
			if user_id != TLG_JOHNNY:
				await utils.answer(message, "Пошёл нахер. Хать фу")
				return

			for i in range(10):
				await self.send_bot("Предметы " + str(i))
			await utils.answer(message, "Ограбление")

	async def timer(self):
		global stats
		global times
		if not stats.get("has"):
			return
		stats["info"] = True
		global times
		now = time.time()
		if now > times.get("work"):
			times["work"] = now + 100
			await self.send_bot("Работать")
		if now > times.get("bonus"):
			times["bonus"] = now + 60 * 60 * 8 + 60
			if stats.get("premium"):
				await self.send_bot("Премиум бонус")
			if stats.get("vip"):
				await self.send_bot("Вип бонус")
			await self.send_bot("Бонус")
		await asyncio.sleep(5)
		await self.timer()


	async def watcher(self, message):
		if not isinstance(message, types.Message):
			return
		if not message.text:
			return
		chat_id = utils.get_chat_id(message)
		if chat_id == lesya:
			await self.receive(message)
		elif chat_id == lesya_chat:
			await self.receivechat(message)
