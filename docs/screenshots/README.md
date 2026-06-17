# Instruções para captura de screenshots/GIFs

Este diretório contém as imagens referenciadas no [README.md](../README.md).

## Imagens necessárias

| Arquivo | Conteúdo | Como capturar |
|---------|----------|---------------|
| `01-login.png` | Tela de login com Supabase Auth | Acesse `http://localhost/login`, tire screenshot da tela de login |
| `02-editor-nasm.png` | Editor Monaco + painel NASM após compilar | Escreva código SIMPLES, clique Compilar, capture os dois painéis (editor + NASM) |
| `03-terminal-execution.png` | Terminal xterm.js após executar programa | Após compilar, execute o programa e capture o terminal com output |
| `00-full-flow.gif` | GIF animado do fluxo completo | Grave: login → escrever código → compilar → ver NASM → executar |

## Código de exemplo para screenshots

```simples
programa
  inteiro x;
  leia(x);
  escreva("O dobro de ", x, " e ", x * 2);
fim
```

### Como gerar o GIF

**Opção 1 — ScreenToGif (Windows, gratuito)**
1. Baixe [ScreenToGif](https://www.screentogif.com/)
2. Abra o Simples Editor em `http://localhost`
3. Grave o fluxo completo (login → código → compilar → executar)
4. Salve como `00-full-flow.gif` neste diretório

**Opção 2 — Peek (Linux, gratuito)**
```bash
peek --output docs/screenshots/00-full-flow.gif
```
Selecione a janela do navegador e execute o fluxo.

**Opção 3 — OBS Studio → converter para GIF**
1. Grave com OBS, exporte como MP4
2. Converta: `ffmpeg -i gravacao.mp4 -vf "fps=10,scale=800:-1:flags=lanczos" 00-full-flow.gif`

## Observações

- Use resolução 1280x720 ou 1920x1080 para consistência
- PNG para screenshots estáticos, GIF para animações
- Não inclua dados sensíveis (emails reais, tokens) nas imagens
- Oculte a barra de endereços se contiver tokens JWT
