# Pinterest na Kobo

Um site leve, sem nada pesado, que mostra pastas escolhidas do Pinterest numa grade de fotos.
Ao tocar numa foto, ela abre grande, com botões de anterior e próxima e um link pra foto original na resolução máxima.

As fotos ficam **copiadas aqui no repositório**. Por isso o site continua funcionando mesmo se um pin sumir do Pinterest.

## Como funciona

- `pastas.txt`: a lista de pastas, com um link por linha.
- O robô (GitHub Actions) baixa só os pins que ainda não tem e refaz as páginas.
- O Cloudflare Pages publica a pasta `site/` sempre que o robô salva algo novo.

## Configurar (uma vez só)

1. **Repositório**: suba estes arquivos num repositório novo do GitHub, incluindo a pasta `.github`.
2. **Primeira rodada**: abra a aba **Actions**, escolha **Atualizar fotos** e toque em **Run workflow**.
   A primeira vez demora mais, porque baixa as pastas inteiras.
3. **Cloudflare Pages**: vá em Workers & Pages › Create › Pages › Connect to Git e escolha o repositório.
   - Build command: *(deixe vazio)*
   - Build output directory: `site`
4. **Botão "Buscar pins novos"** (opcional, mas é o que permite atualizar direto pela Kobo):
   - No GitHub, vá em Settings › Developer settings › Fine-grained tokens › Generate new token.
     Dê acesso só a este repositório e marque a permissão **Actions: Read and write**.
   - No Cloudflare Pages, abra o projeto e vá em Settings › Variables and Secrets. Adicione:
     - `GITHUB_TOKEN`: o token (marque como *Secret*)
     - `GITHUB_REPO`: `lauraferrarini/NOME-DO-REPOSITORIO`
   - Faça um novo deploy (Deployments › Retry deployment).
5. **Na Kobo**: Configurações › Recursos beta › Navegador. Abra o endereço do site e salve nos favoritos.

## Uso no dia a dia

- **Puxar pins novos**: toque em **Buscar pins novos** no site, ou em **Run workflow** no GitHub.
  Em alguns minutos as fotos novas aparecem.
- **Adicionar uma pasta**: cole o link dela em `pastas.txt` e salve. O robô roda sozinho.
- **Tirar uma pasta**: apague a linha em `pastas.txt` e apague a pasta dela dentro de `site/fotos/`.

## Bom saber

- Seções de uma pasta viram subpastas no site.
- Vídeos entram como a imagem de capa.
- O site fica aberto pra quem tiver o endereço. As pastas já são públicas, mas o link não aparece em lugar nenhum.
- Se o robô falhar logo na primeira rodada, abra o registro em Actions e veja a mensagem.
  O mais provável é o Pinterest ter bloqueado o acesso vindo do GitHub.
