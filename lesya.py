from .. import loader, utils

import logging
import datetime
import time

from telethon import types

logger = logging.getLogger("Lesya")

lesya = 757724042 # ID бота

@loader.tds
class AutoLesya(loader.Module):
	"""Автоматизация функций Бот Леся"""

	async def client_ready(self, client, db):
		self._me = await client.get_me()

	async def watcher(self, message):
		if not isinstance(message, types.Message):
			return
		chat_id = utils.get_chat_id(message)
		if chat_id != lesya:
			return
		logger.debug("Got message from bot")
		text = message.text
		if not text:
			logger.debug("Lesya didn't send text")
			return
		if text.find("Ваши питомцы проиграли") or text.find("Ваши питомцы победили"):
			await utils.answer(message, "Бой")
