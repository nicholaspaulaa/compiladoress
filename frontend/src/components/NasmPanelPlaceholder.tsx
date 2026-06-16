import { IdePanel } from "./IdePanel";

const NASM_PLACEHOLDER = `; NASM x32 sera exibido aqui
; apos compilar o codigo SIMPLES.

section .text
  ; aguardando compilacao...
`;

export function NasmPanelPlaceholder() {
  return (
    <IdePanel label="> NASM x32" ariaLabel="Painel NASM">
      <div className="ide-nasm-placeholder">
        <pre className="ide-nasm-placeholder__code">{NASM_PLACEHOLDER}</pre>
        <p className="ide-nasm-placeholder__hint retro-subtitle">
          painel read-only — sprint 2
        </p>
      </div>
    </IdePanel>
  );
}
