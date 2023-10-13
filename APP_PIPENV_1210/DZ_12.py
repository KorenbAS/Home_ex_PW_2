import os
import collections
import re
from datetime import datetime as dt
import pickle

# назва файлу для збереження та читання
FILENAME = 'backup.bin'

# списки можливих команд
EXIT_CMD = ['good bye', 'close', 'exit']
NO_ARGS_CMD = ['hello', 'show all']
WITH_ARGS_CMD = ['add', 'change', 'phone', 'del', 'add_birthday', 'find']
EXIT_ANSWER = 'Good bye!' 

# патерни регулярних виразів
PHONE_PATTERN = r'^\d{3}-\d{3}-\d{2}-\d{2}$'
BD_DATE_PATTERN = r'^(0[1-9]|[12]\d|3[01])\.(0[1-9]|1[0-2])\.\d{4}$'

# формат дати
DATE_FORTMAT = "%d.%m.%Y"

# повідомлення запрошення
INVITATION = """ 
------------------------------------------------------------------------------------------------------------------------------------------------
|                                                PHONE BOOK BOT WELCOMES YOU!                                                                  |
------------------------------------------------------------------------------------------------------------------------------------------------
|    МОЖЛИВІ КОМАНДИ:                                                                                                                          |
|    o	"hello"                                                                                                                                |
|    o	"add ..."             По даній команді бот зберігає в книзі нове ім'я та нормер телефону.                                              |
|                             Замість ... користувач вводить ім'я та номер телефону , обов'язково через пробіл.                                |
|                             Номер телефону має бути в форматі (***-***-**-**)                                                                |
|    o	"add_birthday ..."    По даній команді бот зберігає в книзі для існуючого контакту день народження.                                    |
|                             Замість ... користувач вводить ім'я і дату народження , обов'язково через пробіл.                                |
|    o	"change ..."          По даній команді бот зберігає в памяті новий номер телефону для існуючого контакту.                              |
|                             Дата народження має бути в форматі (дд.мм.РРРР)                                                                  |
|                             Замість ... користувач вводить ім'я , старий і новий номер телефону, обов'язково через пробіл.                   |
|                             Номер телефону має бути в форматі (***-***-**-**)                                                                |
|    o	"phone ...."          По даній команді бот виводить на консоль всю доступну інформацію для указанного контакту.                        |
|                             Замість ... користувач вводить ім'я контакту, інформацію котрого  хоче отримати.                                 |
|    o	"del ..."             По даній команді бот видаляє вказаний номер телефону для вказаного імені.                                        |
|                             Замість ... користувач вводить ім'я контакту і номер котрий потрібно видалити, обов'язково через пробіл.         |
|    o	"show all"            По даній команді бот виводить всі збережені контакти з номерами телефонів на консоль.                            |
|                                                                                                                                              |
|    o  "find ..."            По даній команді бот проводить пошук заданого значення у книзі.                                                  |
|                             Замість ... користувач вводить або частину імені або частину номеру телефону                                     |
|    o	"good bye",                                                                                                                            | 
|    o  "close",                                                                                                                               |
|    o  "exit"                По будь-якій з даних команд бот завершує свою роботу.                                                            |
------------------------------------------------------------------------------------------------------------------------------------------------"""


######################################################################################
#                                  Реалізація класів                                 #
######################################################################################
# унаслідуваний клас виключення
class NotFoundError(Exception): ...


class Field:
    """ Батьківський клас "Поле" -  містить в собі якусь інформацію """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __eq__(self, __value: object) -> bool:
        """ Для порівняння на рівність двох екземплярів даного класу """
        # порівнюються значення поля value
        return self.value == __value.value if isinstance(__value, Field) else False

    def __contains__(self, string):
        """ Для оператора in """
        return string in self.value.replace('-', '').lower()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, __value):
        self._value = __value


class Name(Field):
    """ Поле ім'я """

    def __init__(self, value):
        super().__init__(value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, __value):
        self._value = __value


class Phone(Field):
    """ Поле номер телефону """

    def __init__(self, value=None):
        super().__init__(value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, __value):
        if re.match(PHONE_PATTERN, __value):
            self._value = __value
        else:
            raise ValueError


class Birthday(Field):
    """ Поле день народження """

    def __init__(self, value=None):
        super().__init__(value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, __value):
        if __value is None:
            self._value = None
        elif isinstance(__value, str) and re.match(BD_DATE_PATTERN, __value):
            self._value = __value
        else:
            raise ValueError


class Record:
    """ Запис з книги контактів. Містить в собі поля """

    def __init__(self, name_value, phone_value=None, birth_day=None):
        # атрибут ім'я
        self.name = Name(name_value)
        # атрибут список телефонів
        self.phones = []
        # додаємо телефон в список
        self.phones.append(Phone(phone_value))
        # додаємо день народження в поле
        self.birth_day = Birthday(birth_day)

    def __str__(self) -> str:
        """ Рядкове представлення екземпляру класу """
        # список екземплярів в список рядків
        str_value = ''
        phones = '\n'
        for index, item in enumerate(self.phones):
            phones += f'\t[{index + 1}] {str(item)}\n'

        # пакуємо в загальний рядок
        str_value += f'Name : {self.name}\n'
        # випадок : поле день народження існує
        if self.birth_day.value is not None:
            str_value += f'Birthday : {self.birth_day}\n'
            str_value += f'Days to birthday : {self.days_to_birthday()}\n'
        str_value += f'Phone numbers : {phones}'
        # рядок лінія підкреслення
        str_value += '-' * 80
        # повертаємо рядок
        return str_value

    def __contains__(self, string):
        """ Для оператора in """

        contains = string in self.name
        # перебираємо всі номери телефонів
        for phone in self.phones:
            # випадок : шуканий рядок є в номері
            if string in phone:
                # знайдено - правда
                contains = True
                break
        # повертаємо результат
        return contains

    def add_phone(self, value):
        """ Додає телефон в список """
        new_phone = Phone(value)
        # випадок : чи телефон існує в списку
        if new_phone not in self.phones:
            self.phones.append(new_phone)

    def del_phone(self, value):
        """ Видаляє телефон з списку """
        # випадок : такого номеру не має в базі
        try:
            # Видаляємо номер
            self.phones.remove(Phone(value))
        except ValueError:
            raise ValueError

    def update_phone(self, old_value, new_value):
        """ Оновлює телефон в списку """
        # знаходимо індекс даного номеру в списку
        # якщо індекс не буде знайдено то буде кинуте виключення input_error його відловить
        idx = self.phones.index(Phone(old_value))
        # заміняємо старе значення новим
        self.phones[idx] = Phone(new_value)

    def set_birthday(self, birthday_str):
        """ Додає або оновлює інформацію про дату народжнення """
        self.birth_day = Birthday(birthday_str)

    def days_to_birthday(self):
        """ Обраховує кількість днів що залишилось до наступного дня народжнення """
        # випадок : поле не заповнене
        if self.birth_day is None:
            return None
        else:
            # обраховуємо різницю між датами
            today = dt.today().replace(hour=0, minute=0, second=0, microsecond=0)
            bday = dt.strptime(self.birth_day.value,
                               DATE_FORTMAT).replace(year=today.year)
            diff = (bday - today).days
            return diff if diff >= 0 else 365 + diff


class AddressBook(collections.UserDict):
    """ Книга контактів. Містить в собі записи Record"""

    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.load()

    def backup(self):
        """ Зберігає поточний стан книги у файл """
        with open(self.filename, "wb") as file:
            pickle.dump(self, file)

    def load(self):
        """ Відновлює поточний стан книги з файлу """
        if os.path.exists(self.filename):
            with open(self.filename, "rb") as file:
                loaded_obj = pickle.load(file)
            for k, v in loaded_obj.items():
                self[k] = v

    def add_record(self, name_value, phone_value=None):
        """ Додає новий запис в книгу """
        # випадок : якщо ім'я є в базі
        if name_value in self:
            # додаємо новий номер до запису
            self[name_value].add_phone(phone_value)
        else:
            # додаємо новий запис
            self[name_value] = Record(name_value, phone_value)
        # зберігаємо зміни у файл
        self.backup()

    def set_birthday(self, name_value, birthday_str):
        # випадок : ім'я існує в книзі
        if name_value in self:
            self[name_value].set_birthday(birthday_str)
        else:
            raise KeyError
        # зберігаємо зміни у файл
        self.backup()

    def is_empty(self):
        """ Перевіряє чи книга пуста """
        return len(self.items()) == 0

    def has_record(self, name_value):
        """ Перевіряє чи є дане ім'я в базі """
        return name_value in self

    def iterator(self, size):
        """ Повертає генератор що за одну ітерацію повертає size-шт записів """
        # лічильник доданих записів у список
        counter = 0
        # той самий список в який додаємо
        chunk = []
        # ітеруємось по словнику за порядковим індексом та записами
        for index, item in self.items():
            # випадок : якщо лічильник пустий
            if counter == 0:
                # то і список пустий
                chunk = []
            # додаємо запис у список
            chunk.append(item)
            # збільшуємо лічильник
            counter += 1

            # випадок : якщо в списку рівно скільки потрібно або кінець нашого словника
            if counter == size or index == len(self.items()) - 1:
                # обнуляємо лічильник
                counter = 0
                # та повертаємо список записів
                yield chunk

    def find(self, string: str):
        """ Проводить пошук по книзі та повертає список знайдених записів"""
        # всі літери маленькі
        string = string.lower()
        # видаляємо тире
        string = string.replace('-', '')

        result = []
        # проходимо всі записи
        for record in self.values():
            # випадок : рядок є в записі
            if string in record:
                # додаємо в результуючий список
                result.append(record)

        return result


###################################################################################
#                    Функції що відповідають за роботу бота                       #
###################################################################################

def input_error(func):
    """ Декоратор обробник помилок """

    def wrapper(*args, **kwargs):
        # намагаємось виконати хандлер
        try:
            result = func(*args, **kwargs)
        # відловлюємо помилки
        except SyntaxError:
            result = 'Команда некоректна! Спробуйте ще раз!'
        except KeyError:
            result = 'Ім`я не знайдено в книзі або введене не коректно!'
        except ValueError:
            result = 'Значення не коректне! Спробуйте ще раз!'
        except NotFoundError:
            result = 'Пошук не дав результатів!'
        return result

    return wrapper


def hello_handler(*args):
    """ Обробник команди hello """
    return 'Чим можу допомогти?'


def exit_handler(*args):
    """ Обробник команди на вихід """
    return EXIT_ANSWER


def show_all_handler(address_book: AddressBook):
    """ Обробник команди вивести всі записи """
    # випадок : словнки не пустий
    if not address_book.is_empty():
        # список рядків
        strings = []
        # обходимо книгу записів
        for value in address_book.values():
            # друкуємо ключ значення в рядок
            strings.append(f'{value}\n')
        # повертаємо всі рядки об'єднані в один великий загальний
        return ''.join(strings)
    else:
        return 'Книга пуста! Додайте нові записи!'


@input_error
def parser(expression):
    """ Розбиває рядок на команду та можливі аргументи """
    # розіб'ємо рядок по пробілам та зберемо заново всі частки
    expression = ' '.join(expression.split())
    # випадок : якщо рядок є командою з одного із списків
    if expression in EXIT_CMD or expression in NO_ARGS_CMD:
        # повертаємо вираз як команду і пустий список аргументів
        return expression, []
    # інашке розбиваємо по пробілу
    args = expression.split()
    # випадок : якщо кількість частин від 1 до 4включно
    if 1 < len(args) <= 4 and args[0] in WITH_ARGS_CMD:
        # повертаємо першу частину як команду а інщі частини як агрументи
        return args[0], args[1:]
    else:
        # інакше кидаємо виключення
        raise SyntaxError


@input_error
def add_handler(address_book: AddressBook, *args):
    """ Обробка додавання в книгу  """
    # випадок : якщо кількість агрументівн не коректна
    if len(args) != 2:
        raise SyntaxError

    name, tel = args
    # випадок : ім'я закоротке
    if len(name) < 2:
        raise KeyError
    # додамо в словник
    address_book.add_record(name, tel)
    return f'Запис [{name}] - [{tel}] додано до книги!'


@input_error
def phone_handler(address_book: AddressBook, *args):
    """ Відображення заданого запису по імені """
    # випадок : аргументів забагато або мало
    if len(args) != 1:
        # кидаємо виключення
        raise SyntaxError
    name = args[0]
    #  випадок : ім'я відсутне в книгі
    if not address_book.has_record(name):
        raise KeyError
    # повертаємо рядок
    return f'{address_book[name]}'


@input_error
def change_handler(address_book: AddressBook, *args):
    """ Обробка команди внесення змін по номеру """
    # випадок : аргументи не коректні
    if len(args) != 3:
        raise SyntaxError
    name = args[0]
    old_tel = args[1]
    new_tel = args[2]

    # випадок : ім'я відсутне в книзі
    if not address_book.has_record(name):
        raise KeyError

    # робимо зміни
    address_book[name].update_phone(old_tel, new_tel)
    return f'Контакт [{name}] успішно оновлено!'


@input_error
def del_handler(address_book: AddressBook, *args):
    """ Обробка команди внесення змін по номеру """
    # випадок : аргументи не коректні
    if len(args) != 2:
        raise SyntaxError
    name = args[0]
    tel = args[1]

    # випадок : ім'я відсутне в книзі
    if not address_book.has_record(name):
        raise KeyError

    # робимо зміни
    address_book[name].del_phone(tel)
    return f'Номер [{tel}] успішо видалений!'


@input_error
def add_birthday_handler(address_book: AddressBook, *args):
    """ Обробка додавання в книгу  """
    # випадок : якщо кількість агрументів не коректна
    if len(args) != 2:
        raise SyntaxError

    name, birhday_str = args

    # додамо в запис
    address_book.set_birthday(name, birhday_str)
    return f'Інформація про дату народження [{name}] успішно внесена!'


@input_error
def find_handler(address_book: AddressBook, *args):
    """ Пошук по книзі """
    # випадок : якщо кількість агрументів не коректна
    if len(args) != 1:
        raise SyntaxError

    # аргумент номер 1
    string = args[0]
    # отримуємо результат пошуку
    find_result = address_book.find(string)
    # випадок : якщо результат пустий
    if not find_result:
        raise NotFoundError

    str_result = ""
    # перебираємо всі знайдені записи
    for record in find_result:
        # складаємо в один рядок
        str_result += str(record) + '\n'

    # повертаємо результат
    return str_result


###############################################################################
#                                Головна функція                              #
###############################################################################


def main():
    # пуста книга словник
    address_book = AddressBook(FILENAME)
    # словник обробників команд
    # команда - назва функції
    handlers = {
        'hello': hello_handler,
        'good bye': exit_handler,
        'close': exit_handler,
        'exit': exit_handler,
        'show all': show_all_handler,
        'add': add_handler,
        'add_birthday': add_birthday_handler,
        'phone': phone_handler,
        'change': change_handler,
        'del': del_handler,
        'find': find_handler,
    }

    # безкінечнйи цикл запитів
    while True:
        # очистка консолі
        os.system('cls')
        # друк привітання запрошення
        print(INVITATION)
        # читаємо рядок команд
        # відразу переводимо в нижній регістр
        expression = input('->').lower().strip()
        os.system('cls')
        # якщо рядок пустий то все заново
        if len(expression) == 0:
            continue
        # отримуємо результат парсингу
        answer = parser(expression)
        # випадок : якщо результат не рядок з помилкою
        if not isinstance(answer, str):
            # розпаковуємо кортеж команд і аргументів
            cmd, args = answer
            # викликаємо хандлер по назві команди та передаємо в ного словник-книгу + агрументи
            answer = handlers[cmd](address_book, *args)
        # друкуємо отриманий результат
        print(answer)
        # пауза
        os.system('pause')

        # випадок : отримано команду на вихід
        if answer == EXIT_ANSWER:
            break


if __name__ == "__main__":
    main()
