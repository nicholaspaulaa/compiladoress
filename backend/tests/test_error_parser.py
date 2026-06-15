from error_parser import make_error, parse_error_line, parse_errors


def test_parse_lexer_error():
    result = parse_error_line("lexer:3:15: Caractere invalido.")
    assert result == {
        "phase": "lexer",
        "line": 3,
        "column": 15,
        "message": "Caractere invalido.",
    }


def test_parse_semantic_error():
    result = parse_error_line("semantic:8:5: Identificador 'x' nao declarado.")
    assert result["phase"] == "semantic"
    assert result["line"] == 8
    assert result["column"] == 5


def test_unknown_phase_normalized():
    result = parse_error_line("custom:1:1: algo errado")
    assert result["phase"] == "unknown"


def test_fallback_error_line():
    result = parse_error_line("error: falha generica")
    assert result == {
        "phase": "unknown",
        "line": 0,
        "column": 0,
        "message": "falha generica",
    }


def test_parse_errors_multiline():
    stderr = "lexer:1:1: erro A\nparser:2:3: erro B\nlinha ignorada\n"
    errors = parse_errors(stderr)
    assert len(errors) == 2
    assert errors[0]["phase"] == "lexer"
    assert errors[1]["phase"] == "parser"


def test_make_error_server_phase():
    err = make_error("server", "timeout")
    assert err["phase"] == "server"
    assert err["message"] == "timeout"
