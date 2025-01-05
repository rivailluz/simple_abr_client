import os
import pandas as pd
import matplotlib.pyplot as plt

BB_RESULTS_DIR = "/app/results/results_bb"
STALLION_RESULTS_DIR = "/app/results/results_stallion"

BB_GRAPHS_DIR = "/app/graphs/graphs_bb"
STALLION_GRAPHS_DIR = "/app/graphs/graphs_stallion"

COMPARATIVE_GRAPHS_DIR = "/app/graphs/graphs_comparative"

# Criar diretório para gráficos comparativos
if not os.path.exists(COMPARATIVE_GRAPHS_DIR):
    os.makedirs(COMPARATIVE_GRAPHS_DIR)

def load_data(results_dir):
    data = []
    for log_file in os.listdir(results_dir):
        log_path = os.path.join(results_dir, log_file)

        try:
            df = pd.read_csv(
                log_path,
                names=[
                    "algorithm",
                    "time_stamp",
                    "bit_rate",
                    "buffer_size",
                    "rebuffer_time",
                    "chunk_size",
                    "download_time",
                    "throughput",
                ],
                sep=",",
                engine="python",
            )
            data.append(df)
        except Exception as e:
            print(f"Erro ao ler {log_file}: {e}")
            continue

    return pd.concat(data, ignore_index=True) if data else pd.DataFrame()

def generate_comparative_graphs(bb_data, stallion_data):
    # Bitrate Comparison
    plt.figure()
    plt.plot(bb_data["time_stamp"], bb_data["bit_rate"], label="BB Bitrate (Kbps)")
    plt.plot(stallion_data["time_stamp"], stallion_data["bit_rate"], label="Stallion Bitrate (Kbps)", linestyle="--")
    plt.xlabel("Time (s)")
    plt.ylabel("Bitrate (Kbps)")
    plt.title("Comparação de Bitrate: BB vs Stallion")
    plt.legend()
    plt.savefig(os.path.join(COMPARATIVE_GRAPHS_DIR, "comparative_bitrate.png"))
    plt.close()

    # Buffer Size Comparison
    plt.figure()
    plt.plot(bb_data["time_stamp"], bb_data["buffer_size"], label="BB Buffer Size (s)")
    plt.plot(stallion_data["time_stamp"], stallion_data["buffer_size"], label="Stallion Buffer Size (s)", linestyle="--")
    plt.xlabel("Time (s)")
    plt.ylabel("Buffer Size (s)")
    plt.title("Comparação de Tamanho do Buffer: BB vs Stallion")
    plt.legend()
    plt.savefig(os.path.join(COMPARATIVE_GRAPHS_DIR, "comparative_buffer.png"))
    plt.close()

    # Rebuffering Comparison
    plt.figure()
    plt.plot(bb_data["time_stamp"], bb_data["rebuffer_time"].cumsum(), label="BB Rebuffer Time (s)")
    plt.plot(stallion_data["time_stamp"], stallion_data["rebuffer_time"].cumsum(), label="Stallion Rebuffer Time (s)", linestyle="--")
    plt.xlabel("Time (s)")
    plt.ylabel("Cumulative Rebuffer Time (s)")
    plt.title("Comparação de Rebuffering: BB vs Stallion")
    plt.legend()
    plt.savefig(os.path.join(COMPARATIVE_GRAPHS_DIR, "comparative_rebuffering.png"))
    plt.close()

def main():
    print("Carregando dados do Buffer-Based Algorithm...")
    bb_data = load_data(BB_RESULTS_DIR)

    print("Carregando dados do Stallion Algorithm...")
    stallion_data = load_data(STALLION_RESULTS_DIR)

    if bb_data.empty or stallion_data.empty:
        print("Dados insuficientes para gerar gráficos comparativos.")
        return

    print("Gerando gráficos comparativos...")
    generate_comparative_graphs(bb_data, stallion_data)
    print("Gráficos comparativos gerados com sucesso em 'graphs_comparative'.")

if __name__ == "__main__":
    main()
