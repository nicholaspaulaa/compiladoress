# ============================================================
# Stage 1: Build simplesc compiler from C source
# ============================================================
FROM ubuntu:22.04 AS compiler-builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        nasm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/compiler

COPY compiler/ .

RUN make clean && make all

# Record compiler version for health checks
RUN echo "simplesc $(date -u +%Y-%m-%d) $(uname -m)" > /tmp/compiler-version.txt

# ============================================================
# Stage 2: Backend runtime with Python + simplesc
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# Copy simplesc binary and version info from build stage
COPY --from=compiler-builder /tmp/compiler/build/simplesc /usr/local/bin/simplesc
COPY --from=compiler-builder /tmp/compiler-version.txt /usr/local/bin/simplesc-version.txt

# Make sure it's executable and in PATH
RUN chmod +x /usr/local/bin/simplesc && \
    /usr/local/bin/simplesc 2>&1 || true

# Toolchain i386 — nasm + linker para fases futuras (nasm/ld no mesmo container)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nasm \
        binutils-i686-linux-gnu \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/config.py backend/auth.py backend/app.py backend/compile.py backend/error_parser.py backend/execution.py backend/metrics.py backend/pipeline.py backend/ws_auth.py backend/ws_bridge.py backend/ws_protocol.py backend/ws_run.py .

EXPOSE 5000

CMD ["python", "app.py"]
