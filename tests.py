# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=line-too-long
import io
import os
import tempfile
import pytest
import logging

import translator
import machine
import contextlib


@pytest.mark.golden_test('golden/*.yml')
def test_echo_golden(golden, caplog):
    caplog.set_level(logging.DEBUG)

    with tempfile.TemporaryDirectory() as tmp_dir:
        target: str = os.path.join(tmp_dir, 'output.txt')
        input_stream: str = os.path.join(tmp_dir, 'input.txt')
        result_file: str = os.path.join(tmp_dir, 'cpu.txt')

        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden["input"])

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main(file=golden['source'], target=target)
            print("============================================================")
            machine.main(code_file=target, res_file=result_file, input_file=input_stream)

        with open(target, encoding="utf-8") as file:
            code = file.read()

        assert code == golden.out["code"]
        assert stdout.getvalue() == golden.out["output"]
        assert caplog.text == golden.out["log"]





