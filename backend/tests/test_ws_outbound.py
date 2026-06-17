"""Testes da fila de envio WS (thread-safe, issue #29)."""

import json
import queue
import threading
import time

from ws_run import WsOutbound


class FakeWs:
    def __init__(self):
        self.connected = True
        self.sent: list[str] = []

    def send(self, data: str) -> None:
        self.sent.append(data)


def test_outbound_flushes_from_main_thread_immediately():
    ws = FakeWs()
    outbound = WsOutbound(ws)
    outbound.enqueue({"type": "compile_started"})
    assert len(ws.sent) == 1
    assert json.loads(ws.sent[0])["type"] == "compile_started"


def test_outbound_background_thread_only_sends_on_main_flush():
    ws = FakeWs()
    outbound = WsOutbound(ws)
    barrier = threading.Barrier(2)

    def worker():
        barrier.wait()
        outbound.enqueue({"type": "exec_started"})
        outbound.enqueue({"type": "stdout", "data": "42\n"})

    thread = threading.Thread(target=worker)
    thread.start()
    barrier.wait()
    time.sleep(0.05)
    assert ws.sent == []

    outbound.flush()
    thread.join(timeout=2)

    assert len(ws.sent) == 2
    assert json.loads(ws.sent[0])["type"] == "exec_started"
    assert json.loads(ws.sent[1])["data"] == "42\n"
