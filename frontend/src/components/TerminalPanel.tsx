import { FitAddon } from "@xterm/addon-fit";
import { Terminal } from "@xterm/xterm";
import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
} from "react";

import { xtermFontFamily, xtermTheme } from "../lib/terminal/xtermTheme";
import { IdePanel } from "./IdePanel";

import "@xterm/xterm/css/xterm.css";

const WELCOME_MESSAGE =
  "> terminal SIMPLES — pronto para stdout/stdin (sprint 4)\r\n";

export interface TerminalPanelHandle {
  write: (data: string) => void;
  writeln: (data: string) => void;
  clear: () => void;
  focus: () => void;
}

interface TerminalPanelProps {
  onInput?: (data: string) => void;
}

export const TerminalPanel = forwardRef<TerminalPanelHandle, TerminalPanelProps>(
  function TerminalPanel({ onInput }, ref) {
    const hostRef = useRef<HTMLDivElement>(null);
    const terminalRef = useRef<Terminal | null>(null);
    const fitAddonRef = useRef<FitAddon | null>(null);
    const onInputRef = useRef(onInput);

    useEffect(() => {
      onInputRef.current = onInput;
    }, [onInput]);

    useImperativeHandle(ref, () => ({
      write: (data: string) => {
        terminalRef.current?.write(data);
      },
      writeln: (data: string) => {
        terminalRef.current?.writeln(data);
      },
      clear: () => {
        terminalRef.current?.clear();
      },
      focus: () => {
        terminalRef.current?.focus();
      },
    }));

    useEffect(() => {
      const host = hostRef.current;
      if (!host) {
        return;
      }

      const terminal = new Terminal({
        theme: xtermTheme,
        fontFamily: xtermFontFamily,
        fontSize: 14,
        lineHeight: 1.25,
        cursorBlink: true,
        cursorStyle: "block",
        scrollback: 2000,
        convertEol: true,
      });

      const fitAddon = new FitAddon();
      terminal.loadAddon(fitAddon);
      terminal.open(host);
      fitAddon.fit();
      terminal.write(WELCOME_MESSAGE);

      const dataDisposable = terminal.onData((data) => {
        onInputRef.current?.(data);
      });

      const resizeObserver = new ResizeObserver(() => {
        fitAddon.fit();
      });
      resizeObserver.observe(host);

      terminalRef.current = terminal;
      fitAddonRef.current = fitAddon;

      return () => {
        resizeObserver.disconnect();
        dataDisposable.dispose();
        terminal.dispose();
        terminalRef.current = null;
        fitAddonRef.current = null;
      };
    }, []);

    return (
      <IdePanel
        label="> TERMINAL"
        ariaLabel="Painel terminal"
        className="ide-terminal-panel"
      >
        <div className="terminal-panel">
          <div
            ref={hostRef}
            className="terminal-panel__host"
            id="terminal-host"
            role="region"
            aria-label="Area do terminal interativo"
          />
        </div>
      </IdePanel>
    );
  },
);
