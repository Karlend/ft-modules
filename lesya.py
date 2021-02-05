from .. import loader, utils
from telethon import types

lesya = 757724042  # ID бота


@loader.tds
class AutoLesyaMod(loader.Module):
	"""Автоматизация LesyaBot"""
	strings = {"name": "LesyaBot"}

	async def watcher(self, message):
		if not isinstance(message, types.Message):
			return
		chat_id = message.chat.id
		if chat_id != lesya:
			return
		text = message.text
		if not text:
			return
		if text.find("Ваши питомцы проиграли") or text.find("Ваши питомцы победили"):
			await utils.answer(message, "Бой")
