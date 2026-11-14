import subprocess
import sys

def converter_legado(caminho_arquivo_rpg: str):
    pasta_poc = r"D:\Workspace\01-Products\mega-rag-clean"
    script_atual = r"src\legacy-bridge\rpgle_chunker.py"
    print(f"Iniciando conversão do arquivo: {caminho_arquivo_rpg}...")
    try:
        resultado = subprocess.run(
            ["python", script_atual, caminho_arquivo_rpg],
            cwd=pasta_poc, capture_output=True, text=True, check=True,
        )
        print("\n✅ CONVERSÃO CONCLUÍDA COM SUCESSO!")
        print(resultado.stdout)
    except subprocess.CalledProcessError as e:
        print("\n❌ ERRO NO ATLAS PIPELINE:")
        print(e.stderr)
    except FileNotFoundError:
        print("\n❌ ERRO: O arquivo RPGLE ou o script não foi encontrado.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        converter_legado(sys.argv[1])
    else:
        print("Uso correto: python cli_converter.py <caminho_do_arquivo.cbl>")
