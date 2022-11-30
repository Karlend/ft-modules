"""LesyaBot automation"""

# pylint: disable=relative-beyond-top-level, invalid-name, missing-class-docstring, missing-function-docstring, too-many-instance-attributes
# ^^ да пошел этот пайлинт нахуй, я лучше знаю как писать мой код

# Вообщем коротко о том как тут всё работает.
# Весь процесс (код, файл) делится на три основные части: классификатор, парсер, и хэндлеры.
#
# Классификатор - штука, которая принимает на вход сообщение, а на выходе говорит, что это за
# сообщение. Классификатор определён в классе LesyaClassifier. метод classify_message на вход
# получает текст сообщения, а на выходе отдаёт его тип. Кстате, все типы описаны в Enum классе
# MessageType. Что делает классификатор? Получив текст, он проходится по таблице классификации,
# поочерёдно применяя правила из неё на текст. Если какое-то из правил успешно выполнилось,
# классификатор вернёт тип, с которым это правило связано.
# Ну, для примера, у нас есть текст:
#   🃏 Joker, Ваши питомцы проиграли 😩
#   🐉 Вы нашли нового питомца для клановой войны: «Несси»!
#
# Если мы передадим этот текст в классификатор (предварительно применив к тексту .lower()),
# то он начнёт итерировать по таблице классификации. Рано или поздно он дойдёт до правила:
#   MessageType.AutoFight_Continue: ("ваши питомцы проиграли", "ваши питомцы победили")
# Он вытаскивает отсюда значение (то что перед двоеточием - ключ, после - значение), и проверяет
# его. Буквально, выполняется код:
#   if "ваши питомцы проиграли" in text or "ваши питомнцы победили" in text:
#	   return MessageType.AutoFight_Continue
#
# Так как наше сообщение подпадает под одну из частей данного правила, а именно содержит текст
# "ваши питомцы проиграли", то классификатор вернёт MessageType.AutoFight_Continue, как и записано
# в таблице классификации.
#
# Теперь, о формате записи правил.
#
# Правила могут записываться в tuple, тоесть ("а", "б", "в"). Это значит, что в тексте должно
# содержаться ЛИБО "а" ЛИБО "б" ЛИБО "в".
#
# Далее, правило может быть простой строкой, тоесть "абв" (в коде это записано как ("абв"), но в
# питоне эти скобки незначущие, по этому разницы и нет. записано так просто для удобства чтения).
# Значит такая запись, что "абв" должен содержаться в тексте.
#
# Последнее - лямбда функции. Лямбда функции (почитать о них можно
# тут https://www.w3schools.com/python/python_lambda.asp) это более умные маленькие правила для
# более точного определения чего-то в тексте. Лямбда функции должны возвращать True или False. Для
# простоты понимания, туда можно записывать всё, что пишется в условиях ифа. Например:
#   lambda text: "слава" in text and "україні" in text
#
# Очевидно, что правило сработает только при условии того что обе строки есть в тексте.
# Так же, можно в лямбда функциях получить stats. Для єтого достаточно записать второй параметр:
#   lambda text, stats: stats.get("need_to_buy") and "предметы для ограбления" in text
#
# P.S. В коде лямбда функции так же взяты в круглые скобки, но можно их и не использовать. Опять
# же, они ничего не значат и использованы просто для красоты.
#
#
#
# Следующая важная часть - Парсер. Тут он реализован в классе LesyaParser. Про него можно долго
# не болтать, ибо, я думаю, тут всё и так понятно. Содержит в себе функции для парсинга всякой
# фигни. Можно посмотреть как работает в самом коде.
#
#
# Далее - Хэндлеры. Уже этих ребят вызывает модуль на основе инфы, которую он получил из
# классификатора. Хэндлеры разбиты на некие модули, дабы проще понимать что к чему относится.
# Как главный модуль (тот который LesyaMod, далее буду называть его супервизором, чтобы не путать
# с подмодулями-хэндлерами (а они далее - модули)) понимает какой именно хэндлер нужно вызвать?
# У каждого модуля есть элемент __map__. Туда записываются правила, по которым супервизор будет
# выбирать функцию-обработчик события. Впринципе вся работа с __map__ расписана в докстрингах к
# BaseHandler, но я приведу тут некоторую инфу. В ключ записывается имя элемента в кавычках. В
# ключ можно пихнуть не просто имя, а имя со звёздочкой. например AutoFight_* значит любой ивент,
# имя которого начинается на AutoFight_* (ну тоесть AutoFight_Continue, AutoFight_Waiting, и т.д).
# А в значении же, собственно и записывается имя функции-члена класса, которая будет принимать
# этот самый ивент. Главное не забыть, что имя функции нужно писать как строку, а не как просто
# функцию, ибо self в области видимости где пишется правило __map__ никакого нет.
#
#
# Некоторые части кода достаточно хорошо задокументированы, по этому, в целом должно быть всё
# понятно


import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from types import FunctionType

from math import floor
from random import randint, choice
from datetime import timedelta
from time import time, strftime

from telethon import types

from .. import loader, utils


logger = logging.getLogger("LesyaAuto")


# парочка констант
LESYA_CHATID = 757724042  # чат с ботом
LOGCHANNEL_CHATID = 1462806544  # чат, куда отправлять всякие логи
LESYA_LAG = 0
humanizer_phrases = [
	"Клан",
	"Кв",
	"Город",
	"Город стат",
	"Город склад продать",
	"Город банк снять все",
	"Баланс",
	"Банк",
	"Питомцы",
	"Кейсы",
	"Курс",
	"Рейтинг",
	"Кланы",
	"Анекдот",
	"ПРИМЕР",
	"Казино 1000",
	"Стакан 1 1000",
	"Стакан 2 1000",
	"Стакан 3 1000",
	"Загадка",
	"Сдаюсь",
	"Бизнес снять 1 все",
	"Бизнес снять 2 все",
	"◀️ В главное меню",
	"💎 Основное",
	"📒 Профиль",
	"💲 Баланс",
	"👑 Рейтинг",
	"🛍 Магазин",
	"◀️ В раздел «Основное»",
	"🏆 Топ",
	"⚙️ Настройки",
	"🎉 Развлечения",
	"🚀 Игры",
	"❓ Помощь",
	"🛡 Кланы",
	"🐹 Питомцы",
	"💰 Команды банка",
	"🌆 Мой город",
	"💼 Бизнес",
	"⛏ Рудник",
	"📦 Подработка",
	"👔 Работа",
	"📦 Кейсы"
]

COOLDOWNS = {  # кто тут даун я так и не понял
	"bonus": 60,

	"work": 10,
	"fight": 5,

	"opencase": 60,

	"trade": 5,
	"cup": 5,
	"casino": 5,

	"humanizer": 1800,

	"etc": 10,
}

BITCOIN_FARM_PRICE = 900000000

allowed_commands = [  # Разрешенные команды для админов конфы
	"профиль",
	"баланс",
	"банк",

	"гет",

	"кланы",
	"клан",
	"клан пригласить *",

	"город",
	"город склад продать",
	"город казна снять",

	"кв",
	"кв участники",

	"ограбление",
	"ограбление участники"
]

best_settings = {
	"fight": True,
	"work": True,
	"bonus": True,
	"opencase": True,
	"progress": True,
	"pet_bitcoin": True,
	# "pet_stimulator": True,
	# "pet_food": True,
	# "pet_cases": True,
	"clan_buy": True,
	"humanizer": True
}

settings_tip = {
	"fight": "🤺 Бой",
	"work": "👔 Работа",
	"bonus": "🔔 Бонус",

	"opencase": "🧳 Открытие кейсов",

	"progress": "🚧 Автоматические закупы",

	"pet_bitcoin": "🅱️ Сбор биткоинов перед покупкой",
	"pet_stimulator": "💊 Стимулятор питомцев",
	"pet_food": "🥫 Корм питомцев",
	"pet_cases": "💼 Множитель кейсов питомцев",
	# "pet_helper": "📑 Расчёт лучшего питомца",

	"clan_war": "⚔️ Клановые войны",
	"clan_heist": "🔫 Ограбление",
	"clan_buy": "💸 Закуп для ограбления",

	"auto_trade": "🔧 Трейд на всё",
	"auto_cup": "🥤 Стакан на всё",
	"auto_casino": "🎰 Казино на всё",

	"humanizer": "🗣️ Рандомные сообщения боту"
}

cooldowns_hints = {
	"bonus": "🔔 Бонус",

	"work": "👔 Работа",
	"fight": "🤺 Бои",

	"opencase": "🧳 Между открытием кейсов",

	"trade": "🔧 Авто-трейд",
	"cup": "🥤 Авто-стакан",
	"casino": "🎰 Авто-сазино",

	"humanizer": "🗣️ Рандомные сообщения боту",

	"bot_lag": "🚨 Если бот лагает и не отвечает на сообщения",

	"etc": "📝 Остальное"
}

settings_phrases = {
	"captcha_pidors": "Репорт у меня капчу не принимает"
}

phrases_tips = {
	"captcha_pidors": "Если дауничи пришлют несколько капч"
}


class LesyaAccountStatus(Enum):
	"""Статус акка. Ну тут, думаю, всё ясно"""
	Default = 0
	VIP = 1
	Premium = 2
	Deluxe = 3


class MessageType(Enum):
	"""Класс для классификации сообщений, и поиска для них обработчика"""

	# Основные сообщения
	ProfileInfo = 0  # инфа о профиле
	BannedNotification = 1  # инфа о бане
	Captcha = 2  # капча
	Captcha_bruted = 3  # сбрутил капчу
	VOID1 = 4  # !!

	# бонусы
	Bonus_Message = 5  # бонусы
	Bonus_MoneyMessage = 6  # Автовалюта премиума
	Bonus_MoneyGiveMessage = 7  # Гив лимит

	# Автобой
	AutoFight_Continue = 8  # продолжение боя
	AutoFight_Waiting = 9  # уже в бою или нужно отдохнуть
	AutoFight_NoPets = 10  # нет питомцев
	AutoFight_NewPets = 11  # новые пацаны в отряде

	BalanceInfo = 12  # Деньги с баланса

	VOID3 = 13  # чел..

	BusinessMoneyMessage = 15  # Деньги с бизнесов
	BitcoinsMessage = 16  # Биткоины с фермы

	AutoProgress_MaxFarms = 17  # Для автоматического развития
	AutoProgress_BoughtFarms = 18 # Купил фермы

	# Ограбления кланов
	ClanHeist_BaseMessage = 19  # Основное сообщение
	ClanHeist_BaseNoPlan = 20  # Плана нет
	ClanHeist_BaseWaiting = 21  # Ожидание начала
	ClanHeist_Choose = 22  # Выбор ограбления
	ClanHeist_PlanChoose = 23  # Выбор плана
	ClanHeist_Started = 24  # После ограбление старт / Когда уже идёт, а ты прописал старт
	ClanHeist_Down = 25  # "в ограблении должно участвовать"...

	# Войны кланов
	ClanWar_NotStarted = 26  # Война не запущена
	ClanWar_SearchStarted = 27  # Подготовка или уже сражение
	ClanWar_Preparing = 28  # Подготовка или уже сражение
	ClanWar_UNDEF0 = 29  # примерное время до окончания отборочного этапа
	ClanWar_Collect = 30  # Идёт сбор питомцев с боёв
	ClanWar_FinalFight = 31  # Финальная битва
	ClanWar_FinalWait = 32  # Финальное ожидание

	# Кейсы
	OpenCase_Voids = 33  # ориг коммент: На пустышках максимум можно 1, без указания количества
	OpenCase_Info = 34  # инфа о кейсах
	OpenCase_NoCases = 35  # у нас нет кейсов
	OpenCase_4Got = 36  # 4 предмета
	# ориг: вам пыпал(о) 1(1) кейс(ов) / ваш (VIP/Прем) приз (на сегодня) — 1(00) (донат) кейс(ов)
	OpenCase_GotCase = 37  # коммент выше

	# Авто трейд
	AutoTrade_Earned = 38  # мы заработали
	AutoTrade_Lost = 39  # мы потеряли

	# Авто стакан (auto_cup)
	AutoCup_True = 40  # правильно
	AutoCup_False = 41  # неверно

	# Авто казино
	AutoCasino_Lost = 42  # проиграли
	AutoCasino_Win = 43  # выиграли

	# Работа
	Works_Time = 44  # время работы
	Works_DayEnd = 45  # рабочий день закончен
	# Автоповышение
	Works_NewJob = 46  # новая работа
	Works_JobList = 47  # "можете устроится на одну из работ"
	Works_JobInJobList = 48  # new_job и ", профессии"
	Works_NoJob = 49  # нигде не работаем
	Works_UNDEF0 = 50  # "выберите нужный предмет из списка ниже"

	# Инфа о петах
	Pets_NoPets = 51  # нет питомцев
	Pets_Page = 52  # ", страница"
	Pets_Shop = 53 # Зоотовары

	# Клан
	Clan_Joined = 54  # вступили или уже состоим
	Clan_Invite = 55  # пригласили в клан
	Clan_MultipleInvite = 56  # пригласили и бот просит выбрать

	# Автозакуп
	AutoBuy_Message = 57  # Автозакуп для ограблений
	AutoBuy_NoClan = 58  # нас в клане нет

	# Передача денег
	MoneyTransactions_Received = 59  # нам перевели
	MoneyTransactions_Sent = 60  # мы перевели
	MoneyTransactions_NotEnough = 61 # Недостаточно

	# Деньги с кейса и работы
	WorkMoney_Received = 62  # нам выпала валюта
	WorkMoney_Earned = 63  # мы заработали
	WorkMoney_NoEnoughMoney = 64  # недостаточно монет

	ChatCommands_Ban = 65  # Бан
	ChatCommands_PlanChoosed = 66  # "вы выбрали план"
	ChatCommands_Buy = 67  # Закуп
	ChatCommands_Ping = 68  # Пинг
	ChatCommands_Promo = 69  # Промо


@dataclass
class LesyaBTCMiner:
	"""Класс для интерпретации биткоин ферм"""
	name: str
	count: int


@dataclass
class LesyaBan:
	"""Класс для интерпретации сообщений о бане"""
	permanent: bool  # Пермач или нет
	ban_time: int  # Время, на сколько забанили, в секундах. Если пермач, равно -1
	release_time: int  # Время, когда выпустят, в UNIX-time. Если пермач, равно 9999999999
	reason: str  # причина


@dataclass
class LesyaAccount:
	"""Класс для реинтерпретации текста из /profile"""
	uid: int
	name: str
	status: LesyaAccountStatus
	balance: float
	in_bank: float
	bitcoin_balance: float
	clan: bool
	btcminer: LesyaBTCMiner
	additional_info: dict


# Карта конвертации строки с статусом в машинопонимаемый формат
STATUS_MAP = {
	"V.I.P": LesyaAccountStatus.VIP,
	"v.i.p": LesyaAccountStatus.VIP,
	"Premium": LesyaAccountStatus.Premium,
	"premium": LesyaAccountStatus.Premium,
	"Deluxe": LesyaAccountStatus.Deluxe,
	"deluxe": LesyaAccountStatus.Deluxe
}

STATUS_UNMAP = {
	LesyaAccountStatus.Default: "Игрок",
	LesyaAccountStatus.VIP: "V.I.P",
	LesyaAccountStatus.Premium: "Premium",
	LesyaAccountStatus.Deluxe: "Deluxe"
}


class LesyaClassifier:
	"""Классификатор сообщений. Тоже самое что 30 ифов, но лаконичнее"""
	classify_table = {  # таблица классификации
		MessageType.ProfileInfo: ("ваш профиль:",),
		MessageType.BannedNotification: ("вы заблокированы",),
		MessageType.Captcha: ("ваши действия похожи на автоматические. чтобы доказать, что вы настоящий человек, выполните задание на картинке.",),
		MessageType.Captcha_bruted: (", все ограничения сняты, спасибо",),

		MessageType.Works_Time: ("работа станет доступна"),
		MessageType.Works_DayEnd: ("рабочий день закончен", "рабочая неделя завершена"),
		MessageType.Works_NewJob: ("доступна новая работа"),
		MessageType.Works_JobList: (lambda text: (", вам доступно " in text or ", вам доступен ") and " раздел" in text),
		MessageType.Works_JobInJobList: (", доступные профессии"),
		MessageType.Works_NoJob: ("вы нигде не работаете", "вы не трудоустроены"),
		MessageType.Works_UNDEF0: ("выберите нужный предмет из списка ниже"),

		MessageType.Pets_NoPets: ("у вас нет питомцев"),
		MessageType.Pets_Page: (", ваши питомцы ["),

		MessageType.Pets_Shop: (", товары для питомцев:"),



		MessageType.Bonus_Message: ("бонус будет доступен", "бонус станет доступен",
									"сможете получить бонус", "сможете получить v.i.p бонус",
									"сможете получить premium бонус", ", вы сможете получить deluxe бонус через"),
		MessageType.Bonus_MoneyMessage: ("получить валюту можно будет только через", "получить бонусную валюту можно будет только через "),
		MessageType.Bonus_MoneyGiveMessage: ("вы сможете выдавать валюту через"),

		MessageType.AutoBuy_Message:
			(lambda text, stats: stats.get("need_to_buy") and \
			 "требуемые предметы для участия в ограблении:" in text),
		MessageType.AutoBuy_NoClan:
			(lambda text, stats: stats.get("need_to_buy") and \
			 "этот раздел доступен только участникам клана" in text),

		MessageType.AutoFight_Continue: ("ваши питомцы проиграли", "ваши питомцы победили"),
		MessageType.AutoFight_Waiting: ("вы напали на игрока", "текущий бой:",
										"вашим питомцам требуется отдых",
										"примерное время боя:", "восстанавливает здоровье"),

		MessageType.AutoFight_NoPets: ("наберите питомцев в отряд с помощью команды",
									   "для проведения битвы нужны питомцы",
									   "для начала боя вам требуются питомцы"),
		MessageType.AutoFight_NewPets: ("теперь в вашем отряде"),

		MessageType.ClanHeist_BaseNoPlan: ("план: не выбран", "выбран план: плана нет", "Способы прохождения:"),
		MessageType.ClanHeist_BaseWaiting: ("подготовка завершена, можно начинать ограбление", ", в ограблении требуется минимум"),
		MessageType.ClanHeist_BaseMessage: (", информация об ограблении "),
		MessageType.ClanHeist_Choose: (lambda text: ", доступно " in text and "ограблен" in text and "- стоимость подготовки" in text),
		MessageType.ClanHeist_PlanChoose:
			(lambda text: ", вы начали ограбление" in text and "доступные способы прохождения" in text),
		MessageType.ClanHeist_Started: (", ограбление началось!", ", ограбление уже началось", ", ограбление уже запущено"),
		MessageType.ClanHeist_Down: (", в ограблении должно участвовать"),

		MessageType.ClanWar_NotStarted: (", клановая война не запущена"),
		MessageType.ClanWar_SearchStarted: (", вы начали поиск противника!"),
		MessageType.ClanWar_Preparing: ("НУ, ЭТОГО НЕ БУДЕТ УЖЕ:"),
		MessageType.ClanWar_UNDEF0: ("примерное время до окончания отборочного этапа:"),
		MessageType.ClanWar_Collect: ("до конца отборочного этапа:"),
		MessageType.ClanWar_FinalFight: ("финальная битва через:"),
		MessageType.ClanWar_FinalWait: ("конец войны через:"),

		MessageType.OpenCase_Voids: ("чтобы открывать несколько кейсов за раз, завершите исследование"),
		MessageType.OpenCase_Info: (", ваши кейсы:", "📦 ваши кейсы:"),
		MessageType.OpenCase_NoCases: (", у вас нет кейсов"),
		MessageType.OpenCase_4Got: (lambda text: ", вам выпал" in text and " предмет" in text),
		MessageType.OpenCase_GotCase:
			(lambda text: ("📦 вам выпал" in text and " кейс" in text) or (
				", ваш" in text and " приз" in text and "кейсов" in text)),

		MessageType.AutoCup_True: (", правильно! приз ", ", верно! приз ",
								   ", вы угадали! приз "),
		MessageType.AutoCup_False:
			(lambda text: ", неверно, это был " in text and "-й стаканчик" in text),

		MessageType.AutoCasino_Lost: (", вы проиграли"),
		MessageType.AutoCasino_Win: (", вы выиграли"),

		MessageType.BalanceInfo: (", на руках "),

		MessageType.MoneyTransactions_Received:
			(lambda text: "[УВЕДОМЛЕНИЕ]" in text and "▶️ игрок" in text and "перевел вам" in text),
		MessageType.MoneyTransactions_Sent:
			(lambda text: ", вы передали игроку" in text and "$" in text),
		MessageType.MoneyTransactions_NotEnough: ("должно быть не менее", "недостаточно денег"),

		MessageType.WorkMoney_Received: (lambda text: "вам выпало" in text and "валюта:" in text),
		MessageType.WorkMoney_Earned: ("вы заработали"),

		MessageType.AutoProgress_MaxFarms: ("у Вас максимальное количество ферм",),

		MessageType.ChatCommands_Ban: ("!ban"),
		MessageType.ChatCommands_PlanChoosed: (", вы выбрали план №"),
		MessageType.ChatCommands_Buy: ("!закуп"),
		MessageType.ChatCommands_Ping: ("!пинг"),
		MessageType.ChatCommands_Promo: ("!промо")
	}

	def __init__(self, additional_info):
		self._addinfo = additional_info
		self._logger = logging.getLogger("LesyaAuto::Classifier")

	def classify_message(self, text) -> MessageType:
		"""Проходим по таблице классификации. Если ключ найден в тексте, возвращаем тип сообщения"""
		self._logger.debug("Classifying message %s", text)
		for key, val in self.classify_table.items():
			if isinstance(val, tuple):
				for k in val:
					if k in text:
						return key
			elif isinstance(val, str):
				if val in text:
					return key
			elif isinstance(val, FunctionType):
				profile = self._addinfo.get("profile", None)
				if not profile:
					arg2 = {}
				else:
					arg2 = profile.additional_info
				args = (text, arg2) if val.__code__.co_argcount == 2 else (
					text,)  # pylint: disable=no-member
				if val(*args):
					return key
		self._logger.error("Classification failed")
		return None


class LesyaParser:
	"""Парсер разных приколов из текста"""

	def __init__(self, db):
		self.__db = db

	def __getattr__(self, attrname):
		if attrname == "profile":
			return self.__db["profile"]
		raise AttributeError

	def _get_line_startswith(self, text, startswith) -> str:
		"""Найти строку которая начинается с текста в startswith.
		Юзает генератор вместо разбивки текста на строки"""
		try:
			return next((line for line in text.lower().split(
				"\n") if line.startswith(startswith.lower())))
		except StopIteration:
			return None

	def _find_line_contains(self, text, contains) -> str:
		"""Найти строку которая содержит текст в contains. Аналогично, юзаем генератор"""
		try:
			return next((line for line in text.lower().split(
				"\n") if contains.lower() in line))
		except StopIteration:
			return None

	def _convert_time(self, timestr) -> int:
		"""Получает на вход время в формате чисел, разделённых двоеточием, на выходе секунды.
		Может работать с колвом чисел от 1 до 4, от секунд до дней"""
		# Да, выглядит страшно, и завтра я возможно не смогу обьяснить как это работает.
		# Но, зато компактно, и без левых импортов.

		# Можно накинуть поддержку например недель, месяцов,
		# просто закинув в конец списка внутри zip() значение диапазона в секундах
		return sum(x * int(t[:2]) for x, t in zip([1, 60, 3600, 86400], timestr.split(":")[::-1]))

	def parse_id(self, text) -> int:
		"""Парсит айди из сообщения. Пример:

		Вход:
			Товарищ, Ваш профиль:
			ID: 2107924
			Баланс: 3.951.766.420$
			Биткоины: 1.000₿
			Рейтинг: 2

		Результат:
			2107924

		"""
		return int(self._get_line_startswith(text, "🔎 ID:").split(" ")[2])

	def parse_name(self, text) -> str:
		"""Парсит ник из сообщения"""
		return text.split("\n")[0][:-14] # Пропускаем ", Ваш профиль:"

	def convert_money(self, money):
		money = money.replace(".", "")
		money = money.replace("₿", "")
		money = money.replace("+", "")
		money = int(money[:-1])
		return money

	def parse_status(self, text) -> LesyaAccountStatus:
		"""Парсит статус аккаунта из сообщения"""
		lines = text.split("\n")
		line = None
		for line_text in lines:
			if "статус:" in line_text.lower():
				line = line_text
				break
		if not line:
			return LesyaAccountStatus.Default
		return STATUS_MAP.get(line.rsplit(" ", 1)[1], LesyaAccountStatus.Default)

	def parse_balance(self, text) -> int:
		"""Парсит баланс"""
		line = self._get_line_startswith(text, "💰 Баланс:")
		if not line:
			return 0
		return int(line.rsplit(" ", 1)[1][:-1].replace(".", ""))

	def parse_in_bank(self, text) -> int:
		"""Парсит баланс в банке"""
		line = self._get_line_startswith(text, "💳 В банке:")
		if not line:
			return 0
		return int(line.split(" ")[3][:-1].replace(".", ""))

	def parse_bitcoin(self, text) -> int:
		"""Парсит баланс биткоинов"""
		line = self._get_line_startswith(text, "🌐 Биткоины:")
		if not line:
			return 0
		return int(line.split(" ")[2][:-1].replace(".", ""))

	def parse_clan(self, text) -> bool:
		"""Парсит наличие клана"""
		line = self._find_line_contains(text, "Клан:")
		return line is not None

	def parse_btcminer(self, text) -> LesyaBTCMiner:
		"""Парсит биткоин ферму"""
		line = self._get_line_startswith(text, "⠀🔋 Биткоин ферма:")
		if not line:
			return LesyaBTCMiner("", 0)
		line = line.replace("🔋 Биткоин ферма: ", "")
		count_text_start_idx = line.index("(")
		count_test_stop_idx = line.index(")")
		name = line[1:count_text_start_idx].rstrip()
		count = int(line[count_text_start_idx
					+ 2: count_test_stop_idx].replace(" ", ""))
		return LesyaBTCMiner(name, count)

	def parse_ban(self, text):
		"""Парсит сообщения с уведкой о бане"""
		lines = text.split("\n")
		firstline = lines[0]
		logger.info(firstline)
		permanent = "навсегда" in firstline
		ban_time = -1
		release_time = 999999999999
		if not permanent:
			logger.info(firstline.rsplit(" ", 1)[1])
			ban_time = self._convert_time(firstline.rsplit(" ", 1)[1])
			release_time = time() + ban_time
		reasonline = lines[1]
		reason = "Причина не указана"
		if reasonline:
			reason = reasonline[11:]
		return LesyaBan(permanent, ban_time, release_time, reason)

	def parse_account_info(self, text) -> LesyaAccount:
		"""Спарсить аккаунт из сообщения (ожидается текст из ответа на Профиль)"""
		return LesyaAccount(self.parse_id(text), self.parse_name(text), self.parse_status(text),
							self.parse_balance(text), self.parse_in_bank(text),
							self.parse_bitcoin(text), self.parse_clan(text),
							self.parse_btcminer(text), {})

	def parse_fights(self, text):
		if not "лечение питомцев" in text:
			return False
		lines = text.split("\n")
		times_ = []
		for line in lines:
			if ":" in line:
				timestr = line.rsplit(" ", 1)[1]
				if "[" in timestr and ":" in timestr:
					val = self._convert_time(timestr)
					times_.append(val if val else 0)
		return time() + max(times_) + 2

	def parse_last_entry(self, text):
		last = "1"
		lines = text.split("\n")
		for line in lines:
			dot = line.find(".")
			if line[:1] == "🔹" and dot != -1:
				last = line[2:dot]
		return str(last)

	def lastline_time(self, text):
		return self._convert_time(text.split("\n")[-1].rsplit(" ", 1)[1])

	def clanheist_planchoose(self, text):
		line = self._find_line_contains(text, "время на подготовку:")
		return self._convert_time(line.rsplit(" ", 1)[1])

	def clanwar_parse(self, text):
		mtime = self._convert_time(text.split("\n")[-2].rsplit(" ", 1)[1])
		return mtime, mtime < 666

	def clanwar_parsepoints(self, text):
		text = text.lower()
		lines = text.split("\n")
		max_upgrade = 16
		pets = {}
		points = 0
		for line in lines:
			logger.info(line)
			if "доступно очков способностей:" in line:
				logger.info("found line")
				pos = line.find(":")
				points = line[pos + 2:]
				logger.info(points)
				points = int(points)
			elif "💎" in line and "/" in line:
				start = line.find("⭐")
				end = line.find("/")
				has = line[start + 1:end]
				has = int(has)
				pets[len(pets) + 1] = has
		test = []
		for pet in pets:
			has = pets[pet]
			pet = str(pet)
			if has == max_upgrade:
				continue
			for up_id in range(max_upgrade - has):
				if points <= 0:
					break
				upgrade = has + up_id + 1
				to_send = "Кв улучшить " + pet + " " + str(upgrade)
				points -= 1
				test.append(to_send)
		return test

	def opencase_parse(self, text):
		text = text.replace("<strong>№", "")
		text = text.replace("</strong>", "")
		lines = text.split("\n")

		case_id = None
		for line in lines:
			if not "🔹" in line or not "»" in text:
				continue
			if line[1] != "🔹":
				continue
			dot = line.find(" »")
			case_id = line[3:dot]
		return case_id

	def works_parsejob(self, text):
		line = self._find_line_contains(text, "работа станет доступна")
		if not line:
			return None

		return self._convert_time(line.rsplit(" ", 1)[1])

	def pets_parse(self, text):
		_logger = logging.getLogger("LesyaAuto::PetsParser")
		arr = self.profile.additional_info.get("pets_parsed") or []

		text = text.replace(" ", "")
		text = text.replace("🔟", "10")
		text = text.replace("⃣", "")
		text = text.replace(".", "")
		# text = text.replace(" ", "")
		lines = text.split("\n")
		for line in lines:
			if not "|" in line:
				continue
			_logger.info("Line: %s", line)
			id_end = line.find("[")
			pet_id = line[:id_end]
			hp_start = line.find("❤️")
			hp_end = line.find("|", hp_start)
			hp = line[hp_start + 2:hp_end]
			_logger.info("ID: %s", str(pet_id))
			_logger.info("HP: %s", str(hp))
			dmg = 0
			if "💢" in line:
				dmg_start = line.find("💢")
				dmg_end = line.find("|", dmg_start)
				if dmg_end != -1:
					dmg = line[dmg_start + 1:dmg_end]
				else:
					dmg = line[dmg_start + 1:]
				_logger.info("Damage: %s", str(dmg))
			mgc = 0
			if "🧿" in line:
				mgc_start = line.find("🧿")
				mgc_end = line.find("|", mgc_start)
				if mgc_end != -1:
					mgc = line[mgc_start + 1:mgc_end]
				else:
					mgc = line[mgc_start + 1:]
				_logger.info("Magic: %s", str(mgc))
			mgc_add = floor(int(mgc) * 1.1)
			_logger.info("Magic2: %s", str(mgc_add))
			total_damage = int(dmg) + mgc_add
			_logger.info("Total Damage: %s", str(mgc_add))
			arr.append({"ID": pet_id, "HP": int(hp), "DMG": total_damage})
		arr.sort(key=lambda x: x.get("DMG"), reverse=True)
		return arr

	def petshop_parse(self, text):
		_logger = logging.getLogger("LesyaAuto::PetsParser")
		_logger.info("Started parsing petshop")

		arr = {}#self.profile.additional_info.get("parsed_petshop") or []
		lines = text.split("\n")
		pets = False
		for line in lines:
			if line == "🏠 Домики:":
				pets = True
			elif pets and "⏫ Усилители и ускорители" in line:
				pets = False
			if pets:
				last = line[-1:]
				if last == "₿":
					start = line.find("№")
					end = line.find("</strong>")
					num = line[start+1:end]
					price = self.convert_money(last)
					arr["parsed_petshop"][num] = price
		self.profile.additional_info["parsed_petshop"] = arr


	def bonus_parsebonus(self, text):
		timestr = text.rsplit(" ", 2)
		if ":" not in timestr[-1]:
			timestr.pop(-1)
		return ("vip_bonus" if "v.i.p" in text
				else ("premium_bonus" if "premium" in text else "deluxe_bonus" if "deluxe" in text else "bonus")), \
			self._convert_time(timestr[-1])

	def bonus_parsemoney(self, text):
		return self._convert_time(text.rsplit(" ", 1)[1])

	def parse_balance2(self, text):
		balance = int(self._find_line_contains(text, "на руках").rsplit(" ", 1)[1][:-1].replace(".", ""))
		btc = int(self._find_line_contains(text, "биткоинов:").rsplit(" ", 1)[1][:-1].replace(".", ""))
		return balance, btc


def gen_phrase():
	phrase_id = randint(0, len(humanizer_phrases) - 1)
	phrase = humanizer_phrases[phrase_id]
	if phrase == "ПРИМЕР":
		phrase = "Реши "
		spaces = "" if randint(0, 1) else " "
		for i in range(randint(1, 5)):
			first = str(randint(0, 1000000))
			second = str(randint(0, 1000000))
			action = choice(["+", "-", "*", "/"])
			start = action
			if i == 0:
				start = ""
			phrase = phrase + start + first + spaces + action + spaces + second + spaces
	return phrase


def gen_time(mode="etc"):
	time_ = COOLDOWNS.get(mode)
	if time_ is None:
		time_ = 10
	return randint(0, time_)


class BaseHandler:
	"""Базовый обработчик ивентов

	Вся магия происходит с помощью члена __map__.
	Чтобы указать, что за что отвечает, нужно вписать в словарь __map__ примерно следующее:
	"Имя_ивента": "Имя_обработчика"

	Имя_ивента - что-нибуть из MessageType. Поддерживает звёздочки. AutoTrade_* значит, что
		обработчик получит все ивенты, имя которых начинается на AutoTrade_. Звёздочка может
		быть в любом месте строки.
	Имя_обработчика - имя метода класса, который вызвется обработать ивент.

	ВАЖНО! имя обработчика обязательно писать в кавычках (то есть хранить в строке).
	Компилятор карт сам найдёт её внутри класса"""

	parser: LesyaParser
	profile: LesyaAccount
	times: dict
	_mod: 'LesyaMod'
	__map__: dict
	settings: dict

	def __init__(self, mainmod):
		self.mainmod = mainmod
		self.parser = mainmod.parser
		# self.profile = mainmod._temp_db["profile"]
		self.times = mainmod._times
		self._logger = logging.getLogger("LesyaAuto::%s" % (self.__class__.__name__))
		self._mod = mainmod
		self.__compiled_map__ = self.build_map()
		self.settings = mainmod._settings

	def __getattr__(self, attrname):
		if attrname == "profile":
			return self.mainmod._temp_db["profile"]
		raise AttributeError("Error in %s: attribute %s not found. listing: %s" % (
							 self.__class__.__name__, attrname, str(dir(self))))

	def set_time(self, time_name, entry):
		self._mod.set_time(time_name, entry)

	async def send_bot(self, text):
		return await self._mod.send_bot(text)

	async def send_group(self, text):
		return await self._mod.send_group(text)

	def build_map(self):
		res_map = {}
		possible_types_str = MessageType.__members__.keys()

		for key, val in self.__map__.items():
			if key in possible_types_str:
				res_map[getattr(MessageType, key)] = getattr(self, val)
				continue
			if key[-1] == "*":
				possible_types = [getattr(MessageType, typename) for typename
								  in possible_types_str
								  if typename.startswith(key[:-1])]
				for type_ in possible_types:
					res_map[type_] = getattr(self, val)
				continue
			if "*" in key:
				idx = key.index("*")
				start_text = key[:idx]
				end_text = key[idx + 1:]
				possible_types = [getattr(MessageType, typename) for typename
								  in possible_types_str
								  if typename[:-len(end_text)].startswith(start_text)
								  and typename[len(start_text):].endswith(end_text)]
				for type_ in possible_types:
					res_map[type_] = getattr(self, val)
				continue
			logging.getLogger("AutoLesya::MapCompiler").fatal(
				"No found entry for %s (module %s)", key, self.__class__.__name__)
			raise KeyError
		return res_map


class AutoFight(BaseHandler):
	__map__ = {
		"AutoFight_*": "AF_MAIN"
	}

	async def AF_MAIN(self, message, classified):
		if classified == MessageType.AutoFight_Continue:
			if tmp_x := self.parser.parse_fights(message.text[1:]):
				self.set_time("fight", tmp_x + gen_time("fight"))
			else:
				self.set_time("fight", time() + gen_time("fight"))
				self._logger.info("Gonna start new fight soon")
			if "вам выпал" in message.text and " кейс" in message.text:
				if not self.profile.additional_info.get("opencase"):
					self.profile.additional_info["opencase"] = 5
		elif classified == MessageType.AutoFight_Waiting:
			args = message.text.rsplit(" ", 1)
			if ":" in args[1] and "восстанавливает здоровье" in message.text:
				wait = self.parser._convert_time(args[1]) or 0
				self.set_time("fight", time() + wait)
			else:
				self.set_time("fight", time() + 600)
				self._logger.info("There is battle/waiting. Gonna wait 10 min before the fight")
		elif classified == MessageType.AutoFight_NoPets:
			self.profile.additional_info["no_pets"] = True
			self._logger.info("I dont have pets. No sense for fighting")
		elif classified == MessageType.AutoFight_NewPets:
			self.set_time("fight", time() + gen_time("fight"))
			del self.profile.additional_info["no_pets"]


class ClanHeist(BaseHandler):
	__map__ = {
		"ClanHeist_*": "CH_MAIN"
	}

	async def CH_MAIN(self, message, classified):
		if not self.settings.get("clan_heist"):
			return

		text = message.text.lower()
		if classified == MessageType.ClanHeist_BaseMessage:
			self._logger.info("Основное сообщение")
			self._logger.info(text)
			if "завершение через " in text:
				self._logger.info("Ждём завершение ограбления")
				wait = self.parser._convert_time(text.rsplit(" ", 1)[1])
				self.set_time("clan_heist", time() + wait + 60)
			elif "выбран план: плана нет" in text or "способы прохождения:" in text or "план: не выбран" in text:
				self._logger.info("Запускаем план")
				clan_time = text.rsplit(" ", 1)[1]
				if ":" in clan_time:
					self.set_time("clan_heist", time() + self.parser._convert_time(clan_time))
				await self.send_group("Ограбление план 1")
				await self.send_group("Ограбление план 1")
			elif "подготовка завершена, можно начинать ограбление" in text:
				self._logger.info("Начинаем ограбление")
				self.set_time("clan_heist", time() + 600)
				await self.send_bot("Ограбление старт")
		elif classified == MessageType.ClanHeist_Choose:
			line = message.text.split("\n")[0]
			last = line.rsplit(" ", 2)[1]
			await self.send_bot("Ограбление " + last)
		elif classified == MessageType.ClanHeist_PlanChoose:
			self.set_time("clan_heist", time() + self.parser.clanheist_planchoose(message.text) + 60)
			await self.send_group("Ограбление план 1")
		elif classified == MessageType.ClanHeist_Started:
			if ", ограбление уже запущено" in text and "следите за текущим прогрессом с помощью команды" in text:
				self.set_time("clan_heist", time() + 600)
				await self.send_bot("Ограбление")
				return
			lines = text.split("\n")
			for line in lines:
				if ("будет идти примерно " in line or "завершение через " in line or "ограбление можно начать через" in line) and ":" in line:
					wait = self.parser._convert_time(line.rsplit(" ", 1)[1])
					self.set_time("clan_heist", time() + wait + 60)
		elif classified == MessageType.ClanHeist_Down:
			self.set_time("clan_heist", time() + 3600)
		elif classified == MessageType.ClanHeist_BaseNoPlan:
			self._logger.info("Запускаем план")
			clan_time = message.text.rsplit(" ", 1)[1]
			if ":" in clan_time:
				self.set_time("clan_heist", time() + self.parser._convert_time(clan_time))
			await self.send_group("Ограбление план 1")
			await self.send_group("Ограбление план 1")
		elif classified == MessageType.ClanHeist_BaseWaiting:
			if ", в ограблении требуется минимум" in message.text:
				self.set_time("clan_heist", time() + 3600)
				return
			self.set_time("clan_heist", time() + 600)
			await self.send_bot("Ограбление старт")


class ClanWar(BaseHandler):
	__map__ = {
		"ClanWar_*": "CW_MAIN"
	}

	async def CW_MAIN(self, message, classified):
		if not self.settings.get("clan_war"):
			return

		if classified == MessageType.ClanWar_NotStarted:
			await self.send_bot("Кв старт")
			self.set_time("clan_war", time() + 60)
		elif classified == MessageType.ClanWar_SearchStarted:
			self.set_time("clan_war", time() + 1800)
		elif classified == MessageType.ClanWar_UNDEF0:
			self.set_time("clan_war", time() + 3600)
			self.set_time("clan_war_upgrade", 0)
		elif classified == MessageType.ClanWar_Collect:
			self.set_time("clan_war", time() + self.parser.lastline_time(message.text) + 60)
			self.set_time("clan_war_upgrade", 0)
		elif classified == MessageType.ClanWar_FinalFight:
			wtime, points = self.parser.clanwar_parse(message.text)
			self.set_time("clan_war", time() + wtime + 60)
			if points and "доступно очков способностей" in message.text:
				for st in self.parser.clanwar_parsepoints(message.text):
					await self.send_bot(st)
				self.set_time("clan_war_upgrade", 0)
			else:
				self.set_time("clan_war_upgrade", time() + wtime - 600)
		elif classified == MessageType.ClanWar_FinalWait:
			wtime, _ = self.parser.clanwar_parse(message.text)
			self.set_time("clan_war", time() + wtime + 60)
			self.set_time("clan_war_upgrade", 0)


class OpenCase(BaseHandler):
	__map__ = {
		"OpenCase_*": "OC_MAIN"
	}

	async def OC_MAIN(self, message, classified):
		if not self.settings.get("opencase"):
			return

		if classified == MessageType.OpenCase_Voids:
			self._logger.info("Не могу открыть максимум кейсов. Убираю число")
			self.profile.additional_info["opencase_limit"] = True
			self.set_time("opencase", time() + gen_time("opencase"))
		elif classified == MessageType.OpenCase_Info:
			self.set_time("opencase", time() + gen_time("opencase"))
			self.profile.additional_info["opencase"] = self.parser.opencase_parse(message.text)
		elif classified == MessageType.OpenCase_NoCases:
			del self.profile.additional_info["opencase"]
		elif classified == MessageType.OpenCase_4Got:
			self.set_time("opencase", time() + gen_time("opencase"))
		elif classified == MessageType.OpenCase_GotCase:
			if not self.profile.additional_info.get("opencase"):
				self.profile.additional_info["opencase"] = 1


class AutoMation(BaseHandler):
	__map__ = {
		"AutoTrade_*": "auto_trade",
		"AutoCup_*": "auto_cup",
		"AutoCasino_*": "auto_casino"
	}

	async def auto_trade(self, _, classified):
		if not self.settings.get("auto_trade"):
			return

		if classified == MessageType.AutoTrade_Earned:
			self.set_time("trade", time() + gen_time("trade") + 1)
			await self.send_bot("Банк положить всё")
		elif classified == MessageType.AutoTrade_Lost:
			self.set_time("trade", time() + gen_time("trade"))

	async def auto_cup(self, _, classified):
		if not self.settings.get("auto_cup"):
			return

		if classified == MessageType.AutoCup_True:
			self.set_time("cup", time() + gen_time("cup") + 1)
			await self.send_bot("Банк положить всё")
		elif classified == MessageType.AutoCup_False:
			self.set_time("cup", time() + gen_time("cup"))

	async def auto_casino(self, _, classified):
		if not self.settings.get("auto_casino"):
			return

		if classified == MessageType.AutoCasino_Win:
			self.set_time("casino", time() + gen_time("casino") + 1)
			await self.send_bot("Банк положить всё")
		elif classified == MessageType.AutoCasino_Lost:
			self.set_time("casino", time() + gen_time("casino"))


class AutoProgress(BaseHandler):
	__map__ = {
		"AutoProgress_MaxFarms": "max_farms",
		"AutoProgress_BoughtFarms": "bought_farms",
	}

	async def max_farms(self, _, classified):
		if not self.settings.get("progress"):
			return
		self.profile.btcminer.count = 1000
		await self.send_bot("Профиль")

	async def bought_farms(self, message, classified):
		text = message.text.replace(" шт.", "")
		start = text.find("(")
		end = text.find(")")
		amount = int(text[start+1:end])
		self.profile.balance -= amount * BITCOIN_FARM_PRICE
		self.profile.btcminer.count += amount

class Works(BaseHandler):

	__map__ = {
		"Works_*": "autoelevate_handler",
		"Works_Time": "worktime_handler",
		"Works_DayEnd": "worktime_handler"
	}

	async def worktime_handler(self, message, classified):
		if classified == MessageType.Works_Time:
			self._logger.info("Parsing job")
			job_time = self.parser.works_parsejob(message.text)
			if not job_time:
				return
			self.set_time("work", time() + job_time + gen_time("work"))
		elif classified == MessageType.Works_DayEnd:
			self.set_time("work", time() + gen_time("work"))
			if "Доступна новая работа" in message.text:
				await self.autoelevate_handler(message, MessageType.Works_NewJob)

	async def autoelevate_handler(self, message, classified):
		if not self.settings.get("work"):
			return

		if classified == MessageType.Works_NewJob:
			self.profile.additional_info["new_job"] = True
			await self.send_bot("Уволиться")
			await self.send_bot("Работа")
		elif classified == MessageType.Works_JobList:
			self.profile.additional_info["new_job"] = True
			active = message.text.split("\n")[0].rsplit(" ")[-4]
			await self.send_bot("Работа " + active)
		elif classified == MessageType.Works_JobInJobList:
			del self.profile.additional_info["new_job"]
			text = message.text
			lines = text.split("\n")
			line_len = len(lines) - 2
			if line_len < 1:
				line_len = 1
			await self.send_bot("Работа " + str(line_len))
		elif classified == MessageType.Works_NoJob:
			self.profile.additional_info["new_job"] = True
			await self.send_bot("Работа")
		elif classified == MessageType.Works_UNDEF0:
			reply_id = 0
			line = message.text.split("\n")[1]
			start = line.find("«")
			need = line[start + 1:-1]
			for row in message.reply_markup.rows:
				buttons = row.buttons
				for but in buttons:
					text = but.text
					if text == need:
						await asyncio.sleep(.5)
						await message.click(reply_id)
						break
					reply_id += 1


class Pets(BaseHandler):
	__map__ = {
		"Pets_*": "Pets_MAIN",
		"Pets_Shop": "petshop_handler"
	}

	async def petshop_handler(self, message, classified):
		self._logger.info("Parsing petshop")
		self.parser.petshop_parse(message.text)

	async def Pets_MAIN(self, message, classified):
		msg = self.profile.additional_info.get("pets_waiting")
		if not msg:
			return

		if classified == MessageType.Pets_NoPets:
			del self.profile.additional_info["pets_waiting"]
			del self.profile.additional_info["pets_parsed"]
			await utils.answer(msg, "Питомцев нету")
		elif classified == MessageType.Pets_Page:
			text = message.text
			line = message.text.split("\n")[0]
			page_info = line.rsplit(" ", 1)[1]
			page_info = page_info[1:-2]
			self._logger.info("now - %s - %i", str(page_info), len(page_info))
			page_info = page_info.split("/")
			cur_page = page_info[0]
			arr = self.parser.pets_parse(message.text)
			self.profile.additional_info["pets_parsed"] = arr

			if cur_page == page_info[1]:
				print("got pets")
				arr = self.profile.additional_info.get("pets_parsed")
				reply = "<b>🐾 Топ питомцы</b>"
				for info in arr:
					reply = reply + "\n" + "🆔 " + info.get("ID") + " | ❤️ " + \
						str(info.get("HP")) + " | 🔫 " + str(info.get("DMG"))
				await utils.answer(msg, reply)
				del self.profile.additional_info["pets_waiting"]
				del self.profile.additional_info["pets_parsed"]
			else:
				print("getting to next page")
				await self.send_bot("Питомцы " + str(int(cur_page) + 1))


class Clans(BaseHandler):
	__map__ = {
		"Clan_*": "Clans_MAIN"
	}

	async def Clans_MAIN(self, _, classified):
		if classified == MessageType.Clan_Joined:
			self.profile.clan = True
		elif classified == MessageType.Clan_Joined:
			await self.send_bot("Клан принять")
		elif classified == MessageType.Clan_MultipleInvite:
			await self.send_bot("Клан принять 1")


class AutoBuy(BaseHandler):
	__map__ = {
		"AutoBuy_*": "AB_MAIN"
	}

	async def AB_MAIN(self, message, classified):
		if classified == MessageType.AutoBuy_Message:
			msg = self.profile.additional_info.get("need_to_buy")
			del self.profile.additional_info["need_to_buy"]
			lines = message.text.split("\n")
			for line in lines:
				dot = line.find(".")
				if line[:1] == "🔸" and dot != -1:
					await self.send_bot("Предметы " + line[2:dot])
			if msg:
				await msg.reply("Ограбление")
		elif classified == MessageType.AutoBuy_NoClan:
			msg = self.profile.additional_info.get("need_to_buy")
			del self.profile.additional_info["need_to_buy"]
			if msg:
				await msg.reply("Дебил, меня в клане нету")


class Money(BaseHandler):
	__map__ = {
		"Bonus_*": "bonus_handler",
		"BalanceInfo": "balance_handler",
		"MoneyTransactions_*": "transactions_handler",
		"WorkMoney_*": "transactions_handler"
	}

	async def bonus_handler(self, message, classified):
		if classified == MessageType.Bonus_Message:
			bonus_type, wtime = self.parser.bonus_parsebonus(message.text)
			self.set_time(bonus_type, time() + wtime + 30)
		elif classified == MessageType.Bonus_MoneyMessage:
			self.set_time("premium_money", time() + self.parser.bonus_parsemoney(message.text) + 30)
		elif classified == MessageType.Bonus_MoneyGiveMessage:
			self.set_time("deluxe_give", time() + self.parser.bonus_parsemoney(message.text) + 30)

	async def balance_handler(self, message, classified):
		if classified == MessageType.BalanceInfo:
			self.profile.balance, self.profile.bitcoin_balance = self.parser.parse_balance2(
				message.text)
			self.profile.in_bank = self.parser.parse_in_bank(message.text)

	async def transactions_handler(self, message, _):
		await message.respond("Баланс")


class ChatCommands(BaseHandler):
	__map__ = {
		"ChatCommands_*": "chatcommands_handler"
	}

	async def chatcommands_handler(self, message, classified):
		_logger = logging.getLogger("LesyaAuto::ChatCommands")

		_logger.info("ChatCommands - got")

		chat, user = message.chat.id, message.sender_id
		if chat != LOGCHANNEL_CHATID: # Хекскод на приколе, хочет, чтобы нам бот давал эти сообщения
			_logger.info("Invalid channel for ChatCommands")
			return

		_logger.info("Checking message")

		if user == LESYA_CHATID:
			if classified == MessageType.ChatCommands_PlanChoosed:
				if not self.settings.get("clan_buy"):
					return

				self.profile.additional_info["need_to_buy"] = message
				await self.send_bot("Предметы")
			return

		if classified == MessageType.ChatCommands_Ban:
			if baninfo := self._mod._temp_db["banned"]:  # pylint: disable=protected-access
				await utils.answer(message,
								   "<b>[LesyaAuto]</b> Я в бане, осталось сидеть: %s" %
								   str(timedelta(seconds=floor(baninfo.release_time - time()))))
			else:
				await utils.answer(message, "[LesyaAuto] Бана нет")
		elif classified == MessageType.ChatCommands_Buy:
			self.profile.additional_info["need_to_buy"] = message
			await self.send_bot("Предметы")
		elif classified == MessageType.ChatCommands_Ping:
			text = "[LesyaAuto]\n" \
				   "- Статус: <b>alive</b>\n" \
				   "- Айди у бота: <code>%i</code>\n" \
				   "- Загружено модулей (%i):\n" \
				   "%s" \
				   "\n\n<b>Powered by TheHub</b>"

			modules_list = "\n".join((" - <code>%s</code>" % x.__name__ for x in ACTIVE_MODULES))
			await utils.answer(message,
							   text % (self.profile.uid, len(ACTIVE_MODULES), modules_list))
		elif classified == MessageType.ChatCommands_Promo:
			await utils.answer(message, "Промо %s" % (message.text[7:]))


ACTIVE_MODULES = [AutoFight, ClanHeist, ClanWar, OpenCase, AutoMation, Works, Pets, Clans,
				  AutoBuy, Money, ChatCommands, AutoProgress]


def timetostr(tmp):
	if tmp <= 0:
		return "Готово"
	return str(timedelta(seconds=floor(tmp)))


class LesyaMod(loader.Module):
	"""Автоматизация для LesyaBot"""
	strings = {
		"name": "LesyaAuto"
	}

	parser: LesyaParser  # парсер
	classifier: LesyaClassifier  # классификатор
	_temp_db = {  # временная локальная база данных
		"profile": None,
		"banned": None,
		"captcha": None
	}
	_handlers_table = {}
	_locks = {
		"captcha": asyncio.Lock(),  # блокировочка на время решения капч
		"profile_get": asyncio.get_event_loop().create_future()  # чтобы ждать пока инфа придёт
	}
	_client = None  # клиент телетона
	_db = None  # база данных ФТГ
	_me = None  # кто я
	_settings = {  # настроечки лучше разместить тут, т.к. относится напрямую к боту + будем менять
		"fight": True,
		"work": True,
		"bonus": True,
		"opencase": True,
		"progress": True,
		"pet_bitcoin": True,
		# "pet_stimulator": True,
		# "pet_food": True,
		# "pet_cases": True,
		"clan_buy": True,
		"humanizer": True
	}
	_times = {  # это тоже скопирую. можно сделать круче, но сложнее и дольше
		"bot_lag": 0,

		"bonus": 0,
		"vip_bonus": 0,
		"premium_bonus": 0,
		"premium_money": 0,
		"deluxe_bonus": 0,
		"deluxe_give": 0,

		"work": 0,
		"fight": 0,

		"opencase": 0,

		"progress": 0,
		"progress_collect": 0,

		"pet_bitcoin": 0,
		"pet_stimulator": 0,
		"pet_food": 0,
		"pet_cases": 0,

		"clan_war": 0,
		"clan_war_upgrade": 0,
		"clan_heist": 0,

		"trade": 0,
		"cup": 0,
		"casino": 0,

		"humanizer": 0
	}
	sleep_hours = {}

	def __init__(self):
		self.parser = LesyaParser(self._temp_db)
		self.classifier = LesyaClassifier(self._temp_db)
		self._handlers_table = {
			MessageType.ProfileInfo: self.handle_profile,
			MessageType.Captcha: self.handle_captcha,
			MessageType.Captcha_bruted: self.handle_captcha_bruted,
			MessageType.BannedNotification: self.handle_banned
		}

		modules = (mod(self) for mod in ACTIVE_MODULES)
		for mod in modules:
			for k, v in mod.__compiled_map__.items():
				if k in self._handlers_table:
					logger.fatal("Collision with %s module and %s module in %s. Skipping...",
								 self._handlers_table[k].__self__.__class__.__name__,
								 mod.__class__.__name__, k)
					continue
				self._handlers_table[k] = v

		self._loop = asyncio.get_event_loop()

	def __getattr__(self, attrname):
		if attrname == "profile":
			return self._temp_db["profile"]
		raise AttributeError(attrname)

	def bot_loaddb(self):
		# Подгрузка времени
		global LOGCHANNEL_CHATID
		LOGCHANNEL_CHATID = int(self.db_get("chat_id", 1462806544) or LOGCHANNEL_CHATID)
		# Лучше отправить пару лишних сообщений, чем ловить флудвейт/бан за изменение сообщения
		#for time_name in self._times:
		#	last = self.db_get("time_" + time_name, 0)
		#	self._times[time_name] = last
		# Настройки из lsettings
		for cmd in settings_tip:
			has = self.db_get(cmd)
			self._settings[cmd] = has
		# Настройки куллдаунов
		global COOLDOWNS
		for mode in COOLDOWNS:
			wait = self.db_get("cooldown_" + mode)
			if wait is None:
				continue
			COOLDOWNS[mode] = wait
		# Время сна
		sleep = self.db_get("sleep_hours")
		if sleep:
			self.sleep_hours = sleep
		global settings_phrases
		for phrase in settings_phrases:
			text = self.db_get("phrase_" + phrase)
			if text is None:
				continue
			settings_phrases[phrase] = text

	async def client_ready(self, client, db):
		self._client = client
		self._db = db
		self._me = await client.get_me()
		self._me_id = self._me.id

		self.bot_loaddb()
		asyncio.ensure_future(self.sw_timer0())

	async def null_handler(self, _, message_type):
		logger.error("No handler found for %s", message_type)

	async def handle_profile(self, message, _):
		self._temp_db["profile"] = self.parser.parse_account_info(message.text)
		logger.info("Parsed profile id %i", self.profile.uid)
		if not self._locks["profile_get"].done():  # если кто-то ждёт инфу по профилу, разлочиваем
			self._locks["profile_get"].set_result(True)
			self._locks["profile_get"] = self._loop.create_future()

		captcha_num = self._temp_db.get("captcha")
		if captcha_num == 0:
			self._temp_db["captcha"] = 1

	async def brute_captcha(self):
		captcha_num = self._temp_db.get("captcha")
		await self.send_group("async def brute_captcha - " + str(captcha_num))
		if captcha_num == 0:
			await self.send_bot("Профиль")
			await self.send_group("Запросил профиль")
			return
		text = (
			captcha_num == 1 and self.profile.name or
			captcha_num == 2 and self.profile.balance or
			captcha_num == 3 and self.profile.in_bank or
			captcha_num == 4 and self.profile.bitcoin_balance or
			captcha_num == 5 and self.profile.btcminer.count
			)

		if text:
			await self.send_group("Отправляю #" + str(captcha_num))
			self._temp_db["captcha"] = captcha_num + 1
			await self.send_bot(str(text))

	async def handle_captcha(self, message, _):
		# блокируем мутекс чтобы таймер не начал пукать, пока капча не решена
		captcha_num = self._temp_db.get("captcha")
		if captcha_num == None:
			self._temp_db["captcha"] = 0 # Запросили профиль для получения последней инфы
			captcha_num = 0
			await self.send_group("Мне прислали капчу. Пытаюсь сбрутить")
			await self._client.forward_messages(LOGCHANNEL_CHATID, message)
			await self.brute_captcha(message)

		if captcha_num > 5:
			await self.send_group("Кажись, новый вопрос в капче. 5 попыток проебал. Больше не отсылаю")
			await self._client.forward_messages(LOGCHANNEL_CHATID, message)
			return

	async def handle_captcha_bruted(self, message, _):
		await self.send_group("Успешно сбрутил капчу")
		del self._temp_db["captcha"]

	async def handle_banned(self, message, _):
		logger.info("Received ban notification")
		baninfo = self.parser.parse_ban(message.text)
		self._temp_db["banned"] = baninfo
		if baninfo.permanent:
			text = "Я улетел в пермач(("
		else:
			text = f"Я улетел в бан на {str(timedelta(seconds=floor(baninfo.ban_time)))}"
		if baninfo.reason:
			reason = f"Причина: {baninfo.reason}"
		else:
			reason = "По беспределу суки закрыли"
		await self.send_group(f"#BAN\n<b>[LesyaAuto]</b> {text}\n{reason}")

	async def process_message(self, message, by_bot):
		global LESYA_LAG
		message.text = message.text.lower()

		message_type = self.classifier.classify_message(message.text)
		logger.info("Received message type %s", message_type)

		# если у нас нет инфы о профиле, то принимаем сообщения только с инфой о профиле,
		# о бане, или капчи
		global_handlers = message_type in [MessageType.ProfileInfo, MessageType.BannedNotification, MessageType.Captcha]
		if (not self._temp_db.get("profile") and not global_handlers) or (global_handlers and not by_bot):
			return

		if by_bot: # Говно не лагает
			LESYA_LAG = 0
			self._times["bot_lag"] = 0

		# чекаем на бан
		if self._temp_db["banned"] and self._temp_db["banned"].release_time > time():
			return

		# чекаем таблицу обработчиков, и если найден обработчик на наш тип сообщения, передаём ему
		# руль, а если нет такого, отдаем управление в null_handler, который не делает ничего,
		# только пукает в лог, что получил управление
		await self._handlers_table.get(message_type, self.null_handler)(message, message_type)

	async def get_bitcoins(self):
		now = time()
		if not self._settings.get("pet_bitcoin") or self._times.get("pet_bitcoin") > now:
			return
		self.set_time("pet_bitcoin", now + 60 * 61)
		await self.send_bot("Ферма")

	async def lesyapingcmd(self, message):
		if not self.profile:
			await utils.answer(message, "Ещё нет инфы")
			return
		text = "[LesyaAuto]\n" \
			"- Статус: <b>alive</b>\n" \
			"- Айди у бота: <code>%i</code>\n" \
			"- Загружено модулей (%i):\n" \
			"%s" \
			"\n\n<b>Powered by TheHub</b>"

		modules_list = "\n".join(("   • <code>%s</code>" % x.__name__ for x in ACTIVE_MODULES))
		await utils.answer(message,
						   text % (self.profile.uid, len(ACTIVE_MODULES), modules_list))

	async def lsetchatcmd(self, message):
		global LOGCHANNEL_CHATID
		LOGCHANNEL_CHATID = int(message.chat.id)
		self.db_set("chat_id", LOGCHANNEL_CHATID)
		await utils.answer(message, "Эта беседа установлена, как чат клана")

	async def ltestchatcmd(self, message):
		try:
			await self._client.send_message(LOGCHANNEL_CHATID, "Тестовое сообщение для проверки чата")
			await utils.answer(message, "Отправлено")
		except:
			await utils.answer(message, "Не смог отправить. Возможно, указан чат, который не доступен")

	async def lcmdcmd(self, message):
		"""Выполнение команд для получения ответа"""
		if message.chat.id != LOGCHANNEL_CHATID:
			return
		cmd = utils.get_args_raw(message) or ""
		text = cmd.lower()
		allow = False
		for word in allowed_commands:
			last = word[-1:]
			if last == "*":
				check_len = len(word) - 1
				sub = word[:check_len]
				msg_sub = text[:check_len]
				if sub == msg_sub:
					allow = True
			elif text == word:
				allow = True
		if not allow:
			await utils.answer(message, "Кыш")
			return
		await utils.answer(message, cmd)

	async def lsleepcmd(self, message):
		"""Время отдыха. Без аргументов - даёт инфу"""
		text = utils.get_args_raw(message) or ""
		args = text.rsplit(" ", 2)
		if not args or not args[0]:
			reply = "<b>😴 Время сна. Сейчас - " + str(strftime("%H")) + "</b>"
			for name in self.sleep_hours:
				hours = self.sleep_hours.get(name)
				reply = reply + "\n⏰ <code>" + name + "</code>: " + str(hours[0] or 0) + "ч -> " + str(hours[1] or 0) + "ч"
			reply = reply + "\n\n<b>Для добавления времени - </b><code>.lsleep название час_начало час_конец</code>\n<b>Для удаления - </b><code>.lsleep название</code>"
			await utils.answer(message,reply)
		elif len(args) == 3: # название, начало и конец
			name = args[0]
			if self.sleep_hours.get(name):
				await utils.answer(message, "Такое имя уже есть")
				return
			try:
				hour_start = int(args[1])
				hour_end = int(args[2])
			except:
				await utils.answer(message, "Часы отдыха должны быть указаны числом")
				return
			if hour_start >= hour_end:
				await utils.answer(message, "Первое число должно быть меньше второго ( 4, 7 - отдых от 4 до 7 утра )")
				return
			self.sleep_hours[name] = [hour_start, hour_end]
			self.db_set("sleep_hours", self.sleep_hours)
			await utils.answer(message, "Время отдыха добавлено")
		elif len(args) == 1:
			name = args[0]
			if not self.sleep_hours.get(name):
				await utils.answer(message, "Такого имени нету")
				return
			del self.sleep_hours[name]
			self.db_set("sleep_hours", self.sleep_hours)
			await utils.answer(message, "Время отдыха удалено")
		else:
			await utils.answer(message, "Неверный формат команды. <code>.lsleep название час_начало час_конец</code>")

	def phrases_set(self, phrase, text):
		global settings_phrases
		settings_phrases[phrase] = text
		self.db_set("phrase_" + phrase, text)

	async def lphrasescmd(self, message):
		"""Управление разными фразами"""
		text = utils.get_args_raw(message) or ""
		args = text.split(" ", 1)
		has_phrase = settings_phrases.get(args[0])
		if not args or len(args) < 2 or not has_phrase:  # без аргумента / без текста изменения
			reply = "<b>💬 Настройка фраз</b>"
			for name in settings_phrases:
				value = settings_phrases.get(name)
				reply = reply + "\n<code>" + name + \
					"</code> (<code>" + phrases_tips.get(name) + "</code>) - <code>" + value + "</code>"
			await utils.answer(message, reply)
		elif len(args) == 2 and has_phrase:
			self.phrases_set(args[0], args[1])
			await utils.answer(message, "<code>" + args[0] + "</code> - <code>" + args[1] + "</code>")

	async def lbotreadycmd(self, message):
		"""Команда для установки оптимальных настроек под бота"""
		for func in best_settings:
			should = best_settings.get(func)
			self.settings_set(func, should)

		await utils.answer(message, "<b>Применены адаптивные бот-настройки</b>")

	def set_cooldown(self, mode, seconds):
		global COOLDOWNS
		COOLDOWNS[mode] = seconds
		self.db_set("cooldown_" + mode, seconds)

	async def lcooldowncmd(self, message):
		"""Указать время задержки между командами"""
		text = utils.get_args_raw(message)
		if not text:
			reply = "<b>⌛ Инфомация о заддержках</b>"
			for cd in COOLDOWNS:
				name = cooldowns_hints.get(cd) or "Unknown"
				wait = COOLDOWNS.get(cd) or 0
				reply = reply + "\n<b>" + name + "</b> ( <code>" + cd + "</code> ) - " + timetostr(wait)

			reply = reply + "\n\n<b>💬 Для установки введите</b> <code>.lcooldown type time</code>"
			await utils.answer(message, reply)
			return
		args = text.rsplit(" ", 1)
		mode = args[0]
		if len(args) != 2 or not mode in COOLDOWNS:
			await utils.answer(message, "<b>Неверный формат! .lcooldown type seconds</b>")
			return
		time = args[1]
		try:
			cd_time = int(time)
		except ValueError:
			await utils.answer(message, "<b>Ошибка, укажите время в секундах (без суффикса \"s\", просто число вторым аргументом)</b>")
			return
		if cd_time < 0:
			await utils.answer(message, "<b>Время должно быть равно 0 или больше</b>")
			return
		self.set_cooldown(mode, cd_time)
		await utils.answer(message, "<b>Есть!</b>")

	async def lsettingscmd(self, message):
		"""Настройки LesyaBot"""
		text = utils.get_args_raw(message)
		reply = ""
		if not text or not settings_tip.get(text):
			reply = "⚙️ <b>Доступные настройки:</b>"
			for cmd in settings_tip:
				enabled = self._settings.get(cmd) and "♿️" or ""
				description = settings_tip[cmd]
				reply = reply + "\n" + enabled + description + " - <code>" + cmd + "</code>"

			reply = reply + "\n\n" + "<b>♿ - Индикатор, что функция активна\nФункции с припиской</b>\n\n<b>Для включения/отвключения введите</b> <code>.lsettings var_name</code>"
		else:
			description = settings_tip.get(text)
			should = not self._settings.get(text)
			reply = description + " - <b>" + (should and "Включено" or "Отключено") + "</b>"
			self.settings_set(text, should)

		await utils.answer(message, reply)

	async def lpetscmd(self, message):
		"""Список питомцев. Сортировка по урону"""
		if not self.profile:
			await utils.answer(message, "Нету инфы о профиле")
			return
		self.profile.additional_info["pets_waiting"] = message
		self.profile.additional_info["pets_parsed"] = []
		await utils.answer(message, "Жду инфу от бота")
		await self.send_bot("Питомцы")

	async def lesyainfocmd(self, message):
		"""Инфофрмация о скрипте и инфе, какую собрал"""
		now = time()
		if baninfo := self._temp_db["banned"]:  # pylint: disable=protected-access
			await utils.answer(message,
							   "<b>[LesyaAuto]</b> Я в бане, осталось сидеть: %s" %
							   str(timedelta(seconds=floor(baninfo.release_time - time()))))
			return
		if not self.profile:
			await utils.answer(message, "Нету инфы о профиле")
			return

		text = "<b>Инфа в Бот Леся</b>" + "\n" \
			"☺️ Мой айди - <code>" + str(self.profile.uid) + "</code>\n" \
			"🤔 Статус: " + str(STATUS_UNMAP.get(self.profile.status) or self.profile.status) + "\n" \
			"👨‍👦‍👦 Клан: " + (self.profile.clan and "Есть" or "Нету") + "\n" \
			"💳 Деньги: " + "{:0,}".format(self.profile.balance) + "$" + "\n" \
			"🅱️ Биткоины: " + "{:0,}".format(self.profile.bitcoin_balance) + "BTC" + "\n" \
			"💻 Фермы: " + "{:0,}".format(self.profile.btcminer.count) + "\n\n" \
			"<b>Инфа по таймингам</b>" + "\n" \
			"💰 Бонус: " + timetostr(self._times.get("bonus") - now) + "\n"
		if self.profile.status == LesyaAccountStatus.VIP or self.profile.status == LesyaAccountStatus.Premium or self.profile.status == LesyaAccountStatus.Deluxe:
			text = text + "💵 Вип бонус: " + timetostr(self._times.get("vip_bonus") - now) + "\n"
		if self.profile.status == LesyaAccountStatus.Premium or self.profile.status == LesyaAccountStatus.Deluxe:
			text = text + "💶 Премиум бонус: " + timetostr(self._times.get("premium_bonus") - now) + "\n"
			text = text + "🤑 Премиум валюта: " + timetostr(self._times.get("premium_money") - now) + "\n"
		if self.profile.status == LesyaAccountStatus.Deluxe:
			text = text + "💷 Делюкс бонус: " + timetostr(self._times.get("deluxe_bonus") - now) + "\n"
			text = text + "🏦 Выдача денег: " + timetostr(self._times.get("deluxe_bonus") - now) + "\n"
		text = text + "🛠️ Работа: " + timetostr(self._times.get("work") - now) + "\n"
		battle = self._times.get("fight") - now
		if battle < 10**50:
			text = text + "🤺 Бои: " + timetostr(battle) + "\n"
		if self._settings.get("progress"):
			text = text = text + "🅱️ Сбор биткоинов: " + timetostr(self._times.get("progress_collect") - now) + "\n"
		if self._settings.get("pet_stimulator"):
			text = text + "💊 Стимуляторы: " + timetostr(self._times.get("pet_stimulator") - now) + "\n"
		if self._settings.get("pet_food"):
			text = text + "🥫 Корм: " + \
				timetostr(self._times.get("pet_food") - now) + "\n"
		if self._settings.get("pet_cases"):
			text = text + "💼 Множитель кейсов: " + timetostr(self._times.get("pet_cases") - now) + "\n"
		if self._settings.get("opencase"):
			text = text + "🧳 Открытие кейса: " + timetostr(self._times.get("opencase") - now) + "\n"
		if self._settings.get("clan_war"):
			text = text + "⚔️ Клановая война: " + timetostr(self._times.get("clan_war") - now) + "\n"
			if self._times.get("clan_war_upgrade") != 0:
				text = text + "🦽 Апгрейд питомцев: " + timetostr(self._times.get("clan_war_upgrade") - now) + "\n"
		if self._settings.get("clan_heist"):
			text = text + "🔫 Ограбление: " + timetostr(self._times.get("clan_heist") - now) + "\n"
		if self._settings.get("humanizer"):
			text = text + "🗣️ Хуманайзер: " + timetostr(self._times.get("humanizer") - now) + "\n"
		hour = int(strftime("%H"))
		for sleep_name in self.sleep_hours:
			hours = self.sleep_hours.get(sleep_name)
			if hour >= hours[0] and hour <= hours[1]:
				text = text + "😴 <b>Сейчас сплю ( " + sleep_name + " ). Ещё " + str(hours[1] - hour) + "ч</b>"
		if self._times.get("bot_lag") != 0:
			text = text + "🚨 <b>Бот лагает. Игнор ещё</b> " + timetostr(self._times.get("bot_lag") - now)
		await utils.answer(message, text)

	# таймер
	async def sw_timer0(self):
		while True:  # да простит меня Гвидо

			# модуль выгрузили. зачем работать если не заплатят, правильно?
			if not self in self.allmodules.modules:
				logger.fatal("AutoLesya unloaded. Breaking timer.")
				break

			# если в бане сидим, зачем попусту тратить процессорное время на проверку бана,
			# лучше просто поспим определённое время
			if self._temp_db["banned"]:
				await asyncio.sleep(self._temp_db["banned"].release_time - time() + 600)
				self._temp_db["banned"] = None

			# блокируем мутекс, чтобы бот не начал решать капчу во время того как таймер
			# обрабатывает события. Если в это время мутекс капчи уже занят, таймер терпеливо
			# посидит, звёзды посчитает
			if True:#async with self._locks["captcha"]:

				now = time()

				if self._times.get("bot_lag") > now:
					await asyncio.sleep(10)
					continue

				if self._temp_db.get("captcha") != None:
					await self.brute_captcha()
					await asyncio.sleep(15)
					continue

				logger.info("Working")
				# попросим профиль
				if not self.profile:
					logger.info("Requesting profile")
					await asyncio.sleep(5)
					asyncio.ensure_future(self.send_bot("Профиль"))
					#await self._locks["profile_get"]
					await asyncio.sleep(5)
					continue

				if self._settings.get("clan_war"):
					upgrade = self._times.get("clan_war_upgrade")
					if now > upgrade and upgrade != 0:
						self._times["clan_war_upgrade"] = now + 300
						await self.send_bot("Кв")
					elif now > self._times.get("clan_war"):
						self._times["clan_war"] = now + 600
						await self.send_bot("КВ")

				if self._settings.get("clan_heist") and now > self._times.get("clan_heist"):
					self._times["clan_heist"] = now + 600
					await self.send_bot("Ограбление")

				sleep = False  # Должен ли бот сейчас "спать"
				hour = int(strftime("%H"))
				for sleep_name in self.sleep_hours:
					hours = self.sleep_hours.get(sleep_name)
					if hour >= hours[0] and hour <= hours[1]:
						sleep = True

				if sleep:
					await asyncio.sleep(60)
					continue

				# работа не волк, но попу не моет
				if self._settings.get("work") and now > self._times.get("work"):
					logger.info("Time to Work")
					self._times["work"] =  now + 30
					await self.send_bot("Работать")

				# Бонусы тоже не волк, и тоже попу не моют
				if self._settings.get("bonus"):
					if now > self._times.get("bonus"):
						logger.info("Getting bonus")
						self._times["bonus"] = now + 600
						await self.send_bot("Бонус")
						await asyncio.sleep(5)
					profile_status = self.profile.status

					if (profile_status == LesyaAccountStatus.VIP or profile_status == LesyaAccountStatus.Premium or profile_status == LesyaAccountStatus.Deluxe) and now > self._times.get("vip_bonus"):
						logger.info("Getting vip bonus")
						self._times["vip_bonus"] = now + 600
						await self.send_bot("Вип бонус")
						await asyncio.sleep(5)

					if (profile_status == LesyaAccountStatus.Premium or profile_status == LesyaAccountStatus.Deluxe) and now > self._times.get("premium_bonus"):
						logger.info("Getting premium bonus")
						self._times["premium_bonus"] = now + 600
						await self.send_bot("Премиум бонус")
						await asyncio.sleep(5)

					if (profile_status == LesyaAccountStatus.Premium or profile_status == LesyaAccountStatus.Deluxe) and now > self._times.get("premium_money"):
						logger.info("Getting premium money")
						self._times["premium_money"] = now + 600
						await self.send_bot("Премиум валюта")
						await asyncio.sleep(5)

					if profile_status == LesyaAccountStatus.Deluxe and now > self._times.get("deluxe_bonus"):
						logger.info("Getting deluxe bonus")
						self._times["deluxe_bonus"] = now + 600
						await self.send_bot("Делюкс бонус")
						await asyncio.sleep(5)

					if profile_status == LesyaAccountStatus.Deluxe and now > self._times.get("deluxe_give"):
						logger.info("Getting deluxe money")
						self._times["deluxe_give"] = now + 600
						await self.send_bot("Гив " + str(self.profile.uid) + " 5кккк")
						await asyncio.sleep(5)

				# Блять, да и питомцы не волк
				if self._settings.get("pet_stimulator") and now > self._times.get("pet_stimulator"):
					self.set_time("pet_stimulator", now + 60 * 60 * 24)
					self.get_bitcoins()
					await self.send_bot("Зоотовары 6")

				if self._settings.get("pet_food") and now > self._times.get("pet_food"):
					self.set_time("pet_food", now + 60 * 60 * 24)
					self.get_bitcoins()
					await self.send_bot("Зоотовары 7")

				if self._settings.get("pet_cases") and now > self._times.get("pet_cases"):
					self.set_time("pet_cases", now + 60 * 60 * 24)
					self.get_bitcoins()
					await self.send_bot("Зоотовары 8")

				# Автобой
				if self._settings.get("fight") and now > self._times.get("fight") \
						and not self.profile.additional_info.get("no_pets"):
					self._times["fight" ] = now + 30
					logger.info("Starting new battle")
					await self.send_bot("Бой")

				# Автооткрытие кейсов
				if self._settings.get("opencase") and now > self._times.get("opencase") \
						and self.profile.additional_info.get("opencase"):
					case = self.profile.additional_info.get("opencase")
					self.set_time("opencase", now + gen_time("opencase"))
					if self.profile.additional_info.get("opencase_limit"):
						await self.send_bot("Кейс открыть " + str(case))
					else:
						await self.send_bot("Кейс открыть " + str(case) + " 10")

				if self._settings.get("humanizer") and now > self._times.get("humanizer"):
					self.set_time("humanizer", now + gen_time("humanizer"))
					await self.send_phrase()

				# Если есть апгрейд города - метод поднятия денег и вывода в топ и себя и клана
				if self._settings.get("auto_trade") and now > self._times.get("trade") and not sleep:
					self.set_time("trade", now + 5)
					side = "вверх" if randint(0, 1) else "вниз"
					await self.send_bot("Трейд " + side + " все")

				if self._settings.get("auto_cup") and now > self._times.get("cup") and not sleep:
					self.set_time("cup", now + 5)
					side = str(randint(1, 3))
					await self.send_bot("Стаканчик " + side + " все")

				if self._settings.get("auto_casino") and now > self._times.get("casino") and not sleep:
					self.set_time("casino", now + 5)
					await self.send_bot("Казино все")

				if self._settings.get("progress") and now > self._times.get("progress") and not sleep:
					self.set_time("progress", now + 5)
					if self.profile.btcminer.count < 1000 and self.profile.balance > BITCOIN_FARM_PRICE:
						amount = floor(self.profile.balance / BITCOIN_FARM_PRICE)
						await self.send_bot("Фермы 3 " + str(amount))

					parsed_petshop = self.profile.additional_info.get("parsed_petshop")
					if parsed_petshop is None:
						await self.send_bot("Зоотовары")
					elif parsed_petshop:
						for num in parsed_petshop:
							price = parsed_petshop.get(num)
							if self.profile.bitcoin_balance.get("bitcoin", 0) > price:
								await self.send_bot("Зоотовары " + str(num))

				if self._settings.get("progress") and now > self._times.get("progress_collect") and not sleep:
					self.set_time("progress_collect", now + 10800)
					if self.profile.btcminer.count > 0:
						await self.send_bot("Ферма")

			await asyncio.sleep(5)  # на боковую

	async def send_phrase(self):
		phrase = gen_phrase()
		await self.send_bot(phrase)

	async def watcher(self, message):
		if not isinstance(message, types.Message):  # не обрабатываем несообщения
			return
		if not message.text:  # не обрабатываем сообщения без текста
			return
		if message.from_id == self._me_id:  # не обрабатываем сообщения от себя
			return
		chat_id = utils.get_chat_id(message)
		from_bot = chat_id == LESYA_CHATID
		if chat_id in [LESYA_CHATID, LOGCHANNEL_CHATID]:  # обрабатываем сообщения от бота и от чата
			await self.process_message(message, from_bot)

	async def send_bot(self, text):
		global LESYA_LAG
		LESYA_LAG += 1
		if LESYA_LAG >= 10:
			LESYA_LAG = 0
			self._times["bot_lag"] = time() + 1800
		return await self._client.send_message(LESYA_CHATID, text)

	async def send_group(self, text):
		return await self._client.send_message(LOGCHANNEL_CHATID, text)

	def set_time(self, time_name, entry):
		self._times[time_name] = entry
		#self.db_set("time_" + time_name, entry)

	def db_set(self, key, value):
		self._db.set(__name__, key, value)

	def db_get(self, key, default=None):
		return self._db.get(__name__, key, default)

	def settings_set(self, name, var):
		self._settings[name] = var
		self.db_set(name, var)
