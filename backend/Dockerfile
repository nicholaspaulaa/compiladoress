FROM python:3.11-slim

WORKDIR /app

# ============================================================
# Toolchain i386 — necessário para montar e linkar o código
# Assembly NASM 32-bit gerado pelo compilador simplesc.
#   - nasm: assembler (fonte .asm → objeto .o)
#   - binutils-i686-linux-gnu: linker ld com suporte a elf_i386
#     (o ld nativo do Debian multiarch não inclui o emulador i386)
# ============================================================
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nasm \
        binutils-i686-linux-gnu \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py auth.py app.py .

EXPOSE 5000

CMD ["python", "app.py"]
