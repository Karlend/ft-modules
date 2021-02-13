# requires: captcha-solver

import time # time.time() для времени. Используется для промежутков бонуса, бизнеса и др
import random
import logging
import asyncio
import io

from telethon import types
from captcha_solver import CaptchaSolver
from .. import loader, utils

logger = logging.getLogger("AutoLesya")

lesya = 757724042  # ID бота
lesya_chat = 1462806544

TLG_JOHNNY = 419089999

times = {
	"bonus": 0,
	"work": 0,
	"fight": 10**100
}

stats = {}

formats = {
	"bonus": "Вы сможете получить бонус через",
	"bonus2": "бонус будет доступен через",
	"work": "Вы сможете работать через",
	"id": "ID: "
}

def convert(str):
	arr = str.split(":")
	last = len(arr)
	if last == 3: # H:M:S
		return int(arr[0]) * 3600 + int(arr[1]) * 60 + int(arr[2][:2])
	elif last == 2:
		return int(arr[0]) * 60 + int(arr[1][:2])
	else:
		return int(arr[0][:2])

@loader.tds
class AutoLesyaMod(loader.Module):
	"""Автоматизация LesyaBot"""
	strings = {"name": "LesyaBot"}

	async def send_bot(self, text):
		await asyncio.sleep(random.randint(0, self.db_get("cooldown_time", 10)))
		await self._client.send_message(lesya, text)

	async def client_ready(self, client, db):
		self._me = await client.get_me()
		self._client = client
		self._db = db
		key = self.db_get("api_token")
		if key is not None:
			self.solver = CaptchaSolver('rucaptcha', api_key=key).solve_captcha
		else:
			def solver(raw_data):
				key_ = self.db_get("api_token")
				if key_ is not None:
					self.solver = CaptchaSolver('rucaptcha', api_key=key_).solve_captcha
					return self.solver(raw_data)
				return False
			self.solver = solver
		await self.send_bot("Профиль")

	async def setcaptchatokencmd(self, message):
		"""Указать токен RuCaptcha"""
		api_token = utils.get_args_raw(message)
		self.db_set("api_token", api_token)
		await utils.answer(message, "<b>Есть!</b>")

	async def setcooldowncmd(self, message):
		"""Указать время задержки между командами (в секундах, стандарт - 10)"""
		try:
			cd_time = int(utils.get_args_raw(message))
		except ValueError:
			await utils.answer(message, "<b>Ошибка, укажите время в секундах (без суффикса \"s\", просто число)</b>")
			return
		self.db_set("cooldown_time", cd_time)
		await utils.answer(message, "<b>Есть!</b>")

	async def solvecmd(self, message):
		await message.edit("Ждём ответа...")
		x = await self.solve_captcha(await message.get_reply_message())
		await message.edit(("Ответ: "+str(x)) if x else "<b>Укажите ключ с помощью .setcaptchatoken</b>")

	async def solve_captcha(self, message):
		if not self.solver: return
		file_loc = io.BytesIO()
		await message.download_media(file_loc)
		bytes_ = file_loc.getvalue()
		return self.solver(bytes_)

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
		logger.info("Got profile")
		if not stats.get("info"):
			asyncio.ensure_future(self.timer())

	def parsebonus(self, text, entry):
		if text.find("VIP") != -1 or text.find("PREMIUM") != -1:
			return
		global times

		now = time.time()
		pos = entry + 1 # позиция + длина + пробел
		need = convert(text[pos:])
		times["bonus"] = now + need + 60
	
	def parsejob(self, text, entry): # время для работы
		global times
		now = time.time()
		pos = entry + 1 # позиция + длина + пробел	
		need = convert(text[pos:])
		times["work"] = now + need + 5
		logger.info("need to wait " + str(need))

	def parsefights(self, text):
		global times
		if not "Лечение питомцев" in text:
			return False
		lines = text.split("\n")[1:]
		times_ = []
		for line in lines:
			timestr = line.rsplit(" ", 1)[1]
			if ":" in timestr:
				times_.append(convert(timestr))
		times["fight"] = time.time() + max(times) + 30
		return len(times_) > 0

	async def receive(self, message): # Сообщение от бота
		text = message.text
		if not text:
			return
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
			logger.info("Parsing job")
		# Бонус
		need = formats.get("bonus")
		entry = text.find(need)
		if entry == -1:
			need = formats.get("bonus2")
			entry = text.find(need)
		else:
			self.parsebonus(text, entry + len(need))
		if (text.find("рабочий день закончен") != -1):
			times["work"] = now + 60
			asyncio.ensure_future(self.send_bot("Работать"))
		# Автобой питомцев
		if (text.find("Ваши питомцы проиграли") != -1) or (text.find("Ваши питомцы победили") != -1): # Продолжение боя
			if not self.parsefights(text[1:]):
				await utils.answer(message, "Бой")
		if text.find("код картинки") != -1:
			await self.send_bot(await self.solve_captcha(message))


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
		while True:
			global stats
			global times
			if not stats.get("has"):
				logger.info("no stats")
				return
			logger.info("checking time")
			stats["info"] = True
			global times
			now = time.time()
			if now > times.get("work"):
				logger.info("TIME TO WORK")
				logger.info(str(now) + "/" + str(times.get("work")))
				times["work"] = now + 60
				asyncio.ensure_future(self.send_bot("Работать"))
			if now > times.get("bonus"):
				times["bonus"] = now + 60 * 60 * 8 + 60
				if stats.get("premium"):
					asyncio.ensure_future(self.send_bot("Премиум бонус"))
				if stats.get("vip"):
					asyncio.ensure_future(self.send_bot("Вип бонус"))
				asyncio.ensure_future(self.send_bot("Бонус"))
			if now > times.get("fight"):
				logger.info("TIME TO FIGHT, BABIES")
				asyncio.ensure_future(self.send_bot("Бой"))
				times["fight"] = 10**100
			await asyncio.sleep(5)

	async def watcher(self, message):
		if not isinstance(message, types.Message):
			return
		if not message.text:
			return
		chat_id = utils.get_chat_id(message)
		if chat_id == lesya:
			asyncio.ensure_future(self.receive(message))
		elif chat_id == lesya_chat:
			asyncio.ensure_future(self.receivechat(message))

	def db_set(self, key, value):
		self._db.set(__name__, key, value)

	def db_get(self, key, default=None):
		return self._db.get(__name__, key, default)
