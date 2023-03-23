# csa-lab3

- Павлова Полина `P33102`
- `asm | cisc | harv | hw | tick | struct | stream | mem | prob2`

## Язык программирования
### Синтаксис
``` ebnf
<label> ::= <identifier>：
<identifier> ::= <letter>|<identifier> <letter>
<letter> ::= A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V|W|X|Y|Z 
<statement> ::= <label> <instruction>|<instruction>
<instruction> ::= <opcode> <operand>|<opcode> <operand> <operand>
<opcode> ::= 'mov'|'push'|'pop'|'call'|'ret'|'add'|'mul'|'div'|'jmp'|'cmp'|'jl'|‘halt’
<operand> ::= <identifier>|<number>|<register>
<number> ::= <addrhex>|<memhex>
<addrhex> ::= <hexadecimal number up to ADDR_MAX>
<memhex> ::= <hexadecimal number up to MEM_MAX>
<register> ::= 'ac'|'cr'|'dr'|'br'
```
### Семантика
| mnemonic | purpose |     example |
|:---------|:-------:|------------:|
| mov      |  Title  | Here's this |
| push     |  Text   |    And more |
| pop      |  Text   |    And more |
| call     |  Text   |    And more |
| ret      |  Text   |    And more |
| add      |  Text   |    And more |
| mul      |  Text   |    And more |
| div      |  Text   |    And more |
| jmp      |  Text   |    And more |
| cmp      |  Text   |    And more |
| jl       |  Text   |    And more |
| halt     |  Text   |    And more |


- Область видимости -- пояснить
- Типизация -- пояснить

## Организация памяти
- Работа с переменными/константами:
  - пример с mov
  - ? псведоинструкции
- Модель памяти
  - Гарвардская архитектура --> память неоднородная
  - Память команд. Машинное слово нефиксированно (cisc).
  - Память данных. Машинное слово 32 бита, знаковое/беззнаковое
  - Адрес памяти 12 бит (?)
  - Регистры общего назначения: ac, cr, dr, br
## Система команд
Мнемоника ассемблера совпадает с мнемоникой машинного слова (согласно варианту машинное слово имеет вид struct).
- Для памяти данных машинное слово 32 бита, может быть как знаковым, так и беззнаковым
- 