from .. import loader, utils
import requests

from PIL import Image
from io import BytesIO, StringIO

allowed = {
	"mode": "text/sticker/image",
	"city": "стандартный город",
	"lang": "код языка ( двухзначный - ru / ua / en и тд. )",
	"moreargs": "доп аргументы для запроса ( не лезь, если не знаешь )"
}

class kWeatherMod(loader.Module):
	"""Парсер погоды"""
	strings = {"name": "kWeather"}

	async def client_ready(self, client, db):
		self._me = await client.get_me()
		self._db = db
		self.mode = self.db_get("mode", "text")
		self.city = self.db_get("city", "") # Пустая - смотрит по айпи
		self.lang = self.db_get("lang", "ru")
		self.moreargs = self.db_get("args", "&q&F&0&p&M")

	def db_set(self, key, value):
		self._db.set(__name__, key, value)

	def db_get(self, key, default=None):
		return self._db.get(__name__, key, default)

	async def kweathercmd(self, message):
		city = utils.get_args_raw(message) or self.city
		if self.mode == "text":
			text = requests.get("http://wttr.in/" + city + "?lang=" + self.lang + "&A&T" + self.moreargs).text # A - ANSI формат, T - Убиает цветные теги
			await utils.answer(message, "<code>" + text + "</code>")
		elif self.mode == "sticker" or self.mode == "image":
			fmt = self.mode == "sticker" and "webp" or "png"
			link = "http://wttr.in/" + city + ".png?lang=" + self.lang + "&A" + self.moreargs
			await utils.answer(message, "<b>KWeather:</b> Загрузка")
			response = requests.get(link)

			img = Image.open(BytesIO(response.content))
			w, h = img.size
			if w > h:
				img = img.resize((512, int(h * (512 / w))), Image.ANTIALIAS)
			else:
				img = img.resize((int((w * (512 / h))), 512), Image.ANTIALIAS)

			dat = BytesIO()
			dat.name = "sticker." + fmt
			img.save(dat, format=fmt.upper())
			dat.seek(0)
			await utils.answer(message, dat)
		else:
			await utils.answer(message, "<b>kWeather:</b> неизвестный тип отправки")


	async def kweather_settingscmd(self, message):
		text = utils.get_args_raw(message) or ""
		args = text.split(" ")
		if len(args) < 2:
			modes = ""
			for mode in allowed:
				modes += "\n<code>" + mode + "</code> - <code>" + allowed.get(mode) + "</code>"
			await utils.answer(message, "<b>kWeather:</b> Доступные настройки:" + modes)
			return
		change, new = args[0], args[1]
		if change == "mode":
			self.mode = new
		elif change == "city":
			self.city = new
		elif change == "lang":
			self.lang = new
		elif change == "moreargs":
			self.moreargs = new
		else:
			await utils.answer(message, "<b>kWeather:</b> Неверный аргумент")
			return
		self.db_set(change, new)
		await utils.answer(message, "<b>kWeather:</b> Настройки изменены")
