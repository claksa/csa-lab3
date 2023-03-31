# csa-lab3

- Павлова Полина `P33102`
- `asm | cisc | harv | hw | tick | struct | stream | mem | prob2`

## Язык программирования
### Синтаксис
``` ebnf
<label> ::= <identifier>：
<identifier> ::= <letter>|<identifier> <letter>
<comment> ::= ; <identifier>
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
| mnemonic        |                                                 purpose                                                 |             example |
|:----------------|:-------------------------------------------------------------------------------------------------------:|--------------------:|
| mov dest src    | move data between registers, load immediate data into registers, move data between registers and memory |            mov ac 4 |
| push src        |           insert a value onto the stack.  Useful for passing arguments, saving registers, etc           |              push 4 |
| pop  dest       |                                     remove topmost value from stack                                     |              pop bp |
| call func       |                    push the address of the next instruction and start executing func                    |          call print |
| ret             |                    pop the return program counter, and jump there. Ends a subroutine                    |                 ret |
| add dest, src   |                                            dest = dest + src                                            |          add ac, dr |
| mul   src       |                      multiplay acc and src as unsigned integers, put result on acc                      |              mul dr |
| div   src       |                            divide acc by src: ratio --> acc, reminder --> dr                            |              dic dr |
| jmp   label     |                       goto the instruction label: . skip anything else in the way                       |            jmp loop |
| sub   dest, src |                                             dest = dest-src                                             |           sub ac, 4 |
| jl    label     |                                   goto label if previous comparison <                                   | jl loop ; if ac < 4 |
| halt            |                                              stop running                                               |                halt |


- Область видимости в ассемблере единая; типизации как таковой не существует 

## Организация памяти
- Работа с переменными/константами:
  - команды, работающие с переменными: см. mov, ld, push, pop etc
- Модель памяти
  - Гарвардская архитектура --> память неоднородная
  - Память команд. Машинное слово нефиксированно (cisc).
  - Память данных. Машинное слово 32 бита, знаковое/беззнаковое
  - Адрес памяти 12 бит
  - Регистры общего назначения:
    - ac -- accumulator register: values are returned from functions in this register
    - cr -- scratch register, counter
    - dr -- scratch register, for data read from mem
    - br -- preserved register
## Система команд
Мнемоника ассемблера и машинных слов совпадают (согласно варианту машинное слово имеет небинарное (struct)).
- Для памяти данных машинное слово 32 бита, может быть как знаковым, так и беззнаковым
- В cisc архитектуре системы команд для памяти команд машинное слово нефиксированной длины (1-3 слово):
  - 1 слово -- 16-битный адрес команды
  - 2, 3 слова -- указатели на операнды

### Кодирование инструкций
- Машинный код сериализуется в список JSON
- Адрес команды -- индекс списка

Инструкции и данные кодируются по-разному:

```json
[
    {
        "mem": "instr",
        "opcode": "mov",
        "operands": ["1", "0x4"],
        "term": [2, "0x01"]
    },
  
    {
    "mem": "data",
    "data": 44
    }
]
```
где:
- `mem` -- тип памяти: команд/переменных;
- `opcode` -- строка с кодом операции;
- `data` -- данные, хранящиеся в ячейке памяти
- `operands` -- массив операндов переменной длины: 0-2;

## Транслятор
< тут должно быть описание процесса трансляции>
## Модель процессора
описание
### DataPath
### ControlUnit

## Тестирование