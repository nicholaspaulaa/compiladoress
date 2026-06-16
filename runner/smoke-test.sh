#!/usr/bin/env bash
# smoke-test-runner.sh
# Smoke test para validar a imagem simples-runner executando um hello-world i386.
#
# PRD RF05 — "binários i386 não rodam nativamente em ARM64; qemu-user-static emula".
# Este script:
#   1. Constrói um hello-world ELF i386 mínimo (syscall write + exit via int 0x80)
#   2. Executa-o dentro do container simples-runner via qemu-i386-static
#   3. Verifica a saída "Hello, i386!" no stdout
#
# Pré-requisitos:
#   - Docker (com suporte a multi-arch / qemu)
#   - nasm, i686-linux-gnu-ld (ou ld -m elf_i386 em x86_64)

set -euo pipefail

RUNNER_IMAGE="${RUNNER_IMAGE:-simples-runner:latest}"
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

echo "=== Smoke test: simples-runner com qemu-user-static ==="
echo "  Imagem:  $RUNNER_IMAGE"
echo "  Tempdir: $TMPDIR"

# --- 1. Montar hello-world i386 (syscall write + exit via int 0x80) ---
cat > "$TMPDIR/hello.asm" <<'EOF'
section .data
    msg db "Hello, i386!", 10      ; 10 = '\n'
    len equ $ - msg

section .text
    global _start

_start:
    ; write(1, msg, len)
    mov eax, 4      ; sys_write
    mov ebx, 1      ; fd = stdout
    mov ecx, msg    ; buf
    mov edx, len    ; count
    int 0x80

    ; exit(0)
    mov eax, 1      ; sys_exit
    mov ebx, 0      ; exit code
    int 0x80
EOF

echo "  -> Montando hello.asm com nasm..."
nasm -f elf32 "$TMPDIR/hello.asm" -o "$TMPDIR/hello.o"

echo "  -> Linkando com ld (elf_i386)..."
if command -v i686-linux-gnu-ld &>/dev/null; then
    i686-linux-gnu-ld -m elf_i386 "$TMPDIR/hello.o" -o "$TMPDIR/hello"
elif ld -m elf_i386 --verbose 2>&1 | grep -q "elf_i386"; then
    ld -m elf_i386 "$TMPDIR/hello.o" -o "$TMPDIR/hello"
else
    # Fallback: ld pode funcionar como cross-linker em alguns sistemas
    ld -m elf_i386 "$TMPDIR/hello.o" -o "$TMPDIR/hello" 2>/dev/null || {
        echo "ERRO: linker elf_i386 nao disponivel (instale binutils-i686-linux-gnu)"
        exit 1
    }
fi

echo "  -> Verificando arquitetura do binário..."
file "$TMPDIR/hello"

# --- 2. Executar no container ---
echo ""
echo "  -> Executando hello-world dentro de $RUNNER_IMAGE..."

OUTPUT=$(docker run --rm \
    --network=none \
    --read-only \
    --memory=128m \
    --cpus=0.5 \
    --pids-limit=64 \
    --cap-drop=ALL \
    --user=65534:65534 \
    -v "$TMPDIR:/sandbox:ro" \
    "$RUNNER_IMAGE" \
    /usr/bin/qemu-i386-static /sandbox/hello 2>&1)

# --- 3. Verificar ---
echo ""
if [ "$OUTPUT" = "Hello, i386!" ]; then
    echo "✅ PASS — saída correta: '$OUTPUT'"
    echo "Smoke test concluído com sucesso!"
    exit 0
else
    echo "❌ FAIL — saída esperada 'Hello, i386!', obtida: '$OUTPUT'"
    exit 1
fi
