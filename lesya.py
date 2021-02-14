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
	"bonus": ("бонус будет доступен", "бонус станет доступен", "сможете получить бонус"),
	"work": "вы сможете работать через",
	"id": "ID: "
}

def convert(str_):
	arr = str_.split(":")
	last = len(arr)
	try:
		if last == 3: # H:M:S
			return int(arr[0]) * 3600 + int(arr[1]) * 60 + int(arr[2][:2])
		elif last == 2:
			return int(arr[0]) * 60 + int(arr[1][:2])
		else:
			return int(arr[0][:2])
	except ValueError:
		logger.error(f"CONVERT ERROR WHILE PARSING {str_!r}")
		return -1

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
		stats["premium"] = "статус: premium" in text
		stats["vip"] = "cтатус: premium" or "cтатус: vip" in text
		stats["work"] = "работа:" in text
		stats["clan"] = "клан:" in text
		stats["bitcoin"] = "ферма:" in text
		logger.info("Got profile")
		if not stats.get("info"):
			asyncio.ensure_future(self.timer())

	def parsebonus(self, text):
		global times
		if "vip" in text or "vip" in text:
			return
		now = time.time()

		timestr = text.rsplit(" ", 2)
		if ":" not in (timestr[-1]):
			timestr.pop(-1)
		need = convert(timestr[-1])
		times["bonus"] = now + need + 60
		logger.info("need to wait " + str(need))
	
	def parsejob(self, text): # время для работы
		global times
		now = time.time()

		line = text.split("\n")[1]
		timestr = line.rsplit(" ", 1)[1]
		need = convert(timestr)
		times["work"] = now + need + 5
		logger.info("need to wait " + str(need))

	def parsefights(self, text):
		global times
		if not "лечение питомцев" in text:
			return False
		lines = text.split("\n")
		logger.error(str(lines))
		times_ = []
		for _ in range(len(lines)):
			if "лечение питомцев" in lines[0]:
				lines.pop(0)
				break
			lines.pop(0)
		for line in lines:
			timestr = line.rsplit(" ", 1)[1]
			if ":" in timestr:
				val = convert(timestr)
				times_.append(val if val else 0)
		times["fight"] = time.time() + max(times_) + 30
		return len(times_) > 0

	async def receive(self, message): # Сообщение от бота
		global times
		text = message.text.lower()
		if not text:
			return
		# Инфа из профиля
		if "ваш профиль" in text: # Инфа по профилю привет
			await self.parseprofile(text)
		# Ещё не получил инфу
		if not stats.get("has"):
			return
		# Расчёт действий
		# Время работы
		if formats.get("work") in text:
			self.parsejob(text)
			logger.info("Parsing job")
		# Бонус
		for btext in formats.get("bonus"):
			if btext in text:
				self.parsebonus(text)
				logger.info("Parsing bonus")
		# Автобой питомцев
		if "ваши питомцы проиграли" in text or "ваши питомцы победили" in text: # Продолжение боя
			if not self.parsefights(text[1:]):
				asyncio.ensure_future(self.send_bot("Бой"))
		if "код картинки" in text:
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
			if not self in self.allmodules.modules:
				logger.fatal("AutoLesya unloaded. Breaking timer.")
				break
			global stats
			global times
			if not stats.get("has"):
				logger.info("no stats")
				continue
			stats["info"] = True
			global times
			now = time.time()
			if now > times.get("work") and stats.get("work"):
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
		if message.from_id == self._me.id:
			return
		chat_id = utils.get_chat_id(message)
		if chat_id == lesya:
			await self.receive(message)
		elif chat_id == lesya_chat:
			asyncio.ensure_future(self.receivechat(message))

	def db_set(self, key, value):
		self._db.set(__name__, key, value)

	def db_get(self, key, default=None):
		return self._db.get(__name__, key, default)
