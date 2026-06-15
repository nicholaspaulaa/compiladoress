"""Parser de erros do compilador simplesc.

O simplesc emite erros no formato:
    phase:line:column: message

Exemplos:
    lexer:3:15: Caractere invalido.
    parser:12:1: Esperado ';'.
    semantic:8:5: Identificador 'x' nao declarado.
    codegen:5:1: Erro interno na geracao de codigo.

Este modulo converte essas linhas (e fallbacks) em objetos estruturados
para consumo pelo frontend (marcacao de linha/coluna no editor).
"""

import re
from typing import TypedDict


class CompileError(TypedDict):
    phase: str
    line: int
    column: int
    message: str


# Fases reconhecidas pelo compilador
_VALID_PHASES = frozenset({"lexer", "parser", "semantic", "codegen", "compiler"})

# Regex: captura phase:line:col: message
#   grupo 1: phase  (letras)
#   grupo 2: line   (digitos)
#   grupo 3: column (digitos)
#   grupo 4: message (resto da linha)
_LINE_ERROR_RE = re.compile(r"^(\w+):(\d+):(\d+):\s*(.+)$")

# Fallback: linhas que começam com "error:" ou "erro:" (case-insensitive)
_FALLBACK_RE = re.compile(r"^(?:error|erro)[:\s-]+(.+)$", re.IGNORECASE)


def parse_error_line(line: str) -> CompileError | None:
    """Converte uma linha de stderr do simplesc em erro estruturado.

    Args:
        line: Uma linha da saida de erro do simplesc.

    Returns:
        Dicionario com phase/line/column/message ou None se nao reconhecer o formato.
    """
    line = line.strip()
    if not line:
        return None

    # Formato principal: phase:line:col: message
    match = _LINE_ERROR_RE.match(line)
    if match:
        phase = match.group(1)
        return CompileError(
            phase=phase if phase in _VALID_PHASES else "unknown",
            line=int(match.group(2)),
            column=int(match.group(3)),
            message=match.group(4),
        )

    # Fallback: linhas genericas de erro
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
    """Parseia todo o stderr do simplesc em uma lista de erros estruturados.

    Args:
        stderr_text: Texto completo da saida de erro do subprocesso.

    Returns:
        Lista de CompileError. Se nenhum erro for parseavel, retorna
        lista vazia (o chamador deve decidir se usa fallback generico).
    """
    errors: list[CompileError] = []
    for line in stderr_text.splitlines():
        parsed = parse_error_line(line)
        if parsed is not None:
            errors.append(parsed)
    return errors


def fallback_error(message: str) -> CompileError:
    """Cria um erro generico para casos onde o parsing falha.

    Args:
        message: Mensagem de erro bruta (ex: timeout, binario nao encontrado).

    Returns:
        CompileError com phase='unknown' e line/column=0.
    """
    return CompileError(
        phase="unknown",
        line=0,
        column=0,
        message=message,
    )
