#!/usr/bin/env python3
"""
Инструмент преобразования учебного конфигурационного языка в JSON.
"""

import sys
import json
import argparse
import re
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import os


class TokenType(Enum):
    """Типы токенов языка."""
    COMMENT_SINGLE = "%"
    COMMENT_MULTI_START = "<#"
    COMMENT_MULTI_END = "#>"
    DEFINE = "define"
    CONST_EXPR_START = ".{"
    CONST_EXPR_END = "}."
    ARRAY_START = "["
    ARRAY_END = "]"
    STRING = "@\""
    NUMBER = "NUMBER"
    HEX_NUMBER = "HEX_NUMBER"
    NAME = "NAME"
    OPERATOR = "OPERATOR"
    FUNCTION = "FUNCTION"
    COMMA = ","
    EOF = "EOF"


class Token:
    """Токен языка."""

    def __init__(self, type: TokenType, value: str = "", line: int = 0, col: int = 0):
        self.type = type
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type}, '{self.value}', {self.line}:{self.col})"


class Lexer:
    """Лексический анализатор."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.current_char = self.text[0] if self.text else None

    def error(self, message: str):
        """Вывод ошибки."""
        raise SyntaxError(f"Lexer error at {self.line}:{self.col}: {message}")

    def advance(self):
        """Переход к следующему символу."""
        if self.current_char == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1

        self.pos += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None

    def peek(self, n: int = 1) -> Optional[str]:
        """Просмотр вперед на n символов."""
        pos = self.pos + n
        if pos < len(self.text):
            return self.text[pos]
        return None

    def skip_whitespace(self):
        """Пропуск пробельных символов."""
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def skip_single_comment(self):
        """Пропуск однострочного комментария."""
        while self.current_char is not None and self.current_char != '\n':
            self.advance()
        if self.current_char == '\n':
            self.advance()

    def skip_multi_comment(self):
        """Пропуск многострочного комментария."""
        self.advance()  # Пропускаем '<'
        self.advance()  # Пропускаем '#'

        while self.current_char is not None:
            if self.current_char == '#' and self.peek() == '>':
                self.advance()  # Пропускаем '#'
                self.advance()  # Пропускаем '>'
                break
            self.advance()
        else:
            self.error("Unclosed multi-line comment")

    def read_name(self) -> str:
        """Чтение имени."""
        result = ""
        while (self.current_char is not None and
               (self.current_char.isalnum() or self.current_char == '_')):
            result += self.current_char
            self.advance()
        return result

    def read_number(self) -> str:
        """Чтение числа."""
        result = ""

        # Проверка на шестнадцатеричное число
        if self.current_char == '0' and self.peek() in 'xX':
            result += self.current_char
            self.advance()
            result += self.current_char
            self.advance()

            while (self.current_char is not None and
                   ((self.current_char >= '0' and self.current_char <= '9') or
                    (self.current_char >= 'a' and self.current_char <= 'f') or
                    (self.current_char >= 'A' and self.current_char <= 'F'))):
                result += self.current_char
                self.advance()
            return result

        # Чтение десятичного числа
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()

        return result

    def read_string(self) -> str:
        """Чтение строки."""
        result = ""
        self.advance()  # Пропускаем '@'
        self.advance()  # Пропускаем '"'

        while self.current_char is not None:
            if self.current_char == '"' and self.peek() != '"':
                self.advance()  # Пропускаем закрывающую кавычку
                break
            elif self.current_char == '"' and self.peek() == '"':
                result += self.current_char
                self.advance()
                self.advance()
            else:
                result += self.current_char
                self.advance()
        else:
            self.error("Unclosed string")

        return result

    def get_next_token(self) -> Token:
        """Получение следующего токена."""
        while self.current_char is not None:
            # Пропуск пробелов
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # Однострочный комментарий
            if self.current_char == '%':
                start_line = self.line
                start_col = self.col
                self.advance()
                self.skip_single_comment()
                continue

            # Многострочный комментарий
            if self.current_char == '<' and self.peek() == '#':
                start_line = self.line
                start_col = self.col
                self.skip_multi_comment()
                continue

            # Начало константного выражения
            if self.current_char == '.' and self.peek() == '{':
                start_line = self.line
                start_col = self.col
                self.advance()
                self.advance()
                return Token(TokenType.CONST_EXPR_START, ".{", start_line, start_col)

            # Конец константного выражения
            if self.current_char == '}' and self.peek() == '.':
                start_line = self.line
                start_col = self.col
                self.advance()
                self.advance()
                return Token(TokenType.CONST_EXPR_END, "}.", start_line, start_col)

            # Строка
            if self.current_char == '@' and self.peek() == '"':
                start_line = self.line
                start_col = self.col
                value = self.read_string()
                return Token(TokenType.STRING, value, start_line, start_col)

            # Определение константы
            if self.current_char == '(':
                start_line = self.line
                start_col = self.col
                self.advance()

                # Проверяем, является ли это определением константы
                name = self.read_name()
                if name == "define":
                    return Token(TokenType.DEFINE, "define", start_line, start_col)
                else:
                    self.error(f"Unexpected token after '(': {name}")

            # Массивы и другие символы
            if self.current_char == '[':
                start_line = self.line
                start_col = self.col
                self.advance()
                return Token(TokenType.ARRAY_START, "[", start_line, start_col)

            if self.current_char == ']':
                start_line = self.line
                start_col = self.col
                self.advance()
                return Token(TokenType.ARRAY_END, "]", start_line, start_col)

            if self.current_char == ',':
                start_line = self.line
                start_col = self.col
                self.advance()
                return Token(TokenType.COMMA, ",", start_line, start_col)

            # Числа
            if self.current_char.isdigit():
                start_line = self.line
                start_col = self.col
                number = self.read_number()
                if number.startswith("0x") or number.startswith("0X"):
                    return Token(TokenType.HEX_NUMBER, number, start_line, start_col)
                return Token(TokenType.NUMBER, number, start_line, start_col)

            # Имена и операторы
            if self.current_char.isalpha() and self.current_char.islower():
                start_line = self.line
                start_col = self.col
                name = self.read_name()

                # Проверка на операторы и функции
                if name == "abs":
                    return Token(TokenType.FUNCTION, name, start_line, start_col)
                elif name in ["+", "-", "*", "/"]:
                    return Token(TokenType.OPERATOR, name, start_line, start_col)
                else:
                    return Token(TokenType.NAME, name, start_line, start_col)

            # Операторы
            if self.current_char in "+-*/":
                start_line = self.line
                start_col = self.col
                op = self.current_char
                self.advance()
                return Token(TokenType.OPERATOR, op, start_line, start_col)

            self.error(f"Unexpected character: {self.current_char}")

        return Token(TokenType.EOF, "", self.line, self.col)


class Parser:
    """Синтаксический анализатор."""

    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()
        self.constants: Dict[str, Any] = {}

    def error(self, message: str):
        """Вывод ошибки."""
        raise SyntaxError(f"Parser error at {self.current_token.line}:{self.current_token.col}: {message}")

    def eat(self, token_type: TokenType):
        """Проверка и переход к следующему токену."""
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error(f"Expected {token_type}, got {self.current_token.type}")

    def parse_value(self) -> Any:
        """Парсинг значения."""
        token = self.current_token

        if token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            return int(token.value)

        elif token.type == TokenType.HEX_NUMBER:
            self.eat(TokenType.HEX_NUMBER)
            return int(token.value, 16)

        elif token.type == TokenType.STRING:
            self.eat(TokenType.STRING)
            return token.value

        elif token.type == TokenType.ARRAY_START:
            return self.parse_array()

        elif token.type == TokenType.NAME:
            name = token.value
            self.eat(TokenType.NAME)

            # Проверка на константное выражение
            if self.current_token.type == TokenType.CONST_EXPR_START:
                return self.parse_const_expression(name)

            # Проверка, является ли имя определенной константой
            if name in self.constants:
                return self.constants[name]

            # Если это не константа, это может быть ключом в будущем словаре
            return name

        elif token.type == TokenType.CONST_EXPR_START:
            self.eat(TokenType.CONST_EXPR_START)
            result = self.parse_const_expression_body()
            self.eat(TokenType.CONST_EXPR_END)
            return result

        else:
            self.error(f"Unexpected token in value: {token.type}")

    def parse_array(self) -> List:
        """Парсинг массива."""
        self.eat(TokenType.ARRAY_START)
        values = []

        if self.current_token.type != TokenType.ARRAY_END:
            values.append(self.parse_value())

            while self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                values.append(self.parse_value())

        self.eat(TokenType.ARRAY_END)
        return values

    def parse_const_expression_body(self) -> Any:
        """Парсинг тела константного выражения (постфиксная форма)."""
        stack = []

        while self.current_token.type not in [TokenType.CONST_EXPR_END, TokenType.EOF]:
            token = self.current_token

            if token.type == TokenType.NUMBER:
                self.eat(TokenType.NUMBER)
                stack.append(int(token.value))

            elif token.type == TokenType.HEX_NUMBER:
                self.eat(TokenType.HEX_NUMBER)
                stack.append(int(token.value, 16))

            elif token.type == TokenType.NAME:
                name = token.value
                self.eat(TokenType.NAME)

                # Проверка на константу
                if name in self.constants:
                    stack.append(self.constants[name])
                else:
                    # Предполагаем, что это операнд для операций
                    stack.append(name)

            elif token.type == TokenType.OPERATOR:
                op = token.value
                self.eat(TokenType.OPERATOR)

                if len(stack) < 2:
                    self.error(f"Not enough operands for operator {op}")

                b = stack.pop()
                a = stack.pop()

                if op == '+':
                    if isinstance(a, str) or isinstance(b, str):
                        stack.append(str(a) + str(b))
                    else:
                        stack.append(a + b)
                elif op == '-':
                    stack.append(a - b)
                elif op == '*':
                    stack.append(a * b)
                elif op == '/':
                    if b == 0:
                        self.error("Division by zero")
                    stack.append(a // b)  # Целочисленное деление
                else:
                    self.error(f"Unknown operator: {op}")

            elif token.type == TokenType.FUNCTION:
                func = token.value
                self.eat(TokenType.FUNCTION)

                if func == "abs":
                    if len(stack) < 1:
                        self.error(f"Not enough arguments for function {func}")

                    arg = stack.pop()
                    if isinstance(arg, int):
                        stack.append(abs(arg))
                    else:
                        self.error(f"Function {func} expects numeric argument")

                else:
                    self.error(f"Unknown function: {func}")

            else:
                self.error(f"Unexpected token in constant expression: {token.type}")

        if len(stack) != 1:
            self.error("Invalid constant expression")

        return stack[0]

    def parse_const_expression(self, first_arg: Optional[str] = None) -> Any:
        """Парсинг константного выражения."""
        self.eat(TokenType.CONST_EXPR_START)

        # Если есть первый аргумент, добавляем его в стек
        if first_arg is not None:
            if first_arg in self.constants:
                stack = [self.constants[first_arg]]
            else:
                try:
                    stack = [int(first_arg)]
                except ValueError:
                    self.error(f"Invalid constant expression argument: {first_arg}")
        else:
            stack = []

        # Парсим остальное выражение
        while self.current_token.type != TokenType.CONST_EXPR_END:
            token = self.current_token

            if token.type == TokenType.NUMBER:
                self.eat(TokenType.NUMBER)
                stack.append(int(token.value))

            elif token.type == TokenType.HEX_NUMBER:
                self.eat(TokenType.HEX_NUMBER)
                stack.append(int(token.value, 16))

            elif token.type == TokenType.NAME:
                name = token.value
                self.eat(TokenType.NAME)

                if name in self.constants:
                    stack.append(self.constants[name])
                else:
                    # Пробуем интерпретировать как число
                    try:
                        stack.append(int(name))
                    except ValueError:
                        self.error(f"Unknown constant: {name}")

            elif token.type == TokenType.OPERATOR:
                op = token.value
                self.eat(TokenType.OPERATOR)

                if len(stack) < 2:
                    self.error(f"Not enough operands for operator {op}")

                b = stack.pop()
                a = stack.pop()

                if op == '+':
                    stack.append(a + b)
                elif op == '-':
                    stack.append(a - b)
                elif op == '*':
                    stack.append(a * b)
                elif op == '/':
                    if b == 0:
                        self.error("Division by zero")
                    stack.append(a // b)
                else:
                    self.error(f"Unknown operator: {op}")

            elif token.type == TokenType.FUNCTION:
                func = token.value
                self.eat(TokenType.FUNCTION)

                if func == "abs":
                    if len(stack) < 1:
                        self.error(f"Not enough arguments for function {func}")

                    arg = stack.pop()
                    stack.append(abs(arg))
                else:
                    self.error(f"Unknown function: {func}")

            else:
                self.error(f"Unexpected token in constant expression: {token.type}")

        self.eat(TokenType.CONST_EXPR_END)

        if len(stack) != 1:
            self.error("Invalid constant expression")

        return stack[0]

    def parse_define(self) -> None:
        """Парсинг определения константы."""
        self.eat(TokenType.DEFINE)

        # Парсим имя
        if self.current_token.type != TokenType.NAME:
            self.error("Expected name after define")
        name = self.current_token.value
        self.eat(TokenType.NAME)

        # Парсим значение
        value = self.parse_value()

        # Сохраняем константу
        self.constants[name] = value

    def parse_config(self) -> Dict:
        """Парсинг всей конфигурации."""
        config = {}

        while self.current_token.type != TokenType.EOF:
            # Пропускаем комментарии (они уже обработаны лексером)

            if self.current_token.type == TokenType.DEFINE:
                self.parse_define()

            elif self.current_token.type == TokenType.NAME:
                # Парсим пару ключ-значение
                key = self.current_token.value
                self.eat(TokenType.NAME)

                # Значение может быть константным выражением
                if self.current_token.type == TokenType.CONST_EXPR_START:
                    value = self.parse_const_expression()
                else:
                    # Или обычным значением
                    value = self.parse_value()

                config[key] = value

            else:
                self.error(f"Unexpected token: {self.current_token.type}")

        return config


def convert_to_json(input_text: str) -> Dict:
    """Преобразование входного текста в JSON-совместимый словарь."""
    lexer = Lexer(input_text)
    parser = Parser(lexer)

    try:
        config = parser.parse_config()
        return config
    except SyntaxError as e:
        print(f"Syntax error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Основная функция программы."""
    parser = argparse.ArgumentParser(
        description="Преобразование учебного конфигурационного языка в JSON"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Путь к выходному JSON файлу"
    )

    args = parser.parse_args()

    # Чтение из стандартного ввода
    input_text = sys.stdin.read()

    # Преобразование
    config = convert_to_json(input_text)

    # Запись в файл
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"Конфигурация успешно сохранена в {args.output}")
    except IOError as e:
        print(f"Ошибка записи файла: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()