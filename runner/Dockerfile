# simples-runner — sandbox mínima para executar binários ELF i386
# Usa qemu-user-static para emulação uniforme em hosts x86_64 e ARM64.
#
# Como é invocada pelo backend:
#   docker run --rm --network=none --read-only \
#     --memory=128m --cpus=0.5 --pids-limit=64 \
#     --cap-drop=ALL --user=65534:65534 \
#     -v /tmp/sim-<uuid>:/sandbox:ro \
#     simples-runner:latest /usr/bin/qemu-i386-static /sandbox/programa

FROM debian:12-slim

# qemu-user-static permite executar binários x86 32-bit em hosts x86_64 e ARM64
# (em x86_64 a emulação é redundante, mas o overhead é desprezível e mantém
#  uma única imagem de runner para os dois alvos)
RUN apt-get update && apt-get install -y --no-install-recommends \
      qemu-user-static \
    && rm -rf /var/lib/apt/lists/*

# Usuário não-root para execução
RUN useradd -u 65534 -M -s /usr/sbin/nologin sandbox || true

USER 65534:65534
WORKDIR /sandbox
