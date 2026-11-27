"""Baixa os pins novos de cada pasta listada em pastas.txt e gera o site.

Usa o gallery-dl, que pega as fotos na resolução original e lembra o que já
foi baixado (em dados/baixados.sqlite3), então cada rodada só baixa o que é novo.
"""
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def ler_links():
    links = []
    for linha in (RAIZ / "pastas.txt").read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#"):
            links.append(linha)
    return links


def main():
    links = ler_links()
    if not links:
        print("pastas.txt está vazio — nada pra baixar.")

    falhas = []
    for link in links:
        print(f"\n=== {link} ===", flush=True)
        r = subprocess.run(
            [sys.executable, "-m", "gallery_dl", "-c", "gallery-dl.conf", link],
            cwd=RAIZ,
        )
        # Código diferente de 0 = algo deu errado (pode ser só uma foto, ou a pasta toda).
        if r.returncode != 0:
            falhas.append((link, r.returncode))

    (RAIZ / "dados").mkdir(exist_ok=True)
    agora = datetime.now(ZoneInfo("America/Manaus")).strftime("%d/%m/%Y %H:%M")
    with open(RAIZ / "dados" / "ultima-atualizacao.txt", "w", encoding="utf-8") as f:
        f.write(f"{agora}\n")
        for link, cod in falhas:
            f.write(f"aviso: {link} terminou com código {cod}\n")

    subprocess.run([sys.executable, str(RAIZ / "scripts" / "gerar_site.py")], check=True)

    if falhas:
        print("\nAvisos:")
        for link, cod in falhas:
            print(f"  {link} -> código {cod}")
    fotos = RAIZ / "site" / "fotos"
    tem_fotos = fotos.exists() and any(p.is_file() for p in fotos.rglob("*"))
    if links and not tem_fotos:
        print("Nenhuma foto foi baixada. Veja as mensagens acima.")
        sys.exit(1)


if __name__ == "__main__":
    main()
