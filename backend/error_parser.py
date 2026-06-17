"""Parser de erros do compilador simplesc.

O simplesc emite erros no formato:
    phase:line:column: message

Exemplos:
    lexer:3:15: Caractere invalido.
    parser:12:1: Esperado ';'.
    semantic:8:5: Identificador 'x' nao declarado.
    codegen:5:1: Erro interno na geracao de codigo.
"""

import re
from typing import TypedDict


class CompileError(TypedDict, total=False):
    phase: str
    line: int
    column: int
    message: str
    limit_s: int  # opcional — incluido apenas em erros de timeout


_VALID_PHASES = frozenset(
    {"lexer", "parser", "semantic", "codegen", "compile_timeout", "compiler", "server",
     "nasm", "ld", "assemble", "link"}
)

_LINE_ERROR_RE = re.compile(r"^(\w+):(\d+):(\d+):\s*(.+)$")
_FALLBACK_RE = re.compile(r"^(?:error|erro)[:\s-]+(.+)$", re.IGNORECASE)


def parse_error_line(line: str) -> CompileError | None:
    """Converte uma linha de stderr do simplesc em erro estruturado."""
    line = line.strip()
    if not line:
        return None

    match = _LINE_ERROR_RE.match(line)
    if match:
        phase = match.group(1)
        return CompileError(
            phase=phase if phase in _VALID_PHASES else "unknown",
            line=int(match.group(2)),
            column=int(match.group(3)),
            message=match.group(4),
        )

    match = _FALLBACK_RE.match(line)
    if match:
        return CompileError(
            phase="unknown",
            line=0,
            column=0,
            message=match.group(1),
        )

    return None


def parse_errors(stderr_text: str) -> list[CompileError]:
    """Parseia todo o stderr do simplesc em uma lista de erros estruturados."""
    errors: list[CompileError] = []
    for line in stderr_text.splitlines():
        parsed = parse_error_line(line)
        if parsed is not None:
            errors.append(parsed)
    return errors


def make_error(
    phase: str,
    message: str,
    line: int = 0,
    column: int = 0,
    limit_s: int | None = None,
) -> CompileError:
    """Cria um erro estruturado para falhas do servidor (timeout, binario ausente, etc.).

    Args:
        phase: Fase do erro (lexer, parser, semantic, codegen, compile_timeout, compiler, server).
        message: Mensagem descritiva do erro.
        line, column: Coordenadas opcionais (padrao 0).
        limit_s: Limite de segundos para erros de timeout (opcional).
    """
    err: CompileError = CompileError(
        phase=phase if phase in _VALID_PHASES else "unknown",
        line=line,
        column=column,
        message=message,
    )
    if limit_s is not None:
        err["limit_s"] = limit_s
    return err
