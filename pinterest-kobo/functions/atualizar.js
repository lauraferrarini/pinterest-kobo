// Botão "Buscar pins novos" do site: pede pro GitHub rodar o robô.
// Precisa de duas variáveis no Cloudflare Pages (Settings > Variables and Secrets):
//   GITHUB_TOKEN  -> token do GitHub com permissão "Actions: Read and write" neste repositório
//   GITHUB_REPO   -> ex.: lauraferrarini/pinterest-kobo
// Opcional: GITHUB_BRANCH (padrão: main)

const pagina = (titulo, texto) => new Response(
  `<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>${titulo}</title>
<style>body{font-family:sans-serif;font-size:22px;padding:24px;color:#000;background:#fff}
a{display:inline-block;padding:12px 18px;border:2px solid #000;border-radius:8px;color:#000;text-decoration:none}</style>
</head><body><h1>${titulo}</h1><p>${texto}</p><p><a href="/">‹ Voltar</a></p></body></html>`,
  { headers: { "content-type": "text/html; charset=utf-8" } },
);

export async function onRequestPost({ env }) {
  if (!env.GITHUB_TOKEN || !env.GITHUB_REPO) {
    return pagina("Falta configurar", "O botão ainda não foi ligado ao GitHub (faltam as variáveis GITHUB_TOKEN e GITHUB_REPO no Cloudflare).");
  }
  const r = await fetch(
    `https://api.github.com/repos/${env.GITHUB_REPO}/actions/workflows/atualizar.yml/dispatches`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "pinterest-kobo",
      },
      body: JSON.stringify({ ref: env.GITHUB_BRANCH || "main" }),
    },
  );
  if (r.status === 204) {
    return pagina("Pedido enviado!", "O robô está buscando os pins novos. Em alguns minutos eles aparecem no site — é só voltar e recarregar a página.");
  }
  return pagina("Não deu certo", `O GitHub respondeu com o código ${r.status}. Confira se o token ainda é válido.`);
}

export function onRequestGet() {
  return new Response(null, { status: 302, headers: { Location: "/" } });
}
